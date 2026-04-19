$ErrorActionPreference = "Stop"

param(
    [Parameter(Mandatory = $true)]
    [string]$ApiBase
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$configFile = Join-Path $root "frontend\\config.js"
$normalized = $ApiBase.Trim().TrimEnd("/")

@"
window.__NEXRA_API_BASE__ = "$normalized";
"@ | Set-Content -Path $configFile -Encoding UTF8

Write-Host "Updated frontend API base to $normalized"
