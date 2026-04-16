param(
    [string]$DbType = "sqlite",
    [string]$DbPath = "backend_py/data/nexra-state.json",
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8080,
    [string]$SkillDataFile = "backend_py/data/skills.json",
    [switch]$DisableSkillSync
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path $root "backend_py\config.json"

if (-not (Test-Path $configPath)) {
    throw "Python backend config file not found: $configPath"
}

$normalizedType = $DbType.Trim().ToLowerInvariant()
if ($normalizedType -ne "sqlite") {
    throw "Only SQLite is supported in the current Python Nexra version. Use -DbType sqlite."
}

$config = Get-Content -Path $configPath -Raw | ConvertFrom-Json
$config.host = $BindHost
$config.port = $Port
$config.databasePath = $DbPath
$config.skillDataFile = $SkillDataFile
$config.skillSync.enabled = (-not $DisableSkillSync)

$config | ConvertTo-Json -Depth 6 | Set-Content -Path $configPath -Encoding UTF8

Write-Host "Storage type: JSON state file"
Write-Host "Config updated: $configPath"
Write-Host "State file path: $DbPath"
Write-Host "Backend host: $BindHost"
Write-Host "Backend port: $Port"
Write-Host "Skill sync enabled: $(-not $DisableSkillSync)"
Write-Host ""
Write-Host "Example:"
Write-Host "  .\Configure-NexraDatabase.ps1"
Write-Host "  .\Configure-NexraDatabase.ps1 -DbPath 'backend_py/data/nexra-demo.json' -Port 8090"
