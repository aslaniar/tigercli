# LIVE SERVER LOG TAIL — the recording view.
# One PowerShell window showing the standalone server's log as it happens. The game
# client (destiny2.exe) talks to THIS process; every line below = the live session.
# Usage:  powershell -File RE_scripts\live_server_tail.ps1
$ErrorActionPreference = 'SilentlyContinue'
$log = 'C:\Users\rasla\Downloads\destiny-preservation\RE_output\s1_accept\Sunrise\logs\sunrise.log'
$host.UI.RawUI.WindowTitle = 'SUNRISE SERVER - LIVE'
try {
    $host.UI.RawUI.BufferSize = New-Object System.Management.Automation.Host.Size(180, 3000)
    $host.UI.RawUI.WindowSize = New-Object System.Management.Automation.Host.Size(180, 40)
} catch {}
$p = Get-Process -Name sunrise-server -ErrorAction SilentlyContinue
Write-Host ('=' * 178) -ForegroundColor DarkCyan
Write-Host '  SUNRISE PRIVATE SERVER  -  LIVE LOG    (Destiny 2 Season of Arrivals, standalone external-mode server)' -ForegroundColor Cyan
if ($p) {
    Write-Host ("  pid " + ($p.Id -join ',') + "   |   ports: 443 (https)   30975 (BAP)   3074/3075 (discovery)") -ForegroundColor Cyan
} else {
    Write-Host '  WARNING: no sunrise-server process found - start it first!' -ForegroundColor Red
}
Write-Host '  the game client talks to THIS process. Every line below = the live session, unfiltered.' -ForegroundColor Green
Write-Host ('=' * 178) -ForegroundColor DarkCyan
Write-Host ''
Get-Content $log -Wait -Tail 0 | ForEach-Object {
    if ($_ -match 'ws_capture') {
        Write-Host '>>> CLIENT REQUEST ARRIVED: ' -NoNewline -ForegroundColor White -BackgroundColor DarkMagenta
        Write-Host $_ -ForegroundColor Magenta
    } elseif ($_ -match 'subclass_select|subclass_equip') {
        Write-Host '>>> SERVER PUBLISHED the family-4 answer: ' -NoNewline -ForegroundColor White -BackgroundColor DarkGreen
        Write-Host $_ -ForegroundColor Green
    } elseif ($_ -match 'banner_refresh|family=4') {
        Write-Host $_ -ForegroundColor Green
    } elseif ($_ -match 'stage=request') {
        Write-Host $_ -ForegroundColor Cyan
    } elseif ($_ -match 'result=fail|warn') {
        Write-Host $_ -ForegroundColor Yellow
    } elseif ($_ -match 'stage=listen|initialize result=ok|stage=swap') {
        Write-Host $_ -ForegroundColor Cyan
    } else {
        Write-Host $_ -ForegroundColor Gray
    }
}
