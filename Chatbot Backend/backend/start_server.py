
import os
import sys
import subprocess

backend_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(backend_dir)

sys.path.insert(0, backend_dir)

print(f"Starting FastAPI server from directory: {backend_dir}")
print(f"Python path includes: {backend_dir}")

try:
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "localhost",
        "--port", "8000",
        "--reload"
    ], check=True)
except KeyboardInterrupt:
    print("\\nServer stopped by user")
except Exception as e:
    print(f"Error starting server: {e}")