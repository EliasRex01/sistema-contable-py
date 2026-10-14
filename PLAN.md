# PLAN.md — Hoja de ruta del proyecto

> Estado al 2026-10-14. Ver `STRATEGY.md` para el porqué de cada decisión y
> `HUMAN.md` para qué se necesita del humano en cada fase.

## Fase 0 — Núcleo (hecha)
- [x] FastAPI + SQLite/Postgres + panel web con paleta azul
- [x] Ingesta XML SIFEN / PDF / imagen (PyMuPDF, OpenCV, Tesseract+spa)
- [x] Calidad (nitidez) + detección de documento válido + auto-clasificación rubro
- [x] ABM clientes/comprobantes, auditoría visual, RG 90 TXT + lotes
- [x] Validador DNIT headless (perfil + validez) con captcha manual/HITL
- [x] Docs: AGENTS.md, HUMAN.md, PLAN.md, STRATEGY.md, CI, Docker

## Fase 1 — Cerrar el loop fiscal (siguiente)
- [ ] Confirmar columnas del TXT RG 90 contra el manual DNIT vigente
- [ ] Primer `presentar` real asistido (Tercero Autorizado + captcha HITL) y guardar lote + PDF
- [ ] Completar `PENDING_SELECTORS` de `marangatu_bot.py` con la sesión real
- [ ] Validar topes Ley 6380/19 con un contador (hoy son ejemplo)

## Fase 2 — Automatización total (requiere decisiones humanas)
- [ ] API key captcha (2captcha/CapSolver) en `.env` → validez 100% automática
- [ ] Suscribir API oficial DNIT (EsetApiWS, sin captchas) con clave Marangatú
- [ ] Migrar a Postgres + Redis + worker Celery (docker-compose listo)
- [ ] Alembic para migraciones (hoy `create_all` solo-dev)

## Fase 3 — Producción profesional
- [ ] Login multiusuario + roles (contador vs cliente) — hoy no hay auth
- [ ] Backups de `contable.db`/`uploads`, HTTPS reverso, monitoreo `/health`
- [ ] Suite pytest en CI (hoy `test_basico.py` + `conftest.py` base)
- [ ] Auditoría de seguridad del cifrado y rotación de `MASTER_KEY`

## Deuda conocida (no olvidar)
- `pipeline.pdf` escaneado sin rasterizar (marcado pendiente en `tasks.py`)
- `select_option(label=...)` depende del texto exacto del portal (frágil a cambios)
- `uploads/` crece sin límite: falta purga de temporales `_t*`/`_f*`
