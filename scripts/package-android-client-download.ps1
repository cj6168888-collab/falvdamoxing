param(
    [string]$Version = "2.1.0",
    [string]$OutputDir,
    [switch]$Required
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $OutputDir) {
    $OutputDir = Join-Path $repoRoot "frontend\dist\downloads"
}

$apkName = "LegalAI-Android-Client-v$Version.apk"
$candidatePaths = @(
    (Join-Path $repoRoot "client\android\dist\$apkName"),
    (Join-Path $repoRoot "client\dist-android\$apkName"),
    (Join-Path $repoRoot "client\mobile\$apkName")
)

$apkPath = $candidatePaths | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not $apkPath) {
    $message = "Android APK not found. Expected one of: $($candidatePaths -join ', ')"
    if ($Required) {
        throw $message
    }
    Write-Host "$message. Skipping Android APK packaging."
    exit 0
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$targetPath = Join-Path $OutputDir $apkName
Copy-Item -LiteralPath $apkPath -Destination $targetPath -Force

$apkFile = Get-Item -LiteralPath $targetPath
Write-Host "Packaged Android APK download: $($apkFile.FullName)"
Write-Host "Size: $($apkFile.Length) bytes"

