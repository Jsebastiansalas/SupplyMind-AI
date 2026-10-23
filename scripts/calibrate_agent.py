"""
scripts/calibrate_agent.py
Script de ejecución para el entrenamiento y calibración de criterio de SupplyMind AI.
Enfocado exclusivamente en la cartera de élite:
- Los 2 casos más exigentes (Multi-SKU masivo de alta cuantía y bundle corporativo de red)
- Los 2 casos reales (Logística fulfillment Amazon y cadena de suministro retail Walmart)
Monitorea la precisión rigurosa, cero alucinación numérica y asegura gasto < $1.00 USD.
"""

import sys
from pathlib import Path

# Agregar raíz al sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

if sys.platform == "win32":
    try:
        if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agent.training.trainer import AgentTrainer

# 1. Los 2 casos más exigentes de la plataforma
EXIGENT_CASES = [
    "case_009_mega_retailer_dispute",  # Exigente 1: Mega Retailer 40 SKUs ($385,000 USD)
    "case_007_cisco_large_bundle",       # Exigente 2: Cisco Infrastructure Bundle ($125,000 USD)
]

# 2. Los 2 casos reales nativos en PDF
REAL_CASES = [
    "case_005_amazon_shortage",          # Real 1: Amazon Fulfillment Shortage & ASN Fee ($48,000 USD)
    "case_006_walmart_otif_pricing",     # Real 2: Walmart OTIF Penalty & Unit Price Mismatch ($64,500 USD)
]

# Cartera activa de élite (4 casos benchmark)
ELITE_BENCHMARK_CASES = EXIGENT_CASES + REAL_CASES


def main():
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "--all"
    trainer = AgentTrainer(budget_limit_usd=1.00)

    if arg in ["--exigent", "--extensive", "-e", "exigent", "extensive"]:
        cases = EXIGENT_CASES
        print(f"\n[SupplyMind AI] Iniciando calibración de los 2 casos más exigentes: {cases}\n")
    elif arg in ["--real", "-r", "real", "--reales"]:
        cases = REAL_CASES
        print(f"\n[SupplyMind AI] Iniciando calibración de los 2 casos reales: {cases}\n")
    elif arg in ["--all", "-a", "all", "--elite"]:
        cases = ELITE_BENCHMARK_CASES
        print(f"\n[SupplyMind AI] Iniciando calibración de la cartera élite (2 exigentes + 2 reales): {cases}\n")
    else:
        cases = [sys.argv[1]]
        print(f"\n[SupplyMind AI] Calibrando expediente específico: {cases[0]}\n")

    for cid in cases:
        if not trainer._check_budget():
            print("\n[ALERTA PRESUPUESTO] Límite de inferencia alcanzado. Deteniendo calibración.")
            break
        trainer.run_calibration(case_id=cid)


if __name__ == "__main__":
    main()
