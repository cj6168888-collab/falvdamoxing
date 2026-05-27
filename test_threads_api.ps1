# 测试线索API
$body = @{
    name = "测试线索API修复"
    cause = "测试案由"
    description = "这是通过API创建的测试线索"
    amount = "1万元"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/cases/1/threads" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10
    Write-Host "创建线索成功:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "创建线索失败:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

# 测试获取线索
Write-Host "`n获取线索列表:"
try {
    $threads = Invoke-RestMethod -Uri "http://localhost:8000/api/cases/1/threads" -Method Get -TimeoutSec 10
    Write-Host "找到 $($threads.Count) 条线索:"
    $threads | ForEach-Object { Write-Host "  - $($_.name) ($($_.cause))" }
} catch {
    Write-Host "获取线索失败:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

# 测试创建当事人
Write-Host "`n测试创建当事人:"
$partyBody = @{
    name = "测试当事人"
    party_type = "个人"
    role = "原告"
    phone = "13800138000"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/cases/1/parties" -Method Post -Body $partyBody -ContentType "application/json" -TimeoutSec 10
    Write-Host "创建当事人成功:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "创建当事人失败:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}
