<#
  P2-D1 rig settings survey - READ ONLY. Writes nothing.

  Prints the identity fields that decide the dual-client boot, plus an
  occurrence census of the two account soid bands, so the follow-up edit can
  be targeted instead of a blind global replace.

  Run:  powershell -NoProfile -ExecutionPolicy Bypass -File survey_settings.ps1
  Optional: -Root "<path to ...\bin\x64\Sunrise>"
#>
param([string]$Root = "")

$ErrorActionPreference = "Stop"

function Test-Candidate {
    param([string]$Dir)
    if ($Dir -eq "") { return $false }
    try { return (Test-Path -LiteralPath ($Dir + "\settings.json") -ErrorAction SilentlyContinue) }
    catch { return $false }
}

function Find-Root {
    param([string]$Given)
    if (Test-Candidate $Given) { return $Given }
    $candidates = @(
        "C:\Users\rasla\Desktop\dcv build\bin\x64\Sunrise",
        "C:\dcv build\bin\x64\Sunrise",
        "D:\dcv build\bin\x64\Sunrise",
        "E:\dcv build\bin\x64\Sunrise"
    )
    foreach ($c in $candidates) {
        if (Test-Candidate $c) { return $c }
    }
    # Fall back to a search of every fixed drive for the known tail. Bounded by
    # the filter; errors on unreadable branches are skipped, not fatal.
    $roots = @()
    try {
        $roots = @(Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue |
                   ForEach-Object { $_.Root })
    } catch { $roots = @("C:\") }
    foreach ($r in $roots) {
        $hit = $null
        try {
            $hit = Get-ChildItem -LiteralPath $r -Filter "settings.json" -Recurse -Force `
                     -ErrorAction SilentlyContinue |
                   Where-Object { $_.FullName -like "*\bin\x64\Sunrise\settings.json" } |
                   Select-Object -First 1
        } catch { $hit = $null }
        if ($hit) { return $hit.Directory.FullName }
    }
    return ""
}

$root = Find-Root -Given $Root
if ($root -eq "") {
    Write-Output "SURVEY result=fail reason=settings_not_found"
    exit 1
}
Write-Output ("SURVEY root=" + $root)

function Show-File {
    param([string]$Label, [string]$Path)
    if (-not (Test-Path $Path)) {
        Write-Output ("$Label absent path=" + $Path)
        return
    }
    $item = Get-Item $Path
    $sha  = (Get-FileHash -Algorithm SHA256 -Path $Path).Hash.Substring(0,16)
    Write-Output ("$Label size=" + $item.Length + " mtime=" + $item.LastWriteTime.ToString("s") + " sha256=" + $sha)

    $raw = Get-Content -Path $Path -Raw
    $json = $raw | ConvertFrom-Json

    $acct = $null
    try { $acct = $json.state.account.primary_soid } catch {}
    Write-Output ("$Label state.account.primary_soid=" + $acct)

    $chars = @()
    try { $chars = @($json.state.characters | ForEach-Object { $_.soid }) } catch {}
    Write-Output ("$Label state.characters.soid=" + ($chars -join ","))

    $slots = @()
    try {
        $i = 0
        foreach ($a in @($json.state.accounts)) {
            $p = $a.account.primary_soid
            if ($null -eq $p) { $p = $a.primary_soid }
            $slots += ("slot$i=" + $p)
            $i++
        }
    } catch {}
    Write-Output ("$Label state.accounts=" + ($slots -join " "))

    $guid = $null
    foreach ($p in @("content_manifest","content")) {
        try { if ($null -ne $json.$p.config_guid) { $guid = $json.$p.config_guid } } catch {}
    }
    if ($null -eq $guid) {
        $m = [regex]::Match($raw, '"config_guid"\s*:\s*"([^"]+)"')
        if ($m.Success) { $guid = $m.Groups[1].Value }
    }
    Write-Output ("$Label config_guid=" + $guid)

    $tok = $null
    try { $tok = $json.server.bootstrap_token } catch {}
    if ($tok -ne $null -and $tok.Length -ge 16) { $tok = $tok.Substring(0,16) + ".." }
    Write-Output ("$Label server.bootstrap_token=" + $tok)

    # Occurrence census: how many times each account band appears anywhere in the
    # file. A targeted edit has to know this before touching anything.
    foreach ($band in @("0100100","0110100")) {
        $count = ([regex]::Matches($raw, [regex]::Escape($band))).Count
        Write-Output ("$Label band_" + $band + "_occurrences=" + $count)
    }
}

Show-File -Label "LIVE"   -Path (Join-Path $root "settings.json")
Show-File -Label "RESOID" -Path (Join-Path $root "settings.json.bak_m3g1_resoid")

Write-Output "SURVEY result=ok (nothing written)"
