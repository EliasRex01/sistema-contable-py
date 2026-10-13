import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from playwright.async_api import async_playwright
from app.modules.rpa.browser import launch_browser

async def main():
    async with async_playwright() as p:
        b = await launch_browser(p, headless=True)
        pg = await (await b.new_context(viewport={"width": 1100, "height": 800})).new_page()
        for url, name in [("http://127.0.0.1:8000/", "panel"),
                          ("http://127.0.0.1:8000/cargar", "cargar"),
                          ("http://127.0.0.1:8000/clientes-ui", "clientes"),
                          ("http://127.0.0.1:8000/rg90-ui", "rg90")]:
            await pg.goto(url, wait_until="domcontentloaded", timeout=20000)
            await pg.wait_for_timeout(800)
            await pg.screenshot(path=f"uploads/ui_{name}.png")
            print(name, "OK")
        await b.close()

asyncio.run(main())
