from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.db.session import get_db, engine
from app.db.session import Base
from app.db import models
from app.modules.clientes.router import router as clientes_router
from app.modules.comprobantes.router import router as comp_router
from app.modules.rg90.router import router as rg90_router
from app.modules.auditoria.router import router as aud_router
from app.modules.validador.router import router as val_router
from app.modules.dashboard.router import router as dash_router

import app.modules.clientes.service  # noqa
import app.worker.tasks  # noqa registra tarea celery

app = FastAPI(title="Sistema Contable IVA/IRP Paraguay (RG90/Marangatú)")
Base.metadata.create_all(bind=engine)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(clientes_router)
app.include_router(comp_router)
app.include_router(rg90_router)
app.include_router(aud_router)
app.include_router(val_router)
app.include_router(dash_router)

@app.post("/ingesta/{cliente_id}", tags=["ingesta"])
def ingesta(cliente_id: int, files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    import os
    from app.worker.tasks import process_file
    os.makedirs("uploads", exist_ok=True)
    jobs = []
    for f in files:
        dest = os.path.join("uploads", f.filename or "file")
        with open(dest, "wb") as out:
            out.write(f.file.read())
        # Encola con cliente para trazabilidad; eager si no hay Redis en dev
        try:
            jobs.append(process_file.delay(dest, cliente_id).id)
        except Exception:
            jobs.append(process_file(dest, cliente_id))
    return {"tasks": jobs}

@app.get("/health")
def health():
    return {"ok": True}
