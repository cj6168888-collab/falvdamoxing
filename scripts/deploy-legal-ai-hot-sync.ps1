param(
    [string]$HostAlias = "jilin-prod",
    [string]$RemoteDir = "/opt/legal-ai",
    [string]$Commit = "HEAD",
    [switch]$SkipFrontendBuild,
    [switch]$SkipTests
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

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$resolvedCommit = (git rev-parse --short $Commit).Trim()
$fullCommit = (git rev-parse $Commit).Trim()
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$releaseTar = "release-$resolvedCommit.tar"
$frontendTar = "frontend-dist-$resolvedCommit.tar"

Invoke-Checked "Verify git commit" {
    git rev-parse --verify $Commit
}

if (-not $SkipTests) {
    Invoke-Checked "Backend guardrail tests" {
        $env:PYTHONPATH = $repoRoot
        pytest tests/test_legal_product_guardrails.py -q
    }

    Invoke-Checked "Frontend typecheck" {
        Push-Location frontend
        try {
            npm run typecheck
        } finally {
            Pop-Location
        }
    }
}

if (-not $SkipFrontendBuild) {
    Invoke-Checked "Build frontend" {
        Push-Location frontend
        try {
            npm run build
        } finally {
            Pop-Location
        }
    }
}

Invoke-Checked "Create release archives" {
    if (Test-Path $releaseTar) { Remove-Item $releaseTar }
    if (Test-Path $frontendTar) { Remove-Item $frontendTar }
    git archive --format=tar --output=$releaseTar $Commit
    tar -cf $frontendTar -C "frontend\dist" .
}

Invoke-Checked "Upload release archives" {
    scp $releaseTar "${HostAlias}:${RemoteDir}/$releaseTar"
    scp $frontendTar "${HostAlias}:${RemoteDir}/$frontendTar"
}

$remoteScriptTemplate = @'
set -e
cd "__REMOTE_DIR__"
mkdir -p deploy-backups
tar -czf "deploy-backups/files-before-__RESOLVED_COMMIT__-__STAMP__.tar.gz" app dist Dockerfile.prod requirements-core.txt requirements-optional.txt requirements-worker.txt requirements.txt pytest.ini migrations scripts docker-compose.fl-prod.yml 2>/dev/null || true
docker exec legal-ai-pg pg_dump -U postgres -d legal_ai -Fc -f "/tmp/legal_ai_before___RESOLVED_COMMIT__.dump"
rm -rf "release-__RESOLVED_COMMIT__" "dist-__RESOLVED_COMMIT__"
mkdir "release-__RESOLVED_COMMIT__" "dist-__RESOLVED_COMMIT__"
tar -xf "__RELEASE_TAR__" -C "release-__RESOLVED_COMMIT__"
tar -xf "__FRONTEND_TAR__" -C "dist-__RESOLVED_COMMIT__"
rm -rf app migrations scripts docs .github frontend
cp -a "release-__RESOLVED_COMMIT__/app" ./app
cp -a "release-__RESOLVED_COMMIT__/migrations" ./migrations
cp -a "release-__RESOLVED_COMMIT__/scripts" ./scripts
cp -a "release-__RESOLVED_COMMIT__/docs" ./docs
cp -a "release-__RESOLVED_COMMIT__/.github" ./.github
cp -a "release-__RESOLVED_COMMIT__/frontend" ./frontend
cp -a "release-__RESOLVED_COMMIT__/Dockerfile.prod" "release-__RESOLVED_COMMIT__/requirements-core.txt" "release-__RESOLVED_COMMIT__/requirements-optional.txt" "release-__RESOLVED_COMMIT__/requirements-worker.txt" "release-__RESOLVED_COMMIT__/requirements.txt" "release-__RESOLVED_COMMIT__/pytest.ini" ./
cp -a "release-__RESOLVED_COMMIT__/docker-compose.fl-prod.yml" ./docker-compose.fl-prod.yml
rm -rf dist
mv "dist-__RESOLVED_COMMIT__" dist
docker cp app/. legal-ai-app:/app/app
docker cp migrations/. legal-ai-app:/app/migrations
docker cp scripts/. legal-ai-app:/app/scripts
docker cp pytest.ini legal-ai-app:/app/pytest.ini
docker exec legal-ai-app sh -lc 'rm -rf /app/app/app /app/migrations/migrations /app/scripts/scripts || true; python -m app.db.migrate_all; python -m app.db.migrate_all --check'
docker restart legal-ai-app
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  if curl -fsS http://127.0.0.1:8089/ready >/dev/null; then
    break
  fi
  sleep 2
done
curl -fsS http://127.0.0.1:8089/health >/dev/null
curl -fsS http://127.0.0.1:8089/ready >/dev/null
docker commit legal-ai-app legal-ai-assistant:latest >/tmp/legal-ai-commit-image.txt
cat >/opt/legal-ai/DEPLOYED_VERSION <<EOF
repo_head_commit=__FULL_COMMIT__
runtime_code_commit=__RESOLVED_COMMIT__
deploy_config_commit=__RESOLVED_COMMIT__
deployed_at=$(date -Iseconds)
method=scripts/deploy-legal-ai-hot-sync.ps1
health=ready
EOF
cat /opt/legal-ai/DEPLOYED_VERSION
'@

$remoteScript = $remoteScriptTemplate
$remoteScript = $remoteScript.Replace("__REMOTE_DIR__", $RemoteDir)
$remoteScript = $remoteScript.Replace("__RESOLVED_COMMIT__", $resolvedCommit)
$remoteScript = $remoteScript.Replace("__FULL_COMMIT__", $fullCommit)
$remoteScript = $remoteScript.Replace("__STAMP__", $stamp)
$remoteScript = $remoteScript.Replace("__RELEASE_TAR__", $releaseTar)
$remoteScript = $remoteScript.Replace("__FRONTEND_TAR__", $frontendTar)

$remoteScriptPath = Join-Path $env:TEMP "legal-ai-hot-sync-$resolvedCommit.sh"
$remoteScript | Set-Content -Path $remoteScriptPath -Encoding ascii

Invoke-Checked "Run remote hot sync" {
    scp $remoteScriptPath "${HostAlias}:/tmp/legal-ai-hot-sync-$resolvedCommit.sh"
    ssh $HostAlias "bash /tmp/legal-ai-hot-sync-$resolvedCommit.sh"
}

Invoke-Checked "Verify remote service" {
    ssh $HostAlias "cd $RemoteDir && docker compose --env-file .env.fl-prod -f docker-compose.fl-prod.yml ps && curl -fsS http://127.0.0.1:8089/ready"
}

Write-Host ""
Write-Host "Legal AI hot sync completed for $fullCommit"
