# RIG PHASE 2 - STEP 2: SYNC (applies changes - run ONLY after the probe output is reviewed)
# Run on the rig (Windows):  powershell -ExecutionPolicy Bypass -File rig_phase2_sync.ps1
# 1) fetches the converged history from origin, 2) moves master/integration/refs to it,
# 3) rotates the bootstrap_token in the rig's runtime settings, 4) normalizes line endings,
# 5) re-registers the two worktrees, 6) prints the rebuild + restamp checklist.
$ErrorActionPreference = "Stop"
$repo = "C:\Users\rasla\Downloads\destiny-preservation\RE_build\Sunrise-fork"
$root = "C:\Users\rasla\Downloads\destiny-preservation"
$newToken = [System.Guid]::NewGuid().ToString("N")   # generate fresh per run; then sync to BOTH Mac runtime settings
if (-not (Test-Path "$repo\.git")) { Write-Host "!! repo not found"; exit 1 }

Write-Host "=== 1. fetch origin (the converged history) ==="
git -C $repo fetch origin --prune
git -C $repo fetch upstream --prune   # keep upstream refs fresh

Write-Host "=== 2. move the rig's branches to the converged line ==="
# The rig's master/integration/... were the originals; the Mac's converged line now
# contains everything (integration = upstream-0.3.2 + S1/S2 + 138 rig-era commits
# + the 6 port fixes + Mac tooling). The rig resets its refs to origin's versions.
git -C $repo branch -f integration origin/integration
git -C $repo branch -f master origin/master
git -C $repo branch -f inventory-folded-s2 origin/inventory-folded-s2
Write-Host "refs moved:"
git -C $repo log --oneline -2 integration

Write-Host "`n=== 3. worktree re-registration ==="
git -C $repo worktree prune
# The inventory worktree now tracks integration (the dev line).
git -C $repo worktree add --force "$repo\..\Sunrise-fork-inventory" integration 2>&1 | Select-Object -First 3
# The folded worktree keeps its own branch.
git -C $repo worktree add --force "$repo\..\Sunrise-fork-folded" inventory-folded-s2 2>&1 | Select-Object -First 3
git -C $repo worktree list

Write-Host "`n=== 4. line-ending normalization (LF working trees) ==="
git -C $repo config core.autocrlf false
foreach ($wt in @("$repo","$repo\..\Sunrise-fork-inventory")) {
  git -C $wt add --renormalize . 2>$null
  git -C $wt checkout -- . 2>$null
}

Write-Host "`n=== 5. token rotation in the rig's runtime settings ==="
foreach ($sf in @(
  "$root\RE_output\s1_accept\settings.json",
  "$root\RE_output\s1_accept\Sunrise\settings.json")) {
  if (Test-Path $sf) {
    $j = Get-Content $sf -Raw | ConvertFrom-Json
    if (-not $j.server) { $j | Add-Member -NotePropertyName server -NotePropertyValue @{} }
    $j.server.bootstrap_token = $newToken
    $j | ConvertTo-Json -Depth 10 | Set-Content $sf -Encoding UTF8
    Write-Host "token set: $sf"
  }
}
$clientSettings = @("$root\dcv build\bin\x64\Sunrise\settings.json") | Where-Object { Test-Path $_ }
foreach ($sf in $clientSettings) {
  $j = Get-Content $sf -Raw | ConvertFrom-Json
  if ($j.server) { $j.server.bootstrap_token = $newToken
    $j | ConvertTo-Json -Depth 10 | Set-Content $sf -Encoding UTF8
    Write-Host "token set: $sf" }
}

Write-Host "`n=== 6. REBUILD + RESTAMP CHECKLIST (do these next, manually) ==="
Write-Host " A. Build from the converged tree: MSBuild Sunrise\sunrise-server.vcxproj + the client DLL"
Write-Host " B. The rebuild invalidates build_data.bin identity (ts/size) ->"
Write-Host "    boot once, read the logged expected_ts/expected_size, patch the cache"
Write-Host "    header offsets 12 (imageTimestamp) + 16 (imageSize), u32 LE, then boot again."
Write-Host " C. The pre-existing cached_eq vs expected_eq WARN is benign - do not chase it."
Write-Host " D. Deploy only after a clean boot + the acceptance-hash re-verification."
Write-Host "SYNC DONE."