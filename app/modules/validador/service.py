"""Scraping headless de consultas públicas DNIT. Retorna solo la respuesta."""
import re

BASE = "https://servicios.set.gov.py/eset-publico"
TIPOS = {"PREIMPRESOS": 1, "AUTOIMPRESORES": 2, "MAQUINAS": 3,
         "VIRTUALES": 4, "ELECTRONICOS": 5}

async def _open(p):
    from app.modules.rpa.browser import launch_browser
    browser = await launch_browser(p, headless=True)
    ctx = await browser.new_context(locale="es-PY")
    page = await ctx.new_page()
    try:
        from playwright_stealth import stealth_async
        await stealth_async(page)
    except Exception:
        pass
    return browser, page


async def consultar_perfil(ruc: str) -> dict:
    from playwright.async_api import async_playwright
    from app.modules.rpa.captcha import ensure_captcha
    async with async_playwright() as p:
        browser, pg = await _open(p)
        try:
            await pg.goto(f"{BASE}/perfilPublicoContribIService.do",
                          wait_until="domcontentloaded", timeout=45000)
            await pg.wait_for_timeout(3000)
            await pg.fill("input[name=ruc]", ruc.strip())
            if not await ensure_captcha(pg):
                return {"ok": False, "codigo": "CAPTCHA_MANUAL",
                        "mensaje": "Captcha no resuelto automáticamente "
                                   "(configurar CAPTCHA_PROVIDER + CAPTCHA_API_KEY)"}
            await pg.click("text=Búsqueda")
            await pg.wait_for_timeout(6000)
            texto = await pg.inner_text("body")
            if re.search(r"no tiene permiso", texto, re.I):
                return {"ok": False, "codigo": "SIN_PERMISO",
                        "mensaje": "DNIT rechazó la consulta (captcha inválido)"}
            if re.search(r"no se ha encontrado", texto, re.I):
                return {"ok": True, "encontrado": False,
                        "mensaje": f"No se ha encontrado el contribuyente {ruc}"}
            datos = {}
            for campo in ["RUC - DV", "Nombre / Razón Social", "Estado",
                          "RUC Anterior", "SITUACIÓN FISCO"]:
                m = re.search(campo + r"\s*\n?\s*(.+)", texto)
                if m:
                    datos[campo] = m.group(1).split("\n")[0].strip()[:160]
            return {"ok": True, "encontrado": True,
                    "mensaje": "Contribuyente localizado", "datos": datos}
        finally:
            await browser.close()


async def consultar_validez(d: dict) -> dict:
    """d: ruc,dv,nombre,tipo_idx,tipo_doc,timbrado,est,punto,sec,fecha."""
    from playwright.async_api import async_playwright
    from app.modules.rpa.captcha import ensure_captcha
    async with async_playwright() as p:
        browser, pg = await _open(p)
        try:
            await pg.goto(f"{BASE}/consultarValidezDocumentos.do",
                          wait_until="domcontentloaded", timeout=45000)
            await pg.wait_for_timeout(3000)
            await pg.fill("input[name=ruc]", d["ruc"])
            await pg.fill("input[name=dv]", d["dv"])
            await pg.evaluate("""(nom) => {
                const el = document.querySelector('input[name=nombre]');
                el.removeAttribute('readonly');
                angular.element(el).scope().vm.datos.nombre = nom;
                angular.element(el).scope().$apply();
            }""", d["nombre"])
            await pg.select_option("select[name=tipoTimbrado]", index=int(d.get("tipo_idx", 5)))
            await pg.wait_for_timeout(1500)
            await pg.fill("input[name=numeroTimbrado]", d["timbrado"])
            await pg.select_option("select[name=tipoDocumento]", label=d["tipo_doc"])
            await pg.fill("input[name=establecimiento]", d["est"])
            await pg.fill("input[name=puntoExpedicion]", d["punto"])
            await pg.fill("input[name=nroSecuencia]", d["sec"])
            await pg.click("input[placeholder='Elegir Fecha']")
            await pg.keyboard.press("ControlOrMeta+a")
            await pg.keyboard.type(d["fecha"], delay=40)
            await pg.keyboard.press("Tab")
            await pg.wait_for_timeout(800)
            if not await ensure_captcha(pg):
                return {"ok": False, "codigo": "CAPTCHA_MANUAL",
                        "mensaje": "Captcha no resuelto automáticamente "
                                   "(configurar CAPTCHA_PROVIDER + CAPTCHA_API_KEY)"}
            await pg.click("text=Consultar Comprobante")
            await pg.wait_for_timeout(8000)
            paginas = pg.context.pages
            texto = await paginas[-1].inner_text("body")
            if re.search(r"no tiene permiso", texto, re.I):
                return {"ok": False, "codigo": "SIN_PERMISO",
                        "mensaje": "DNIT rechazó la consulta (captcha inválido)"}
            m = re.search(r"(documento\s+(es\s+)?válido|auténtico|vigente)", texto, re.I)
            if m:
                return {"ok": True, "valido": True,
                        "mensaje": "Documento VÁLIDO según DNIT",
                        "detalle": texto[:600]}
            m2 = re.search(r"(no\s+(es\s+)?válido|inválido|no se ha encontrado|no existe)", texto, re.I)
            if m2:
                return {"ok": True, "valido": False,
                        "mensaje": f"Documento NO válido: {m2.group(1)}",
                        "detalle": texto[:600]}
            return {"ok": True, "valido": None,
                    "mensaje": "Respuesta DNIT sin veredicto claro (revisar detalle)",
                    "detalle": texto[:800]}
        finally:
            await browser.close()
