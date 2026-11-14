@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Funciona com os scripts soltos na pasta ou dentro de pipeline\
set P=
if exist pipeline\01_processar_focos.py set P=pipeline\
echo.
echo === Dividindo os focos por ano e sensor (para o CSV do app) ===
python %P%05_exportar_focos.py
if errorlevel 1 goto erro
echo.
echo Tudo pronto!
pause
exit /b
:erro
echo.
echo Deu erro. Tire um print desta janela e mande para o Claude.
pause
