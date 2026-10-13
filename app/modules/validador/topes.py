"""Control de topes Ley 6380/19: alertas en tiempo real por rubro/periodo."""
from collections import defaultdict

# Topes configurables (montos ejemplo — ajustar por reglamentación vigente)
TOPES_ANUAL = {
    "ESPARCIMIENTO": 20_000_000,
    "VEHICULO": 100_000_000,
    "INMUEBLE": None,  # condicional, no monto fijo
}

def chequear_topes(acumulado_por_rubro: dict[str, float], nuevo_rubro: str, nuevo_monto: float) -> list[str]:
    alertas: list[str] = []
    rubro = (nuevo_rubro or "").upper()
    tope = TOPES_ANUAL.get(rubro)
    if tope:
        proyectado = acumulado_por_rubro.get(rubro, 0) + nuevo_monto
        if proyectado > tope:
            alertas.append(f"{rubro}: proyectado Gs. {proyectado:,.0f} supera tope Gs. {tope:,.0f}")
        elif proyectado > tope * 0.8:
            alertas.append(f"{rubro}: al 80% del tope ({proyectado:,.0f}/{tope:,.0f})")
    if rubro == "INMUEBLE":
        alertas.append("INMUEBLE: verificar escritura y condición de deducibilidad IRP")
    return alertas
