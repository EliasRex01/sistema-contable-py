"""Inspecciona el input sin nombre: HTML y texto vecino."""
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
        info = await pg.evaluate("""() => {
            const els = [...document.querySelectorAll('input')].filter(e => !e.name && e.type !== 'hidden');
            return els.map(e => ({html: e.outerHTML.slice(0,300),
                parent: e.parentElement ? e.parentElement.innerText.slice(0,200) : '',
                prev: e.previousElementSibling ? e.previousElementSibling.outerHTML.slice(0,200) : ''}));
        }""")
        for i in info:
            print(i)
        await pg.screenshot(path="uploads/validez_elec.png")
        await b.close()

asyncio.run(main())
