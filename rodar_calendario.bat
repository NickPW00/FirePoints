@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Funciona com os scripts soltos na pasta ou dentro de pipeline\
set P=
if exist pipeline\01_processar_focos.py set P=pipeline\
echo.
echo === 1/2 Trazendo o contorno dos estados dos Downloads ===
if exist "%USERPROFILE%\Downloads\BR_UF_*.zip" (move "%USERPROFILE%\Downloads\BR_UF_*.zip" .) else (echo Contorno dos estados nao esta nos Downloads - procurando na pasta do projeto.)
echo.
echo === 2/2 Montando o calendario de queimadas ===
python %P%04_calendario.py
if errorlevel 1 goto erro
echo.
echo Tudo pronto!
pause
exit /b
:erro
echo.
echo Deu erro. Tire um print desta janela e mande para o Claude.
pause
