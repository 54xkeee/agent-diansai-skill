param(
    [string]$CodexHome = (Join-Path $HOME ".codex"),
    [switch]$FromGitHub
)

$ErrorActionPreference = "Stop"

# 如果从 GitHub 直接安装，先 clone 到临时目录再递归调用
if ($FromGitHub) {
    $tmp = Join-Path $env:TEMP "agent-diansai-skill"
    if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
    Write-Host "Cloning from GitHub..."
    git clone https://github.com/54xkeee/agent-diansai-skill.git $tmp
    & (Join-Path $tmp "install.ps1") -CodexHome $CodexHome
    Remove-Item -Recurse -Force $tmp
    return
}

$repoRoot    = Split-Path -Parent $MyInvocation.MyCommand.Path
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

Write-Host ""
Write-Host "Done. Skills installed to: $targetSkills"
Write-Host ""
Write-Host "Available skills:"
Get-ChildItem -LiteralPath $targetSkills -Directory | ForEach-Object {
    $skillMd = Join-Path $_.FullName "SKILL.md"
    if (Test-Path $skillMd) {
        $desc = Select-String -Path $skillMd -Pattern "^description:" | Select-Object -First 1
        if ($desc) {
            $descText = $desc.Line -replace "^description:\s*", ""
            Write-Host "  - $($_.Name): $descText"
        } else {
            Write-Host "  - $($_.Name)"
        }
    }
}
