"""Seed demo: cliente + proveedor + 2 comprobantes para ver la UI."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.db.session import SessionLocal
from app.db import models
from app.modules.clientes.service import crear_cliente, upsert_proveedor
from types import SimpleNamespace

db = SessionLocal()
cli = db.query(models.Cliente).filter_by(ruc="80012345").first()
if not cli:
    cli = crear_cliente(db, SimpleNamespace(
        ruc="80012345", dv="1", razon_social="TEST SA", obligaciones="211,715",
        dnit_user="test", dnit_pass="test", familiares=["1234567"]))
    print("cliente creado:", cli.id)
else:
    print("cliente existe:", cli.id)

upsert_proveedor(db, "80099999", "SUPER DEMO SA", "SUPERMERCADO", True)

if not db.query(models.Comprobante).filter_by(cliente_id=cli.id).first():
    for i, (nro, g10, g5, exe, tot) in enumerate([
        ("001-002-0001234", 1100000, 210000, 0, 1310000),
        ("001-002-0001235", 550000, 0, 100000, 650000),
    ]):
        db.add(models.Comprobante(
            cliente_id=cli.id, fuente="OCR", imagen_path="",
            ruc_emisor="80099999", razon_emisor="SUPER DEMO SA",
            timbrado="1234567890", nro_comprobante=nro, fecha="15/03/2026",
            grav10=g10, grav5=g5, exenta=exe, total=tot, estado="PENDIENTE"))
    db.commit()
    print("comprobantes demo creados")
else:
    print("comprobantes ya existen")
