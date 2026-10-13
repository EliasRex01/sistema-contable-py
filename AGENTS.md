# AGENTS.md — Sistema Contable IVA/IRP Paraguay (RG90 / Marangatú)

> Instrucciones operativas para agentes de código (humanos y IA).
> Stack: FastAPI + SQLAlchemy 2 + PostgreSQL + Celery/Redis.
> Shell del proyecto: **Windows PowerShell**, launcher Python: `py`.
> Python objetivo: **3.11+** (entorno actual: 3.14 — no usar sintaxis <3.11).

## 1. Mapa del repo

```text
app/main.py                        FastAPI, monta routers, POST /ingesta/{cliente_id}
app/core/config.py                 Settings (.env) — DATABASE_URL, REDIS_URL, MASTER_KEY
app/core/security.py               AES-256 Fernet (cifrado pass DNIT)
app/db/session.py | models.py      engine/SessionLocal/Base + Cliente, ProveedorRubro, Comprobante, LoteRG90
app/db/init_db.py                  create_all (solo dev; prod = Alembic)
app/modules/clientes/              schemas.py, service.py, router.py (clientes + proveedores por rubro)
app/modules/clientes/router.py     ABM clientes (PUT/DELETE; borrado bloqueado con comprobantes) + proveedores
app/modules/comprobantes/router.py PUT /{id}/revision, POST /{id}/rechazar, ABM (POST/PUT/DELETE), POST /{id}/desde-imagen (nitidez→OCR)
app/modules/ingestion/             regex_py.py, xml_sifen.py (canal prioritario), pipeline.py (PyMuPDF/OpenCV/Tesseract+spa), calidad.py (nitidez), documento.py (¿es comprobante? RUC+timbrado/nro)
app/modules/ingestion/             regex_py.py, xml_sifen.py (canal prioritario), pipeline.py (PyMuPDF/OpenCV/Tesseract)
app/modules/validador/             timbrado.py (URLs/campos DNIT reales), clasificador.py (IVA/IRP), topes.py (Ley 6380/19), service.py (scraping headless), router.py (UI /validador + API)
app/modules/rg90/                  generator.py (TXT tabulado), marangatu_bot.py (Playwright), router.py (exportar/presentar/lotes)
app/modules/rpa/browser.py         launch_browser(): Chromium Playwright o Chrome/Edge del sistema (CDN bloqueado)
app/modules/rpa/captcha.py         ensure_captcha(): 2captcha/capsolver vía CAPTCHA_* o False (manual/HITL)
app/modules/auditoria/             router.py + templates (base/menu/auditoria/validador, paleta azul)
app/modules/dashboard/router.py    dueño vistas HTML: panel, cargar (asistente 3 pasos), comprobantes-ui, clientes-ui, ingesta-ui (masiva), rg90-ui (guiado). Cada página elige su cliente en su propio formulario.
app/modules/rg90/                  generator.py (TXT tabulado), marangatu_bot.py (Playwright), router.py (exportar/presentar/lotes; /lotes antes que /{id}/{per})
app/worker/tasks.py                ocr.process_file + auto-clasificación rubro (sigue PENDIENTE)
tests/test_basico.py               5 tests sin BD ni red (regex, IVA, formato, topes, RG90)
scripts/dev.ps1                    arranque dev en Windows
```

## 2. Setup y arranque (PowerShell)

```powershell
docker compose up -d
py -m venv .venv; .\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
copy .env.example .env          # luego editar MASTER_KEY y DATABASE_URL
py -m app.db.init_db
py -m uvicorn app.main:app --reload            # http://localhost:8000/docs
celery -A app.worker.celery_app worker --loglevel=info   # en otra terminal, con Redis arriba
py -m playwright install chromium              # solo si se toca RPA
```

Docs: `/docs`, auditoría visual: `/auditoria/{cliente_id}`, adjuntos: `/uploads`.

## 3. Tests y verificación (obligatorio antes de entregar)

```powershell
py -m py_compile $(Get-ChildItem -Recurse -Filter *.py -Exclude __pycache__ | ForEach-Object FullName)
py tests/test_basico.py                        # 5 PASS + ALL OK, sin BD ni red
py -m pytest -q                                # tras: py -m pip install -r requirements-dev.txt
py -m ruff check . && py -m ruff format --check .   # lint + formato
```

Toda tarea termina con: compile OK + `test_basico.py` OK. Si se toca BD, probar
`py -m app.db.init_db` contra Postgres de `docker-compose.yml`.
Si se toca Celery, importar `app.worker.tasks` sin Redis debe funcionar
(la tarea solo conecta al encolar con `.delay()`, con fallback eager en `main.py:36`).
Al reiniciar el servidor en Windows: matar por dueño del puerto
(`Get-NetTCPConnection -LocalPort 8000`) y confirmar puerto libre antes de
levantar otro — los hijos `--reload` huérfanos retienen el socket y sirven
código viejo (fantasma diagnosticado 2026-10-06).

## 4. Convenciones de código

- **Routers**: un `router = APIRouter(prefix=...)` por módulo en `router.py`; `main.py` solo monta.
- **Lógica** en `service.py` / módulos puros; los routers validan y persisten.
- **Schemas** Pydantic v2 en `schemas.py` (`pattern=`, `model_dump()`).
- **Modelos**: solo SQLAlchemy 2 (`Mapped`/`mapped_column`) en `app/db/models.py`.
- **Imports pesados opcionales SIEMPRE lazy** (dentro de la función):
  `playwright` en `timbrado.py:9` y `marangatu_bot.py:8`, `pytesseract` en
  `pipeline.py:23` — importar arriba rompe tests/API sin esas deps.
- **Montos PY**: parsear con `parse_py_number()` (`regex_py.py`); IVA incluido:
  10 % = `total/11`, 5 % = `total/21` (`iva_credito`).
- Formato comprobante estricto `000-000-0000000`, timbrado 7–10 dígitos
  (`validar_formato_local`, `timbrado.py:31`).
- Comentarios en español, concisos, sin chain-of-thought. Referencias a código
  como `ruta:línea`.
- UI: toda consulta lenta (DNIT/RPA, hasta ~2 min) usa spinner bloqueante de
  pantalla (`#overlay` en `base.html` + `bloquear(true/false)` en finally,
  botones deshabilitados mientras dura). Sin spinner no se entrega.
- UX no técnicos: lenguaje simple (sin "ingesta/API"), asistentes por pasos
  (`.pasos`), textos `.ayuda`, estados vacíos con siguiente acción, confirmar
  borrados, cliente global recordado. Nada técnico en el nav (API solo en footer).
- Foto: orden calidad → documento → OCR. Mensajes exactos: "La imagen no está
  muy clara…" (IMAGEN_BORROSA) y "La imagen no pertenece a un comprobante
  válido" (IMAGEN_NO_VALIDA). Tesseract por winget + `tessdata/spa` local
  (ver `pipeline.py:24`, `.gitignore`: tessdata/ no se commitea).
- No crear archivos salvo necesarios; preferir editar. Nuevos módulos =
  `router.py` + (`service.py`|`schemas.py`) + test en `tests/`.

## 5. Reglas de dominio (no relajar sin pedir)

- **XML SIFEN primero**: `xml_sifen.py` es el canal limpio; OCR es fallback.
- **RG90 `generator.py` es plantilla simplificada**: validar columnas contra el
  manual DNIT vigente antes de presentar. Cambios de formato → test en `tests/`.
- **RPA Marangatú**: `marangatu_bot.py` sigue en `PENDING_SELECTORS`.
  Consultas públicas (`timbrado.py`, `service.py`): URLs y campos verificados
  2026-10-06. Formularios con reCAPTCHA v2: sin `CAPTCHA_PROVIDER` + key el
  servicio responde `CAPTCHA_MANUAL` (fallback HITL en `scripts/`).
  Headless + stealth + Chrome del sistema siempre; nunca credenciales en logs.
- **Topes Ley 6380/19**: `topes.py:4` (`ESPARCIMIENTO`, `VEHICULO`, `INMUEBLE`)
  son montos de ejemplo — ajustar por reglamentación y alertar, nunca bloquear
  silenciosamente.
- **Trazabilidad**: todo comprobante guarda `fuente` (OCR/XML/PDF) +
  `imagen_path`; la revisión humana en `/auditoria` es previa a `VALIDADO`.

## 6. Seguridad y secretos

- `MASTER_KEY` solo vía `.env` (nunca commitear `.env`; ver `.env.example`).
  Derivación SHA-256 → Fernet en `security.py:7`; si cambia la clave, los
  `dnit_pass_enc` existentes no descifran (error explícito, no fallback).
- Pass DNIT siempre `encrypt_secret()` al guardar, `decrypt_secret()` solo en
  el worker/bot de presentación. Jamás en respuestas API ni logs.
- `uploads/` puede contener facturas reales → no commitear (ver `.gitignore`).

## 7. Prohibido para agentes

- No cambiar `requirements.txt` sin actualizar `Dockerfile` si afecta sistema
  (tesseract, playwright).
- No exponer endpoints sin validación Pydantic ni estados distintos de
  `PENDIENTE/VALIDADO/RECHAZADO` en comprobantes.
- No "adivinar" URLs/selectores DNIT: marcar `TODO` + `PENDING_SELECTORS` y
  pedir confirmación contra el portal vigente.
- No usar `shell`/`os.system` para I/O de archivos (usar herramientas de
  ficheros) ni `time.sleep` fijo en RPA (usar pausas aleatorias).
