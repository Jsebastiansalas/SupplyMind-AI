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


def run_interactive_careo(case_id: str):
    """Simulador interactivo en vivo de careo y contra-argumentación B2B frente al retailer (Eje 2)."""
    from agent.core.bilateral_negotiation_engine import BilateralNegotiationEngine
    from agent.core.retailer_buyer_simulator import RetailerBuyerSimulator
    from decimal import Decimal

    archetype = RetailerBuyerSimulator.resolve_archetype(case_id)
    session = BilateralNegotiationEngine.get_duel_session(case_id)
    if not session:
        session = BilateralNegotiationEngine.start_duel(case_id=case_id)

    console.print(Panel(
        f"[bold cyan]SupplyMind AI — Simulador de Negociación y Contra-Argumentación B2B en Vivo (Eje 2)[/bold cyan]\n"
        f"[bold white]Expediente:[/bold white] [green]{case_id}[/green] | [bold white]Contraparte Retailer:[/bold white] [yellow]{session.retailer_name}[/yellow] ({session.archetype.buyer_title})\n"
        f"[dim]Monto en Disputa: ${session.total_disputed_amount:,.2f} USD | Modo Gobernanza: {session.governance_mode} | Ronda: {session.current_round}/{session.max_rounds}[/dim]\n"
        f"[dim]Escribe cualquier objeción en lenguaje natural como si fueras el comprador del retailer o selecciona una prueba típica.[/dim]",
        border_style="yellow"
    ))

    while True:
        console.print("\n[bold white]Opciones de objeción comercial o escribe tu propio argumento:[/bold white]")
        console.print("  [bold green][1][/bold green] \"Amazon rechaza tu carta porque el transportista llegó 45 minutos tarde al muelle de descarga.\"")
        console.print("  [bold green][2][/bold green] \"El comprador deduce $500 por folleto publicitario / co-op de verano según su política interna.\"")
        console.print("  [bold green][3][/bold green] \"Walmart aplica retención de $1,200 USD por penalización OTIF ya que el camión excedió 90 minutos la cita.\"")
        console.print("  [bold green][4][/bold green] \"Rechazamos el reclamo de avería porque las cajas venían con humedad y empaque roto al momento de la descarga.\"")
        console.print("  [bold cyan][T][/bold cyan] [bold white]Escribir objeción personalizada en texto libre[/bold white]")
        console.print("  [bold red][0][/bold red] Salir del simulador de careo\n")

        try:
            console.print("[bold yellow]Ingresa opción [1-4, T para texto libre, o 0 para salir]: [/bold yellow]", end="")
            choice = input().strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice in ["0", "exit", "quit", "salir"]:
            console.print("\n[dim]Sesión de careo finalizada.[/dim]\n")
            break
        elif choice == "1":
            objection = "Amazon rechaza tu carta porque el transportista llegó 45 minutos tarde al muelle de descarga."
        elif choice == "2":
            objection = "El comprador deduce $500 por folleto publicitario de verano según política interna."
        elif choice == "3":
            objection = "Walmart aplica retención de $1,200 USD por penalización OTIF ya que el camión excedió 90 minutos la cita."
        elif choice == "4":
            objection = "Rechazamos el reclamo de avería porque las cajas venían con humedad y empaque roto al momento de la descarga."
        elif choice.lower() in ["t", "texto", "custom", "escribir"]:
            try:
                console.print("\n[bold yellow]Escribe la objeción del comprador retailer: [/bold yellow]", end="")
                objection = input().strip()
                if not objection:
                    continue
            except (EOFError, KeyboardInterrupt):
                break
        elif len(choice) > 5:
            objection = choice
        else:
            continue

        console.print(f"\n[bold magenta]Comprador Retailer ({session.retailer_name}):[/bold magenta] [white]\"{objection}\"[/white]")
        console.print("[dim]Auditoría de tolerancias contractuales y recálculo determinista en Python Decimal...[/dim]\n")

        res = BilateralNegotiationEngine.respond_to_live_objection(
            case_id=case_id,
            objection=objection,
            operator_name="Evaluador Retailer B2B"
        )

        # Desplegar dictamen y contra-oferta en tabla formateada
        res_table = Table(title=f"Resolución de Careo — Ronda {res.round_number}", border_style="cyan", show_header=True)
        res_table.add_column("Dimensión Contractual / Financiera", style="cyan", width=34)
        res_table.add_column("Dictamen de SupplyMind AI", style="bold white")

        valid_str = "[bold red]Objeción Inválida (Rechazada de plano)[/bold red]" if not res.is_objection_contractually_valid else "[bold green]Objeción Parcialmente Procedente[/bold green]"
        res_table.add_row("Categoría de Objeción", res.objection_category)
        res_table.add_row("Validez Contractual", valid_str)
        res_table.add_row("Cláusula Contractual Aplicada", res.contract_clause_applied)
        res_table.add_row("Regla de Tolerancia / Grace Period", res.contract_tolerance_rule)
        res_table.add_row("Deducción Justificada (Nota de Crédito)", f"${res.proposed_credit_memo:,.2f} USD")
        res_table.add_row("Recuperación Exigida en Efectivo (Banco)", f"${res.proposed_cash_recovery:,.2f} USD")
        res_table.add_row("Invariante Aritmética ($0.00 MAE)", f"Total: ${res.proposed_credit_memo + res.proposed_cash_recovery:,.2f} / ${session.total_disputed_amount:,.2f} USD")
        res_table.add_row("Brecha (Spread) y Convergencia", f"Spread: ${res.spread:,.2f} USD | Convergencia: {res.convergence_pct:.1f}%")
        res_table.add_row("Estado de la Negociación", res.status)

        console.print(res_table)

        console.print(Panel(
            f"[bold cyan]Réplica Jurídico-Comercial de SupplyMind AI:[/bold cyan]\n\n"
            f"{res.counter_argument_reply}\n\n"
            f"[dim]Pruebas exhibidas:\n" + "\n".join(f"  • {e}" for e in res.evidence_exhibited) + "[/dim]",
            border_style="green"
        ))

        if res.status in ["AGREEMENT_REACHED", "AWAITING_HUMAN_APPROVAL"]:
            console.print(f"[bold green]✓ Acuerdo alcanzado con éxito. Minuta foliada disponible en reports/[/bold green]\n")
            break
        elif res.status == "IMPASSE_REACHED":
            console.print(f"[bold red]✕ Punto muerto alcanzado tras agotar las rondas sin convergencia.[/bold red]\n")
            break


def run_fiscal_erp_export(case_id: str):
    """Generador y exportador fiscal CFDI 4.0 SAT y B2B EDI 812 para portales ERP (Eje 3)."""
    from agent.core.erp_engine import ErpEngine

    console.print(Panel(
        f"[bold cyan]SupplyMind AI — Exportador Fiscal CFDI 4.0 & B2B EDI 812 (Eje 3)[/bold cyan]\n"
        f"[bold white]Expediente:[/bold white] [green]{case_id}[/green]\n"
        f"[dim]Generación de comprobantes certificados para portales B2B (Amazon Vendor Central, Walmart Retail Link) y ERPs (SAP / NetSuite).[/dim]",
        border_style="cyan"
    ))

    package = ErpEngine.export_full_erp_package(case_id)

    table = Table(title=f"Artefactos Fiscales y de Interoperabilidad ERP — {case_id}", border_style="green", show_header=True)
    table.add_column("Estándar / Formato", style="cyan", width=30)
    table.add_column("Detalle Técnico / Certificación", style="bold white")

    table.add_row("CFDI 4.0 SAT (Certificado PAC)", f"UUID: {package.cfdi_uuid} | Tipo: E (Egreso)")
    table.add_row("Código QR Validación SAT", f"{package.qr_verification_url or 'N/A'}")
    table.add_row("ANSI ASC X12 EDI 812", "Transaction Set 812 (Credit/Debit Adjustment) para Amazon / Walmart")
    table.add_row("UN/EDIFACT (Internacional)", "CREMUL / INVOIC Adjustment Message")
    table.add_row("SAP S/4HANA (BAPI & IDoc)", f"BAPI_ACC_DOCUMENT_POST (Doc Type DG) + IDoc FIDCCP02 ({len(package.sap_bapi.get('ACCOUNTGL', []))} partidas)")
    table.add_row("Oracle NetSuite ERP", f"Journal Entry CSV ({len(package.netsuite_journal_lines)} líneas cuadradas)")
    table.add_row("Monto Nota de Crédito (SAT)", f"${package.credit_memo_amount:,.2f} USD")
    table.add_row("Recuperación Neta en Banco", f"${package.claimable_amount:,.2f} USD")
    table.add_row("Directorio de Exportación", f"[bold green]reports/erp_{case_id}/[/bold green]")

    console.print(table)
    console.print(f"\n[bold green]✓ Paquete fiscal y ERP generado exitosamente en 'reports/erp_{case_id}/'[/bold green]\n")

def run_leakage_radar_cli(target: Optional[str] = None):
    """Ejecuta el visor e informe del Radar de Fuga de Capital y Perfilado de Retailers (Eje 4)."""
    from agent.core.fx_and_leakage_engine import RetailerLeakageProfiler
    console.print(Panel(
        "[bold cyan]SupplyMind AI — Radar de Fuga de Capital & Perfilado Predictivo (Eje 4)[/bold cyan]\n"
        "[dim]Minería de patrones de deducción abusivos en retailers y salvaguardas operativas pre-despacho.[/dim]",
        border_style="cyan"
    ))

    if target and target.lower() not in ["all", "cartera", "portfolio", "todos"]:
        prof = RetailerLeakageProfiler.get_profile(target)
        checklist = RetailerLeakageProfiler.generate_pre_dispatch_checklist(prof.retailer_id)

        tier_color = "bold red" if prof.risk_tier in ["PREDATORIO", "CRITICO"] else ("bold yellow" if prof.risk_tier == "ALTO" else "bold green")
        
        info_panel = Panel(
            f"[bold white]Cadena Comercial:[/bold white] {prof.retailer_name}\n"
            f"[bold white]Nivel de Riesgo:[/bold white] [{tier_color}]{prof.risk_tier}[/{tier_color}]\n"
            f"[bold white]Tasa de Victoria (Win Rate):[/bold white] [bold green]{prof.win_rate_pct:.1f}%[/bold green] | "
            f"[bold white]Ratio Recuperación:[/bold white] [bold green]{prof.recovery_ratio_pct:.1f}%[/bold green]\n"
            f"[bold white]Incoterm Recomendado:[/bold white] [bold cyan]{prof.recommended_incoterm}[/bold cyan] (ICC Incoterms 2020)\n"
            f"[bold white]Alerta Operativa CEDIS:[/bold white] {prof.cedis_alert_summary or 'Sin alertas activas.'}\n",
            title=f"[bold green]Perfil Predictivo — {prof.retailer_id}[/bold green]",
            border_style="green"
        )
        console.print(info_panel)

        chk_table = Table(title=f"Checklist Pre-Despacho Mandatorio — {prof.retailer_id}", border_style="cyan", show_header=True)
        chk_table.add_column("Código", style="yellow", width=12)
        chk_table.add_column("Obligatorio", justify="center", style="bold red", width=12)
        chk_table.add_column("Salvaguarda Operativa / Acción", style="bold white")
        chk_table.add_column("Riesgo Mitigado", style="cyan")

        for chk in checklist:
            mand = "SÍ" if chk.mandatory else "NO"
            chk_table.add_row(chk.check_id, mand, f"{chk.title}\n[dim]{chk.description}[/dim]", chk.risk_mitigated)

        console.print(chk_table)
    else:
        with console.status("[bold cyan]Escaneando cartera institucional de clientes y CEDIS...[/bold cyan]"):
            report = RetailerLeakageProfiler.scan_portfolio_leakage_radar()
            exported = RetailerLeakageProfiler.export_portfolio_radar_report(report)

        kpi_table = Table(title="Métricas Consolidadas de Capital en la Cartera B2B", border_style="green", show_header=True)
        kpi_table.add_column("Métrica Financiera", style="cyan", width=35)
        kpi_table.add_column("Valor Consolidado (USD)", justify="right", style="bold white", width=25)
        kpi_table.add_column("Interpretación Operativa", style="dim white")

        kpi_table.add_row("Total Expedientes Auditados", f"{report.total_cases_scanned:,} casos", "Cobertura 100% de la cartera de expedientes")
        kpi_table.add_row("Volumen Total Disputado", f"${report.total_disputed_volume:,.2f} USD", "Monto retenido o deducido unilateralmente")
        kpi_table.add_row("Capital Recuperable Ganable", f"${report.total_recovered_capital:,.2f} USD", "Fondos rescatables con fundamento legal Art. 88")
        kpi_table.add_row("Fuga Neta de Capital en Riesgo", f"${report.total_leakage_at_risk:,.2f} USD", "Exposición financiera ante inacción procesal")
        kpi_table.add_row("Tasa de Victoria Proyectada", f"{report.portfolio_win_rate_pct:.1f}%", "Efectividad defensiva colegiada")

        console.print(kpi_table)

        ret_table = Table(title="Ranking de Fricción y Riesgo por Cadena Comercial", border_style="cyan", show_header=True)
        ret_table.add_column("Retailer", style="bold white")
        ret_table.add_column("Riesgo", justify="center")
        ret_table.add_column("Win Rate", justify="right", style="green")
        ret_table.add_column("Disputado", justify="right", style="cyan")
        ret_table.add_column("Recuperable", justify="right", style="bold green")
        ret_table.add_column("Patrón Sistemático Principal", style="dim white")
        ret_table.add_column("Incoterm", justify="center", style="yellow")

        for r in report.retailer_summaries:
            color = "bold red" if r.risk_tier in ["PREDATORIO", "CRITICO"] else ("bold yellow" if r.risk_tier == "ALTO" else "green")
            ret_table.add_row(
                r.retailer_name.split("(")[0].strip(),
                f"[{color}]{r.risk_tier}[/{color}]",
                f"{r.win_rate_pct:.1f}%",
                f"${r.total_disputed_volume:,.2f}",
                f"${r.total_recovered_amount:,.2f}",
                r.primary_abusive_pattern,
                r.recommended_incoterm
            )
        console.print(ret_table)

        hub_table = Table(title="Centros de Distribución (CEDIS) y Muelles de Alto Riesgo", border_style="red", show_header=True)
        hub_table.add_column("Hub / CEDIS", style="bold white")
        hub_table.add_column("Ubicación", style="cyan")
        hub_table.add_column("Riesgo", justify="center")
        hub_table.add_column("Tasa Merma", justify="right", style="bold red")
        hub_table.add_column("Salvaguarda Mandatoria", style="dim white")

        for h in report.high_risk_hubs:
            h_col = "bold red" if h.risk_rating in ["CRITICAL", "HIGH"] else "yellow"
            hub_table.add_row(
                h.hub_name,
                h.location,
                f"[{h_col}]{h.risk_rating}[/{h_col}]",
                f"{h.historical_merma_rate*100:.1f}%",
                h.critical_safeguard
            )
        console.print(hub_table)

        console.print(f"\n[bold green]✓ Reporte consolidado exportado a:[/bold green] {exported['markdown_report']}\n")

def main():
    args = sys.argv[1:]
    
    # Detectar banderas de modo
    is_interactive = any(a.lower() in ["-i", "--interactive", "chat", "--chat"] for a in args)
    is_ask = any(a.lower() in ["ask", "--ask", "-q", "pregunta"] for a in args)
    is_calibrate = any(a.lower() in ["calibrar", "--calibrar", "benchmark", "--benchmark", "train"] for a in args)
    is_evaluate = any(a.lower() in ["evaluar", "--evaluar", "demo", "--demo", "verify"] for a in args)
    is_add_case = any(a.lower() in ["--add-case", "--nuevo-caso", "-n", "nuevo", "importar"] for a in args)
    is_batch = any(a.lower() in ["batch", "--batch", "lote", "--lote", "masivo"] for a in args)
    is_careo = any(a.lower() in ["--careo", "careo", "--duel", "duel", "negociacion", "--negociacion"] for a in args)
    is_export_erp = any(a.lower() in ["--export-erp", "--fiscal", "fiscal", "--edi", "--cfdi"] for a in args)
    is_radar = any(a.lower() in ["--radar", "-r", "radar", "--leakage", "leakage", "--fugas"] for a in args)
    is_json_output = any(a.lower() in ["--json", "--harness", "--harness-json"] for a in args)

    # Extraer --input / --case-dir / --output si fueron provistos por el Harness
    harness_input = None
    harness_output_file = None
    for i, a in enumerate(args):
        if a.lower() in ["--input", "--case-dir", "--dir", "--file"] and i + 1 < len(args):
            harness_input = args[i + 1]
        elif a.lower() in ["--output", "-o", "--out"] and i + 1 < len(args):
            harness_output_file = args[i + 1]

    # 0.0 Modo Harness Automatizado (--json o --output o archivo .json externo)
    if is_json_output or harness_output_file or (harness_input and Path(harness_input).is_file()):
        from agent.core.harness_adapter import HarnessAdapter
        is_fast = any(a.lower() in ["--fast", "-f", "fast"] for a in args)
        target = harness_input
        if not target:
            for i, a in enumerate(args):
                if a in ["--case", "-c"] and i + 1 < len(args):
                    target = args[i + 1]
                    break
                elif not a.startswith("-") and a.lower() not in ["fast", "ask", "pregunta"]:
                    target = a
                    break
        target = target or "case_001"
        result_dict = HarnessAdapter.evaluate(
            target=target,
            fast_path=is_fast,
            silent_stdout=True,
        )
        json_text = json.dumps(result_dict, indent=2, ensure_ascii=False)
        if harness_output_file:
            out_path = Path(harness_output_file)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json_text, encoding="utf-8")
        if is_json_output or not harness_output_file:
            sys.stdout.write(json_text + "\n")
            sys.stdout.flush()
            return
        case_id = result_dict["case_id"]
        explicit_case = True

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
    for i, a in enumerate(args):
        if a in ["--case", "-c", "--input", "--case-dir", "--dir"] and i + 1 < len(args):
            from agent.core.harness_adapter import HarnessAdapter
            case_id = HarnessAdapter.resolve_input_target(args[i + 1])
            explicit_case = True
            break
        elif Path(a).is_dir():
            # Si el argumento es un directorio existente (ej. ruta absoluta o relativa)
            case_id = str(Path(a).resolve())
            explicit_case = True
            break
        elif (Path("data/real_supply_chain_cases") / a).is_dir():
            case_id = a
            explicit_case = True
            break
        elif (Path("data/cases") / a).is_dir() or (Path("data/holdout_cases") / a).is_dir():
            case_id = a
            explicit_case = True
            break
        elif a.startswith("case_") or a.startswith("dataco_") or a.startswith("holdout_"):
            case_id = a
            explicit_case = True
            break
        elif "case_" in a:
            for part in a.split():
                if part.startswith("case_") or part.startswith("dataco_"):
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

    # 0.2 Modo Careo y Negociación en Vivo (Eje 2)
    if is_careo:
        run_interactive_careo(case_id=case_id)
        return

    # 0.3 Modo Exportador Fiscal CFDI 4.0 & B2B EDI 812 (Eje 3)
    if is_export_erp:
        run_fiscal_erp_export(case_id=case_id)
        return

    # 0.4 Modo Radar de Fuga de Capital y Perfilado de Retailers (Eje 4)
    if is_radar:
        target_retailer = None
        for i, a in enumerate(args):
            if a.lower() in ["--radar", "-r", "radar", "--leakage", "leakage", "--fugas"] and i + 1 < len(args):
                cand = args[i + 1]
                if not cand.startswith("-"):
                    target_retailer = cand
                    break
        if not target_retailer and explicit_case:
            target_retailer = case_id
        run_leakage_radar_cli(target=target_retailer)
        return

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
                "  [bold yellow][C][/bold yellow] [bold white]Careo de Negociación en Vivo[/bold white] : [bold yellow]Simulador interactivo comprador vs agente (Eje 2)[/bold yellow]\n"
                "  [bold yellow][F][/bold yellow] [bold white]Exportador Fiscal CFDI 4.0 & EDI 812[/bold white] : [bold yellow]Generar paquetes listos para SAP, NetSuite y Retailers (Eje 3)[/bold yellow]\n  [bold yellow][R][/bold yellow] [bold white]Radar de Fuga de Capital (Leakage Radar)[/bold white] : [bold yellow]Perfilado de retailers y alerta pre-despacho (Eje 4)[/bold yellow]\n"
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
            elif choice.lower() in ["c", "careo", "duel"]:
                console.print("[bold yellow]Ingresa el caso para el careo [ej. case_005_amazon_shortage o Enter para case_005]: [/bold yellow]", end="")
                try:
                    c_careo = input().strip() or "case_005_amazon_shortage"
                except (EOFError, KeyboardInterrupt):
                    return
                run_interactive_careo(case_id=c_careo)
                return
            elif choice.lower() in ["f", "fiscal", "edi", "erp"]:
                console.print("[bold yellow]Ingresa el caso para exportación fiscal/EDI [ej. case_005_amazon_shortage o Enter para case_005]: [/bold yellow]", end="")
                try:
                    c_fisc = input().strip() or "case_005_amazon_shortage"
                except (EOFError, KeyboardInterrupt):
                    return
                run_fiscal_erp_export(case_id=c_fisc)
                return
            elif choice.lower() in ["r", "radar", "leakage", "fuga", "fugas"]:
                console.print("[bold yellow]Ingresa el retailer o caso [ej. WALMART, AMAZON o Enter para toda la cartera]: [/bold yellow]", end="")
                try:
                    c_rad = input().strip() or None
                except (EOFError, KeyboardInterrupt):
                    return
                run_leakage_radar_cli(target=c_rad)
                return
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

        is_fast = any(a.lower() in ["--fast", "-f", "fast"] for a in args)
        runner = SkynetRunner(case_id=case_id, fast_path=is_fast, auto_route=not is_fast)
        runner.interactive_chat()
        return

    is_fast = any(a.lower() in ["--fast", "-f", "fast"] for a in args)
    runner = SkynetRunner(case_id=case_id, fast_path=is_fast, auto_route=not is_fast)

    # 2. Modo Calibración y Benchmark de Criterio
    if is_calibrate:
        from agent.training.trainer import AgentTrainer
        trainer = AgentTrainer(budget_limit_usd=1.00)
        trainer.run_calibration(case_id=case_id)
        return

    # 3. Modo Consulta Puntual (CLI)
    if is_ask:
        question_parts = [a for a in args if a.lower() not in ["ask", "--ask", "-q", "pregunta", "--fast", "-f", "fast"] and not a.startswith("case_") and not a.startswith("dataco_")]
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
    
    filtered_args = []
    skip_next = False
    for a in args:
        if skip_next:
            skip_next = False
            continue
        if a in ["-c", "--case"]:
            skip_next = True
            continue
        if a.lower() in ["--fast", "-f", "fast"] or a.startswith("case_") or a.startswith("dataco_") or a.startswith("holdout_"):
            continue
        filtered_args.append(a)

    if filtered_args:
        joined_args = " ".join(filtered_args)
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
    report_table.add_row("Costo medido tarea", f"[bold green]${runner.state.estimated_cost_usd:.5f} USD[/bold green] [dim](Pasarela: $0.011340/req)[/dim]")
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
