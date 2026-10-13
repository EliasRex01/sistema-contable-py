import json
from sqlalchemy.orm import Session
from app.db import models
from app.core.security import encrypt_secret

def crear_cliente(db: Session, data) -> models.Cliente:
    c = models.Cliente(
        ruc=data.ruc, dv=data.dv, razon_social=data.razon_social,
        obligaciones=data.obligaciones, dnit_user=data.dnit_user,
        dnit_pass_enc=encrypt_secret(data.dnit_pass),
        familiares=json.dumps(data.familiares or []),
    )
    db.add(c); db.commit(); db.refresh(c)
    return c

def upsert_proveedor(db: Session, ruc: str, razon: str, rubro: str, deducible: bool = True):
    p = db.get(models.ProveedorRubro, ruc)
    if p:
        p.razon_social = razon; p.rubro = rubro; p.deducible_irp = deducible
    else:
        p = models.ProveedorRubro(ruc=ruc, razon_social=razon, rubro=rubro, deducible_irp=deducible)
        db.add(p)
    db.commit(); return p
