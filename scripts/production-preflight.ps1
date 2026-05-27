param(
    [string]$EnvFile = ".env.prod",
    [string]$RuntimeConfigFile = "data/config/api-keys.env",
    [string]$ComposeFile = "docker-compose.prod.yml",
    [switch]$RequireExternalApis,
    [switch]$RequireTls
)

$ErrorActionPreference = "Stop"

function Write-Check {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Detail = ""
    )

    $line = "{0,-36} {1}" -f $Name, $Status
    if ($Detail) {
        $line = "$line  $Detail"
    }
    Write-Host $line
}

function Read-EnvFile {
    param([string]$Path)

    $values = @{}
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Environment file not found: $Path"
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

function Test-Placeholder {
    param([AllowNull()][string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $true
    }
    $lower = $Value.ToLowerInvariant()
    return $lower.Contains("change_me") -or
        $lower.Contains("your_") -or
        $lower.Contains("your-") -or
        $lower.Contains("your-domain.com") -or
        $lower.Contains("example.com")
}

function Test-Http {
    param(
        [string]$Name,
        [string]$Url,
        [int[]]$AllowedStatus = @(200)
    )

    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 15
        if ($AllowedStatus -contains [int]$response.StatusCode) {
            Write-Check $Name "PASS" "HTTP $($response.StatusCode)"
            return $true
        }
        Write-Check $Name "FAIL" "HTTP $($response.StatusCode)"
        return $false
    }
    catch {
        $statusCode = $null
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }
        if ($statusCode -and ($AllowedStatus -contains $statusCode)) {
            Write-Check $Name "PASS" "HTTP $statusCode"
            return $true
        }
        Write-Check $Name "FAIL" $_.Exception.Message
        return $false
    }
}

$failures = 0
$warnings = 0

try {
    $envValues = Read-EnvFile $EnvFile
    Write-Check "env file" "PASS" $EnvFile
}
catch {
    Write-Check "env file" "FAIL" $_.Exception.Message
    exit 1
}

if (Test-Path -LiteralPath $RuntimeConfigFile) {
    $runtimeValues = Read-EnvFile $RuntimeConfigFile
    foreach ($key in $runtimeValues.Keys) {
        if (-not $envValues.ContainsKey($key) -or (Test-Placeholder $envValues[$key])) {
            $envValues[$key] = $runtimeValues[$key]
        }
    }
    Write-Check "runtime config file" "PASS" $RuntimeConfigFile
}
else {
    Write-Check "runtime config file" "SKIP" "not found; using env file only"
}

$required = @(
    "POSTGRES_USER",
    "POSTGRES_DB",
    "POSTGRES_PASSWORD",
    "DATABASE_URL",
    "REDIS_PASSWORD",
    "REDIS_URL",
    "APP_ENV",
    "SECRET_KEY",
    "JWT_SECRET",
    "CORS_ORIGINS",
    "FILE_STORAGE_PATH"
)

foreach ($key in $required) {
    $value = $envValues[$key]
    if (Test-Placeholder $value) {
        Write-Check "env $key" "FAIL" "missing or placeholder"
        $failures++
    }
    else {
        Write-Check "env $key" "PASS"
    }
}

if (($envValues["APP_ENV"] -ne "production")) {
    Write-Check "APP_ENV production" "FAIL" "APP_ENV must be production"
    $failures++
}
else {
    Write-Check "APP_ENV production" "PASS"
}

$cors = ($envValues["CORS_ORIGINS"] -split ",") | ForEach-Object { $_.Trim().ToLowerInvariant() } | Where-Object { $_ }
if ($cors -contains "*" -or ($cors | Where-Object { $_.Contains("localhost") -or $_.Contains("127.0.0.1") })) {
    Write-Check "CORS production origins" "FAIL" "wildcard/localhost origins are not allowed"
    $failures++
}
else {
    Write-Check "CORS production origins" "PASS"
}

$externalKeys = @(
    "DASHSCOPE_API_KEY",
    "LAW_API_KEY",
    "COMPANY_INFO_API_BASE_URL",
    "COMPANY_INFO_API_KEY"
)
foreach ($key in $externalKeys) {
    $configured = -not (Test-Placeholder $envValues[$key])
    if ($configured) {
        Write-Check "external $key" "PASS"
    }
    elseif ($RequireExternalApis) {
        Write-Check "external $key" "FAIL" "required but not configured"
        $failures++
    }
    else {
        Write-Check "external $key" "WARN" "not configured"
        $warnings++
    }
}

$certPath = "config/nginx/ssl/fullchain.pem"
$keyPath = "config/nginx/ssl/privkey.pem"
$hasTls = (Test-Path -LiteralPath $certPath) -and (Test-Path -LiteralPath $keyPath)
if ($hasTls) {
    Write-Check "TLS certificate files" "PASS"
}
elseif ($RequireTls) {
    Write-Check "TLS certificate files" "FAIL" "missing fullchain.pem or privkey.pem"
    $failures++
}
else {
    Write-Check "TLS certificate files" "WARN" "missing; HTTP-only local stack can still run"
    $warnings++
}

if (Test-Path -LiteralPath $ComposeFile) {
    Write-Check "compose file" "PASS" $ComposeFile
}
else {
    Write-Check "compose file" "FAIL" "$ComposeFile not found"
    $failures++
}

$dockerAvailable = $false
try {
    docker version --format "{{.Server.Version}}" | Out-Null
    $dockerAvailable = $true
    Write-Check "docker daemon" "PASS"
}
catch {
    Write-Check "docker daemon" "WARN" "not reachable; skipping live checks"
    $warnings++
}

if ($dockerAvailable) {
    try {
        docker compose -f $ComposeFile config --quiet
        Write-Check "compose config" "PASS"
    }
    catch {
        Write-Check "compose config" "FAIL" $_.Exception.Message
        $failures++
    }

    try {
        docker compose -f $ComposeFile ps | Out-Null
        Write-Check "compose ps" "PASS"
    }
    catch {
        Write-Check "compose ps" "WARN" "stack is not running or compose project is unavailable"
        $warnings++
    }

    if (-not (Test-Http "HTTP /ready" "http://127.0.0.1/ready")) {
        $failures++
    }
    # In production this endpoint may require auth. HTTP 401 still proves the
    # route is reachable and protected; authenticated smoke tests validate
    # provider behavior separately.
    if (-not (Test-Http "HTTP /api/llm/router/status" "http://127.0.0.1:8000/api/llm/router/status" @(200, 401))) {
        $failures++
    }
    if (-not (Test-Http "HTTP /api/third-party/health" "http://127.0.0.1:8000/api/third-party/health")) {
        $failures++
    }
}

Write-Host ""
Write-Host "Preflight summary: failures=$failures warnings=$warnings"

if ($failures -gt 0) {
    exit 1
}
