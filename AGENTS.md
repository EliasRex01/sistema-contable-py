# AGENTS.md — Sistema Contable IVA/IRP Paraguay (RG90 / Marangatú)

> Instrucciones operativas para agentes de código (humanos y IA).
> Stack: FastAPI + SQLAlchemy 2 + PostgreSQL + Celery/Redis.
> Shell del proyecto: **Windows PowerShell**, launcher Python: `py`.
> Python objetivo: **3.11+** (entorno actual: 3.14 — no usar sintaxis <3.11).
> Docs del proyecto: `HUMAN.md` (rol del humano), `PLAN.md` (hoja de ruta),
> `STRATEGY.md` (estrategia a largo plazo). Leerlos antes de cambios grandes.

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
app/modules/validador/             timbrado.py (URLs/campos DNIT reales), clasificador.py (IVA/IRP), topes.py (Ley 6380/19), service.py (scraping headless), router.py (UI /validador + API)
app/modules/rg90/                  generator.py (TXT tabulado), marangatu_bot.py (Playwright), router.py (exportar/presentar/lotes; /lotes antes que /{id}/{per})
app/modules/rpa/browser.py         launch_browser(): Chromium Playwright o Chrome/Edge del sistema (CDN bloqueado)
app/modules/rpa/captcha.py         ensure_captcha(): 2captcha/capsolver vía CAPTCHA_* o False (manual/HITL)
app/modules/auditoria/             router.py + templates (base/dashboard/auditoria/validador/cargar/clientes/comprobantes/ingesta/rg90, paleta azul)
app/modules/dashboard/router.py    dueño vistas HTML: panel, cargar (asistente 3 pasos), comprobantes-ui, clientes-ui, ingesta-ui (masiva), rg90-ui (guiado). Cada página elige su cliente en su propio formulario.
app/worker/tasks.py                ocr.process_file + auto-clasificación rubro (sigue PENDIENTE)
tests/test_basico.py               7 tests sin BD ni red (regex, IVA, formato, topes, RG90, calidad, documento)
scripts/dev.ps1                    arranque dev en Windows
```

## 2. Setup y arranque (PowerShell)

```powershell
py -m venv .venv; .\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
copy .env.example .env          # dev: DATABASE_URL=sqlite:///./contable.db ; prod: postgres de docker-compose.yml
py -m app.db.init_db
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000   # SIN --reload (ver §3)
celery -A app.worker.celery_app worker --loglevel=info   # opcional: sin Redis hay fallback eager
py -m playwright install chromium              # falla si cdn.playwright.dev está bloqueado → usar Chrome del sistema (rpa/browser.py)
winget install -e --id UB-Mannheim.TesseractOCR --silent   # OCR fotos (solo lang eng incluido)
# + descargar tessdata/spa.traineddata de github tesseract-ocr/tessdata_fast (no se commitea)
```

Docs: `/docs`, panel: `/`, auditoría: `/auditoria/{cliente_id}`, adjuntos: `/uploads`.

## 3. Tests y verificación (obligatorio antes de entregar)

```powershell
py -m py_compile $(Get-ChildItem -Recurse -Filter *.py -Exclude __pycache__ | ForEach-Object FullName)
py tests/test_basico.py                        # 7 PASS + ALL OK, sin BD ni red
py -m pytest -q                                # tras: py -m pip install -r requirements-dev.txt
py -m ruff check . && py -m ruff format --check .   # lint + formato
```

Toda tarea termina con: compile OK + `test_basico.py` OK + prueba viva del
endpoint/página tocada (Invoke-WebRequest + screenshot con `scripts/shot_ui.py`
si es UI). Si se toca BD, probar `py -m app.db.init_db`.
Si se toca Celery, importar `app.worker.tasks` sin Redis debe funcionar
(la tarea solo conecta al encolar con `.delay()`, con fallback eager en `main.py:36`).
Al reiniciar el servidor en Windows: matar por dueño del puerto
(`Get-NetTCPConnection -LocalPort 8000`) y confirmar puerto libre antes de
levantar otro — los hijos `--reload` huérfanos retienen el socket y sirven
código viejo (fantasma diagnosticado 2026-10-06). Por eso se corre SIN `--reload`.
Los artefactos de prueba (filas/archivos `_t*`, `uploads/_f*`) se borran siempre.

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
  borrados. Nada técnico en el nav (API solo en footer). Cada página elige su
  cliente en su propio formulario (sin selector global).
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
- PowerShell no tiene `&&`, heredoc `<<`, `sed`, `tail`, ni `del` múltiple
  (usar `Remove-Item a,b` o `;`). `Select-Object -First N` para recortar salidas.

## 8. Comportamientos aprendidos del proyecto (obligatorios)

1. **Evidencia antes que síntesis**: leer el archivo/log real antes de afirmar.
   Los tracebacks muestran el fuente actual en disco, no el bytecode cargado:
   ante un error "imposible", sospechar código viejo en memoria y reiniciar.
2. **Puerto único, un solo servidor**: sin `--reload` en sesiones agente; matar
   por dueño del puerto y verificar libre antes de levantar.
3. **Nada del portal por adivinanza**: URLs, campos y tipos se descubren con
   Playwright contra el sitio real (`scripts/*campos*.py`) y se fechan en el
   docstring. Lo no verificado se marca `PENDING_SELECTORS` + `TODO`.
4. **Formularios AngularJS por su vía**: readonly/autocompletados se manejan vía
   scope (`$apply`) o tecleo real; verificar valores en DOM antes de enviar;
   capturas + `expect_response` para distinguir "no se envió" de "rechazado".
5. **Umbrales con datos, no a ojo**: nitidez/brillo se calibran con imágenes
   sintéticas (nítida vs borrosa) antes de fijarlos.
6. **Fallo honesto y tipificado**: la UI muestra el veredicto exacto
   (`IMAGEN_BORROSA`, `IMAGEN_NO_VALIDA`, `CAPTCHA_MANUAL`, `SIN_PERMISO`);
   nunca datos inventados ni spinner eterno (siempre `finally`).
7. **Anti-fragilidad RPA**: `launch_browser` (Chromium→Chrome→Edge),
   `ensure_captcha` (proveedor→HITL), stealth siempre, reintentos acotados.
8. **Jinja vs JS**: prohibido `{{` dentro de `<script>` (rompe el render);
   usar concatenación. Verificado con screenshot, no solo status 200.
9. **Orden de rutas**: literales (`/lotes/...`) antes que parámetros
   (`/{id}/...`); el opacamiento da 422 silencioso (detectado en logs).
10. **Limpieza y secretos**: borrar artefactos `_t*`/`_f*`; revisar `git status`
    antes de commitear (`.env`, `.venv`, `uploads/`, `*.db`, `tessdata/` fuera).
