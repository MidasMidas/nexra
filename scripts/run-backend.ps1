$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$backendDir = Join-Path $root "backend"
$logsDir = Join-Path $root "logs"

New-Item -ItemType Directory -Force $logsDir | Out-Null

$backendLog = Join-Path $logsDir "backend.log"
$backendErrLog = Join-Path $logsDir "backend-error.log"
$jarPath = Join-Path $backendDir "target\nexra-console-backend-0.0.1-SNAPSHOT.jar"

Set-Location $backendDir

if (Test-Path $jarPath) {
    & java -jar $jarPath 1>> $backendLog 2>> $backendErrLog
}
else {
    & mvn spring-boot:run 1>> $backendLog 2>> $backendErrLog
}
