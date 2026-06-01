param(
    [string]$Version = "2.1.0",
    [string]$OutputDir
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $OutputDir) {
    $OutputDir = Join-Path $repoRoot "frontend\dist\downloads"
}

$installerName = "LegalAI-Setup-v$Version.exe"
$zipName = "LegalAI-Windows-Client-v$Version.zip"
$installerPath = Join-Path $repoRoot "client\dist-installer\$installerName"
$manualPath = Join-Path $repoRoot "client\WINDOWS_CLIENT_USER_GUIDE.txt"
$stagingDir = Join-Path $env:TEMP "legal-ai-windows-client-v$Version"
$zipPath = Join-Path $OutputDir $zipName
$manualFileName = [string]::Concat([char]0x4f7f, [char]0x7528, [char]0x8bf4, [char]0x660e, [char]0x4e66, ".txt")

if (-not (Test-Path $installerPath)) {
    throw "Windows client installer not found: $installerPath"
}

if (-not (Test-Path $manualPath)) {
    throw "Windows client user guide not found: $manualPath"
}

if (Test-Path $stagingDir) {
    Remove-Item -LiteralPath $stagingDir -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $stagingDir | Out-Null
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

Copy-Item -LiteralPath $installerPath -Destination (Join-Path $stagingDir $installerName) -Force
Copy-Item -LiteralPath $manualPath -Destination (Join-Path $stagingDir $manualFileName) -Force

if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Compress-Archive -Path (Join-Path $stagingDir "*") -DestinationPath $zipPath -CompressionLevel Optimal -Force

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
try {
    $entryNames = @($zip.Entries | ForEach-Object { $_.FullName })
} finally {
    $zip.Dispose()
}

$requiredEntries = @($installerName, $manualFileName)
foreach ($entry in $requiredEntries) {
    if ($entryNames -notcontains $entry) {
        throw "Windows client zip is missing required entry: $entry"
    }
}

Remove-Item -LiteralPath $stagingDir -Recurse -Force

$zipFile = Get-Item -LiteralPath $zipPath
Write-Host "Packaged Windows client download: $($zipFile.FullName)"
Write-Host "Size: $($zipFile.Length) bytes"
