# HUMAN.md — Rol del humano en este proyecto

> El sistema se construye entre dos partes: el agente (código) y vos (contexto,
> accesos y decisiones). Este archivo define qué se espera de cada lado para no
> trabarse. Idioma: español, respuestas cortas.

## 1. Lo que solo vos podés dar

| Tema | Detalle |
|---|---|
| Credenciales DNIT | RUC + clave, o idealmente un **Tercero Autorizado** (ver §2). Nunca las pidas por chat si no hace falta: alcanzan para el primer `presentar` real. |
| Captchas | Los formularios públicos usan reCAPTCHA v2. Flujo HITL: se abre Chrome en tu PC, marcas "No soy un robot", el script sigue solo. Sin tu clic no hay avance. |
| Verdad del portal | Si Marangatú cambió un menú o mensaje, tu captura/texto vale más que cualquier suposición del agente. |
| Decisiones | Elegir proveedor captcha (2captcha vs CapSolver), pasar a Postgres prod, hacer público el repo, borrar datos. El agente propone, vos disponés. |
| Red local | Tu PC tiene Chrome instalado, winget, y `cdn.playwright.dev` **bloqueado** (por eso existe el fallback a Chrome del sistema). Avisá si cambia. |

## 2. Cuentas y accesos (cómo colaborar sin compartir tu clave)

1. Entrá a Marangatú con tu RUC + clave.
2. Creá un **Tercero Autorizado** para el contador/robot, por el periodo que quieras.
3. Pasá ese usuario/clave al sistema (Clientes → editar). Se guarda cifrada (AES-256).
4. Cuando quieras, revocás el acceso desde Marangatú. Nada que borrar en el sistema.

## 3. Cómo pedir cosas (para que salgan en un intento)

- Una tarea por mensaje, con el resultado esperado ("al subir foto borrosa debe decir X").
- Si algo falla, pegá el mensaje exacto o la captura; no re-describas.
- "Abrí la aplicación" = levantar servidor + abrir navegador. "Publicá" = commit + push.

## 4. Lo que el agente hace sin preguntar

- Verificar con ejecución (tests, endpoints vivos, screenshots).
- Limpiar archivos de prueba y no commitear secretos.
- Documentar en `AGENTS.md`/`PLAN.md` lo aprendido.
- Decirte cuando algo **no** se puede (ej. captcha sin API key) en vez de simularlo.

## 5. Límites

- El agente no opera Marangatú con tu clave personal ni resuelve captchas por vos.
- No se presentan declaraciones reales sin tu confirmación explícita por periodo.
- Los montos de topes Ley 6380/19 son ejemplo hasta que un contador los valide.
