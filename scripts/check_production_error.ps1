# Check Production Server Error Log
# PowerShell script to view Django error logs on Production Server

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "CeremonyBadge - Error Log Checker" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Define possible log locations
$logLocations = @(
    "C:\CeremonyBadge\server.log",
    "C:\CeremonyBadge\error.log",
    "C:\CeremonyBadge\django.log",
    "C:\CeremonyBadge\logs\error.log",
    "C:\inetpub\CeremonyBadge\error.log"
)

Write-Host "Searching for log files..." -ForegroundColor Yellow
Write-Host ""

$foundLogs = @()

foreach ($logPath in $logLocations) {
    if (Test-Path $logPath) {
        $foundLogs += $logPath
        Write-Host "✓ Found: $logPath" -ForegroundColor Green
    }
}

if ($foundLogs.Count -eq 0) {
    Write-Host "No log files found in standard locations." -ForegroundColor Red
    Write-Host ""
    Write-Host "Searching entire C:\CeremonyBadge directory..." -ForegroundColor Yellow

    $allLogs = Get-ChildItem -Path "C:\CeremonyBadge" -Filter "*.log" -Recurse -ErrorAction SilentlyContinue

    if ($allLogs) {
        Write-Host ""
        Write-Host "Found log files:" -ForegroundColor Green
        $allLogs | ForEach-Object { Write-Host "  - $($_.FullName)" }
        $foundLogs = $allLogs | Select-Object -ExpandProperty FullName
    }
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Recent Errors (Last 50 lines)" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

foreach ($logFile in $foundLogs) {
    Write-Host ""
    Write-Host "File: $logFile" -ForegroundColor Yellow
    Write-Host "--------------------------------------" -ForegroundColor Gray

    # Show last 50 lines
    Get-Content $logFile -Tail 50 -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Search for specific errors" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

$errorKeywords = @("ERROR", "CRITICAL", "Exception", "Traceback", "OSError", "libgobject", "weasyprint")

foreach ($logFile in $foundLogs) {
    foreach ($keyword in $errorKeywords) {
        $matches = Select-String -Path $logFile -Pattern $keyword -SimpleMatch -ErrorAction SilentlyContinue | Select-Object -Last 10

        if ($matches) {
            Write-Host ""
            Write-Host "Keyword: $keyword in $logFile" -ForegroundColor Red
            $matches | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        }
    }
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Check Django Settings" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Check if DEBUG is enabled
$settingsFile = "C:\CeremonyBadge\ceremony_badge\settings.py"

if (Test-Path $settingsFile) {
    $debugSetting = Select-String -Path $settingsFile -Pattern "DEBUG\s*=\s*(True|False)" -ErrorAction SilentlyContinue

    if ($debugSetting) {
        Write-Host "Django DEBUG setting:" -ForegroundColor Yellow
        Write-Host "  $debugSetting" -ForegroundColor Gray
    }
}

# Check .env file
$envFile = "C:\CeremonyBadge\.env"

if (Test-Path $envFile) {
    Write-Host ""
    Write-Host "Environment file exists: $envFile" -ForegroundColor Green

    $debugEnv = Select-String -Path $envFile -Pattern "DEBUG" -ErrorAction SilentlyContinue
    if ($debugEnv) {
        Write-Host "  DEBUG setting: $debugEnv" -ForegroundColor Gray
    }
} else {
    Write-Host ""
    Write-Host "⚠ Environment file not found: $envFile" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Check Django Process" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

$pythonProcesses = Get-Process | Where-Object {$_.ProcessName -like "*python*"}

if ($pythonProcesses) {
    Write-Host "Python processes running:" -ForegroundColor Green
    $pythonProcesses | Format-Table ProcessName,Id,StartTime -AutoSize
} else {
    Write-Host "⚠ No Python processes found running!" -ForegroundColor Red
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Done" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
