cd C:\Users\broke\Desktop\wc-show-game

$files = @{
    "README.md" = @"
# 🏆 ЧЕМПИОНАТ МИРА ПО ФУТБОЛУ 2026
Production-ready Telegram bot + Dashboard
"@
    ".gitignore" = @"
__pycache__/
.env
venv/
*.log
"@
    "requirements.txt" = @"
aiogram==3.7.0
fastapi==0.111.0
sqlalchemy==2.0.30
"@
}

foreach ($file in $files.GetEnumerator()) {
    $file.Value | Out-File -Encoding UTF8 $file.Key
}

git add .
git commit -m "Initial commit"
git push -u origin main
Write-Host "✅ ГОТОВО!" -ForegroundColor Green
