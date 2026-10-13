from app.worker.celery_app import celery_app

@celery_app.task(name="ocr.process_file")
def process_file(path: str, cliente_id: int = 0) -> dict:
    """Procesa archivo y persiste Comprobante PENDIENTE. Retorna entidades."""
    import os
    from app.db.session import SessionLocal
    from app.db import models
    from app.modules.ingestion import pipeline, regex_py

    fuente, data = "OCR", {}
    low = path.lower()
    if low.endswith(".xml"):
        from app.modules.ingestion.xml_sifen import parse_sifen_xml
        data = parse_sifen_xml(path); fuente = "XML"
    elif low.endswith(".pdf"):
        text = pipeline.pdf_text_native(path)
        if len(text.strip()) < 50:
            text = "[PDF escaneado: rasterizar + ocr_image pendiente]"
        data = regex_py.extract_entities(text)
    else:
        img = pipeline.preprocess_voucher(path)
        data = regex_py.extract_entities(pipeline.ocr_image(img))
    if cliente_id:
        db = SessionLocal()
        try:
            c = models.Comprobante(cliente_id=cliente_id, fuente=fuente, imagen_path=path,
                ruc_emisor=data.get("ruc_emisor", ""), razon_emisor=data.get("razon_emisor", ""),
                timbrado=data.get("timbrado", ""), nro_comprobante=data.get("nro_comprobante", ""),
                fecha=data.get("fecha", ""), grav10=data.get("grav10", 0) or 0,
                grav5=data.get("grav5", 0) or 0, exenta=data.get("exenta", 0) or 0,
                total=data.get("total", 0) or 0, estado="PENDIENTE")
            # XML trae razon con otra clave
            if not c.razon_emisor:
                c.razon_emisor = str(data.get("razon_emisor", "") or "")
            # Automatización: clasifica rubro/deducibilidad al ingresar
            from app.modules.validador.clasificador import clasificar
            cli = db.get(models.Cliente, cliente_id)
            prov = db.get(models.ProveedorRubro, c.ruc_emisor) if c.ruc_emisor else None
            cls = clasificar(c.ruc_emisor or "", prov.rubro if prov else None,
                             cli.obligaciones if cli else "211,715", float(c.total or 0))
            c.rubro = cls["rubro"]
            db.add(c); db.commit(); db.refresh(c)
            return {"id": c.id, "fuente": fuente, "rubro": c.rubro,
                    "credito_iva": cls["credito_iva"], "egreso_irp": cls["egreso_irp"],
                    **{k: str(v) for k, v in data.items()}}
        finally:
            db.close()
    return {"fuente": fuente, **data}
