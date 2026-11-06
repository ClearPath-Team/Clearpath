param([switch]$RestoreOnly)
$ErrorActionPreference = 'Stop'
$demoRoot = Split-Path -Parent $PSScriptRoot
$statePath = Join-Path $demoRoot 'data\offline-adapters.json'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Physical-network rehearsal requires an elevated PowerShell window.'
}
function Restore-DemoAdapters {
    if (Test-Path -LiteralPath $statePath) {
        $saved = @(Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json)
        foreach ($adapter in $saved) {
            Get-NetAdapter | Where-Object { $_.InterfaceGuid.ToString() -eq $adapter.Guid } |
                Enable-NetAdapter -Confirm:$false
        }
        Remove-Item -LiteralPath $statePath
    }
}
if ($RestoreOnly) {
    Start-Sleep -Seconds 60
    Restore-DemoAdapters
    exit 0
}
New-Item -ItemType Directory -Path (Join-Path $demoRoot 'data') -Force | Out-Null
$adapters = @(Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' })
if ($adapters.Count -eq 0) { throw 'No active physical adapters found; no adapter state was changed.' }
$savedState = @($adapters | ForEach-Object { @{ Guid = $_.InterfaceGuid.ToString() } })
ConvertTo-Json -InputObject $savedState | Set-Content -LiteralPath $statePath -Encoding UTF8
# A separate elevated watchdog restores the captured adapters even if this
# process is interrupted. The normal finally block restores them immediately.
$watchdogArgs = '-NoProfile -ExecutionPolicy Bypass -File "{0}" -RestoreOnly' -f $PSCommandPath
Start-Process -FilePath powershell.exe -ArgumentList $watchdogArgs -WindowStyle Hidden | Out-Null
$testProcess = $null
try {
    foreach ($adapter in $adapters) {
        $adapter | Disable-NetAdapter -Confirm:$false
    }
    if (@(Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' }).Count -ne 0) {
        throw 'A physical adapter is still active; offline test refused.'
    }
    $python = Join-Path $demoRoot '.venv\Scripts\python.exe'
    $testArgs = '"{0}" --require-disconnected --launch-stack' -f (Join-Path $PSScriptRoot 'verify_offline.py')
    $testProcess = Start-Process -FilePath $python -ArgumentList $testArgs -WorkingDirectory $demoRoot `
        -RedirectStandardOutput (Join-Path $demoRoot 'data\offline-physical-test.log') `
        -RedirectStandardError (Join-Path $demoRoot 'data\offline-physical-test.err') `
        -PassThru -WindowStyle Hidden
    if (-not $testProcess.WaitForExit(45000)) {
        & taskkill.exe /PID $testProcess.Id /T /F | Out-Null
        throw 'Offline rehearsal exceeded 45 seconds; restoring network.'
    }
    $testProcess.Refresh()
    if ($testProcess.ExitCode -ne 0) { throw 'Offline test failed; inspect data/offline-physical-test.err.' }
    $evidencePath = Join-Path $PSScriptRoot 'verification.json'
    $evidence = Get-Content -LiteralPath $evidencePath -Raw | ConvertFrom-Json
    $evidence | Add-Member -NotePropertyName physical_adapters_disabled -NotePropertyValue $adapters.Count -Force
    [IO.File]::WriteAllText($evidencePath, ($evidence | ConvertTo-Json -Depth 10) + [Environment]::NewLine,
                           (New-Object Text.UTF8Encoding($false)))
} finally {
    Restore-DemoAdapters
}
Write-Output 'Physical network rehearsal passed and the adapters were re-enabled.'
