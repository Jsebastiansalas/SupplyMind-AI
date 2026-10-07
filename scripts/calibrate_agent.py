"""
Script de ejecución para el entrenamiento y calibración de criterio de SupplyMind AI.
Monitorea la precisión y asegura que el gasto no exceda $1.00 USD.
"""

import sys
from pathlib import Path

# Agregar raíz al sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

if sys.platform == "win32":
    try:
        if sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agent.training.trainer import AgentTrainer

def main():
    case_id = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "case_001"
    trainer = AgentTrainer(budget_limit_usd=1.00)
    trainer.run_calibration(case_id=case_id)

if __name__ == "__main__":
    main()
