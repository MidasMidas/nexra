$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeDir = Join-Path $root ".runtime"
$logsDir = Join-Path $root "logs"
$pidFile = Join-Path $runtimeDir "nexra-services.json"

New-Item -ItemType Directory -Force $runtimeDir | Out-Null
New-Item -ItemType Directory -Force $logsDir | Out-Null

function Start-BackgroundProcess {
    param(
        [string]$FilePath,
        [string]$Arguments,
        [string]$WorkingDirectory,
        [string]$StdOutPath,
        [string]$StdErrPath
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = $Arguments
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.UseShellExecute = $true
    $psi.CreateNoWindow = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    [void]$process.Start()
    return $process
}

function Get-PortProcessId {
    param([int]$Port)

    $matches = netstat -ano | Select-String -Pattern "LISTENING\s+(\d+)$"
    foreach ($match in $matches) {
        $line = $match.Line.Trim() -replace "\s+", " "
        $parts = $line.Split(" ")
        if ($parts.Length -ge 5) {
            $localAddress = $parts[1]
            $processId = $parts[-1]
            if ($localAddress -match ":(\d+)$" -and [int]$Matches[1] -eq $Port) {
                return [int]$processId
            }
        }
    }

    return $null
}

if (Test-Path $pidFile) {
    $existing = Get-Content $pidFile -Raw | ConvertFrom-Json
    $running = @()

    foreach ($procInfo in @($existing.backend, $existing.frontend)) {
        if ($null -ne $procInfo -and $procInfo.pid) {
            $proc = Get-Process -Id $procInfo.pid -ErrorAction SilentlyContinue
            if ($proc) {
                $running += "$($procInfo.name)($($procInfo.pid))"
            }
        }
    }

    if ($running.Count -gt 0) {
        Write-Host "Nexra services are already running: $($running -join ', ')"
        Write-Host "If you want a clean restart, run .\Stop-Nexra.ps1 first."
        exit 0
    }
}

$backendPortPid = Get-PortProcessId -Port 8080
$frontendPortPid = Get-PortProcessId -Port 4173
if ($backendPortPid -or $frontendPortPid) {
    $runningPorts = @()
    if ($backendPortPid) { $runningPorts += "backend-port-8080($backendPortPid)" }
    if ($frontendPortPid) { $runningPorts += "frontend-port-4173($frontendPortPid)" }
    Write-Host "Nexra services appear to already be running: $($runningPorts -join ', ')"
    Write-Host "If you want a clean restart, run .\Stop-Nexra.ps1 first."
    exit 0
}

$backendLog = Join-Path $logsDir "backend.log"
$backendErrLog = Join-Path $logsDir "backend-error.log"
$frontendLog = Join-Path $logsDir "frontend.log"
$frontendErrLog = Join-Path $logsDir "frontend-error.log"

Write-Host "Starting Nexra backend..."
$backendClasses = Join-Path $root "backend\target\classes"
$backendDependencyDir = Join-Path $root "backend\target\dependency"
$backendLibs = if (Test-Path $backendDependencyDir) {
    Join-Path $backendDependencyDir "*"
} else {
    Join-Path $root ".runtime\jar-work\BOOT-INF\lib\*"
}
if (-not (Test-Path $backendClasses)) {
    Write-Host "Backend classes not found: $backendClasses"
    exit 1
}
$backendClasspath = "$backendClasses;$backendLibs"
$backendCommand = "/c `"java -cp `"$backendClasspath`" com.nexra.console.NexraConsoleApplication 1>>`"$backendLog`" 2>>`"$backendErrLog`"`""
$backend = Start-BackgroundProcess `
    -FilePath "cmd.exe" `
    -Arguments $backendCommand `
    -WorkingDirectory $root `
    -StdOutPath $backendLog `
    -StdErrPath $backendErrLog

Write-Host "Starting Nexra frontend..."
$frontendScript = Join-Path $root "frontend\server.py"
$frontendCommand = "/c `"python `"$frontendScript`" 1>>`"$frontendLog`" 2>>`"$frontendErrLog`"`""
$frontend = Start-BackgroundProcess `
    -FilePath "cmd.exe" `
    -Arguments $frontendCommand `
    -WorkingDirectory $root `
    -StdOutPath $frontendLog `
    -StdErrPath $frontendErrLog

$serviceState = [PSCustomObject]@{
    startedAt = (Get-Date).ToString("s")
    backend   = [PSCustomObject]@{
        name = "backend"
        pid  = $backend.Id
        log  = $backendLog
        errLog = $backendErrLog
        url  = "http://localhost:8080/api"
    }
    frontend  = [PSCustomObject]@{
        name = "frontend"
        pid  = $frontend.Id
        log  = $frontendLog
        errLog = $frontendErrLog
        url  = "http://127.0.0.1:4173"
    }
}

$serviceState | ConvertTo-Json | Set-Content $pidFile -Encoding UTF8

Start-Sleep -Seconds 4

$backendAlive = Get-Process -Id $backend.Id -ErrorAction SilentlyContinue
$frontendAlive = Get-Process -Id $frontend.Id -ErrorAction SilentlyContinue

if (-not $backendAlive -or -not $frontendAlive) {
    Write-Host "One or more services exited early. Check logs:"
    Write-Host "Backend log: $backendLog"
    Write-Host "Backend error log: $backendErrLog"
    Write-Host "Frontend log: $frontendLog"
    Write-Host "Frontend error log: $frontendErrLog"
    exit 1
}

Write-Host ""
Write-Host "Nexra is starting up."
Write-Host "Frontend: http://127.0.0.1:4173"
Write-Host "Backend API: http://localhost:8080/api"
Write-Host "Backend log: $backendLog"
Write-Host "Backend error log: $backendErrLog"
Write-Host "Frontend log: $frontendLog"
Write-Host "Frontend error log: $frontendErrLog"
Write-Host ""
Write-Host "If the page is not ready yet, wait a few seconds and refresh."
