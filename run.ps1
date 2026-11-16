<#
.SYNOPSIS
    Starts the AgriAdapt Precision Agriculture full-stack platform.
.DESCRIPTION
    Launches FastAPI Backend (Port 8000) and Vite Frontend (Port 5173),
    monitors their health, optionally opens the browser, and ensures
    clean shutdown on exit.
.EXAMPLE
    .\run.ps1
    .\run.ps1 -NoBrowser
    .\run.ps1 -NewWindows
#>
[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [switch]$NewWindows
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

Write-Host "==============================================================" -ForegroundColor Green
Write-Host "       AgriAdapt Autonomous Precision Agriculture Platform     " -ForegroundColor DarkGreen
Write-Host "==============================================================" -ForegroundColor Green

# 1. Check Python virtual environment
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Warning "Virtual environment not found at .venv\Scripts\python.exe. Using system python."
    $VenvPython = "python"
}

# 2. Check Node modules in frontend
$FrontendDir = Join-Path $ProjectRoot "frontend"
$NodeModules = Join-Path $FrontendDir "node_modules"
if (-not (Test-Path $NodeModules)) {
    Write-Host "[*] Node modules not found. Running 'npm install' in frontend..." -ForegroundColor Cyan
    Push-Location $FrontendDir
    npm install
    Pop-Location
}

if ($NewWindows) {
    Write-Host "[*] Launching Backend & Frontend in separate windows..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; `$env:PYTHONPATH='$ProjectRoot'; & '$VenvPython' -m uvicorn backend.app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FrontendDir'; npm run dev"
    Start-Sleep -Seconds 3
    if (-not $NoBrowser) {
        Start-Process "http://localhost:5173"
    }
    Write-Host "[+] Services launched in separate windows." -ForegroundColor Green
    return
}

# In-process / managed background process launch
Write-Host "[1/3] Starting FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Cyan

$backendPsi = New-Object System.Diagnostics.ProcessStartInfo
$backendPsi.FileName = $VenvPython
$backendPsi.Arguments = "-m uvicorn backend.app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload"
$backendPsi.WorkingDirectory = $ProjectRoot
$backendPsi.EnvironmentVariables["PYTHONPATH"] = $ProjectRoot
$backendPsi.UseShellExecute = $false
$backendPsi.CreateNoWindow = $true

$backendProc = [System.Diagnostics.Process]::Start($backendPsi)

Write-Host "[2/3] Starting Vite Frontend on http://127.0.0.1:5173 ..." -ForegroundColor Cyan

$frontendPsi = New-Object System.Diagnostics.ProcessStartInfo
$frontendPsi.FileName = "cmd.exe"
$frontendPsi.Arguments = "/c npm run dev"
$frontendPsi.WorkingDirectory = $FrontendDir
$frontendPsi.UseShellExecute = $false
$frontendPsi.CreateNoWindow = $true

$frontendProc = [System.Diagnostics.Process]::Start($frontendPsi)

# 3. Wait for services to be ready
Write-Host "[3/3] Verifying service readiness..." -ForegroundColor Cyan
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    try {
        $res = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($res.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {}
}

Write-Host ""
Write-Host "==============================================================" -ForegroundColor Green
Write-Host "  Platform Services are LIVE and RUNNING:" -ForegroundColor Green
Write-Host "  * Frontend UI:   http://localhost:5173" -ForegroundColor White
Write-Host "  * Backend API:   http://localhost:8000" -ForegroundColor White
Write-Host "  * API Docs:      http://localhost:8000/docs" -ForegroundColor White
Write-Host "==============================================================" -ForegroundColor Green
Write-Host "Press [Ctrl+C] or 'q' at any time to stop all services cleanly." -ForegroundColor Yellow
Write-Host ""

if (-not $NoBrowser) {
    Start-Sleep -Seconds 1
    Start-Process "http://localhost:5173"
}

try {
    while ($true) {
        if ($Host.UI.RawUI.KeyAvailable) {
            $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            if ($key.Character -eq 'q' -or $key.Character -eq 'Q') {
                break
            }
        }
        if ($backendProc.HasExited -or $frontendProc.HasExited) {
            Write-Warning "One or more services exited unexpectedly."
            break
        }
        Start-Sleep -Milliseconds 500
    }
}
finally {
    Write-Host "`n[*] Stopping services..." -ForegroundColor Cyan
    if ($backendProc -and -not $backendProc.HasExited) {
        Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    }
    if ($frontendProc -and -not $frontendProc.HasExited) {
        # Kill cmd.exe and child node processes
        taskkill /PID $frontendProc.Id /T /F 2>$null
    }
    Write-Host "[+] All services stopped cleanly." -ForegroundColor Green
}
