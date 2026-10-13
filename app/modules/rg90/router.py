from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.modules.rg90.generator import to_txt, RG90Row

router = APIRouter(prefix="/rg90", tags=["rg90"])

def _rows(db: Session, cliente_id: int):
    return db.query(models.Comprobante).filter_by(cliente_id=cliente_id, estado="VALIDADO").all()

@router.get("/lotes/{cliente_id}")
def lotes(cliente_id: int, db: Session = Depends(get_db)):
    return [{"id": l.id, "periodo": l.periodo, "estado": l.estado, "lote_dnit": l.nro_lote_dnit}
            for l in db.query(models.LoteRG90).filter_by(cliente_id=cliente_id).order_by(models.LoteRG90.id.desc()).all()]

@router.get("/{cliente_id}/{periodo}", response_class=PlainTextResponse)
def exportar(cliente_id: int, periodo: str, db: Session = Depends(get_db)):
    rows = _rows(db, cliente_id)
    txt = to_txt([RG90Row(r.ruc_emisor, r.razon_emisor, r.timbrado, r.nro_comprobante, r.fecha,
                          float(r.grav10), float(r.grav5), float(r.exenta), float(r.total)) for r in rows])
    lote = models.LoteRG90(cliente_id=cliente_id, periodo=periodo, archivo_txt=txt)
    db.add(lote); db.commit()
    return txt

@router.post("/{cliente_id}/{periodo}/presentar")
def presentar(cliente_id: int, periodo: str, db: Session = Depends(get_db)):
    """Encola presentación RPA. Requiere MASTER_KEY y credenciales del cliente."""
    """Encola presentación RPA. Requiere MASTER_KEY y credenciales del cliente."""
    from app.core.security import decrypt_secret
    cli = db.get(models.Cliente, cliente_id)
    if not cli:
        return {"ok": False, "error": "Cliente no existe"}
    pwd = decrypt_secret(cli.dnit_pass_enc)
    # Ejecución diferida: en prod usar Celery; aquí retorno instructivo + stub async
    import asyncio
    from app.modules.rg90.marangatu_bot import presentar_rg90
    # Se genera el txt temporal para el bot
    rows = _rows(db, cliente_id)
    txt = to_txt([RG90Row(r.ruc_emisor, r.razon_emisor, r.timbrado, r.nro_comprobante, r.fecha,
                          float(r.grav10), float(r.grav5), float(r.exenta), float(r.total)) for r in rows])
    tmp = f"uploads/RG90_{cliente_id}_{periodo}.txt"
    open(tmp, "w", encoding="utf-8").write(txt)
    try:
        res = asyncio.run(presentar_rg90(cli.ruc, pwd, tmp, headless=True))
    except Exception as e:
        res = {"status": "ERROR", "nota": str(e)}
    lote = models.LoteRG90(cliente_id=cliente_id, periodo=periodo, archivo_txt=txt,
                           nro_lote_dnit=str(res.get("lote", "")), estado=res.get("status", "ERROR"))
    db.add(lote); db.commit()
    return {"ok": True, "resultado": res, "lote_id": lote.id}

@router.get("/lotes/{cliente_id}")
def lotes(cliente_id: int, db: Session = Depends(get_db)):
    return [{"id": l.id, "periodo": l.periodo, "estado": l.estado, "lote_dnit": l.nro_lote_dnit}
            for l in db.query(models.LoteRG90).filter_by(cliente_id=cliente_id).order_by(models.LoteRG90.id.desc()).all()]
