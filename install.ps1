param(
    [string]$CodexHome = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }),
    [string[]]$SkillName = @('diansai-collab'),
    [switch]$All,
    [switch]$FromGitHub
)

$ErrorActionPreference = 'Stop'

if ($FromGitHub) {
    $tmp = Join-Path ([IO.Path]::GetTempPath()) ('agent-diansai-skill-' + [guid]::NewGuid().ToString('N'))
    git clone https://github.com/54xkeee/agent-diansai-skill.git $tmp
    if ($LASTEXITCODE -ne 0) { throw 'Git clone failed; installation stopped.' }
    & (Join-Path $tmp 'install.ps1') -CodexHome $CodexHome -SkillName $SkillName -All:$All
    Write-Host "Source checkout retained at: $tmp"
    return
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceSkills = Join-Path $repoRoot 'skills'
$homePath = [IO.Path]::GetFullPath($CodexHome)
$targetSkills = Join-Path $homePath 'skills'

function Assert-PlainPath([string]$Path) {
    $current = [IO.Path]::GetFullPath($Path)
    while ($current) {
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Linked path needs manual review: $current"
            }
        }
        $current = Split-Path -Parent $current
    }
}

function Get-ContentDigest([string]$Path) {
    $hash = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try { return [Convert]::ToBase64String($hash.ComputeHash($stream)) }
    finally { $stream.Dispose(); $hash.Dispose() }
}

if ($All) {
    $SkillName = @(Get-ChildItem -LiteralPath $sourceSkills -Directory | Select-Object -ExpandProperty Name)
}
$selected = @($SkillName | Select-Object -Unique)
if ($selected.Count -eq 0) { throw 'No skills selected.' }

# Validate every selected source and destination before writing any files.
Assert-PlainPath $targetSkills
foreach ($name in $selected) {
    if ($name -notmatch '^[a-z0-9]+(-[a-z0-9]+)*$') { throw "Invalid skill name: $name" }
    $source = Join-Path $sourceSkills $name
    $target = Join-Path $targetSkills $name
    if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) {
        throw "Skill source missing: $name"
    }
    if ([IO.Path]::GetFullPath($source).TrimEnd('\', '/') -eq [IO.Path]::GetFullPath($target).TrimEnd('\', '/')) {
        throw 'Source and installation path must differ.'
    }
    foreach ($path in @($source, $target)) {
        Assert-PlainPath $path
        if (Test-Path -LiteralPath $path) {
            $links = @(Get-ChildItem -LiteralPath $path -Recurse -Force | Where-Object {
                $_.Attributes -band [IO.FileAttributes]::ReparsePoint
            })
            if ($links.Count) { throw "Linked skill contents need manual review: $path" }
        }
    }
}

$backupRoot = Join-Path (Join-Path $homePath 'skill-backups') ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N'))
Assert-PlainPath $backupRoot
foreach ($name in $selected) {
    $target = Join-Path $targetSkills $name
    if (Test-Path -LiteralPath $target) {
        New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
        Copy-Item -LiteralPath $target -Destination (Join-Path $backupRoot $name) -Recurse
        Write-Host "Backup: $(Join-Path $backupRoot $name)"
    }
}

foreach ($name in $selected) {
    $source = Join-Path $sourceSkills $name
    $target = Join-Path $targetSkills $name
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    Get-ChildItem -LiteralPath $source -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse -Force
    }
    foreach ($file in Get-ChildItem -LiteralPath $source -Recurse -File -Force) {
        $relative = $file.FullName.Substring($source.Length).TrimStart('\', '/')
        if ((Get-ContentDigest $file.FullName) -ne (Get-ContentDigest (Join-Path $target $relative))) {
            throw "Installed file verification failed: $relative"
        }
    }
    Write-Host "Installed and verified: $name"
}
Write-Host "Verified $($selected.Count) selected skills in: $targetSkills"
Write-Host 'Files installed. Confirm skill loading separately in a new assistant session.'
