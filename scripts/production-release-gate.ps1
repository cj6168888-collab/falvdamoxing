param(
    [string]$EnvFile = ".env.prod",
    [string]$ComposeFile = "docker-compose.prod.yml",
    [switch]$RequireExternalApis,
    [switch]$RequireTls,
    [switch]$SkipBackup,
    [switch]$SkipAudits,
    [switch]$SkipAiAudit,
    [switch]$SkipBrowserAudit
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Block
    )

    Write-Host ""
    Write-Host "== $Name =="
    & $Block
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed"
    }
}

Invoke-Step "Production preflight" {
    $args = @("-ExecutionPolicy", "Bypass", "-File", "scripts\production-preflight.ps1", "-EnvFile", $EnvFile, "-ComposeFile", $ComposeFile)
    if ($RequireExternalApis) { $args += "-RequireExternalApis" }
    if ($RequireTls) { $args += "-RequireTls" }
    powershell @args
}

if (-not $SkipBackup) {
    Invoke-Step "Database backup" {
        powershell -ExecutionPolicy Bypass -File scripts\production-backup.ps1 -EnvFile $EnvFile -ComposeFile $ComposeFile
    }
}

Invoke-Step "Migration check" {
    docker compose --env-file $EnvFile -f $ComposeFile run --rm app python -m app.db.migrate_all --check
}

if (-not $SkipAudits) {
    Invoke-Step "Bokai data lifecycle audit" {
        node scripts\bokai-function-audit.mjs --mode=data --skip-browser --timeout-ms=30000 --ai-timeout-ms=240000 --request-delay-ms=800
    }

    if (-not $SkipAiAudit) {
        Invoke-Step "Bokai AI audit" {
            node scripts\bokai-function-audit.mjs --mode=ai --skip-browser --include-expensive --include-debate --timeout-ms=30000 --ai-timeout-ms=240000 --expensive-timeout-ms=900000 --request-delay-ms=600
        }
    }

    if (-not $SkipBrowserAudit) {
        Invoke-Step "Browser route audit" {
            node scripts\bokai-function-audit.mjs --mode=browser --timeout-ms=30000 --request-delay-ms=300
        }
    }
}

Invoke-Step "Audit residue check" {
    docker exec legal-postgres-prod psql -U legal_user -d legal_db -t -A -c "select 'case3_evidence', count(*) from evidence_items_v2 where case_id=3 union all select 'letters', count(*) from letters where case_id=3 union all select 'audit_temp_cases', count(*) from cases where title like 'Bokai Audit Temp Case %' union all select 'audit_leftovers', (select count(*) from reminders where title like 'Bokai Audit Reminder %') + (select count(*) from letters where case_id=3 and title like '%审计临时%') + (select count(*) from adversarial_analyses where case_id=3 and title like '对抗性分析报告 - %') + (select count(*) from legal_deadlines where case_id=3 and deadline_name like 'Bokai Audit Deadline %');"
}

Write-Host ""
Write-Host "Production release gate completed."
