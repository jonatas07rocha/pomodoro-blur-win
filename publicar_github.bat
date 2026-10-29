@echo off
title Publicar no GitHub
cd /d "%~dp0"
echo ========================================================
echo Publicando Pomodoro Blur no GitHub (@jonatas07rocha)...
echo ========================================================
echo.
git push -u origin main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Se o repositorio ainda nao foi criado na sua conta:
    echo 1. Acesse: https://github.com/new
    echo 2. Crie com o nome: pomodoro-blur-win
    echo 3. Execute este arquivo novamente para enviar os arquivos!
    echo.
    pause
) else (
    echo.
    echo ========================================================
    echo Publicado com sucesso!
    echo Acesse: https://github.com/jonatas07rocha/pomodoro-blur-win
    echo ========================================================
    echo.
    pause
)
