"""Clasificador deducibilidad IVA/IRP + topes Ley 6380/19 (alertas)."""
RUBRO_MAP = {
    "SUPERMERCADO": ("ALIMENTACION", True),
    "FARMACIA": ("SALUD", True),
    "CLINICA": ("SALUD", True),
    "COMBUSTIBLE": ("VEHICULO", True),  # tope
    "VEHICULO": ("VEHICULO", True),
    "INMUEBLE": ("INMUEBLE", True),
    "ESPACIMIENTO": ("ESPARCIMIENTO", True),  # tope legal
}

TOPES_MSG = {
    "ESPARCIMIENTO": "Tope esparcimiento Ley 6380/19: verificar límite deducible",
    "VEHICULO": "Tope vehículos: verificar plafond reglamentario",
    "INMUEBLE": "Inmueble: verificar condiciones de deducibilidad",
}

def clasificar(ruc_emisor: str, rubro_db: str | None, obligaciones: str, total: float) -> dict:
    rubro, deducible = RUBRO_MAP.get((rubro_db or "").upper(), ("OTROS", True))
    es_iva = "211" in obligaciones
    es_irp = "715" in obligaciones
    credito_iva = deducible and es_iva
    egreso_irp = deducible and es_irp
    alerta = TOPES_MSG.get(rubro)
    return {"rubro": rubro, "credito_iva": credito_iva, "egreso_irp": egreso_irp,
            "alerta_tope": alerta or ""}
