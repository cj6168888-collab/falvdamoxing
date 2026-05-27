param(
    [string]$ComposeFile = "docker-compose.prod.yml",
    [string]$Container = "legal-postgres-prod",
    [string]$Database = "",
    [string]$User = "",
    [string]$OutputDir = "backups",
    [string]$EnvFile = ".env.prod"
)

$ErrorActionPreference = "Stop"

function Read-EnvFile {
    param([string]$Path)

    $values = @{}
    if (-not (Test-Path -LiteralPath $Path)) {
        return $values
    }

    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }
        $idx = $trimmed.IndexOf("=")
        if ($idx -lt 1) {
            continue
        }
        $key = $trimmed.Substring(0, $idx).Trim()
        $value = $trimmed.Substring($idx + 1).Trim().Trim('"').Trim("'")
        $values[$key] = $value
    }
    return $values
}

$envValues = Read-EnvFile $EnvFile
if (-not $Database) {
    $Database = $envValues["POSTGRES_DB"]
}
if (-not $User) {
    $User = $envValues["POSTGRES_USER"]
}
if (-not $Database) {
    throw "Database is required. Pass -Database or set POSTGRES_DB in $EnvFile."
}
if (-not $User) {
    throw "User is required. Pass -User or set POSTGRES_USER in $EnvFile."
}

docker inspect $Container | Out-Null

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$fileName = "${Database}_${stamp}.dump"
$containerPath = "/tmp/$fileName"
$hostPath = Join-Path $OutputDir $fileName

Write-Host "Creating PostgreSQL backup: ${Container}:$containerPath"
docker exec $Container pg_dump -U $User -d $Database -Fc -f $containerPath
if ($LASTEXITCODE -ne 0) {
    throw "pg_dump failed"
}

docker cp "${Container}:$containerPath" $hostPath
if ($LASTEXITCODE -ne 0) {
    throw "docker cp failed"
}

docker exec $Container rm -f $containerPath | Out-Null

$resolved = Resolve-Path -LiteralPath $hostPath
$size = (Get-Item -LiteralPath $resolved).Length
Write-Host "Backup written: $resolved ($size bytes)"
