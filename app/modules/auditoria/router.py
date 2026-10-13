"""Pantalla auditoría: izquierda imagen factura, derecha datos extraídos."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models

router = APIRouter(prefix="/auditoria", tags=["auditoria"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/{cliente_id}", response_class=HTMLResponse)
def pantalla(request: Request, cliente_id: int, db: Session = Depends(get_db)):
    rows = db.query(models.Comprobante).filter_by(cliente_id=cliente_id).order_by(models.Comprobante.id.desc()).limit(50).all()
    return templates.TemplateResponse(request, "auditoria.html", {"activa": "auditoria", "rows": rows, "cliente_id": cliente_id})
