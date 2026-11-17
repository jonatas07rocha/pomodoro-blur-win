@echo off
setlocal
set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Pomodoro Blur.lnk"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$s = $ws.CreateShortcut('%SHORTCUT%'); " ^
  "$s.TargetPath = 'pythonw.exe'; " ^
  "$s.Arguments = '\"%APP_DIR%\main.py\"'; " ^
  "$s.WorkingDirectory = '%APP_DIR%'; " ^
  "$s.IconLocation = '%APP_DIR%\assets\pomodoro.ico,0'; " ^
  "$s.Save()"

echo Atalho criado no Menu Iniciar do Windows: %SHORTCUT%
pause
