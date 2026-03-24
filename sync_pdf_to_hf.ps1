param(
    [switch]$Push,
    [string]$Message = "deploy: sync pdf service from main repo"
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceDir = Join-Path $repoRoot "finsight-pdf"
$hfCloneDir = Join-Path (Split-Path $repoRoot -Parent) "finsight-pdf-hf"

if (-not (Test-Path $sourceDir)) {
    throw "Source directory not found: $sourceDir"
}

if (-not (Test-Path $hfCloneDir)) {
    throw "HF clone not found: $hfCloneDir"
}

if (-not (Test-Path (Join-Path $hfCloneDir ".git"))) {
    throw "HF clone has no .git directory: $hfCloneDir"
}

# Keep HF clone current before syncing files.
Push-Location $hfCloneDir
try {
    git checkout main
    git pull origin main
}
finally {
    Pop-Location
}

# Mirror source into HF clone, excluding git metadata and caches.
robocopy $sourceDir $hfCloneDir /MIR /XD ".git" "__pycache__" > $null
$robocopyExit = $LASTEXITCODE
if ($robocopyExit -ge 8) {
    throw "Robocopy failed with exit code $robocopyExit"
}

Push-Location $hfCloneDir
try {
    $status = git status --short
    if (-not $status) {
        Write-Output "No HF changes to commit."
        exit 0
    }

    Write-Output "HF clone has changes:"
    Write-Output $status

    if ($Push) {
        git add .
        git commit -m $Message
        git push origin main
        Write-Output "HF push complete."
    } else {
        Write-Output "Preview only. Run with -Push to commit and push to Hugging Face."
    }
}
finally {
    Pop-Location
}
