"""Extractor prioritario: XML SIFEN / E-kuatia (100% limpio, sin OCR)."""
from lxml import etree

NS = {"s": "http://ekuatia.set.gov.py/sifen/xsd"}

def parse_sifen_xml(path: str) -> dict:
    tree = etree.parse(path)
    root = tree.getroot()
    def xp(expr: str) -> str:
        el = root.find(expr, NS)
        return (el.text or "").strip() if el is not None else ""
    # Rutas comunes SIFEN DE; tolera variantes sin namespace
    def any_tag(*names: str) -> str:
        for n in names:
            e = root.find(f".//{{*}}{n}")
            if e is not None and e.text:
                return e.text.strip()
        return ""
    return {
        "ruc_emisor": any_tag("dRucEm", "rucEmisor") or xp(".//s:dRucEm"),
        "razon_emisor": any_tag("dNomEmi", "dNomEm"),
        "timbrado": any_tag("dNumTim", "timbrado"),
        "nro_comprobante": _join_num(any_tag("dEst"), any_tag("dPunExp"), any_tag("dNumDoc")) or any_tag("dNumDoc"),
        "fecha": any_tag("dFecEmi", "fechaEmision"),
        "grav10": float(any_tag("dTotGrav10") or 0),
        "grav5": float(any_tag("dTotGrav5") or 0),
        "exenta": float(any_tag("dTotExenta") or 0),
        "total": float(any_tag("dTotGralOpe", "dTotGral") or 0),
    }

def _join_num(est: str, exp: str, num: str) -> str:
    if est and exp and num:
        return f"{est.zfill(3)}-{exp.zfill(3)}-{num.zfill(7)}"
    return num or ""
