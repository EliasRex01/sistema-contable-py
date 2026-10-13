from pydantic import BaseModel, Field

class ClienteIn(BaseModel):
    ruc: str = Field(pattern=r"^\d{4,10}$")
    dv: str = Field(pattern=r"^\d$")
    razon_social: str
    obligaciones: str = "211,715"
    dnit_user: str
    dnit_pass: str
    familiares: list[str] = []

class ProveedorIn(BaseModel):
    ruc: str
    razon_social: str = ""
    rubro: str
    deducible_irp: bool = True

class ComprobanteRevision(BaseModel):
    ruc_emisor: str = ""
    razon_emisor: str = ""
    timbrado: str = ""
    nro_comprobante: str = ""
    fecha: str = ""
    grav10: float = 0
    grav5: float = 0
    exenta: float = 0
    total: float = 0
    rubro: str = ""
