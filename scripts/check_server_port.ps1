# Check Server Port - CeremonyBadge
# PowerShell script to check what port the Django server is running on

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "CeremonyBadge - Port Checker" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Method 1: Check Python processes with ports
Write-Host "Method 1: Python Processes with Ports" -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Yellow
try {
    $pythonProcesses = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object {
        try {
            $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
            $proc.ProcessName -like "*python*"
        } catch {
            $false
        }
    } | Select-Object LocalAddress,LocalPort,@{Name="ProcessName";Expression={(Get-Process -Id $_.OwningProcess).ProcessName}},@{Name="PID";Expression={$_.OwningProcess}}

    if ($pythonProcesses) {
        $pythonProcesses | Format-Table -AutoSize
    } else {
        Write-Host "No Python processes found listening on any port." -ForegroundColor Gray
    }
} catch {
    Write-Host "Error checking Python processes: $_" -ForegroundColor Red
}

Write-Host ""

# Method 2: Check common Django ports
Write-Host "Method 2: Common Django Ports (8000-8010)" -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Yellow

$commonPorts = 8000..8010
$foundPorts = @()

foreach ($port in $commonPorts) {
    $connection = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($connection) {
        $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
        $foundPorts += [PSCustomObject]@{
            Port = $port
            PID = $connection.OwningProcess
            ProcessName = $process.ProcessName
            Status = "LISTENING"
        }
    }
}

if ($foundPorts) {
    $foundPorts | Format-Table -AutoSize
} else {
    Write-Host "No processes found on ports 8000-8010." -ForegroundColor Gray
}

Write-Host ""

# Method 3: Check for CeremonyBadge in process paths
Write-Host "Method 3: Processes with 'CeremonyBadge' in Path" -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Yellow

try {
    $ceremonyProcesses = Get-Process | Where-Object {$_.Path -like "*CeremonyBadge*"}

    if ($ceremonyProcesses) {
        foreach ($proc in $ceremonyProcesses) {
            Write-Host "Process: $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Green
            Write-Host "  Path: $($proc.Path)" -ForegroundColor Gray

            # Get ports for this process
            $ports = Get-NetTCPConnection -OwningProcess $proc.Id -State Listen -ErrorAction SilentlyContinue
            if ($ports) {
                foreach ($port in $ports) {
                    Write-Host "  Listening on: $($port.LocalAddress):$($port.LocalPort)" -ForegroundColor Cyan
                }
            } else {
                Write-Host "  No listening ports found." -ForegroundColor Gray
            }
            Write-Host ""
        }
    } else {
        Write-Host "No processes with 'CeremonyBadge' in path found." -ForegroundColor Gray
    }
} catch {
    Write-Host "Error checking CeremonyBadge processes: $_" -ForegroundColor Red
}

Write-Host ""

# Method 4: Check Windows Service
Write-Host "Method 4: Windows Service Check" -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Yellow

try {
    $services = Get-Service | Where-Object {$_.Name -like "*ceremony*" -or $_.DisplayName -like "*ceremony*"}

    if ($services) {
        $services | Format-Table Name,DisplayName,Status -AutoSize
    } else {
        Write-Host "No CeremonyBadge Windows Service found." -ForegroundColor Gray
    }
} catch {
    Write-Host "Error checking services: $_" -ForegroundColor Red
}

Write-Host ""

# Method 5: Check configuration files
Write-Host "Method 5: Check Configuration Files" -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Yellow

# Try to find CeremonyBadge directory
$possiblePaths = @(
    "C:\CeremonyBadge",
    "C:\inetpub\CeremonyBadge",
    "C:\projects\CeremonyBadge",
    "D:\CeremonyBadge"
)

$foundPath = $null
foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $foundPath = $path
        break
    }
}

if ($foundPath) {
    Write-Host "Found CeremonyBadge at: $foundPath" -ForegroundColor Green

    # Check run_server.py
    $runServerPath = Join-Path $foundPath "run_server.py"
    if (Test-Path $runServerPath) {
        Write-Host "  Checking run_server.py..." -ForegroundColor Cyan
        $content = Get-Content $runServerPath -Raw
        if ($content -match "port\s*=\s*(\d+)") {
            Write-Host "  Found port in run_server.py: $($matches[1])" -ForegroundColor Green
        }
    }

    # Check .env files
    $envFiles = Get-ChildItem -Path $foundPath -Filter ".env*" -ErrorAction SilentlyContinue
    if ($envFiles) {
        foreach ($envFile in $envFiles) {
            Write-Host "  Checking $($envFile.Name)..." -ForegroundColor Cyan
            $content = Get-Content $envFile.FullName -Raw -ErrorAction SilentlyContinue
            if ($content -match "PORT\s*=\s*(\d+)") {
                Write-Host "  Found PORT in $($envFile.Name): $($matches[1])" -ForegroundColor Green
            }
        }
    }
} else {
    Write-Host "CeremonyBadge directory not found in common locations." -ForegroundColor Gray
    Write-Host "Please run this script from the CeremonyBadge directory." -ForegroundColor Gray
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Check Complete" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
