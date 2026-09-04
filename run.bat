@echo off
title Chess Player Analyzer
echo ========================================================
echo   Dang khoi dong Chess Player Analyzer...
echo   Trinh duyet se tu dong mo tai http://localhost:8501
echo ========================================================
cd /d "%~dp0"
".venv\Scripts\streamlit.exe" run app.py
pause
