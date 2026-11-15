@echo off
rem AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md and docs/ai-log/2026-11-15_1515_nicholas_ingles-e-ia.md
chcp 65001 >nul
cd /d "%~dp0"
rem Works with the scripts loose in the folder or inside pipeline\
set P=
if exist pipeline\01_processar_focos.py set P=pipeline\
echo.
echo === 1/2 Moving the state boundaries from Downloads ===
if exist "%USERPROFILE%\Downloads\BR_UF_*.zip" (move "%USERPROFILE%\Downloads\BR_UF_*.zip" .) else (echo State boundaries are not in Downloads - looking in the project folder.)
echo.
echo === 2/2 Building the burning calendar ===
python %P%04_calendario.py
if errorlevel 1 goto erro
echo.
echo All done!
pause
exit /b
:erro
echo.
echo Something went wrong. Take a screenshot of this window and share it with the team.
pause
