# RIG PHASE 2 - STEP 1: PROBE (print-only, makes NO changes)
# Run on the rig (Windows):  powershell -ExecutionPolicy Bypass -File rig_phase2_probe.ps1
# Paste the output back to the session before running sync.ps1.
$ErrorActionPreference = "Stop"
$repo = "C:\Users\rasla\Downloads\destiny-preservation\RE_build\Sunrise-fork"
if (-not (Test-Path "$repo\.git")) { Write-Host "!! repo not found at $repo"; exit 1 }

Write-Host "=== 1. worktrees ==="
git -C $repo worktree list
Write-Host "`n=== 2. branches + last commits ==="
git -C $repo branch -a
foreach ($b in @("master","integration","inventory-folded-s2")) {
  Write-Host "--- $b:"; git -C $repo log --oneline -3 $b 2>$null
}
Write-Host "`n=== 3. remotes ==="
git -C $repo remote -v
Write-Host "`n=== 4. dirty states (counts) — the loose-work check ==="
foreach ($wb in @("$repo","$repo\..\Sunrise-fork-inventory","$repo\..\Sunrise-fork-folded")) {
  $res = git -C $wb status --porcelain 2>$null
  Write-Host ("{0}: {1} dirty lines" -f $wb, @($res).Count)
  $res | Select-Object -First 12
}
Write-Host "`n=== 5. rig runtime settings: bootstrap_token present? ==="
foreach ($sf in @(
  "C:\Users\rasla\Downloads\destiny-preservation\RE_output\s1_accept\settings.json",
  "C:\Users\rasla\Downloads\destiny-preservation\RE_output\s1_accept\Sunrise\settings.json",
  "C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\Sunrise\settings.json")) {
  if (Test-Path $sf) {
    $tok = (Get-Content $sf -Raw | ConvertFrom-Json).server.bootstrap_token
    Write-Host ("{0} -> {1}" -f $sf, ($(if ($tok) { $tok } else { "(absent)" })))
  } else { Write-Host "$sf -> (missing)" }
}
Write-Host "`n=== 6. deployed stack hashes (pre-sync record) ==="
foreach ($b in @(
  "$repo\..\..\RE_output\s1_accept\sunrise-server.exe",
  "$repo\..\..\Game\bin\x64\steam_api64.dll",
  "C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\steam_api64.dll")) {
  if (Test-Path $b) { Write-Host ("{0}: {1}" -f $b, (Get-FileHash $b -Algorithm SHA256).Hash.Substring(0,16)) }
}
Write-Host "PROBE DONE - paste this output to the session."