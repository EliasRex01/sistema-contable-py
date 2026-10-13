"""Panel web: dashboard + páginas de ingesta y RG 90 (dueño de las vistas HTML)."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.modules.rpa.captcha import captcha_status

router = APIRouter(tags=["panel"])
templates = Jinja2Templates(directory="app/templates")

def _stats(db: Session) -> dict:
    por_estado = dict(db.query(models.Comprobante.estado, func.count(models.Comprobante.id))
                      .group_by(models.Comprobante.estado).all())
    total_val = db.query(func.coalesce(func.sum(models.Comprobante.total), 0))\
        .filter_by(estado="VALIDADO").scalar() or 0
    return {
        "clientes": db.query(func.count(models.Cliente.id)).scalar() or 0,
        "pendientes": por_estado.get("PENDIENTE", 0),
        "validados": por_estado.get("VALIDADO", 0),
        "rechazados": por_estado.get("RECHAZADO", 0),
        "total_validado": float(total_val),
        "lotes": db.query(models.LoteRG90).order_by(models.LoteRG90.id.desc()).limit(5).all(),
        "ultimos": db.query(models.Comprobante).order_by(models.Comprobante.id.desc()).limit(8).all(),
    }

@router.get("/", response_class=HTMLResponse)
def panel(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request, "dashboard.html", {"activa": "panel", "s": _stats(db), "captcha": captcha_status()})

@router.get("/ingesta-ui", response_class=HTMLResponse)
def ingesta_ui(request: Request):
    return templates.TemplateResponse(request, "ingesta.html", {"activa": "ingesta"})

@router.get("/comprobantes-ui", response_class=HTMLResponse)
def comprobantes_ui(request: Request):
    return templates.TemplateResponse(request, "comprobantes.html", {"activa": "comprobantes"})

@router.get("/cargar", response_class=HTMLResponse)
def cargar(request: Request):
    return templates.TemplateResponse(request, "cargar.html", {"activa": "cargar"})

@router.get("/clientes-ui", response_class=HTMLResponse)
def clientes_ui(request: Request):
    return templates.TemplateResponse(request, "clientes.html", {"activa": "clientes"})

@router.get("/rg90-ui", response_class=HTMLResponse)
def rg90_ui(request: Request):
    return templates.TemplateResponse(request, "rg90.html", {"activa": "rg90"})
