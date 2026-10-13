import re

# Patrones Paraguay / DNIT
RE_RUC = re.compile(r"\bRUC\s*[:\-]?\s*(\d{4,10})\s*[-–]?\s*(\d)\b", re.I)
RE_TIMBRADO = re.compile(r"TIMBRADO\s*(?:N[°ºo]\.?|NRO\.?)?\s*[:\-]?\s*(\d{7,10})", re.I)
RE_COMPROBANTE = re.compile(r"\b(\d{3})\s*[-–]\s*(\d{3})\s*[-–]\s*(\d{7})\b")
RE_FECHA = re.compile(r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b")
RE_MONTO = re.compile(r"([\d\.]+,\d{2}|\d[\d,\.]*\d)")

def parse_py_number(s: str) -> float:
    """'1.234.567' -> 1234567. Acepta coma decimal."""
    s = s.strip().replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        # sin coma: puntos son miles
        if s.count(".") > 1 or ("." in s and len(s.split(".")[-1]) == 3):
            s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return 0.0

def extract_entities(text: str) -> dict:
    out: dict = {"ruc_emisor": "", "dv": "", "timbrado": "", "nro_comprobante": "",
                 "fecha": "", "grav10": 0.0, "grav5": 0.0, "exenta": 0.0, "total": 0.0}
    m = RE_RUC.search(text)
    if m:
        out["ruc_emisor"], out["dv"] = m.group(1), m.group(2)
    m = RE_TIMBRADO.search(text)
    if m:
        out["timbrado"] = m.group(1)
    m = RE_COMPROBANTE.search(text)
    if m:
        out["nro_comprobante"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = RE_FECHA.search(text)
    if m:
        out["fecha"] = m.group(1).replace("-", "/")
    # Desglose por etiquetas (tolerante)
    for label, key in [("GRAVAD?A?S?\\s*10\\s*%?", "grav10"), ("GRAVAD?A?S?\\s*5\\s*%?", "grav5"),
                       ("EXENT", "exenta"), ("TOTAL", "total")]:
        mm = re.search(label + r"[^0-9]*(" + RE_MONTO.pattern + r")", text, re.I)
        if mm:
            out[key] = parse_py_number(mm.group(1))
    return out

def iva_credito(grav10: float, grav5: float) -> tuple[float, float]:
    """Retorna (iva10, iva5) incluidos en el precio: total/11 y total/21."""
    return round(grav10 / 11, 2), round(grav5 / 21, 2)
