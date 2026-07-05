@echo off
chcp 65001 >nul 2>&1
echo.
echo === Голосовой помощник — удаление из автозагрузки ===
echo.

set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\voice-assistant.lnk"

if exist "%STARTUP%" (
    del "%STARTUP%"
    echo Готово! Ярлык удалён из автозагрузки.
    echo Теперь помощник НЕ будет запускаться автоматически при включении.
) else (
    echo Ярлык не найден в автозагрузке. Возможно, он уже удалён.
)
echo.
pause