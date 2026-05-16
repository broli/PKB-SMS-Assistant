Write-Host "Building PKB SMS Assistant..." -ForegroundColor Cyan

# Remove old executable if it exists to ensure we get a fresh build
if (Test-Path ".\dist\PKB SMS Assistant.exe") {
    Write-Host "Cleaning up old build..." -ForegroundColor Yellow
    Remove-Item ".\dist\PKB SMS Assistant.exe" -Force
}

& ".\.venv\Scripts\pyinstaller.exe" main.spec --noconfirm

# Check if build was successful
if ($LASTEXITCODE -eq 0 -and (Test-Path ".\dist\PKB SMS Assistant.exe")) {
    Write-Host "Build completed successfully! The executable is located in the 'dist' folder." -ForegroundColor Green
} else {
    Write-Host "Build failed. Please check the output above for errors." -ForegroundColor Red
    exit 1
}
