@echo off
cd /d "%~dp0"
python -m streamlit run src/app.py
pause
