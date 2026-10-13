from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.modules.clientes.schemas import ClienteIn, ProveedorIn
from app.modules.clientes.service import crear_cliente, upsert_proveedor

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
