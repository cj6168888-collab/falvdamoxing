param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,
    [string]$Container = "legal-postgres-prod",
    [string]$Database = "",
    [string]$User = "",
    [string]$EnvFile = ".env.prod",
    [switch]$ConfirmRestore
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

if (-not $ConfirmRestore) {
    throw "Restore is destructive. Re-run with -ConfirmRestore after verifying BackupFile, Database, and Container."
}

if (-not (Test-Path -LiteralPath $BackupFile)) {
    throw "Backup file not found: $BackupFile"
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

$resolved = Resolve-Path -LiteralPath $BackupFile
$fileName = Split-Path -Leaf $resolved
$containerPath = "/tmp/$fileName"

Write-Host "Copying backup into container: $resolved"
docker cp $resolved "${Container}:$containerPath"
if ($LASTEXITCODE -ne 0) {
    throw "docker cp failed"
}

Write-Host "Terminating active database sessions for $Database"
docker exec $Container psql -U $User -d postgres -v ON_ERROR_STOP=1 -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '$Database' and pid <> pg_backend_pid();" | Out-Null

Write-Host "Dropping and recreating database: $Database"
docker exec $Container psql -U $User -d postgres -v ON_ERROR_STOP=1 -c "drop database if exists $Database;" | Out-Null
docker exec $Container psql -U $User -d postgres -v ON_ERROR_STOP=1 -c "create database $Database owner $User;" | Out-Null

Write-Host "Restoring backup"
docker exec $Container pg_restore -U $User -d $Database --clean --if-exists $containerPath
if ($LASTEXITCODE -ne 0) {
    throw "pg_restore failed"
}

docker exec $Container rm -f $containerPath | Out-Null
Write-Host "Restore completed: $Database"
