import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import shutil
from pathlib import Path
from agent.core.skynet_runner import SkynetRunner

BOOTCAMP_DIR = Path("data/cases")

def create_corrupt_case(case_name: str, corrupt_content: str):
    case_path = BOOTCAMP_DIR / case_name
    case_path.mkdir(exist_ok=True, parents=True)
    
    # Create a corrupt invoice.json
    with open(case_path / "invoice.json", "w") as f:
        f.write(corrupt_content)
        
    print(f"[*] Creado caso corrupto: {case_name}")

def run_bootcamp():
    print("========================================")
    print(" SKYNET BOOTCAMP: RESILIENCE TESTING")
    print("========================================")
    
    # 1. Crear un JSON malformado (sin llaves de cierre)
    create_corrupt_case("test_corrupt_json", '{\n"invoice_id": "ERR-001",\n"total_amount": 100')
    
    # 2. Crear un JSON con tipos incorrectos (letras donde van números)
    create_corrupt_case("test_bad_schema", json.dumps({
        "invoice_id": "ERR-002",
        "vendor_id": "V-123",
        "customer_id": "C-123",
        "issue_date": "2026-01-01",
        "currency": "USD",
        "items": [],
        "subtotal": "CIEN DOLARES",
        "tax": "CERO",
        "total_amount": "MUCHO"
    }))
    
    # 3. Testear motor contra los casos corruptos
    cases_to_test = ["test_corrupt_json", "test_bad_schema"]
    
    for case in cases_to_test:
        print(f"\n[BOOTCAMP] Ejecutando SKYNET contra {case}...")
        runner = SkynetRunner(case_id=str(BOOTCAMP_DIR / case))
        try:
            report = runner.run()
            print(f"-> Resultado: {report.root_cause}")
            if "TECHNICAL_ERROR" in report.root_cause:
                print("   [PASS] SKYNET degradó elegantemente y capturó el error técnico.")
            else:
                print("   [FAIL] SKYNET intentó procesar la basura y no devolvió un error técnico claro.")
        except Exception as e:
            print(f"   [FATAL FAIL] El motor explotó y lanzó una excepción no controlada: {e}")

if __name__ == "__main__":
    run_bootcamp()
