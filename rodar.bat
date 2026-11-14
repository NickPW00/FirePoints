@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Funciona com os scripts soltos na pasta ou dentro de pipeline\
set P=
if exist pipeline\01_processar_focos.py set P=pipeline\
echo.
echo === 1/4 Trazendo o zip do MODIS dos Downloads ===
if exist "%USERPROFILE%\Downloads\DL_FIRE_M-C61*.zip" (move "%USERPROFILE%\Downloads\DL_FIRE_M-C61*.zip" .) else (echo Zip do MODIS nao esta nos Downloads - procurando na pasta do projeto.)
echo.
echo === 2/4 Instalando as bibliotecas ===
python -m pip install -r requirements.txt
if errorlevel 1 goto erro
echo.
echo === 3/4 Processando os focos (pode demorar, nao feche a janela) ===
python %P%01_processar_focos.py
if errorlevel 1 goto erro
echo.
echo === 4/4 Gerando o grafico MODIS x S-NPP ===
python %P%02_comparar_sensores.py
if errorlevel 1 goto erro
echo.
echo Tudo pronto!
pause
exit /b
:erro
echo.
echo Deu erro. Tire um print desta janela e mande para o Claude.
pause
