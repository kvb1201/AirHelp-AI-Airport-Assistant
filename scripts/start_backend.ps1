# scripts/start_backend.ps1

# Get the directory of this script
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ROOT_DIR = Split-Path -Parent $SCRIPT_DIR
Set-Location $ROOT_DIR

$VENV_PATH = Join-Path $ROOT_DIR ".venv"

if (-Not (Test-Path $VENV_PATH)) {
    Write-Host "Creating virtual environment at $VENV_PATH..."
    python -m venv $VENV_PATH
}

Write-Host "Activating virtual environment..."
$PIP = Join-Path $VENV_PATH "Scripts\pip.exe"
$PYTHON = Join-Path $VENV_PATH "Scripts\python.exe"

Write-Host "Installing uvicorn, fastapi, and pydantic..."
& $PIP install uvicorn fastapi pydantic

Write-Host "Installing requirements from backend/requirements.txt..."
& $PIP install -r backend/requirements.txt

Write-Host "Installing ML libraries (this may take a few minutes)..."
& $PIP install faster-whisper transformers torch torchaudio

Write-Host "Starting backend server..."
Set-Location (Join-Path $ROOT_DIR "backend")
& $PYTHON run.py
