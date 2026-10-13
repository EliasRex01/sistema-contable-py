"""¿La imagen/texto corresponde a un comprobante fiscal válido?

Un comprobante válido (factura, recibo, pagaré, nota de crédito/débito,
autofactura, boleta) trae marcadores fiscales: RUC del emisor, timbrado,
numeración 000-000-0000000, fecha y montos. Si el texto extraído no los
tiene, se responde "La imagen no pertenece a un comprobante válido"
en vez de guardar datos basura.
"""
import re

PALABRAS_CLAVE = [
    "factura", "recibo", "pagaré", "pagare", "nota de crédito", "nota de credito",
    "nota de débito", "nota de debito", "notacredito", "autofactura", "boleta",
    "nota de remisión", "nota de remision", "comprobante de retención",
    "comprobante de retencion", "timbrado", "ruc", "kude", "kuatia",
]

MENSAJE_NO_VALIDO = "La imagen no pertenece a un comprobante válido"


def es_comprobante(texto: str, entidades: dict) -> dict:
    txt = (texto or "").lower()
    tiene_palabra = any(p in txt for p in PALABRAS_CLAVE)
    tiene_ruc = bool(entidades.get("ruc_emisor"))
    tiene_timbrado = bool(entidades.get("timbrado"))
    tiene_nro = bool(entidades.get("nro_comprobante"))
    tiene_fecha = bool(entidades.get("fecha"))
    tiene_monto = any(float(entidades.get(k) or 0) > 0
                      for k in ("grav10", "grav5", "exenta", "total"))
    # Regla: RUC + (timbrado o numeración) + (fecha o monto o palabra clave)
    es_valido = (tiene_ruc and (tiene_timbrado or tiene_nro)
                 and (tiene_fecha or tiene_monto or tiene_palabra))
    faltantes: list[str] = []
    if not tiene_ruc:
        faltantes.append("RUC del emisor")
    if not (tiene_timbrado or tiene_nro):
        faltantes.append("timbrado o número de comprobante")
    if not (tiene_fecha or tiene_monto or tiene_palabra):
        faltantes.append("fecha, montos o tipo de documento")
    return {"es_valido": es_valido, "tiene_palabra": tiene_palabra,
            "tiene_ruc": tiene_ruc, "tiene_timbrado": tiene_timbrado,
            "tiene_nro": tiene_nro, "tiene_fecha": tiene_fecha,
            "tiene_monto": tiene_monto, "faltantes": faltantes,
            "mensaje": "" if es_valido else
                       f"{MENSAJE_NO_VALIDO} (falta: {', '.join(faltantes)})"}
