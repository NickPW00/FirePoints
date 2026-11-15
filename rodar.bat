@echo off
rem AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md and docs/ai-log/2026-11-15_1515_nicholas_ingles-e-ia.md
chcp 65001 >nul
cd /d "%~dp0"
rem Works with the scripts loose in the folder or inside pipeline\
set P=
if exist pipeline\01_processar_focos.py set P=pipeline\
echo.
echo === 1/4 Moving the MODIS zip from Downloads ===
if exist "%USERPROFILE%\Downloads\DL_FIRE_M-C61*.zip" (move "%USERPROFILE%\Downloads\DL_FIRE_M-C61*.zip" .) else (echo MODIS zip is not in Downloads - looking in the project folder.)
echo.
echo === 2/4 Installing the libraries ===
python -m pip install -r requirements.txt
if errorlevel 1 goto erro
echo.
echo === 3/4 Processing the detections (this may take a while, do not close the window) ===
python %P%01_processar_focos.py
if errorlevel 1 goto erro
echo.
echo === 4/4 Building the MODIS x S-NPP chart ===
python %P%02_comparar_sensores.py
if errorlevel 1 goto erro
echo.
echo All done!
pause
exit /b
:erro
echo.
echo Something went wrong. Take a screenshot of this window and share it with the team.
pause
