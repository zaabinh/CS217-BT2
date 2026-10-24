#!/usr/bin/env bash
cd "$(dirname "$0")"
if [ -x .venv/bin/python ]; then
    .venv/bin/python -m streamlit run src/app.py
else
    python3 -m streamlit run src/app.py
fi
