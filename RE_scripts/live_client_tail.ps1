# LIVE CLIENT LOG TAIL — the recording's second window.
# The GAME's own trace, filtered to the interesting lines: the gate_trace census
# observers (the resolve/expr/stamp hooks), the queuez applies, and the BAP pushes
# the client receives from the server. Start this AFTER the game launches (the game
# rotates its log at each boot; a tail started earlier follows the rotated-away file).
# Usage:  powershell -File RE_scripts\live_client_tail.ps1
$ErrorActionPreference = 'SilentlyContinue'
$log = 'C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\Sunrise\logs\sunrise.log'
$host.UI.RawUI.WindowTitle = 'DESTINY CLIENT - LIVE'
try {
    $host.UI.RawUI.BufferSize = New-Object System.Management.Automation.Host.Size(180, 3000)
    $host.UI.RawUI.WindowSize = New-Object System.Management.Automation.Host.Size(180, 40)
} catch {}
Write-Host ('=' * 178) -ForegroundColor DarkCyan
Write-Host '  DESTINY 2 CLIENT  -  LIVE TRACE    (the gate_trace census + the queuez/BAP apply, filtered)' -ForegroundColor Cyan
Write-Host '  start this window AFTER the game launches (the game rotates its log at each boot)' -ForegroundColor Green
Write-Host ('=' * 178) -ForegroundColor DarkCyan
Write-Host ''
Get-Content $log -Wait -Tail 0 |
    Where-Object { $_ -match 'gate_trace|ability_gate|stage=queuez|handle_message|bootflow|emit_2100|out of order|world_controller: successfully' } |
    ForEach-Object {
        if ($_ -match 'stage=resolve|emit_2100') {
            Write-Host $_ -ForegroundColor Magenta
        } elseif ($_ -match 'stage=marker_poll|stage=stamp_') {
            Write-Host $_ -ForegroundColor Green
        } elseif ($_ -match 'handle_message') {
            Write-Host $_ -ForegroundColor Cyan
        } else {
            Write-Host $_ -ForegroundColor Gray
        }
    }
