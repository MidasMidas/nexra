$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path (Join-Path $root ".runtime") "nexra-services.json"

if (-not (Test-Path $pidFile)) {
    Write-Host "No running service record found."
    exit 0
}

$state = Get-Content $pidFile -Raw | ConvertFrom-Json

foreach ($procInfo in @($state.backend, $state.frontend)) {
    if ($null -eq $procInfo -or -not $procInfo.pid) {
        continue
    }

    $proc = Get-Process -Id $procInfo.pid -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "Stopping $($procInfo.name) (PID $($procInfo.pid))..."
        Stop-Process -Id $procInfo.pid -Force
    }
    else {
        Write-Host "$($procInfo.name) already stopped."
    }
}

foreach ($port in @(8080, 4173)) {
    $matches = netstat -ano | Select-String -Pattern "LISTENING\s+(\d+)$"
    foreach ($match in $matches) {
        $line = $match.Line.Trim() -replace "\s+", " "
        $parts = $line.Split(" ")
        if ($parts.Length -lt 5) {
            continue
        }

        $localAddress = $parts[1]
        $processId = [int]$parts[-1]

        if ($localAddress -match ":(\d+)$" -and [int]$Matches[1] -eq $port) {
            $portProcess = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($portProcess) {
                Write-Host "Stopping listener on port $port (PID $processId)..."
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

try {
    Remove-Item $pidFile -Force
}
catch {
    Set-Content -LiteralPath $pidFile -Value "{}"
}

Write-Host "Nexra services stopped."
