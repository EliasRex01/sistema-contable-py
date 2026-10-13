"""Intento real: perfil RUC 5293956 + vigencia timbrado (sin clave)."""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from playwright.async_api import async_playwright
from app.modules.rpa.browser import launch_browser

BASE = "https://servicios.set.gov.py/eset-publico"

async def main():
    os.makedirs("uploads", exist_ok=True)
    async with async_playwright() as p:
        b = await launch_browser(p, headless=True)
        pg = await (await b.new_context(locale="es-PY")).new_page()

        # 1) PERFIL
        await pg.goto(f"{BASE}/perfilPublicoContribIService.do", wait_until="domcontentloaded", timeout=45000)
        await pg.wait_for_timeout(3000)
        await pg.fill("input[name=ruc]", "5293956")
        await pg.screenshot(path="uploads/perfil_form.png")
        await pg.click("text=Búsqueda")
        await pg.wait_for_timeout(6000)
        print("== PERFIL resultado:")
        print(((await pg.inner_text("body"))[:2000]))
        await pg.screenshot(path="uploads/perfil_result.png")

        # 2) VIGENCIA (preimpresos)
        await pg.goto(f"{BASE}/consultarVigenciaTimbradoIService.do", wait_until="domcontentloaded", timeout=45000)
        await pg.wait_for_timeout(3000)
        await pg.fill("input[name=ruc]", "5293956")
        await pg.select_option("select[name=medio]", index=2)
        await pg.click("text=Búsqueda")
        await pg.wait_for_timeout(6000)
        print("== VIGENCIA resultado:")
        print(((await pg.inner_text("body"))[:2000]))
        await pg.screenshot(path="uploads/vigencia_result.png")
        await b.close()

asyncio.run(main())
