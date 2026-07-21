param(
    [ValidateSet('crm', 'logistics', 'crm-attach', 'all')]
    [string]$Bot = 'all'
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$VenvActivate = Join-Path $ProjectRoot '.venv\Scripts\Activate.ps1'
$LogsDir = Join-Path $ProjectRoot 'data\logs\scheduler'

if (-not (Test-Path $VenvActivate)) {
    throw "Virtualenv não encontrada em $VenvActivate"
}

New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null

Set-Location $ProjectRoot

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$logFile = Join-Path $LogsDir "task_${Bot}_${timestamp}.log"

. $VenvActivate

"[$(Get-Date -Format s)] Starting bot '$Bot' from '$ProjectRoot'" | Out-File -FilePath $logFile -Encoding utf8
python main.py --bot $Bot *>> $logFile
$exitCode = $LASTEXITCODE
"[$(Get-Date -Format s)] Finished with exit code $exitCode" | Out-File -FilePath $logFile -Append -Encoding utf8

exit $exitCode
