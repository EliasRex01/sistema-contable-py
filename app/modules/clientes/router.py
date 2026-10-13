from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.modules.clientes.schemas import ClienteIn, ProveedorIn
from app.modules.clientes.service import crear_cliente, upsert_proveedor
from app.core.security import encrypt_secret
import json

router = APIRouter(prefix="/clientes", tags=["clientes"])

@router.post("")
def crear(data: ClienteIn, db: Session = Depends(get_db)):
    c = crear_cliente(db, data)
    return {"id": c.id, "ruc": c.ruc}

@router.get("")
def listar(db: Session = Depends(get_db)):
    return [{"id": c.id, "ruc": c.ruc, "razon": c.razon_social, "oblig": c.obligaciones}
            for c in db.query(models.Cliente).all()]

@router.post("/proveedores")
def clasificar_proveedor(data: ProveedorIn, db: Session = Depends(get_db)):
    upsert_proveedor(db, data.ruc, data.razon_social, data.rubro, data.deducible_irp)
    return {"ok": True}

@router.get("/proveedores")
def listar_prov(db: Session = Depends(get_db)):
    return [{"ruc": p.ruc, "rubro": p.rubro, "deducible": p.deducible_irp}
            for p in db.query(models.ProveedorRubro).all()]

@router.put("/{cliente_id}")
def modificar(cliente_id: int, data: ClienteIn, db: Session = Depends(get_db)):
    c = db.get(models.Cliente, cliente_id)
    if not c:
        raise HTTPException(404, "Cliente no existe")
    c.ruc, c.dv, c.razon_social = data.ruc, data.dv, data.razon_social
    c.obligaciones, c.dnit_user = data.obligaciones, data.dnit_user
    c.dnit_pass_enc = encrypt_secret(data.dnit_pass)
    c.familiares = json.dumps(data.familiares or [])
    db.commit()
    return {"ok": True, "id": c.id}

@router.delete("/{cliente_id}")
def eliminar(cliente_id: int, db: Session = Depends(get_db)):
    c = db.get(models.Cliente, cliente_id)
    if not c:
        raise HTTPException(404, "Cliente no existe")
    n = db.query(models.Comprobante).filter_by(cliente_id=cliente_id).count()
    if n:
        raise HTTPException(409, f"Tiene {n} comprobantes; bórrelos primero")
    db.delete(c); db.commit()
    return {"ok": True}
