"""Etiquetas visibles de cada campo en DOCUMENTOS ELECTRONICOS."""
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
        await pg.select_option("select[name=tipoTimbrado]", index=5)
        await pg.wait_for_timeout(1500)
        rows = await pg.eval_on_selector_all(
            "input, select",
            """els => els.map(e => {
                const lbl = e.closest('div') ? e.closest('div').innerText.split('\\n')[0] : '';
                return {name: e.name || '(sin nombre)', id: e.id || '', label: lbl.slice(0,80)};
            })""")
        for r in rows:
            if r["name"] != "g-recaptcha-response":
                print(r)
        await b.close()

asyncio.run(main())
