# ============================================================
# An-Nadaa Diagnostic Centre — Fresh migration script
# Run this once after the model refactor.
# ============================================================

Write-Host "=== Clearing old migrations ===" -ForegroundColor Cyan

$apps = @("accounts","clients","services","invoices","reports","dashboard")
foreach ($app in $apps) {
    $dir = "apps\$app\migrations"
    if (Test-Path $dir) {
        Get-ChildItem $dir -Filter "*.py" | Where-Object { $_.Name -ne "__init__.py" } | Remove-Item -Force
        Write-Host "  Cleared $dir"
    }
}

Write-Host "`n=== Removing old database ===" -ForegroundColor Cyan
if (Test-Path "db.sqlite3") {
    Remove-Item "db.sqlite3" -Force
    Write-Host "  db.sqlite3 deleted"
}

Write-Host "`n=== Removing pycache ===" -ForegroundColor Cyan
Get-ChildItem -Path "apps" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

Write-Host "`n=== Running makemigrations ===" -ForegroundColor Green
.\venv\Scripts\python.exe manage.py makemigrations

Write-Host "`n=== Running migrate ===" -ForegroundColor Green
.\venv\Scripts\python.exe manage.py migrate

Write-Host "`n=== Creating superuser ===" -ForegroundColor Yellow
Write-Host "You will be prompted to enter a username/email/password."
.\venv\Scripts\python.exe manage.py createsuperuser

Write-Host "`n=== Done! Start the server with: ===" -ForegroundColor Cyan
Write-Host "  .\venv\Scripts\python.exe manage.py runserver" -ForegroundColor White
