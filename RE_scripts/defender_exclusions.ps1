$paths = @(
    'C:\Users\rasla\Downloads\destiny-preservation',
    'C:\Users\rasla\tools\ghidra_12.1.2_PUBLIC',
    'C:\Users\rasla\AppData\Local\Temp\opencode',
    'C:\Users\rasla\AppData\Roaming\opencode',
    'C:\Users\rasla\.config\opencode'
)
foreach ($p in $paths) {
    if (Test-Path $p) {
        Add-MpPreference -ExclusionPath $p -ErrorAction Continue
    } else {
        Write-Output "SKIPPED (missing): $p"
    }
}
Write-Output '--- current exclusions ---'
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
