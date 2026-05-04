# scripts/start_backend_fast.ps1

# Get the directory of this script
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ROOT_DIR = Split-Path -Parent $SCRIPT_DIR
Set-Location $ROOT_DIR

$VENV_PATH = Join-Path $ROOT_DIR ".venv"

if (-Not (Test-Path $VENV_PATH)) {
    Write-Host "Creating virtual environment..."
    python -m venv $VENV_PATH
}

$PIP = Join-Path $VENV_PATH "Scripts\pip.exe"
$PYTHON = Join-Path $VENV_PATH "Scripts\python.exe"

Write-Host "Installing core web dependencies (FAST)..."
& $PIP install fastapi uvicorn pydantic httpx requests chromadb sentence-transformers networkx Pillow

Write-Host "Skipping heavy ML libraries (torch, transformers, faster-whisper) to start quickly."
Write-Host "The system will use MOCK responses for Voice-to-Text and Translation."

Write-Host "Starting backend server..."
Set-Location (Join-Path $ROOT_DIR "backend")
& $PYTHON run.py
