"""Run the local API and Vite together; stop only processes started here."""

import importlib.util
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent


def stop(process: subprocess.Popen) -> None:
    if os.name == "nt":
        if process.poll() is None:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
            )
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()


def main() -> int:
    processes = []
    try:
        if sys.version_info < (3, 11):
            raise RuntimeError("Python 3.11+ is required.")
        if any(importlib.util.find_spec(name) is None for name in ("uvicorn", "fastapi", "pydantic")):
            raise RuntimeError("Install backend dependencies: python -m pip install -r requirements.txt")
        node = shutil.which("node")
        vite = ROOT / "frontend/node_modules/vite/bin/vite.js"
        if not node or not vite.is_file():
            raise RuntimeError("Install Node.js 20+ and run npm install inside Bai1/frontend.")
        # Fail before starting either server if a required port is already occupied.
        for port in (8000, 5173):
            with socket.socket() as probe:
                try:
                    probe.bind(("127.0.0.1", port))
                except OSError as error:
                    raise RuntimeError(f"Port {port} is unavailable. Stop its server and retry.") from error
        options = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
                   if os.name == "nt" else {"start_new_session": True})
        commands = [
            ([sys.executable, "-m", "uvicorn", "triangle_knowledge_base.app.api.main:app",
              "--host", "127.0.0.1", "--port", "8000"], ROOT),
            ([node, str(vite), "--host", "127.0.0.1", "--port", "5173", "--strictPort"], ROOT / "frontend"),
        ]
        for command, cwd in commands:
            processes.append(subprocess.Popen(command, cwd=cwd, **options))
        print("Web: http://127.0.0.1:5173 | API: http://127.0.0.1:8000/docs", flush=True)
        print("Press Ctrl+C to stop both servers.", flush=True)
        while True:
            for process in processes:
                code = process.poll()
                if code is not None:
                    print(f"Server exited (code {code}); stopping the application.", flush=True)
                    return code or 1
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("\nStopping the application...", flush=True)
        return 0
    except (OSError, RuntimeError) as error:
        print(f"Cannot start Bai1: {error}", file=sys.stderr)
        return 1
    finally:
        for process in reversed(processes):
            stop(process)


if __name__ == "__main__":
    def interrupted(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    raise SystemExit(main())
