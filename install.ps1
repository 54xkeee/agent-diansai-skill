param(
    [string]$CodexHome = (Join-Path $HOME ".codex")
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceSkills = Join-Path $repoRoot "skills"
$targetSkills = Join-Path $CodexHome "skills"

if (-not (Test-Path -LiteralPath $sourceSkills)) {
    throw "Cannot find skills directory: $sourceSkills"
}

New-Item -ItemType Directory -Force -Path $targetSkills | Out-Null

Get-ChildItem -LiteralPath $sourceSkills -Directory | ForEach-Object {
    $target = Join-Path $targetSkills $_.Name
    New-Item -ItemType Directory -Force -Path $target | Out-Null
    Copy-Item -Path (Join-Path $_.FullName "*") -Destination $target -Recurse -Force
    Write-Host "Installed skill: $($_.Name)"
}

Write-Host "Done. Skills installed to: $targetSkills"
