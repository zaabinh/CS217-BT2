@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run src/app.py
) else (
    python -m streamlit run src/app.py
)
pause
