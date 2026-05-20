# scripts/start_backend.ps1

# Get the directory of this script
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ROOT_DIR = Split-Path -Parent $SCRIPT_DIR
Set-Location $ROOT_DIR

$VENV_PATH = Join-Path $ROOT_DIR ".venv"

if (-Not (Test-Path $VENV_PATH)) {
    Write-Host "Creating virtual environment at $VENV_PATH..."
    & "python" -m venv $VENV_PATH
}

# Activate the virtual environment for this script session
. (Join-Path $VENV_PATH "Scripts\Activate.ps1")

Write-Host "Installing uvicorn, fastapi, and pydantic..."
pip install uvicorn fastapi pydantic

Write-Host "Installing requirements from backend/requirements.txt..."
pip install -r (Join-Path $ROOT_DIR "backend\requirements.txt")

Write-Host "Installing ML libraries (this may take a few minutes)..."
pip install faster-whisper transformers torch torchaudio

Write-Host "Starting backend server..."
Set-Location (Join-Path $ROOT_DIR "backend")
python run.py
