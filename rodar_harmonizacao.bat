@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Funciona com os scripts soltos na pasta ou dentro de pipeline\
set P=
if exist pipeline\01_processar_focos.py set P=pipeline\
echo.
echo === 1/3 Trazendo o contorno de biomas dos Downloads ===
if exist "%USERPROFILE%\Downloads\Biomas_250mil*.zip" (move "%USERPROFILE%\Downloads\Biomas_250mil*.zip" .) else (echo Contorno de biomas nao esta nos Downloads - procurando na pasta do projeto.)
echo.
echo === 2/3 Instalando as bibliotecas ===
python -m pip install -r requirements.txt
if errorlevel 1 goto erro
echo.
echo === 3/3 Harmonizando MODIS e VIIRS ===
python %P%03_harmonizar.py
if errorlevel 1 goto erro
echo.
echo Tudo pronto!
pause
exit /b
:erro
echo.
echo Deu erro. Tire um print desta janela e mande para o Claude.
pause
