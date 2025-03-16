@echo off
:: Script para executar o timetracker de qualquer lugar no Windows

:: Obtém o diretório onde o script está instalado (a pasta bin)
set BIN_DIR=%~dp0

:: Obtém o diretório pai (a pasta do projeto timetracker)
for %%I in ("%BIN_DIR%..") do set PROJECT_DIR=%%~fI

:: Navega para o diretório do projeto para manter as referências corretas entre arquivos
cd /d "%PROJECT_DIR%"

:: Executa o script Python principal com todos os argumentos passados
python "%PROJECT_DIR%\timetracker.py" %*
