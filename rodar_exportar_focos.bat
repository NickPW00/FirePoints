@echo off
rem AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md and docs/ai-log/2026-11-15_1515_nicholas_ingles-e-ia.md
chcp 65001 >nul
cd /d "%~dp0"
rem Works with the scripts loose in the folder or inside pipeline\
set P=
if exist pipeline\01_processar_focos.py set P=pipeline\
echo.
echo === Splitting the detections by year and sensor (for the app's CSV) ===
python %P%05_exportar_focos.py
if errorlevel 1 goto erro
echo.
echo All done!
pause
exit /b
:erro
echo.
echo Something went wrong. Take a screenshot of this window and share it with the team.
pause
