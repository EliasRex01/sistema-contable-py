"""Resolución automática de reCAPTCHA v2 para los formularios públicos DNIT.

Estrategia honesta: el checkbox "No soy un robot" no se puede resolver de
forma fiable solo con código (a propósito). Este módulo delega en servicios
anti-captcha por API (requieren API key de pago del cliente):
  CAPTCHA_PROVIDER=2captcha | capsolver, CAPTCHA_API_KEY=...
Sin clave configurada, ensure_captcha() retorna False y el flujo responde
"captcha manual requerido" (fallback HITL en scripts/consulta_hitl.py).
"""
import json
import time
import urllib.parse
import urllib.request
from app.core.config import settings

_POLL_MAX = 110  # segundos máx. esperando al proveedor


async def _sitekey(page) -> str:
    el = await page.query_selector(".g-recaptcha")
    return (await el.get_attribute("data-sitekey") or "") if el else ""


async def _inject(page, token: str) -> None:
    await page.evaluate(
        """(tok) => {
            const ta = document.querySelector("textarea[name=g-recaptcha-response]");
            if (ta) { ta.value = tok;
                ta.dispatchEvent(new Event("input", {bubbles: true}));
                ta.dispatchEvent(new Event("change", {bubbles: true})); }
            try {  // invocar callback del widget si es descubrible
                const clients = window.___grecaptcha_cfg && window.___grecaptcha_cfg.clients;
                if (clients) Object.values(clients).forEach(c => {
                    const cb = c && c.callback; if (typeof cb === "function") cb(tok);
                });
            } catch (e) {}
        }""",
        token,
    )


def _post_json(url: str, payload: dict, timeout: int = 30) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _get(url: str, params: dict, timeout: int = 30) -> dict:
    full = url + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(full, timeout=timeout) as r:
        return json.load(r)


def _twocaptcha(sitekey: str, pageurl: str) -> str | None:
    key = settings.CAPTCHA_API_KEY
    created = _get("https://2captcha.com/in.php", {
        "key": key, "method": "userrecaptcha", "googlekey": sitekey,
        "pageurl": pageurl, "json": 1})
    if created.get("status") != 1:
        raise RuntimeError(f"2captcha in.php: {created}")
    rid = created["request"]
    deadline = time.time() + _POLL_MAX
    while time.time() < deadline:
        time.sleep(5)
        res = _get("https://2captcha.com/res.php", {
            "key": key, "action": "get", "id": rid, "json": 1})
        if res.get("status") == 1:
            return str(res["request"])
        if res.get("request") not in ("CAPCHA_NOT_READY",):
            raise RuntimeError(f"2captcha res.php: {res}")
    return None


def _capsolver(sitekey: str, pageurl: str) -> str | None:
    key = settings.CAPTCHA_API_KEY
    task = _post_json("https://api.capsolver.com/createTask", {
        "clientKey": key, "task": {
            "type": "ReCaptchaV2TaskProxyless",
            "websiteURL": pageurl, "websiteKey": sitekey}})
    tid = (task.get("taskId") or "")
    if not tid:
        raise RuntimeError(f"capsolver createTask: {task}")
    deadline = time.time() + _POLL_MAX
    while time.time() < deadline:
        time.sleep(5)
        res = _post_json("https://api.capsolver.com/getTaskResult", {
            "clientKey": key, "taskId": tid})
        if res.get("status") == "ready":
            return str(res["solution"]["gRecaptchaResponse"])
        if res.get("status") not in ("processing", "idle"):
            raise RuntimeError(f"capsolver getTaskResult: {res}")
    return None


async def ensure_captcha(page) -> bool:
    """True si el captcha quedó resuelto (ya tickeado o vía proveedor)."""
    try:
        current = await page.eval_on_selector(
            "textarea[name=g-recaptcha-response]", "e => e.value || ''")
        if len(current or "") > 20:
            return True
    except Exception:
        pass
    provider = (settings.CAPTCHA_PROVIDER or "").lower()
    if provider not in ("2captcha", "capsolver") or not settings.CAPTCHA_API_KEY:
        return False
    sitekey = await _sitekey(page)
    if not sitekey:
        return False
    token = (_twocaptcha if provider == "2captcha" else _capsolver)(sitekey, page.url)
    if token:
        await _inject(page, token)
        return True
    return False


def captcha_status() -> dict:
    provider = (settings.CAPTCHA_PROVIDER or "").lower()
    return {"automatico": provider in ("2captcha", "capsolver") and bool(settings.CAPTCHA_API_KEY),
            "provider": provider or "manual"}
