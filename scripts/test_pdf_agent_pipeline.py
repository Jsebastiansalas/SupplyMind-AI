"""
Test Suite y Demostración Automatizada del Pipeline de Documentos PDF en SupplyMind AI.
Verifica que el agente SKYNET ingeste directamente expedientes en PDF sin archivos JSON auxiliares,
extraiga las entidades Pydantic, concilie matemáticamente y emita los veredictos legales.
"""

import sys
from pathlib import Path
from decimal import Decimal

# Salida segura en Windows
if sys.platform == "win32":
    try:
        if sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.append(str(Path(__file__).resolve().parent.parent))

from agent.core.skynet_runner import SkynetRunner
from tools.document_reader.reader import load_case_documents
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console(highlight=False)

def run_pdf_cases_benchmark():
    test_cases = [
        {
            "id": "case_005_amazon_shortage",
            "name": "Caso Real Amazon: Faltante de Muelle (Dock Shortage) y Multa ASN",
            "expected_billed": Decimal("48000.00"),
            "expected_received": Decimal("40500.00"),
            "expected_difference": Decimal("-7500.00"),
            "expected_justified": Decimal("5000.00"),
            "expected_claimable": Decimal("2500.00"),
            "expected_primary_type": "FALTANTE_DE_MERCANCIA"
        },
        {
            "id": "case_006_walmart_otif_pricing",
            "name": "Caso Real Walmart: Discrepancia de Precio Unitario y Descuento Extemporáneo",
            "expected_billed": Decimal("64500.00"),
            "expected_received": Decimal("56500.00"),
            "expected_difference": Decimal("-8000.00"),
            "expected_justified": Decimal("4500.00"),
            "expected_claimable": Decimal("3500.00"),
            "expected_primary_type": "DIFERENCIA_DE_PRECIO"
        }
    ]
    
    console.print(Panel(
        "[bold cyan]TEST SUITE: PROCESAMIENTO AUTÓNOMO DE DOCUMENTOS PDF REALES[/bold cyan]\n"
        "[dim]Demostración del Agente SKYNET ingiriendo expedientes exclusivamente en PDF[/dim]",
        border_style="cyan"
    ))
    
    results = []
    
    for tc in test_cases:
        case_id = tc["id"]
        case_dir = Path("data/cases") / case_id
        console.print(f"\n[bold yellow]>>> Auditando Expediente PDF: {case_id}[/bold yellow] ({tc['name']})")
        
        # 1. Verificar presencia de PDFs y ausencia obligatoria de JSONs
        pdf_files = list(case_dir.glob("*.pdf"))
        json_files = list(case_dir.glob("*.json"))
        console.print(f"  [cyan]Archivos PDF encontrados:[/cyan] {[p.name for p in pdf_files]}")
        console.print(f"  [cyan]Archivos JSON en expediente:[/cyan] {len(json_files)} (Debe ser 0 para validar ingesta pura de PDF)")
        assert len(pdf_files) >= 5, f"Faltan PDFs en {case_id}"
        assert len(json_files) == 0, f"No debe haber JSONs en {case_id} para esta prueba pura de PDF"
        
        # 2. Ingesta a través de load_case_documents
        docs = load_case_documents(case_id)
        console.print(f"  [green][OK] Ingesta completada con éxito. Modelos Pydantic tipados:[/green] {list(docs.keys())}")
        
        # 3. Ejecución del Agente SkynetRunner
        runner = SkynetRunner(case_id=case_id)
        report = runner.run()
        
        console.print(f"  [green][OK] Reporte agéntico emitido con éxito.[/green]")
        console.print(f"    - Facturado: ${report.billed_amount:,.2f} USD")
        console.print(f"    - Recibido:  ${report.received_amount:,.2f} USD")
        console.print(f"    - Justificado: ${report.justified_amount:,.2f} USD")
        console.print(f"    - Reclamable:  ${report.claimable_amount:,.2f} USD")
        
        passed = (
            report.billed_amount == tc["expected_billed"] and
            report.received_amount == tc["expected_received"] and
            report.justified_amount == tc["expected_justified"] and
            report.claimable_amount == tc["expected_claimable"]
        )
        results.append({
            "case_id": case_id,
            "name": tc["name"],
            "status": "PASS" if passed else "FAIL",
            "billed": report.billed_amount,
            "received": report.received_amount,
            "justified": report.justified_amount,
            "claimable": report.claimable_amount
        })
        
    # Tabla de Resultados
    table = Table(title="Resumen de Pruebas: Ingesta y Resolución de PDFs Reales", border_style="green")
    table.add_column("Expediente", style="cyan")
    table.add_column("Facturado", justify="right")
    table.add_column("Recibido", justify="right")
    table.add_column("Justificado", justify="right")
    table.add_column("Reclamable (A Favor)", justify="right", style="bold green")
    table.add_column("Estado", justify="center")
    
    for r in results:
        status_badge = "[bold green]PASS[/bold green]" if r["status"] == "PASS" else "[bold red]FAIL[/bold red]"
        table.add_row(
            r["case_id"],
            f"${r['billed']:,.2f}",
            f"${r['received']:,.2f}",
            f"${r['justified']:,.2f}",
            f"${r['claimable']:,.2f}",
            status_badge
        )
        
    console.print("\n")
    console.print(table)
    all_passed = all(r["status"] == "PASS" for r in results)
    if all_passed:
        console.print("\n[bold green][EXITO] TODOS LOS CASOS PDF FUERON AUDITADOS Y VALIDADOS CON EXITO.[/bold green]\n")
    else:
        console.print("\n[bold red][FALLO] SE ENCONTRARON DISCREPANCIAS EN LAS PRUEBAS.[/bold red]\n")
        sys.exit(1)

if __name__ == "__main__":
    run_pdf_cases_benchmark()
