"""Lanzador Playwright con fallback a navegadores del sistema.

En redes donde cdn.playwright.dev está bloqueado no se puede descargar
Chromium; si hay Chrome/Edge instalado se usa vía `channel`.
"""
async def launch_browser(p, headless: bool = False):
    try:
        return await p.chromium.launch(
            headless=headless, args=["--disable-blink-features=AutomationControlled"])
    except Exception as e:
        if "Executable doesn't exist" not in str(e):
            raise
    for channel in ("chrome", "msedge"):
        try:
            return await p.chromium.launch(
                headless=headless, channel=channel,
                args=["--disable-blink-features=AutomationControlled"])
        except Exception:
            continue
    raise RuntimeError("Sin Chromium descargado ni Chrome/Edge del sistema "
                       "(ejecutar: python -m playwright install chromium)")
