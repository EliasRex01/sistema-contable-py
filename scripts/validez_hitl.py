"""HITL validez de documento electrónico (factura KuDE)."""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from playwright.async_api import async_playwright
from app.modules.rpa.browser import launch_browser

async def token_ok(pg) -> bool:
    v = await pg.eval_on_selector("textarea[name=g-recaptcha-response]", "e => e.value || ''")
    return len(v) > 20

async def main():
    async with async_playwright() as p:
        b = await launch_browser(p, headless=False)
        pg = await (await b.new_context(locale="es-PY")).new_page()
        await pg.goto("https://servicios.set.gov.py/eset-publico/consultarValidezDocumentos.do",
                      wait_until="domcontentloaded", timeout=45000)
        await pg.wait_for_timeout(3000)
        await pg.fill("input[name=ruc]", "5290956")
        await pg.fill("input[name=dv]", "5")
        await pg.eval_on_selector("input[name=ruc]", "e => e.blur()")
        # nombre es readonly: forzar vía scope Angular (la lupa recorta el RUC)
        await pg.evaluate("""() => {
            const el = document.querySelector('input[name=nombre]');
            el.removeAttribute('readonly');
            const scope = angular.element(el).scope();
            scope.vm.datos.nombre = 'ZARACHO OVIEDO LUCAS HERNAN';
            scope.$apply();
        }""")
        await pg.wait_for_timeout(500)
        ruc_val = await pg.eval_on_selector("input[name=ruc]", "e => e.value")
        if ruc_val != "5290956":  # reponer si algún binding lo alteró
            await pg.fill("input[name=ruc]", "5290956")
            await pg.eval_on_selector("input[name=ruc]", "e => e.blur()")
        print("ruc:", await pg.eval_on_selector("input[name=ruc]", "e => e.value"))
        print("nombre:", await pg.eval_on_selector("input[name=nombre]", "e => e.value"))
        await pg.select_option("select[name=tipoTimbrado]", index=5)
        await pg.wait_for_timeout(1500)
        await pg.fill("input[name=numeroTimbrado]", "18156046")
        await pg.select_option("select[name=tipoDocumento]", label="FACTURA ELECTRONICA")
        await pg.fill("input[name=establecimiento]", "003")
        await pg.fill("input[name=puntoExpedicion]", "001")
        await pg.fill("input[name=nroSecuencia]", "0001274")
        # fechaExpedicion: tecleo real para que Angular bindee el modelo
        await pg.click("input[placeholder='Elegir Fecha']")
        await pg.keyboard.press("ControlOrMeta+a")
        await pg.keyboard.type("05/10/2026", delay=60)
        await pg.keyboard.press("Tab")
        await pg.wait_for_timeout(1000)
        print("fecha:", await pg.evaluate(
            "() => [...document.querySelectorAll('input')].find(e => !e.name && e.type !== 'hidden').value"))
        print("ACCIÓN USUARIO: marque 'No soy un robot' en la ventana Chrome (120s)...")
        for _ in range(60):
            await pg.wait_for_timeout(2000)
            if await token_ok(pg):
                break
        else:
            print("TIMEOUT: captcha no resuelto"); await b.close(); return
        print("Captcha OK, consultando documento...")
        try:
            from playwright_stealth import stealth_async
            await stealth_async(pg)
        except Exception:
            pass
        async with pg.expect_response("**/*.do*", timeout=30000) as resp_info:
            await pg.click("text=Consultar Comprobante")
        try:
            resp = await resp_info.value
            print("HTTP POST ->", resp.status, resp.url[:120])
        except Exception as e:
            print("sin respuesta POST:", str(e)[:150])
        await pg.wait_for_timeout(7000)
        for i, pgx in enumerate(pg.context.pages):
            print(f"-- pestaña[{i}]: {pgx.url[:130]}")
        last = pg.context.pages[-1]
        print("== VALIDEZ resultado:")
        print((await last.inner_text("body"))[:2500])
        await last.screenshot(path="uploads/validez_result.png")
        await b.close()

asyncio.run(main())
