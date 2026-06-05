param(
    [string]$Version = "2.1.0",
    [string]$GradleVersion = "8.10.2",
    [string]$CommandLineToolsVersion = "14742923",
    [string]$CompileSdk = "35",
    [string]$BuildToolsVersion = "35.0.0"
)

$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [string]$Name,
        [scriptblock]$Block
    )

    Write-Host ""
    Write-Host "== $Name =="
    & $Block
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

function Download-File {
    param(
        [string]$Url,
        [string]$OutFile
    )

    if (Test-Path -LiteralPath $OutFile) {
        $existing = Get-Item -LiteralPath $OutFile
        if ($existing.Length -gt 1048576) {
            return
        }
        Remove-Item -LiteralPath $OutFile -Force
    }

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutFile) | Out-Null
    Write-Host "Downloading $Url"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $downloaded = $false
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            Invoke-WebRequest -Uri $Url -OutFile $OutFile
            $downloaded = $true
            break
        } catch {
            Write-Host "Download attempt $attempt failed: $($_.Exception.Message)"
            if (Test-Path -LiteralPath $OutFile) {
                Remove-Item -LiteralPath $OutFile -Force
            }
            Start-Sleep -Seconds (2 * $attempt)
        }
    }

    if (-not $downloaded) {
        curl.exe -L --retry 5 --retry-delay 3 --fail --output $OutFile $Url
        if ($LASTEXITCODE -ne 0) {
            throw "curl download failed with exit code $LASTEXITCODE"
        }
    }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$androidProject = Join-Path $repoRoot "client\android"
$toolsRoot = Join-Path $repoRoot ".tools"
$sdkRoot = Join-Path $repoRoot ".android-sdk"
$gradleRoot = Join-Path $toolsRoot "gradle-$GradleVersion"
$gradleBat = Join-Path $gradleRoot "bin\gradle.bat"
$cmdlineRoot = Join-Path $sdkRoot "cmdline-tools\latest"
$sdkManager = Join-Path $cmdlineRoot "bin\sdkmanager.bat"

Invoke-Checked "Verify Java" {
    java -version
}

if (-not (Test-Path -LiteralPath $gradleBat)) {
    $gradleZip = Join-Path $toolsRoot "gradle-$GradleVersion-bin.zip"
    Download-File `
        -Url "https://services.gradle.org/distributions/gradle-$GradleVersion-bin.zip" `
        -OutFile $gradleZip

    if (Test-Path -LiteralPath $gradleRoot) {
        Remove-Item -LiteralPath $gradleRoot -Recurse -Force
    }

    Expand-Archive -LiteralPath $gradleZip -DestinationPath $toolsRoot -Force
}

if (-not (Test-Path -LiteralPath $sdkManager)) {
    $cmdlineZip = Join-Path $toolsRoot "commandlinetools-win-$CommandLineToolsVersion`_latest.zip"
    $cmdlineTemp = Join-Path $toolsRoot "cmdline-tools-temp"
    Download-File `
        -Url "https://dl.google.com/android/repository/commandlinetools-win-$CommandLineToolsVersion`_latest.zip" `
        -OutFile $cmdlineZip

    if (Test-Path -LiteralPath $cmdlineTemp) {
        Remove-Item -LiteralPath $cmdlineTemp -Recurse -Force
    }

    Expand-Archive -LiteralPath $cmdlineZip -DestinationPath $cmdlineTemp -Force
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $cmdlineRoot) | Out-Null
    if (Test-Path -LiteralPath $cmdlineRoot) {
        Remove-Item -LiteralPath $cmdlineRoot -Recurse -Force
    }
    Move-Item -LiteralPath (Join-Path $cmdlineTemp "cmdline-tools") -Destination $cmdlineRoot
    Remove-Item -LiteralPath $cmdlineTemp -Recurse -Force
}

$env:ANDROID_HOME = $sdkRoot
$env:ANDROID_SDK_ROOT = $sdkRoot
$env:JAVA_HOME = (Split-Path -Parent (Split-Path -Parent (Get-Command java).Source))

Invoke-Checked "Accept Android SDK licenses" {
    cmd /c "for /L %i in (1,1,20) do @echo y" | & $sdkManager --sdk_root=$sdkRoot --licenses
}

Invoke-Checked "Install Android SDK packages" {
    & $sdkManager --sdk_root=$sdkRoot "platform-tools" "platforms;android-$CompileSdk" "build-tools;$BuildToolsVersion"
}

$localProperties = Join-Path $androidProject "local.properties"
if (Test-Path -LiteralPath $localProperties) {
    Remove-Item -LiteralPath $localProperties -Force
}

Invoke-Checked "Build Android APK" {
    Push-Location $androidProject
    try {
        & $gradleBat --no-daemon clean assembleDebug
    } finally {
        Pop-Location
    }
}

$apkName = "LegalAI-Android-Client-v$Version.apk"
$sourceApk = Join-Path $androidProject "app\build\outputs\apk\debug\app-debug.apk"
$distDir = Join-Path $androidProject "dist"
$targetApk = Join-Path $distDir $apkName

if (-not (Test-Path -LiteralPath $sourceApk)) {
    throw "APK build output not found: $sourceApk"
}

New-Item -ItemType Directory -Force -Path $distDir | Out-Null
Copy-Item -LiteralPath $sourceApk -Destination $targetApk -Force
$apk = Get-Item -LiteralPath $targetApk

Write-Host "Built Android APK: $($apk.FullName)"
Write-Host "Size: $($apk.Length) bytes"
