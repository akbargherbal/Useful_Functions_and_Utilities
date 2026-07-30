```powershell
$failed = @()

Get-ChildItem -Filter *.ipynb | ForEach-Object {
    Write-Host "▶ Running: $($_.Name)"
    jupyter nbconvert --to notebook --execute --inplace $_.Name --ExecutePreprocessor.timeout=600
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ FAILED: $($_.Name)" -ForegroundColor Red
        $failed += $_.Name
    } else {
        Write-Host "✅ OK: $($_.Name)" -ForegroundColor Green
    }
}

Write-Host "`n===== الملخص ====="
if ($failed.Count -eq 0) {
    Write-Host "كل النوتبوكات اشتغلت بدون مشاكل 🎉"
} else {
    Write-Host "النوتبوكات اللي فشلت:"
    $failed | ForEach-Object { Write-Host "  - $_" }
}
```