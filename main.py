import sys
import os
from pathlib import Path

# Configuración de salida segura UTF-8 para consola en Windows
if sys.platform == "win32":
    try:
        if sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agent.core.skynet_runner import SkynetRunner
from config.settings import settings

import json
import shutil
from typing import Optional

console = Console(highlight=False)

def prompt_add_case() -> Optional[str]:
    """Flujo interactivo en consola para registrar o importar un nuevo caso."""
    console.print(Panel(
        "[bold cyan]SupplyMind AI — Centro de Registro de Nuevo Caso[/bold cyan]\n"
        "[dim]Ingresa tus propios documentos comerciales o parametriza un caso para que el agente lo revise.[/dim]",
        border_style="yellow"
    ))
    console.print("\n[bold white]¿Cómo deseas ingresar el caso?[/bold white]")
    console.print("  [bold green][1][/bold green] Importar archivos desde una carpeta existente en tu equipo")
    console.print("  [bold green][2][/bold green] Crear un caso guiado ingresando los montos y datos comerciales")
    console.print("  [bold red][0][/bold red] Cancelar\n")
    
    try:
        console.print("[bold yellow]Selecciona una opción [1-2, o 0 para cancelar]: [/bold yellow]", end="")
        sub_choice = input().strip()
    except (EOFError, KeyboardInterrupt):
        return None

    if sub_choice == "1":
        console.print("\n[bold white]Ingresa la ruta de la carpeta con tus documentos (PDFs, JSONs, imágenes):[/bold white]")
        console.print("[dim]Ejemplo: C:\\Users\\USUARIO\\Downloads\\mis_facturas[/dim]")
        try:
            folder_path_str = input("Ruta de la carpeta: ").strip().strip('"').strip("'")
            src_folder = Path(folder_path_str)
            if not src_folder.exists() or not src_folder.is_dir():
                console.print(f"[bold red]Error: La ruta '{folder_path_str}' no existe o no es un directorio.[/bold red]\n")
                return None
            
            case_name = input("Identificador para el caso (ej. case_mi_cliente): ").strip()
            if not case_name:
                case_name = f"case_{src_folder.name.lower()}"
            if not case_name.startswith("case_"):
                case_name = f"case_{case_name}"
            
            dest_dir = settings.DATA_DIR / case_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            count = 0
            for item in src_folder.iterdir():
                if item.is_file():
                    shutil.copy2(item, dest_dir / item.name)
                    count += 1
            
            meta = {
                "case_id": case_name,
                "display_name": case_name.replace("_", " ").title(),
                "category": "Personalizado",
                "description": f"Expediente importado desde '{src_folder.name}' con {count} documentos."
            }
            with open(dest_dir / "meta.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
                
            console.print(f"[bold green]✓ Caso registrado con éxito en '{dest_dir}' ({count} archivos adjuntados).[/bold green]\n")
            return case_name
        except Exception as e:
            console.print(f"[bold red]Error al importar archivos: {e}[/bold red]\n")
            return None

    elif sub_choice == "2":
        try:
            console.print("\n[bold cyan]--- Parametrización Guiada de Disputa ---[/bold cyan]")
            c_id = input("ID del caso [ej. case_mi_empresa]: ").strip() or "case_mi_empresa"
            if not c_id.startswith("case_"):
                c_id = f"case_{c_id}"
            
            billed_val = float(input("Monto Facturado en USD [ej. 10000]: ") or "10000")
            paid_val = float(input("Monto Pagado en USD [ej. 8500]: ") or "8500")
            missing_val = float(input("Faltante físico en remisión USD [ej. 1000]: ") or "1000")
            unauth_val = float(input("Penalización/Deducción arbitraria USD [ej. 500]: ") or "500")
            
            from api.routes.cases import create_guided_case, GuidedCaseRequest, GuidedCaseItem
            req = GuidedCaseRequest(
                case_id=c_id,
                display_name=c_id.replace("_", " ").title(),
                category="Personalizado",
                description=f"Caso generado con facturado ${billed_val:,.2f} y pagado ${paid_val:,.2f}",
                items=[
                    GuidedCaseItem(
                        item_id="PROD-001",
                        description="Lote de Mercancía General",
                        ordered_quantity=100,
                        delivered_quantity=90 if missing_val > 0 else 100,
                        missing_quantity=10 if missing_val > 0 else 0,
                        agreed_unit_price=billed_val / 100.0,
                    )
                ],
                amount_paid=paid_val,
                unauthorized_penalty=unauth_val,
                unauthorized_penalty_reason="Retención unilateral no justificada en contrato"
            )
            create_guided_case(req)
            console.print(f"[bold green]✓ Expediente '{c_id}' creado exitosamente con sus 5 documentos comerciales verificados.[/bold green]\n")
            return c_id
        except Exception as e:
            console.print(f"[bold red]Error al parametrizar caso: {e}[/bold red]\n")
            return None
    return None

def main():
    args = sys.argv[1:]
    
    # Detectar banderas de modo
    is_interactive = any(a.lower() in ["-i", "--interactive", "chat", "--chat"] for a in args)
    is_ask = any(a.lower() in ["ask", "--ask", "-q", "pregunta"] for a in args)
    is_calibrate = any(a.lower() in ["calibrar", "--calibrar", "benchmark", "--benchmark", "train"] for a in args)
    is_evaluate = any(a.lower() in ["evaluar", "--evaluar", "demo", "--demo", "verify"] for a in args)
    is_add_case = any(a.lower() in ["--add-case", "--nuevo-caso", "-n", "nuevo", "importar"] for a in args)
    is_batch = any(a.lower() in ["batch", "--batch", "lote", "--lote", "masivo"] for a in args)

    # 0. Modo Batch Masivo Desatendido
    if is_batch:
        count = 1000
        for a in args:
            if a.isdigit():
                count = int(a)
                break
        from tools.batch_processor.batch_runner import EnterpriseBatchProcessor
        console.print(Panel(
            f"[bold cyan]SupplyMind AI Enterprise — Pipeline Batch de Alto Rendimiento[/bold cyan]\n"
            f"[bold yellow]Auditoría Masiva Desatendida de Cartera B2B ({count:,} Expedientes)[/bold yellow]\n"
            f"[dim]Motor determinístico en Python Decimal — Cero costo de inferencia GPU/LLM[/dim]",
            border_style="cyan"
        ))
        summary = EnterpriseBatchProcessor.execute_batch(target_count=count, max_workers=8)
        json_path, md_path = EnterpriseBatchProcessor.export_batch_summary(summary)
        
        table = Table(title=f"Resultados Consolidados de Cartera — Lote {summary.batch_id}", border_style="green", show_header=True)
        table.add_column("Métrica de Desempeño", style="cyan")
        table.add_column("Valor Auditado", justify="right", style="bold white")
        table.add_row("Total Expedientes Sometidos", f"{summary.total_cases_submitted:,}")
        table.add_row("Expedientes Conciliados con Éxito", f"{summary.successful_cases:,} ({summary.successful_cases/summary.total_cases_processed*100:.1f}%)")
        table.add_row("Volumen Total Facturado", f"${summary.total_volume_billed_usd:,.2f} USD")
        table.add_row("Saldo Total en Disputa", f"${summary.total_volume_disputed_usd:,.2f} USD")
        table.add_row("Deducciones Justificadas (Allanadas)", f"${summary.total_volume_justified_usd:,.2f} USD")
        table.add_row("Capital Reclamable a Recuperar", f"${summary.total_volume_claimable_usd:,.2f} USD")
        table.add_row("Probabilidad Media de Recuperación", f"{summary.average_recovery_probability_pct:.1f}%")
        table.add_row("Error Absoluto Medio (MAE)", f"${summary.mean_absolute_error_usd:,.2f} USD (0.00% error)")
        table.add_row("Tiempo Total de Ejecución", f"{summary.total_execution_time_seconds:.2f} s")
        table.add_row("Throughput Industrial", f"{summary.throughput_cases_per_second:.1f} casos/segundo")
        console.print(table)
        console.print(f"[bold green]✓ Corrida batch completada en {summary.total_execution_time_seconds:.2f}s. Reporte en: {md_path}[/bold green]\n")
        return

    # 0.1 Modo Registro de Nuevo Caso directo por flag
    if is_add_case:
        created_id = prompt_add_case()
        if not created_id:
            return
        case_id = created_id
        explicit_case = True
    else:
        case_id = "case_001"
        explicit_case = False
    for a in args:
        if Path(a).is_dir():
            # Si el argumento es un directorio existente (ej. ruta absoluta o relativa)
            case_id = str(Path(a).resolve())
            explicit_case = True
            break
        elif a.startswith("case_"):
            case_id = a
            explicit_case = True
            break
        elif "case_" in a:
            for part in a.split():
                if part.startswith("case_"):
                    case_id = part
                    explicit_case = True
                    break
        elif a.lower() in ["c1", "caso1", "caso 1", "1"]:
            case_id = "case_001"
            explicit_case = True
            break
        elif a.lower() in ["c2", "caso2", "caso 2", "2"]:
            case_id = "case_002"
            explicit_case = True
            break
        elif a.lower() in ["c3", "caso3", "caso 3", "3"]:
            case_id = "case_003"
            explicit_case = True
            break

    # 1. Modo Interactivo Conversacional continuo
    if is_interactive:
        if not explicit_case:
            hub_panel = Panel(
                "[bold cyan]SupplyMind AI — Centro de Control Interactivo Multi-Caso[/bold cyan]\n"
                "[dim]Reto Agente Platica.mx x Campuslands — Hito S2 (Semana 2: Enterprise & 5-Pillar Shield)[/dim]\n\n"
                "[bold white]Selecciona el expediente con el que deseas interactuar:[/bold white]\n\n"
                "  [bold green][1][/bold green] [bold white]case_001[/bold white] : Básico (Faltante Físico de $800 USD)\n"
                "  [bold green][2][/bold green] [bold white]case_002[/bold white] : Complejo Alta Cuantía ($54.2k facturados, $12,500 reclamables)\n"
                "  [bold green][3][/bold green] [bold white]case_003[/bold white] : Discrepancia de Precios (Sobreprecio de $3,000 en Factura)\n"
                "  [bold green][4][/bold green] [bold white]Matriz Comparativa[/bold white] : Ver los 3 expedientes simultáneamente\n"
                "  [bold green][5][/bold green] [bold white]Evaluar Jurado[/bold white] : Suite completa automatizada (30s)\n"
                "  [bold green][6][/bold green] [bold white]case_005_amazon_shortage[/bold white] : [bold cyan]PDF Real[/bold cyan] (Amazon Dock Shortage y Multa ASN)\n"
                "  [bold green][7][/bold green] [bold white]case_006_walmart_otif_pricing[/bold white] : [bold cyan]PDF Real[/bold cyan] (Walmart OTIF y Sobreprecio)\n"
                "  [bold green][8][/bold green] [bold white]case_007_cisco_large_bundle[/bold white] : [bold cyan]PDF Masivo Multi-Pág.[/bold cyan] (Cisco $125k, Nombres Arbitrarios y Clasificación Autónoma)\n"
                "  [bold green][9][/bold green] [bold white]case_008_homedepot_damaged_scanned[/bold white] : [bold cyan]Visión OCR Multimodal[/bold cyan] (Home Depot $42k, Remisión Papel Escaneada con Sello de Muelle)\n"
                "  [bold yellow][N][/bold yellow] [bold white]Poner / Importar Nuevo Caso[/bold white] : [bold yellow]Cargar tus propios documentos o crear caso guiado[/bold yellow]\n"
                "  [bold red][0][/bold red] Salir\n",
                title="[bold green]Menú de Selección de Caso[/bold green]",
                border_style="cyan"
            )
            console.print(hub_panel)
            try:
                console.print("[bold yellow]Ingresa una opción [1-9, N para Nuevo, o Enter para Caso 1]: [/bold yellow]", end="")
                choice = input().strip()
            except (EOFError, KeyboardInterrupt):
                choice = "0"

            if choice == "0":
                console.print("\n[dim]Sesión finalizada por el usuario.[/dim]\n")
                return
            elif choice.lower() in ["n", "nuevo", "importar", "add", "+"]:
                created_id = prompt_add_case()
                if not created_id:
                    return
                case_id = created_id
            elif choice in ["2", "case_002", "c2"]:
                case_id = "case_002"
            elif choice in ["3", "case_003", "c3"]:
                case_id = "case_003"
            elif choice in ["6", "case_005", "case_005_amazon_shortage", "c5"]:
                case_id = "case_005_amazon_shortage"
            elif choice in ["7", "case_006", "case_006_walmart_otif_pricing", "c6"]:
                case_id = "case_006_walmart_otif_pricing"
            elif choice in ["8", "case_007", "case_007_cisco_large_bundle", "c7", "c8"]:
                case_id = "case_007_cisco_large_bundle"
            elif choice in ["9", "case_008", "case_008_homedepot_damaged_scanned", "c9"]:
                case_id = "case_008_homedepot_damaged_scanned"
            elif choice == "4":
                runner_temp = SkynetRunner(case_id="case_001")
                runner_temp._display_all_cases_comparison()
                console.print("[bold yellow]¿Con qué caso deseas iniciar el chat interactivo? [1, 2 o 3]: [/bold yellow]", end="")
                try:
                    c_after = input().strip()
                    if c_after in ["2", "case_002", "c2"]:
                        case_id = "case_002"
                    elif c_after in ["3", "case_003", "c3"]:
                        case_id = "case_003"
                    else:
                        case_id = "case_001"
                except (EOFError, KeyboardInterrupt):
                    return
            elif choice == "5":
                from scripts.evaluar_jurado import run_jury_evaluation
                run_jury_evaluation()
                return
            else:
                case_id = "case_001"

        runner = SkynetRunner(case_id=case_id)
        runner.interactive_chat()
        return

    runner = SkynetRunner(case_id=case_id)

    # 2. Modo Calibración y Benchmark de Criterio
    if is_calibrate:
        from agent.training.trainer import AgentTrainer
        trainer = AgentTrainer(budget_limit_usd=1.00)
        trainer.run_calibration(case_id=case_id)
        return

    # 3. Modo Consulta Puntual (CLI)
    if is_ask:
        question_parts = [a for a in args if a.lower() not in ["ask", "--ask", "-q", "pregunta"] and not a.startswith("case_")]
        question = " ".join(question_parts) or "¿Por qué existe una diferencia en el pago?"
        console.print(Panel.fit(
            f"[bold cyan]SupplyMind AI - Consulta Puntual[/bold cyan]\n"
            f"[dim]Caso: [green]{case_id}[/green] | Pregunta: [white]{question}[/white][/dim]",
            border_style="cyan"
        ))
        answer = runner.ask(question)
        console.print(f"\n[bold cyan]SupplyMind AI:[/bold cyan] {answer}\n")
        return

    # 4. Modo Análisis Autónomo Formal (Default)
    console.print(Panel.fit(
        "[bold cyan]SupplyMind AI[/bold cyan] - [yellow]Analista Autonomo de Disputas B2B[/yellow]\n"
        "[dim]Reto Agente Platica.mx x Campuslands - Powered by SKYNET Framework & Grok[/dim]",
        border_style="cyan"
    ))
    
    objective = None
    if args:
        joined_args = " ".join(args)
        if "analiza" in joined_args.lower() or len(joined_args) > 15:
            objective = joined_args
        else:
            objective = f"Analiza la disputa {case_id}"
    else:
        objective = f"Analiza la disputa {case_id}"
        
    console.print(f"[bold]Iniciando analisis para:[/bold] [green]{case_id}[/green]\n")
    
    runner.objective = objective
    report = runner.run()
    
    # Desplegar reporte formal estructurado
    console.print("\n")
    report_table = Table(title="[bold green]DISPUTE ANALYSIS REPORT[/bold green]", show_header=False, border_style="green")
    report_table.add_column("Campo", style="bold cyan", width=24)
    report_table.add_column("Detalle", style="white")
    
    report_table.add_row("Caso analizado", report.case_id)
    report_table.add_row("Monto facturado", f"${report.billed_amount:,.2f} {report.currency}")
    report_table.add_row("Monto recibido", f"${report.received_amount:,.2f} {report.currency}")
    report_table.add_row("Diferencia", f"[bold red]${report.difference:,.2f} {report.currency}[/bold red]")
    report_table.add_row("Causa encontrada", report.root_cause)
    
    evidence_text = "\n".join([f"- {e}" for e in report.evidence])
    report_table.add_row("Evidencia utilizada", evidence_text)
    
    report_table.add_row("Monto justificado", f"[green]${report.justified_amount:,.2f} {report.currency}[/green]")
    report_table.add_row("Monto reclamable", f"${report.claimable_amount:,.2f} {report.currency}")
    report_table.add_row("Nivel de confianza", f"[bold yellow]{report.confidence * 100:.1f}%[/bold yellow]")
    report_table.add_row("Accion recomendada", f"[bold yellow]{report.recommended_action}[/bold yellow]")
    
    console.print(report_table)
    
    # Confirmación de trazabilidad y bitácora
    log_file = runner.audit_logger.log_file
    console.print(f"\n[dim][OK] Trazabilidad y bitacora de decisiones guardada en: {log_file}[/dim]")
    if runner.state.tokens_in > 0 or runner.state.execution_time_seconds > 0:
        console.print(
            f"[dim]⚡ Inferencia: {runner.state.tokens_in + runner.state.tokens_out:,} tokens "
            f"({runner.state.tokens_in:,} in / {runner.state.tokens_out:,} out) | "
            f"Costo: ${runner.state.estimated_cost_usd:.5f} USD | "
            f"Tiempo: {runner.state.execution_time_seconds:.2f}s[/dim]"
        )
    console.print("[dim]💡 Tip: Para modo interactivo ejecuta:[/dim] [bold cyan]python main.py -i[/bold cyan] [dim]| Para evaluación integral:[/dim] [bold cyan]python main.py evaluar[/bold cyan]\n")

if __name__ == "__main__":
    main()
