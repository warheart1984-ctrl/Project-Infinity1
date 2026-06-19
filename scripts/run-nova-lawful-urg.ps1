# Run Lawful Nova from URG (Windows)
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$env:LAWFUL_NOVA_REPO_ROOT = $RepoRoot
if (-not $env:PYTHONPATH) { $env:PYTHONPATH = $RepoRoot } else { $env:PYTHONPATH = "$RepoRoot;$env:PYTHONPATH" }
& "$PSScriptRoot\nova-bootstrap-lsg.ps1"
if ($args.Count -gt 0) {
    python -m nova @args
} else {
    python -m nova health
}
