"""HITL: abre Chrome visible, el usuario resuelve el captcha, el script captura el resultado."""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from playwright.async_api import async_playwright
from app.modules.rpa.browser import launch_browser

BASE = "https://servicios.set.gov.py/eset-publico"
RUC = sys.argv[1] if len(sys.argv) > 1 else "5290956"

async def token_present(pg) -> bool:
    v = await pg.eval_on_selector("textarea[name=g-recaptcha-response]", "e => e.value || ''")
    return len(v) > 20

async def main():
    async with async_playwright() as p:
        b = await launch_browser(p, headless=False)  # ventana visible
        pg = await (await b.new_context(locale="es-PY")).new_page()
        await pg.goto(f"{BASE}/perfilPublicoContribIService.do", wait_until="domcontentloaded", timeout=45000)
        await pg.wait_for_timeout(2000)
        await pg.fill("input[name=ruc]", RUC)
        print("ACCIÓN USUARIO: marque 'No soy un robot' en la ventana Chrome (120s)...")
        for _ in range(60):
            await pg.wait_for_timeout(2000)
            if await token_present(pg):
                break
        else:
            print("TIMEOUT: captcha no resuelto"); await b.close(); return
        print("Captcha OK, consultando...")
        await pg.click("text=Búsqueda")
        await pg.wait_for_timeout(6000)
        print(f"== PERFIL {RUC}:")
        print((await pg.inner_text("body"))[:2500])
        await pg.screenshot(path="uploads/perfil_humano.png")
        await b.close()

asyncio.run(main())
