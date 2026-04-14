param(
    [string]$DbType = "h2",
    [string]$DbPath = "./backend/data/nexra-db",
    [string]$Username = "sa",
    [string]$Password = "",
    [string]$HibernateDdlAuto = "update",
    [switch]$DisableH2Console
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path $root "backend\src\main\resources\application.properties"

if (-not (Test-Path $configPath)) {
    throw "Spring Boot config file not found: $configPath"
}

$normalizedType = $DbType.Trim().ToLowerInvariant()
if ($normalizedType -ne "h2") {
    throw "Only H2 is supported in the current Nexra version. Use -DbType h2."
}

$dbUrl = "jdbc:h2:file:$DbPath;DB_CLOSE_ON_EXIT=FALSE;FILE_LOCK=NO"
$properties = [ordered]@{
    "spring.datasource.url" = $dbUrl
    "spring.datasource.driver-class-name" = "org.h2.Driver"
    "spring.datasource.username" = $Username
    "spring.datasource.password" = $Password
    "spring.jpa.hibernate.ddl-auto" = $HibernateDdlAuto
    "spring.jpa.database-platform" = "org.hibernate.dialect.H2Dialect"
    "spring.h2.console.enabled" = $(if ($DisableH2Console) { "false" } else { "true" })
    "spring.h2.console.path" = "/h2-console"
}

$lines = Get-Content -Path $configPath
foreach ($entry in $properties.GetEnumerator()) {
    $pattern = '^{0}=' -f [regex]::Escape($entry.Key)
    $replacement = '{0}={1}' -f $entry.Key, $entry.Value
    $index = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match $pattern) {
            $index = $i
            break
        }
    }

    if ($index -ge 0) {
        $lines[$index] = $replacement
    } else {
        $lines += $replacement
    }
}

Set-Content -Path $configPath -Value $lines -Encoding UTF8

Write-Host "Database type: H2"
Write-Host "Config updated: $configPath"
Write-Host "Datasource URL: $dbUrl"
Write-Host "Username: $Username"
Write-Host "H2 console enabled: $(-not $DisableH2Console)"
Write-Host ""
Write-Host "Example:"
Write-Host "  .\Configure-NexraDatabase.ps1"
Write-Host "  .\Configure-NexraDatabase.ps1 -DbPath './backend/data/nexra-demo' -DisableH2Console"
