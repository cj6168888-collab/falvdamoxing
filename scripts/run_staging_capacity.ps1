param(
    [int]$HealthConcurrency = 200,
    [int]$ApiConcurrency = 200,
    [int]$DurationSeconds = 30,
    [int]$AppReplicas = 4,
    [string]$BaseUrl = "http://127.0.0.1:8080",
    [string]$Username = "loadtest-admin",
    [string]$Password = "loadtest-password-123456"
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = if ($env:PYTHON_EXE) {
    $env:PYTHON_EXE
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    "py"
} else {
    throw "Python was not found. Set PYTHON_EXE to a Python executable with project dependencies installed."
}
$Compose = @("--env-file", ".env.staging.example", "-f", "docker-compose.staging.yml")

if (-not $env:COMPOSE_BAKE) {
    $env:COMPOSE_BAKE = "false"
}
if (-not $env:DOCKER_BUILDKIT) {
    $env:DOCKER_BUILDKIT = "0"
}

Push-Location $Root
try {
    & $Python scripts/validate_production_config.py .env.staging.example --expected-app-replicas $AppReplicas
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    docker compose @Compose config --quiet
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    docker compose @Compose build app frontend pgbouncer
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    docker compose @Compose up -d postgres redis sms-mock
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    docker compose @Compose --profile migrate run --rm migrate
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    docker compose @Compose up -d --scale app=$AppReplicas app frontend nginx
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing "$BaseUrl/ready" -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                $ready = $true
                break
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    if (-not $ready) {
        throw "Staging stack did not become ready at $BaseUrl/ready"
    }

    docker compose @Compose run --rm app python scripts/seed_load_test_user.py --username $Username --password $Password
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    & $Python scripts/load_test_api.py --base-url $BaseUrl --endpoint /health --concurrency $HealthConcurrency --duration $DurationSeconds --target-p95-ms 500
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    & $Python scripts/load_test_api.py --base-url $BaseUrl --username $Username --password $Password --endpoint /api/cases --concurrency $ApiConcurrency --duration $DurationSeconds --target-p95-ms 1000
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}
