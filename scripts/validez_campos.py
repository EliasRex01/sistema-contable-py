"""Descubre campos de IDENTIFICACIÓN DOCUMENTO por cada tipo (sin enviar)."""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from playwright.async_api import async_playwright
from app.modules.rpa.browser import launch_browser

async def main():
    async with async_playwright() as p:
        b = await launch_browser(p, headless=True)
        pg = await (await b.new_context(locale="es-PY")).new_page()
        await pg.goto("https://servicios.set.gov.py/eset-publico/consultarValidezDocumentos.do",
                      wait_until="domcontentloaded", timeout=45000)
        await pg.wait_for_timeout(4000)
        opts = await pg.eval_on_selector_all("select[name=tipoTimbrado] option",
                                             "els => els.map(e => e.text.trim())")
        print("tipos:", opts)
        for i in range(len(opts)):
            await pg.select_option("select[name=tipoTimbrado]", index=i)
            await pg.wait_for_timeout(1500)
            fields = await pg.eval_on_selector_all(
                "input, select",
                "els => els.map(e => ({t: e.tagName, type: e.type || '', name: e.name || '', "
                "id: e.id || '', opts: e.tagName === 'SELECT' ? [...e.options].map(o => o.text.trim()).join('|') : ''}))")
            print(f"--- tipo[{i}] campos:")
            for f in fields:
                if f["name"] != "g-recaptcha-response":
                    print("   ", f)
        await b.close()

asyncio.run(main())
