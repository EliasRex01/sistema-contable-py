from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.modules.clientes.schemas import ComprobanteRevision
from app.modules.validador.timbrado import validar_formato_local
from app.modules.validador.clasificador import clasificar
from app.modules.validador.topes import chequear_topes

router = APIRouter(prefix="/comprobantes", tags=["comprobantes"])

def _autoclasificar(db: Session, r: models.Comprobante, total: float) -> dict:
    cli = db.get(models.Cliente, r.cliente_id)
    prov = db.get(models.ProveedorRubro, r.ruc_emisor) if r.ruc_emisor else None
    cls = clasificar(r.ruc_emisor or "", prov.rubro if prov else None,
                     cli.obligaciones if cli else "211,715", total)
    r.rubro = cls["rubro"]
    return cls

@router.get("/{cliente_id}")
def listar(cliente_id: int, db: Session = Depends(get_db)):
    rows = db.query(models.Comprobante).filter_by(cliente_id=cliente_id).order_by(models.Comprobante.id.desc()).all()
    return [{"id": r.id, "ruc_emisor": r.ruc_emisor, "razon": r.razon_emisor, "nro": r.nro_comprobante,
             "fecha": r.fecha, "total": float(r.total), "rubro": r.rubro, "estado": r.estado,
             "imagen": r.imagen_path, "fuente": r.fuente} for r in rows]

@router.put("/{comp_id}/revision")
def revision(comp_id: int, data: ComprobanteRevision, db: Session = Depends(get_db)):
    r = db.get(models.Comprobante, comp_id)
    if not r:
        raise HTTPException(404, "No existe")
    ok, msg = validar_formato_local(data.ruc_emisor, data.timbrado, data.nro_comprobante)
    if not ok:
        raise HTTPException(422, msg)
    for k, v in data.model_dump().items():
        setattr(r, k, v)
    cli = db.get(models.Cliente, r.cliente_id)
    prov = db.get(models.ProveedorRubro, data.ruc_emisor)
    cls = clasificar(data.ruc_emisor, prov.rubro if prov else None, cli.obligaciones if cli else "211,715", data.total)
    r.rubro = cls["rubro"]
    r.estado = "VALIDADO"
    db.commit()
    # topes: acumulado simple del periodo por rubro
    acum = {}
    for x in db.query(models.Comprobante).filter_by(cliente_id=r.cliente_id, estado="VALIDADO").all():
        acum[x.rubro] = acum.get(x.rubro, 0) + float(x.total)
    alertas = chequear_topes(acum, r.rubro, 0)  # ya incluido
    if cls["alerta_tope"]:
        alertas.append(cls["alerta_tope"])
    return {"ok": True, "rubro": r.rubro, "clasificacion": cls, "alertas": alertas}

@router.post("/{comp_id}/rechazar")
def rechazar(comp_id: int, db: Session = Depends(get_db)):
    r = db.get(models.Comprobante, comp_id)
    if not r:
        raise HTTPException(404, "No existe")
    r.estado = "RECHAZADO"; db.commit()
    return {"ok": True}

# --- ABM ---

@router.post("/{cliente_id}", tags=["comprobantes"])
def alta(cliente_id: int, data: ComprobanteRevision, db: Session = Depends(get_db)):
    """Alta manual de comprobante (queda PENDIENTE, rubro auto)."""
    if not db.get(models.Cliente, cliente_id):
        raise HTTPException(404, "Cliente no existe")
    r = models.Comprobante(cliente_id=cliente_id, fuente="MANUAL", **data.model_dump())
    r.estado = "PENDIENTE"
    _autoclasificar(db, r, data.total)
    db.add(r); db.commit(); db.refresh(r)
    return {"ok": True, "id": r.id, "rubro": r.rubro}

@router.put("/{comp_id}", tags=["comprobantes"])
def modificacion(comp_id: int, data: ComprobanteRevision, db: Session = Depends(get_db)):
    """Modificación libre de datos (no cambia estado)."""
    r = db.get(models.Comprobante, comp_id)
    if not r:
        raise HTTPException(404, "No existe")
    for k, v in data.model_dump().items():
        setattr(r, k, v)
    _autoclasificar(db, r, data.total)
    db.commit()
    return {"ok": True, "id": r.id, "rubro": r.rubro}

@router.delete("/{comp_id}", tags=["comprobantes"])
def baja(comp_id: int, db: Session = Depends(get_db)):
    r = db.get(models.Comprobante, comp_id)
    if not r:
        raise HTTPException(404, "No existe")
    db.delete(r); db.commit()
    return {"ok": True}

@router.post("/{cliente_id}/desde-imagen", tags=["comprobantes"])
def desde_imagen(cliente_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Foto/upload → nitidez → ¿es comprobante? → OCR → borrador PENDIENTE.

    Si la imagen no está clara, o no pertenece a un comprobante válido,
    retorna el aviso sin procesar ni guardar nada.
    """
    import os
    from app.modules.ingestion.calidad import evaluar_imagen
    if not db.get(models.Cliente, cliente_id):
        raise HTTPException(404, "Cliente no existe")
    os.makedirs("uploads", exist_ok=True)
    dest = os.path.join("uploads", file.filename or "foto.jpg")
    with open(dest, "wb") as out:
        out.write(file.file.read())
    cal = evaluar_imagen(dest)
    if not cal["nitida"]:
        return {"ok": False, "codigo": "IMAGEN_BORROSA", "calidad": cal,
                "mensaje": "La imagen no está muy clara: " + " ".join(cal["mensajes"])}
    from app.worker.tasks import process_file
    try:
        res = process_file.delay(dest, cliente_id)
        creado = res.get(timeout=120)
    except Exception:
        creado = process_file(dest, cliente_id)
    if not creado.get("ok", True):
        creado["calidad"] = cal
        return creado
    creado["calidad"] = cal
    return {"ok": True, **creado}
