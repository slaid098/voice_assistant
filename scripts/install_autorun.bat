@echo off
chcp 65001 >nul 2>&1
echo.
echo === Голосовой помощник — добавление в автозагрузку ===
echo.

set "EXE=%~dp0voice-assistant.exe"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\voice-assistant.lnk"

if not exist "%EXE%" (
    echo ОШИБКА: voice-assistant.exe не найден рядом со скриптом.
    echo Ожидаемый путь: %EXE%
    echo.
    pause
    exit /b 1
)

powershell -NoProfile -Command ^
  "$s=(New-Object -COM WScript.Shell).CreateShortcut('%STARTUP%');" ^
  "$s.TargetPath='%EXE%';" ^
  "$s.WorkingDirectory='%~dp0';" ^
  "$s.WindowStyle=7;" ^
  "$s.Description='Голосовой помощник';" ^
  "$s.Save()"

if exist "%STARTUP%" (
    echo Готово! Ярлык добавлен в автозагрузку:
    echo   %STARTUP%
    echo.
    echo Теперь помощник будет запускаться автоматически при включении компьютера.
) else (
    echo ОШИБКА: не удалось создать ярлык.
)
echo.
pause