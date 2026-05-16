Write-Host "Starting Build and Deploy process..." -ForegroundColor Cyan

# Run the build script
.\build.ps1

# Verify the executable exists before trying to copy
if (!(Test-Path ".\dist\PKB SMS Assistant.exe")) {
    Write-Host "Deployment aborted because the build failed or the executable was not found." -ForegroundColor Red
    exit 1
}

$targetDir = "C:\Users\carlo\Desktop\PKB Apps\SMS Companion"
Write-Host "Deploying to $targetDir..." -ForegroundColor Cyan

# Create the target directory if it doesn't exist
if (!(Test-Path -Path $targetDir)) {
    Write-Host "Creating target directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
}

# Copy the executable
try {
    Copy-Item -Path ".\dist\PKB SMS Assistant.exe" -Destination "$targetDir\PKB SMS Assistant.exe" -Force
    Write-Host "Deployment successful! Executable copied to $targetDir" -ForegroundColor Green
} catch {
    Write-Host "Failed to copy the executable: $_" -ForegroundColor Red
    Write-Host "Make sure the application is closed before deploying." -ForegroundColor Yellow
    exit 1
}
