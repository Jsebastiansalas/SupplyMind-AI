"""
run_api.py
Lanzador del servidor backend FastAPI en http://localhost:8000.
"""

import sys
from pathlib import Path
import uvicorn

# Configuración de salida segura UTF-8 en Windows
if sys.platform == "win32":
    try:
        if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Asegurar path raíz
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


import os

def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload_opt = os.getenv("UVICORN_RELOAD", "false").lower() in ("1", "true", "yes")

    print("=" * 60)
    print(" SupplyMind AI Enterprise — Backend API Server")
    print(f" Servidor REST FastAPI disponible en: http://{host}:{port}")
    print(f" Documentación interactiva Swagger: http://{host}:{port}/docs")
    print(f" Modo recarga en caliente (Reload): {reload_opt}")
    print("=" * 60)
    uvicorn.run("api.main:app", host=host, port=port, reload=reload_opt)



if __name__ == "__main__":
    main()
