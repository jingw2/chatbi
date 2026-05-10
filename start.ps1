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

# ── Paths ──────────────────────────────────────────────────
$VenvDir  = Join-Path $ScriptDir "backend\venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$PipExe    = Join-Path $VenvDir "Scripts\pip.exe"

# ── Backend setup ──────────────────────────────────────────
Write-Host "[1/4] Creating Python virtual environment..."
if (-not (Test-Path $VenvDir)) {
    python -m venv $VenvDir
    Write-Host "       venv created."
} else {
    Write-Host "       venv already exists, skipping."
}

Write-Host "[2/4] Installing Python dependencies..."
$pipResult = & $PipExe install -q -r (Join-Path $ScriptDir "backend\requirements.txt") 2>&1
# Show only if there were actual installs (not "already satisfied")
$installed = $pipResult | Where-Object { $_ -match "Successfully installed" }
if ($installed) {
    Write-Host "       $installed"
} else {
    Write-Host "       All dependencies already installed."
}

# ── Start backend ──────────────────────────────────────────
Write-Host "[3/4] Starting backend (SQLite + in-memory vectors)..."
$backendProc = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", (Join-Path $ScriptDir "backend") `
    -WorkingDirectory $ScriptDir `
    -PassThru -NoNewWindow

# Give backend a moment to start
Start-Sleep -Seconds 3

if ($backendProc.HasExited) {
    Write-Host "ERROR: Backend failed to start (exit code $($backendProc.ExitCode))." -ForegroundColor Red
    Write-Host "Check your .env configuration and try running manually:" -ForegroundColor Yellow
    Write-Host "  cd backend"
    Write-Host "  venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    exit 1
}

# ── Frontend setup + start ─────────────────────────────────
Write-Host "[4/4] Starting frontend..."
Set-Location (Join-Path $ScriptDir "frontend")
if (-not (Test-Path "node_modules")) {
    Write-Host "       Installing npm dependencies (first run, may take a minute)..."
    npm install --silent
}
$frontendProc = Start-Process -FilePath "npm" `
    -ArgumentList "run", "dev" `
    -WorkingDirectory (Join-Path $ScriptDir "frontend") `
    -PassThru -NoNewWindow

Set-Location $ScriptDir

Write-Host ""
Write-Host "=== ChatBI is running ===" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:5173"
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  Login:    admin@chatbi.local / admin123"
Write-Host ""
Write-Host "Press Ctrl+C to stop both services."

try {
    while ($true) {
        Start-Sleep -Seconds 2
        if ($backendProc.HasExited) {
            Write-Host ""
            Write-Host "Backend process exited (code $($backendProc.ExitCode))." -ForegroundColor Red
            break
        }
        if ($frontendProc.HasExited) {
            Write-Host ""
            Write-Host "Frontend process exited (code $($frontendProc.ExitCode))." -ForegroundColor Red
            break
        }
    }
} finally {
    Write-Host "Stopping services..."
    if (-not $backendProc.HasExited)  { Stop-Process -Id $backendProc.Id  -ErrorAction SilentlyContinue }
    if (-not $frontendProc.HasExited) { Stop-Process -Id $frontendProc.Id -ErrorAction SilentlyContinue }
    # Also kill any child processes (uvicorn workers, node)
    Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.Id -ne $PID -and ($_.ProcessName -match "python|node") -and $_.StartTime -gt (Get-Date).AddMinutes(-60)
    } | Stop-Process -ErrorAction SilentlyContinue
    Write-Host "Done."
}
