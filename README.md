# Sistema Automatizado Contable — IVA/IRP Paraguay (RG90 / Marangatú)

## Arranque rápido
```powershell
docker compose up -d
python -m venv .venv; .\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m app.db.init_db
uvicorn app.main:app --reload
celery -A app.worker.celery_app worker --loglevel=info
playwright install chromium   # solo para RPA
```
Abrir: `http://localhost:8000/docs`, auditoría: `/auditoria/{cliente_id}`.

## Flujo
1. `POST /clientes` (guarda pass DNIT cifrada AES-256).
2. `POST /clientes/proveedores` clasifica RUC por rubro.
3. `POST /ingesta/{cliente_id}` con JPG/PNG/PDF/XML (XML SIFEN prioritario, sin OCR).
4. Revisar en `/auditoria/{cliente_id}` → `PUT /comprobantes/{id}/revision` (valida formato, clasifica IVA/IRP, alerta topes Ley 6380/19).
5. `GET /rg90/{id}/{YYYY-MM}` descarga TXT tabulado; `POST .../presentar` ejecuta bot Playwright.
6. `GET /rg90/lotes/{id}` ve estado y nro. de lote.

## Notas críticas
- RG90 `generator.py` es plantilla: validar columnas contra manual DNIT vigente.
- `timbrado.py` y `marangatu_bot.py` tienen `PENDING_SELECTORS`: completar con el portal real y usar headed + pausas human-like.
- `tests/test_basico.py`: `python tests/test_basico.py`.

## Agentes
Ver `AGENTS.md` (setup, tests, lint, convenciones, reglas DNIT/RPA y secretos).
Dev extra: `pip install -r requirements-dev.txt`, `pytest -q`, `ruff check .`.
