"""Generador TXT tabulado RG90 Compras.
NOTA: estructura simplificada y configurable. Validar contra manual DNIT vigente
antes de presentar: orden de columnas y tipos de comprobante pueden cambiar.
"""
from dataclasses import dataclass

@dataclass
class RG90Row:
    ruc_emisor: str
    razon: str
    timbrado: str
    nro: str  # 000-000-0000000
    fecha: str  # DD/MM/YYYY
    grav10: float
    grav5: float
    exenta: float
    total: float

def to_txt(rows: list[RG90Row], sep: str = "\t") -> str:
    lines = []
    for r in rows:
        cols = [r.ruc_emisor, r.razon, r.timbrado, r.nro, r.fecha,
                f"{r.grav10:.2f}", f"{r.grav5:.2f}", f"{r.exenta:.2f}", f"{r.total:.2f}"]
        lines.append(sep.join(cols))
    return "\n".join(lines) + ("\n" if lines else "")
