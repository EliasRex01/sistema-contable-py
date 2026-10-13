import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from playwright.async_api import async_playwright
from app.modules.rpa.browser import launch_browser

async def t():
    p = await async_playwright().start()
    b = await launch_browser(p, headless=True)
    pg = await b.new_page()
    await pg.goto("about:blank")
    print("BROWSER OK:", b.version)
    await b.close()
    await p.stop()

asyncio.run(t())
