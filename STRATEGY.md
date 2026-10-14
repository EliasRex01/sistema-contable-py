# STRATEGY.md — Estrategia a largo plazo

> Decisiones estructurales del sistema y su fundamento. Cambiar una estrategia
> requiere actualizar este archivo y el código afectado.

## 1. Fuente de verdad por capas (orden de prioridad)
1. **XML SIFEN** — dato estructurado oficial, cero error. Siempre preferido.
2. **PDF nativo** (texto embebido) — extracción directa con PyMuPDF.
3. **OCR de foto** — último recurso, con compuertas (nitidez → documento → OCR).
4. **RPA del portal** — solo para lo que no tiene API (presentar, captchas).

## 2. Anti-fragilidad frente a la DNIT
- El portal cambia sin aviso: URLs/campos se fechan en docstrings y se
  re-descubren con scripts de sondeo, nunca se adivinan.
- Todo flujo con red externa falla **tipificado** (`CAPTCHA_MANUAL`,
  `SIN_PERMISO`, `IMAGEN_NO_VALIDA`) en vez de colgarse o inventar datos.
- Capas de respaldo en cascada: Chromium Playwright → Chrome → Edge del
  sistema; captcha proveedor → HITL; Tesseract spa → eng.
- Meta final: **cero scraping** — migrar cada consulta al API oficial (EsetApiWS)
  en cuanto haya apiKey (Fase 2 de `PLAN.md`).

## 3. Humano en el loop, donde suma
- La máquina extrae y clasifica; el humano **confirma** (estados
  `PENDIENTE → VALIDADO/RECHAZADO`, nunca auto-VALIDADO).
- Captchas y presentaciones reales siempre con humano enterado (HITL o key
  provista por él). Ver `HUMAN.md`.
- UX para no técnicos: el contador no debe saber qué es una API; el sistema
  habla de facturas, meses y presentaciones.

## 4. Costos y sostenibilidad
- Captcha solvers (~USD 1–3/1000) solo cuando el volumen lo justifique;
  mientras tanto HITL es gratis.
- Infra mínima viable: SQLite + eager basta para 1 estudio contable;
  Postgres/Redis solo al escalar (compose ya listo).
- Tesseract local (gratis) vs Vision/Textract (pago, más preciso en tablas):
  cambiar solo si el OCR local falla sistemáticamente en tiques.

## 5. Cumplimiento y riesgo
- Credenciales DNIT cifradas (AES-256), Tercero Autorizado en vez de clave
  personal, nada sensible en logs ni en git.
- Sin presentaciones reales sin confirmación explícita por periodo.
- Topes legales como **alertas**, nunca como bloqueos silenciosos.
- Conservar `fuente` + `imagen_path` de cada comprobante (trazabilidad fiscal).
