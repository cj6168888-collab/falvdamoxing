param(
    [string]$EnvFile = ".env.staging.example",
    [string]$ComposeFile = "docker-compose.staging.yml",
    [int]$Samples = 12,
    [int]$IntervalSeconds = 5,
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Compose = @("--env-file", $EnvFile, "-f", $ComposeFile)

function Convert-LinesToJsonObjects {
    param([string[]]$Lines)
    $items = @()
    foreach ($line in $Lines) {
        if (-not [string]::IsNullOrWhiteSpace($line)) {
            $items += ($line | ConvertFrom-Json)
        }
    }
    return $items
}

function Convert-RedisInfo {
    param([string[]]$Lines)
    $info = @{}
    foreach ($line in $Lines) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
            continue
        }
        $parts = $line.Split(":", 2)
        if ($parts.Count -eq 2) {
            $info[$parts[0]] = $parts[1]
        }
    }
    return $info
}

if ($Samples -le 0) {
    throw "Samples must be greater than 0."
}
if ($IntervalSeconds -le 0) {
    throw "IntervalSeconds must be greater than 0."
}

Push-Location $Root
try {
    if (-not $OutputPath) {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $OutputPath = Join-Path $Root "logs\staging-metrics-$stamp.jsonl"
    }
    $outputDir = Split-Path -Parent $OutputPath
    if ($outputDir) {
        New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
    }

    $postgresSql = @"
select json_build_object(
  'max_connections', current_setting('max_connections')::int,
  'database_size_bytes', pg_database_size(current_database()),
  'connections_total', (select count(*) from pg_stat_activity),
  'connections_by_state', coalesce((
    select json_agg(row_to_json(t))
    from (
      select coalesce(state, 'none') as state, count(*)::int as count
      from pg_stat_activity
      group by state
      order by state
    ) t
  ), '[]'::json),
  'oldest_query_seconds', coalesce((
    select extract(epoch from now() - min(query_start))
    from pg_stat_activity
    where state = 'active' and query_start is not null
  ), 0)
);
"@

    for ($i = 0; $i -lt $Samples; $i++) {
        $timestamp = (Get-Date).ToUniversalTime().ToString("o")
        $sample = [ordered]@{
            timestamp = $timestamp
            compose = $null
            docker_stats = $null
            postgres = $null
            redis = $null
            errors = @()
        }

        try {
            $psLines = docker compose @Compose ps --format json
            $sample.compose = Convert-LinesToJsonObjects $psLines
        } catch {
            $sample.errors += "compose_ps: $($_.Exception.Message)"
        }

        try {
            $containerIds = @(docker compose @Compose ps -q | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
            if ($containerIds.Count -gt 0) {
                $statLines = docker stats --no-stream --format "{{json .}}" $containerIds
                $sample.docker_stats = Convert-LinesToJsonObjects $statLines
            } else {
                $sample.docker_stats = @()
            }
        } catch {
            $sample.errors += "docker_stats: $($_.Exception.Message)"
        }

        try {
            $pgRaw = $postgresSql | docker compose @Compose exec -T postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atq'
            $sample.postgres = ($pgRaw | Select-Object -First 1 | ConvertFrom-Json)
        } catch {
            $sample.errors += "postgres: $($_.Exception.Message)"
        }

        try {
            $redisLines = docker compose @Compose exec -T redis sh -lc 'redis-cli -a "$REDIS_PASSWORD" --no-auth-warning INFO stats; redis-cli -a "$REDIS_PASSWORD" --no-auth-warning INFO memory'
            $sample.redis = Convert-RedisInfo $redisLines
        } catch {
            $sample.errors += "redis: $($_.Exception.Message)"
        }

        $json = $sample | ConvertTo-Json -Depth 10 -Compress
        Add-Content -Encoding utf8 -Path $OutputPath -Value $json
        Write-Output $json

        if ($i -lt ($Samples - 1)) {
            Start-Sleep -Seconds $IntervalSeconds
        }
    }

    Write-Output "metrics_output=$OutputPath"
} finally {
    Pop-Location
}
