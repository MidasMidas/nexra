$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$frontendDir = Join-Path $root "frontend"
$logsDir = Join-Path $root "logs"

New-Item -ItemType Directory -Force $logsDir | Out-Null

$frontendLog = Join-Path $logsDir "frontend.log"
$frontendErrLog = Join-Path $logsDir "frontend-error.log"

Set-Location $frontendDir

& python server.py 1>> $frontendLog 2>> $frontendErrLog
