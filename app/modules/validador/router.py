from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel
from app.modules.rpa.captcha import captcha_status

router = APIRouter(prefix="/validador", tags=["validador"])
templates = Jinja2Templates(directory="app/templates")

class PerfilIn(BaseModel):
    ruc: str

class ValidezIn(BaseModel):
    ruc: str = "5290956"
    dv: str = "5"
    nombre: str = "ZARACHO OVIEDO LUCAS HERNAN"
    tipo_idx: int = 5  # 1 PREIMPRESOS, 2 AUTOIMPRESORES, 5 ELECTRONICOS
    tipo_doc: str = "FACTURA ELECTRONICA"
    timbrado: str = "18156046"
    est: str = "003"
    punto: str = "001"
    sec: str = "0001274"
    fecha: str = "05/10/2026"

@router.get("", response_class=HTMLResponse)
def pagina(request: Request):
    return templates.TemplateResponse(
        request, "validador.html", {"activa": "validador", "captcha": captcha_status()})

@router.post("/perfil")
def perfil(data: PerfilIn):
    import asyncio
    from app.modules.validador.service import consultar_perfil
    from app.modules.validador.timbrado import validar_formato_local
    ok, msg = validar_formato_local(data.ruc, "1000000", "001-001-0000001")
    if not ok and "RUC" in msg:
        return {"ok": False, "codigo": "FORMATO", "mensaje": msg}
    return asyncio.run(consultar_perfil(data.ruc))

@router.post("/validez")
def validez(data: ValidezIn):
    import asyncio
    from app.modules.validador.service import consultar_validez
    return asyncio.run(consultar_validez(data.model_dump()))
