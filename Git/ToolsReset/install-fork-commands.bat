@echo off
chcp 65001 >nul
setlocal EnableExtensions

set "SRC=%~dp0custom-commands.json"
set "DEST_DIR=%LOCALAPPDATA%\Fork"
set "DEST=%DEST_DIR%\custom-commands.json"

echo ============================================
echo  Установка команд Soft Reset для Fork
echo ============================================
echo.

rem --- 1. файл рядом с батником на месте? ---
if not exist "%SRC%" (
    echo [ОШИБКА] Рядом с этим файлом нет custom-commands.json
    echo Положите оба файла в одну папку и запустите снова.
    goto :end
)

rem --- 2. Fork вообще установлен? ---
if not exist "%DEST_DIR%" (
    echo [ОШИБКА] Не найдена папка настроек Fork:
    echo   %DEST_DIR%
    echo Убедитесь, что Fork установлен и был хотя бы раз запущен.
    goto :end
)

rem --- 3. Fork не должен быть запущен, иначе перезапишет файл своими настройками ---
tasklist /FI "IMAGENAME eq Fork.exe" 2>nul | find /I "Fork.exe" >nul
if not errorlevel 1 (
    echo Fork сейчас запущен. Его нужно закрыть перед установкой.
    echo.
    choice /C YN /M "Закрыть Fork автоматически"
    if errorlevel 2 (
        echo Отменено. Закройте Fork вручную и запустите этот файл снова.
        goto :end
    )
    taskkill /IM Fork.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo Fork закрыт.
    echo.
)

rem --- 4. бэкап того, что было ---
if exist "%DEST%" (
    for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "TS=%%i"
    copy /Y "%DEST%" "%DEST_DIR%\custom-commands.backup-%TS%.json" >nul
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось сделать резервную копию. Установка прервана.
        goto :end
    )
    echo Старые команды сохранены в:
    echo   custom-commands.backup-%TS%.json
    echo.
)

rem --- 5. копируем ---
copy /Y "%SRC%" "%DEST%" >nul
if errorlevel 1 (
    echo [ОШИБКА] Не удалось скопировать файл в папку Fork.
    echo Попробуйте запустить от имени администратора.
    goto :end
)

echo ============================================
echo  Готово!
echo ============================================
echo.
echo Запустите Fork, нажмите Ctrl+P и наберите: soft
echo Должны появиться две команды:
echo   - Soft Reset (undo last commit)
echo   - Soft Reset to Remote
echo.

:end
echo.
pause
endlocal
