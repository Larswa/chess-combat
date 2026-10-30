"""Container entrypoint: run DB migration (failure tolerated), then serve the app.

Replaces the former start.sh so the runtime image needs no shell.
"""
import subprocess
import sys

print("Chess Combat - Starting container...", flush=True)

print("Running database migration...", flush=True)
if subprocess.run([sys.executable, "migrate_db.py"]).returncode == 0:
    print("Database migration completed successfully", flush=True)
else:
    print("Database migration failed, but continuing to start application...", flush=True)
    print("The application will create tables automatically if possible", flush=True)

print("Starting FastAPI application...", flush=True)
import uvicorn  # noqa: E402

uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
