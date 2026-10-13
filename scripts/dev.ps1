#Requires -Version 5.1
# Arranque dev Windows. Uso: .\scripts\dev.ps1 [-Setup]
param([switch]$Setup)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if ($Setup) {
  docker compose up -d
  if (!(Test-Path .venv)) { py -m venv .venv }
  .\.venv\Scripts\Activate.ps1
  py -m pip install -r requirements.txt
  if (!(Test-Path .env)) { Copy-Item .env.example .env; Write-Host "EDITAR .env (MASTER_KEY)" }
  py -m playwright install chromium
}
.\.venv\Scripts\Activate.ps1
py -m app.db.init_db
py -m uvicorn app.main:app --reload
