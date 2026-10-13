import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from playwright.async_api import async_playwright
from app.modules.rpa.browser import launch_browser

async def main():
    async with async_playwright() as p:
        b = await launch_browser(p, headless=True)
        pg = await (await b.new_context(viewport={"width": 1100, "height": 800})).new_page()
        await pg.goto("http://127.0.0.1:8000/validador", wait_until="domcontentloaded", timeout=20000)
        await pg.wait_for_timeout(500)
        await pg.evaluate("bloquear(true, 'Consultando DNIT en headless… no cierres esta página (hasta ~2 min).')")
        await pg.wait_for_timeout(1200)
        await pg.screenshot(path="uploads/ui_spinner.png")
        print("spinner OK")
        await b.close()

asyncio.run(main())
