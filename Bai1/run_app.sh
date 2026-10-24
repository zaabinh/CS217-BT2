#!/usr/bin/env bash
set -e
cd -- "$(dirname -- "$0")"
if [ -x .venv/bin/python ]; then
    exec .venv/bin/python run_app.py
elif [ -x .venv/Scripts/python.exe ]; then
    exec .venv/Scripts/python.exe run_app.py
else
    exec python3 run_app.py
fi
