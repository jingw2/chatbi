# ============================================================
# ChatBI — One-click start script (lite mode) — Windows
#
# Starts backend + frontend locally with SQLite + in-memory
# vector store. No Docker/PostgreSQL/Redis/Qdrant needed.
#
# Prerequisites:
#   - Python 3.11+
#   - Node.js 18+
#   - An LLM API key (OpenAI or Anthropic)
#
# Usage:
#   .\start.ps1
# ============================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# ── .env setup ──────────────────────────────────────────────
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from template..."

    $Secret = python -c "import secrets; print(secrets.token_hex(32))"
    $Encrypt = python -c "import secrets; print(secrets.token_hex(32))"

    @"
# === Lite Mode (SQLite + in-memory vector store) ===
DB_MODE=sqlite
SQLITE_PATH=data/chatbi.db

# === Security ===
SECRET_KEY=$Secret
ENCRYPTION_KEY=$Encrypt

# === LLM Configuration ===
# Option A: OpenAI (uncomment and set your key)
# INTENT_MODEL_PROVIDER=openai_compatible
# INTENT_MODEL_BASE_URL=https://api.openai.com/v1
# INTENT_MODEL_NAME=gpt-4o-mini
# INTENT_MODEL_API_KEY=sk-...
# TEXT_TO_SQL_PROVIDER=openai_compatible
# TEXT_TO_SQL_BASE_URL=https://api.openai.com/v1
# TEXT_TO_SQL_MODEL_NAME=gpt-4o
# TEXT_TO_SQL_API_KEY=sk-...

# Option B: Anthropic (uncomment and set your key)
# BASE_MODEL_PROVIDER=anthropic
# BASE_MODEL_API_KEY=sk-ant-...
# BASE_MODEL_NAME=claude-sonnet-4-6
"@ | Out-File -FilePath ".env" -Encoding utf8

    Write-Host ""
    Write-Host "=== .env created ==="
    Write-Host "IMPORTANT: Edit .env to add your LLM API keys before continuing."
    Write-Host "Then re-run this script."
    Write-Host ""
    exit 0
}

Write-Host "=== ChatBI Lite Mode ==="
Write-Host ""

# ── Load .env ───────────────────────────────────────────────
Get-Content ".env" | ForEach-Object {
    if ($_ -match "^\s*#" -or $_ -match "^\s*$") { return }
    $parts = $_ -split "=", 2
    if ($parts.Count -eq 2) {
        [Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process")
    }
}

# ── Backend ─────────────────────────────────────────────────
Write-Host "[1/3] Setting up backend..."
Set-Location "$ScriptDir\backend"

if (-not (Test-Path "venv")) {
    python -m venv venv
}
& "venv\Scripts\Activate.ps1"
pip install -q -r requirements.txt 2>$null

Write-Host "[2/3] Starting backend (SQLite + in-memory vectors)..."
Set-Location $ScriptDir
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:ScriptDir
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^\s*#" -or $_ -match "^\s*$") { return }
        $parts = $_ -split "=", 2
        if ($parts.Count -eq 2) {
            [Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process")
        }
    }
    & "$using:ScriptDir\backend\venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend
}
Start-Sleep -Seconds 3

# ── Frontend ────────────────────────────────────────────────
Write-Host "[3/3] Starting frontend..."
Set-Location "$ScriptDir\frontend"
if (-not (Test-Path "node_modules")) {
    npm install --silent
}
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:ScriptDir\frontend"
    npm run dev
}

Write-Host ""
Write-Host "=== ChatBI is running ==="
Write-Host "  Frontend: http://localhost:5173"
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  Login:    admin@chatbi.local / admin123"
Write-Host ""
Write-Host "Press Ctrl+C to stop."

try {
    while ($true) {
        Start-Sleep -Seconds 2
        if ($backendJob.State -eq "Failed") {
            Write-Host "Backend failed:" -ForegroundColor Red
            Receive-Job $backendJob
            break
        }
    }
} finally {
    Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
}
