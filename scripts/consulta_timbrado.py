"""Exploración pública DNIT sin clave: perfil RUC + formularios de timbrado."""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from playwright.async_api import async_playwright
from app.modules.rpa.browser import launch_browser

BASE = "https://servicios.set.gov.py/eset-publico"
RUC, DV = "5293956", "5"

async def dump_fields(page, tag):
    print(f"--- {tag}: URL={page.url}")
    inputs = await page.eval_on_selector_all(
        "input, select, textarea",
        "els => els.map(e => ({tag: e.tagName, type: e.type || '', name: e.name || '', "
        "id: e.id || '', placeholder: e.placeholder || '', text: (e.innerText || '').slice(0,120)}))")
    for i in inputs:
        print("   ", i)
    btns = await page.eval_on_selector_all(
        "button, input[type=submit], input[type=button], a.btn",
        "els => els.map(e => (e.innerText || e.value || '').trim().slice(0,60))")
    print("    botones:", [b for b in btns if b][:10])
    body = (await page.inner_text("body"))[:1500]
    print("    texto:", " | ".join(body.splitlines())[:800])

async def main():
    os.makedirs("uploads", exist_ok=True)
    async with async_playwright() as p:
        b = await launch_browser(p, headless=True)
        ctx = await b.new_context(locale="es-PY")
        pg = await ctx.new_page()
        for slug, tag in [
            ("perfilPublicoContribIService.do", "PERFIL"),
            ("consultarVigenciaTimbradoIService.do", "VIGENCIA"),
            ("consultarValidezDocumentos.do", "VALIDEZ"),
        ]:
            try:
                await pg.goto(f"{BASE}/{slug}", wait_until="domcontentloaded", timeout=45000)
                await pg.wait_for_timeout(4000)
                await dump_fields(pg, tag)
                await pg.screenshot(path=f"uploads/consulta_{tag.lower()}.png")
            except Exception as e:
                print(f"--- {tag}: ERROR {type(e).__name__}: {str(e)[:200]}")
        await b.close()

asyncio.run(main())
