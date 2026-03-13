@echo off
chcp 65001 >nul
title ЦениBG

echo.
echo  =============================================
echo    CeniBG -- Проследяване на цени
echo  =============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ГРЕШКА] Python не е намерен!
    echo  Изтегли от: https://python.org/downloads
    echo  Важно: "Add Python to PATH" при инсталация!
    start https://python.org/downloads
    pause
    exit /b 1
)

echo  Избери действие:
echo  ------------------------------------------------
echo  1  Стартирай приложението
echo  2  Настрой Stripe платежи
echo  3  Настрой Gmail известия
echo  4  Тествай scraping (1-3 мин)
echo  5  Подготви за качване онлайн
echo  6  Изход
echo  ------------------------------------------------
echo.
set /p choice="Избор (1-6): "

if "%choice%"=="2" goto stripe
if "%choice%"=="3" goto email
if "%choice%"=="4" goto scraper
if "%choice%"=="5" goto deploy
if "%choice%"=="6" exit /b 0

:start
echo.
if not exist ".env" (
    copy .env.example .env >nul
    echo  [!] .env файлът е създаден от шаблона.
    echo  Препоръчително е да настроиш Stripe и Gmail (опции 2 и 3).
    echo.
)

echo  Инсталиране на зависимости...
pip install -r requirements.txt -q --no-warn-script-location
python -m playwright install chromium --quiet >nul 2>&1
echo  Готово.
echo.
echo  =============================================
echo   Приложение: http://localhost:5000
echo   Спиране: CTRL+C
echo  =============================================
echo.
timeout /t 2 /nobreak >nul
start http://localhost:5000
python app.py
pause
exit /b 0

:stripe
echo.
pip install stripe -q
python stripe_setup.py
pause
goto start

:email
echo.
python email_setup.py
pause
goto start

:scraper
echo.
pip install requests beautifulsoup4 playwright -q
python -m playwright install chromium --quiet >nul 2>&1
python scrapers\scraper.py
pause
exit /b 0

:deploy
echo.
python deploy.py
pause
exit /b 0
