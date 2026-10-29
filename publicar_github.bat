@echo off
title Publicar no GitHub
cd /d "%~dp0"
echo ========================================================
echo Publicando Pomodoro Blur no GitHub (@jonatas07rocha)...
echo ========================================================
echo.
echo Se abrir uma janela do navegador, confirme o login na sua conta jonatas07rocha.
echo.
git push -u origin main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo --------------------------------------------------------
    echo Ocorreu um erro ao enviar.
    echo Se o navegador nao abriu para autorizar, voce tambem pode
    echo gerar um Personal Access Token (PAT) em:
    echo https://github.com/settings/tokens
    echo e executar: git push https://SEU_TOKEN@github.com/jonatas07rocha/pomodoro-blur-win.git main
    echo --------------------------------------------------------
    echo.
    pause
) else (
    echo.
    echo ========================================================
    echo Publicado com sucesso!
    echo Acesse seu repositorio em:
    echo https://github.com/jonatas07rocha/pomodoro-blur-win
    echo ========================================================
    echo.
    pause
)
