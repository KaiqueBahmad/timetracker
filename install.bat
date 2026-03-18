@echo off
setlocal enabledelayedexpansion

:: Script de instalação do Timetracker para Windows
:: Adiciona automaticamente a pasta bin ao PATH do sistema

echo Instalando Timetracker...
echo.

:: Obtém o diretório do projeto
set "PROJECT_DIR=%~dp0"
set "BIN_DIR=%PROJECT_DIR%bin"

:: Remove a barra final se existir
if "%BIN_DIR:~-1%"=="\" set "BIN_DIR=%BIN_DIR:~0,-1%"

:: Verifica se o diretório bin existe
if not exist "%BIN_DIR%" (
    echo Erro: Diretorio bin nao encontrado em %BIN_DIR%
    pause
    exit /b 1
)

:: Obtém o PATH atual do usuário
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "CURRENT_PATH=%%b"

:: Verifica se o BIN_DIR já está no PATH
echo %CURRENT_PATH% | findstr /C:"%BIN_DIR%" >nul
if %errorlevel%==0 (
    echo O Timetracker ja esta configurado no PATH!
    echo.
    pause
    exit /b 0
)

:: Adiciona o diretório bin ao PATH
if defined CURRENT_PATH (
    set "NEW_PATH=%BIN_DIR%;%CURRENT_PATH%"
) else (
    set "NEW_PATH=%BIN_DIR%"
)

:: Atualiza o PATH no registro
reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%NEW_PATH%" /f >nul

if %errorlevel%==0 (
    echo.
    echo ========================================
    echo   Timetracker instalado com sucesso!
    echo ========================================
    echo.
    echo O diretorio foi adicionado ao PATH:
    echo   %BIN_DIR%
    echo.
    echo IMPORTANTE: Para aplicar as mudancas:
    echo   1. Feche este prompt de comando
    echo   2. Abra um NOVO prompt de comando
    echo.
    echo Apos isso, voce podera usar o comando 'timetracker'
    echo de qualquer diretorio.
    echo.
) else (
    echo.
    echo Erro ao adicionar ao PATH.
    echo Tente executar este script como Administrador.
    echo.
)

pause
