# scripts/start_frontend.ps1

Write-Host "Installing frontend dependencies..."
Set-Location frontend
npm install

Write-Host "Starting frontend dev server..."
npm run dev
