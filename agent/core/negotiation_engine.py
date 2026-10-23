"""
agent/core/negotiation_engine.py
Motor de Negociación B2B Multitáctico (Fase 2 de SupplyMind AI Enterprise).
Genera 3 escenarios estratégicos de contrapropuesta comercial (Agresivo, Equilibrado, Conservación)
con matemática estricta en Decimal, cálculo de contraprestaciones recíprocas del comprador
y redacción automática de minutas formales de acuerdo de conciliación extrajudicial.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import re

from data.models import (
    DisputeAnalysisReport,
    CommercialConcession,
    NegotiationScenario,
    NegotiationPlan
)
from agent.core.concession_engine import ConcessionEngine, ConcessionIntent
from config.settings import settings

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def parse_negotiation_query(text: str) -> Optional[Dict[str, Any]]:
    """
    Analiza una consulta conversacional para detectar si el usuario solicita
    conocer los escenarios de negociación o si ordena ejecutar un escenario específico.
    """
    t = text.lower().strip()

    # 1. Selección directa de escenario
    if any(k in t for k in ["aplica escenario agresivo", "aplicar agresivo", "escenario agresivo", "postura agresiva", "cobro integro", "cobro íntegro", "via legal", "vía legal"]):
        return {"action": "apply", "scenario_id": "AGGRESSIVE"}

    if any(k in t for k in ["aplica escenario equilibrado", "aplicar equilibrado", "escenario equilibrado", "postura equilibrada", "conciliacion tactica", "conciliación táctica", "win-win", "win win", "acuerdo balanceado"]):
        return {"action": "apply", "scenario_id": "BALANCED"}

    if any(k in t for k in ["aplica escenario conservador", "aplicar conservador", "escenario conservador", "conservar relacion", "conservar relación", "preservar cliente", "retencion de cuenta", "retención de cuenta"]):
        return {"action": "apply", "scenario_id": "CONSERVATIVE"}

    # 2. Consulta general sobre opciones o escenarios de negociación
    negotiation_triggers = [
        "escenario", "escenarios", "negociar", "negociacion", "negociación",
        "contrapropuesta", "estrategia comercial", "que propones", "qué propones",
        "como negociar", "cómo negociar", "opciones de acuerdo", "tácticas de cobro",
        "tacticas de cobro", "minuta de acuerdo", "acuerdo bilateral"
    ]
    if any(k in t for k in negotiation_triggers):
        return {"action": "show_scenarios", "scenario_id": None}

    return None


class NegotiationEngine:
    """Motor central de generación, simulación y aplicación de estrategias de negociación B2B."""

    _cached_plans: Dict[str, NegotiationPlan] = {}

    @classmethod
    def get_account_metadata(cls, case_id: str) -> Dict[str, Any]:
        """Determina el nombre de la cuenta y su clasificación de nivel (Tier 1 vs Tier 2)."""
        cid = case_id.lower()
        if "amazon" in cid:
            return {"name": "Amazon Fulfillment Services LLC", "tier": "TIER_1_STRATEGIC", "annual_volume": 4500000.0}
        if "walmart" in cid:
            return {"name": "Walmart Inc. Retail Operations", "tier": "TIER_1_STRATEGIC", "annual_volume": 6800000.0}
        if "cisco" in cid:
            return {"name": "Cisco Systems Global Logistics", "tier": "TIER_1_STRATEGIC", "annual_volume": 3200000.0}
        if "mega" in cid or "retailer" in cid:
            return {"name": "Mega Retailer National S.A. de C.V.", "tier": "TIER_1_STRATEGIC", "annual_volume": 12000000.0}

        # Intento de lectura de invoice o delivery
        case_dir = ROOT_DIR / "data" / "cases" / case_id
        inv_path = case_dir / "invoice.json"
        if inv_path.exists():
            try:
                with open(inv_path, "r", encoding="utf-8") as f:
                    inv_data = json.load(f)
                    cust = inv_data.get("customer_id") or inv_data.get("customer_name") or "Cliente Comercial B2B"
                    amt = float(inv_data.get("total_amount", 0.0))
                    tier = "TIER_1_STRATEGIC" if amt >= 50000.0 else "TIER_2_REGULAR"
                    return {"name": cust, "tier": tier, "annual_volume": amt * 10}
            except Exception:
                pass

        return {"name": "Distribuidor Mayorista B2B", "tier": "TIER_2_REGULAR", "annual_volume": 500000.0}

    @classmethod
    def build_negotiation_plan(cls, case_id: str) -> NegotiationPlan:
        """
        Construye determinísticamente los 3 escenarios multi-tácticos de negociación
        basados en la auditoría contractual y las tolerancias comerciales de la cuenta.
        """
        base_report = ConcessionEngine.get_or_create_base_report(case_id)
        acct_meta = cls.get_account_metadata(case_id)

        total_dispute = abs(base_report.difference)
        base_justified = base_report.justified_amount
        base_claimable = base_report.claimable_amount

        # ====================================================================
        # ESCENARIO 1: AGRESIVO / COBRO CONTRACTUAL ÍNTEGRO (LEGAL STRICT)
        # ====================================================================
        # Postura de cero concesiones comerciales: cobro del 100% de lo reclamable.
        scen_agg_claimable = base_claimable
        scen_agg_justified = base_justified
        scen_agg_concession = Decimal("0.00")
        recovery_pct_agg = 100.0 if base_claimable > Decimal("0.00") else 100.0

        scenario_aggressive = NegotiationScenario(
            scenario_id="AGGRESSIVE",
            title="Escenario 1: Cobro Contractual Íntegro (Legal Strict)",
            strategy_summary=(
                "Exigencia estricta del 100% del saldo retenido ilegítimamente sin concesiones. "
                "Respaldo en cláusulas contractuales vinculantes y apercibimiento de intereses moratorios mercantiles."
            ),
            justified_amount=scen_agg_justified,
            claimable_amount=scen_agg_claimable,
            concession_amount=scen_agg_concession,
            recovery_rate_pct=recovery_pct_agg,
            friction_risk="ALTO",
            expected_timeline_days=25,
            counterparty_concession_requested=(
                f"Transferencia electrónica inmediata del 100% del saldo insoluto (${scen_agg_claimable:,.2f} USD) "
                f"en un plazo perentorio de 5 días hábiles, bajo apercibimiento de intereses moratorios (1.5% mensual) "
                f"y retención de entregas de órdenes de compra en proceso."
            ),
            tactical_action="Emisión de Requerimiento Formal Extrajudicial con apercibimiento legal mercantil.",
            formal_memo=(
                f"REQUERIMIENTO EXTRAJUDICIAL: Se requiere la liquidación inmediata de ${scen_agg_claimable:,.2f} USD. "
                f"Las retenciones aplicadas contravienen las cláusulas del contrato marco. No se autoriza ninguna "
                f"bonificación ni nota de crédito adicional."
            )
        )

        # ====================================================================
        # ESCENARIO 2: EQUILIBRADO / CONCILIACIÓN TÁCTICA (WIN-WIN RECÍPROCO)
        # ====================================================================
        # Concesión del 50% de la penalidad en disputa condicionada a pago inmediato del saldo restante
        if base_claimable > Decimal("0.00"):
            scen_bal_concession = (base_claimable * Decimal("0.50")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            scen_bal_claimable = (base_claimable - scen_bal_concession).quantize(Decimal("0.01"))
            scen_bal_justified = (base_justified + scen_bal_concession).quantize(Decimal("0.01"))
            recovery_pct_bal = float((scen_bal_claimable / base_claimable) * 100)
        else:
            scen_bal_concession = Decimal("0.00")
            scen_bal_claimable = Decimal("0.00")
            scen_bal_justified = base_justified
            recovery_pct_bal = 100.0

        scenario_balanced = NegotiationScenario(
            scenario_id="BALANCED",
            title="Escenario 2: Conciliación Táctica Comercial (Win-Win Recíproco)",
            strategy_summary=(
                f"Concesión del 50% de la penalidad (${scen_bal_concession:,.2f} USD) mediante Nota de Crédito comercial, "
                f"condicionada a liquidación bancaria del saldo restante en 5 días y salvaguarda contra multas en futuros despachos."
            ),
            justified_amount=scen_bal_justified,
            claimable_amount=scen_bal_claimable,
            concession_amount=scen_bal_concession,
            recovery_rate_pct=round(recovery_pct_bal, 1),
            friction_risk="MEDIO",
            expected_timeline_days=7,
            counterparty_concession_requested=(
                f"1. Pago bancario expedito del saldo neto acordado (${scen_bal_claimable:,.2f} USD) en menos de 5 días hábiles.\n"
                f"2. Firma de Minuta de Conciliación con exención de penalizaciones logísticas análogas en las siguientes 2 Órdenes de Compra.\n"
                f"3. Reasignación de citas prioritarias en muelle de CEDIS sin recargos por reprogramación."
            ),
            tactical_action="Propuesta formal de Adenda Bilateral de Finiquito con reciprocidad comercial.",
            formal_memo=(
                f"PROPUESTA DE CONCILIACIÓN BILATERAL: Ofrecemos emitir Nota de Crédito comercial por ${scen_bal_justified:,.2f} USD "
                f"(incluyendo ${scen_bal_concession:,.2f} USD de concesión voluntaria) a cambio del pago inmediato del saldo "
                f"de ${scen_bal_claimable:,.2f} USD en un plazo de 5 días hábiles y adenda de no penalización para los pedidos subsecuentes."
            )
        )

        # ====================================================================
        # ESCENARIO 3: CONSERVACIÓN DE CUENTA / RETENCIÓN ESTRATÉGICA (TIER-1)
        # ====================================================================
        # Absorción del 100% de la penalidad en litigio vía Nota de Crédito a cambio de concesiones de volumen
        scen_cons_concession = base_claimable
        scen_cons_claimable = Decimal("0.00")
        scen_cons_justified = (base_justified + scen_cons_concession).quantize(Decimal("0.01"))
        recovery_pct_cons = 0.0 if base_claimable > Decimal("0.00") else 100.0

        scenario_conservative = NegotiationScenario(
            scenario_id="CONSERVATIVE",
            title="Escenario 3: Conservación de Relación Estratégica (Account Retention)",
            strategy_summary=(
                f"Absorción comercial total del saldo en litigio (${scen_cons_concession:,.2f} USD) mediante Nota de Crédito integral. "
                f"Blindaje absoluto de la cuenta estratégica Tier-1 a cambio de compromisos vinculantes de volumen de compra anual."
            ),
            justified_amount=scen_cons_justified,
            claimable_amount=scen_cons_claimable,
            concession_amount=scen_cons_concession,
            recovery_rate_pct=recovery_pct_cons,
            friction_risk="BAJO",
            expected_timeline_days=2,
            counterparty_concession_requested=(
                f"1. Emisión de Nota de Crédito comercial por ${scen_cons_concession:,.2f} USD que finiquita la disputa.\n"
                f"2. Compromiso formal del comprador de incrementar en un 15% el volumen de compra en el siguiente trimestre.\n"
                f"3. Sello de cuenta en estatus 'Vendor Gold' con eliminación de penalizaciones automáticas por ASN/OTIF en el sistema EDI."
            ),
            tactical_action="Convenio de Cooperación Comercial Estratégica y Alianza a Largo Plazo.",
            formal_memo=(
                f"CONVENIO DE CONTINUIDAD ESTRATÉGICA: Como muestra de nuestro compromiso como proveedor estratégico Tier-1, "
                f"emitiremos Nota de Crédito por ${scen_cons_justified:,.2f} USD amparando la totalidad de la partida, sujeta al "
                f"cumplimiento del acuerdo de volumen y preferencia en órdenes de compra del siguiente período."
            )
        )

        recommended = "BALANCED" if acct_meta["tier"] == "TIER_1_STRATEGIC" else "AGGRESSIVE"

        plan = NegotiationPlan(
            case_id=case_id,
            account_name=acct_meta["name"],
            account_tier=acct_meta["tier"],
            recommended_scenario=recommended,
            total_dispute_amount=total_dispute,
            scenarios=[scenario_aggressive, scenario_balanced, scenario_conservative],
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        )

        cls._cached_plans[case_id] = plan
        return plan

    @classmethod
    def apply_scenario(
        cls,
        case_id: str,
        scenario_id: str,
        operator_name: str = "Director Comercial B2B"
    ) -> DisputeAnalysisReport:
        """
        Ejecuta y sella la selección de un escenario estratégico, recalculando
        los balances contables en Decimal y generando la Minuta Formal de Conciliación.
        """
        plan = cls.build_negotiation_plan(case_id)
        target_scenario = next((s for s in plan.scenarios if s.scenario_id.upper() == scenario_id.upper()), None)
        if not target_scenario:
            raise ValueError(f"Escenario '{scenario_id}' no válido. Opciones: AGGRESSIVE, BALANCED, CONSERVATIVE")

        # Configurar intención de concesión correspondiente
        if target_scenario.scenario_id == "AGGRESSIVE":
            intent = ConcessionIntent(
                is_concession=True,
                is_reset=True,
                reason="Adopción de Escenario Agresivo: Cobro íntegro del 100% del saldo reclamable bajo rigor contractual"
            )
        elif target_scenario.scenario_id == "BALANCED":
            intent = ConcessionIntent(
                is_concession=True,
                is_reset=False,
                percentage=Decimal("50.0"),
                target_concept="CONCILIACION_TACTICA_50",
                reason=f"Adopción de Escenario Equilibrado (Win-Win): Concesión del 50% condicionada a reciprocidad comercial"
            )
        else:  # CONSERVATIVE
            intent = ConcessionIntent(
                is_concession=True,
                is_reset=False,
                percentage=Decimal("100.0"),
                target_concept="CONSERVACION_CUENTA_100",
                reason="Adopción de Escenario Conservador: Condonación comercial total para preservar cuenta estratégica Tier-1"
            )

        # Aplicar mediante el ConcessionEngine probado
        updated_report = ConcessionEngine.apply_concession(case_id, intent, operator_name=operator_name)
        updated_report.active_scenario = target_scenario.scenario_id

        # Guardar la Minuta Formal de Conciliación Bilateral
        cls.generate_settlement_minutes(case_id, plan, target_scenario, updated_report, operator_name)

        return updated_report

    @classmethod
    def generate_settlement_minutes(
        cls,
        case_id: str,
        plan: NegotiationPlan,
        scenario: NegotiationScenario,
        report: DisputeAnalysisReport,
        operator_name: str = "Director Comercial B2B"
    ) -> str:
        """
        Redacta una Minuta Formal de Conciliación Extrajudicial y Transacción Comercial
        vinculante para enviar al comprador.
        """
        reports_dir = ROOT_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        minutes_path = reports_dir / f"minuta_acuerdo_{case_id}.md"

        now_str = datetime.now(timezone.utc).strftime("%d de %B de %Y")

        minutes_content = f"""# MINUTA DE CONCILIACIÓN Y CONVENIO DE TRANSACCIÓN COMERCIAL EXTRAJUDICIAL
**Expediente Arbitral:** `{case_id}`  
**Fecha de Emisión:** {now_str}  
**Partes:** Proveedor Autorizado de Suministro vs **{plan.account_name}** ({plan.account_tier})  
**Estrategia Aplicada:** **{scenario.title}**  
**Representante y Árbitro de Conciliación:** {operator_name} / SupplyMind AI Enterprise Platform  

---

### 1. ANTECEDENTES Y MATERIA DE LA DISPUTA
1. Con fecha contractual, se despacharon y facturaron mercancías correspondientes al expediente **`{case_id}`** por un importe nominal de **${report.billed_amount:,.2f} USD**.
2. La parte compradora realizó una liquidación bancaria neta de **${report.received_amount:,.2f} USD**, registrando una retención total de **${abs(report.difference):,.2f} USD** bajo conceptos de deducciones logísticas y operativas.
3. Tras la auditoría técnica documental y cruzamiento de remisiones de muelle contra el contrato comercial, las partes convienen de mutuo acuerdo la presente resolución transaccional.

---

### 2. ACUERDO DE LIQUIDACIÓN Y BALANCE FINANCIERO DEFINITIVO

| Rubro Financiero | Monto Liquidado (USD) | Término y Efecto Contable |
| :--- | :---: | :--- |
| **Total Facturado Original** | `${report.billed_amount:,.2f}` | Reconocido plenamente |
| **Deducción Justificada Aceptada** | `${report.justified_amount:,.2f}` | **Emisión de Nota de Crédito Comercial inmediata** |
| **Saldo Neto Exigible en Efectivo** | **`${report.claimable_amount:,.2f}`** | **Transferencia bancaria incondicional pactada** |
| **Tasa Efectiva de Recuperación** | **{scenario.recovery_rate_pct:.1f}%** | Eficiencia financiera alcanzada |

---

### 3. CLÁUSULAS DE RECIPROCIDAD Y CONTRAPRESTACIONES VINCULANTES
* **Cláusula 1 (Emisión de Nota de Crédito):** El proveedor emitirá y timbrará la Nota de Crédito comercial correspondiente por la cantidad de **${report.justified_amount:,.2f} USD** dentro de los 3 días hábiles posteriores a la firma de este convenio.
* **Cláusula 2 (Compromiso de Pago de Cartera):** La empresa **{plan.account_name}** se compromete a liquidar el saldo neto de **${report.claimable_amount:,.2f} USD** en un plazo no mayor a **{scenario.expected_timeline_days} días hábiles** mediante transferencia bancaria identificada.
* **Cláusula 3 (Contraprestaciones Comerciales Específicas):**  
{scenario.counterparty_concession_requested}
* **Cláusula 4 (Finiquito y No Repetición):** El cumplimiento de los términos aquí estipulados otorga finiquito total y recíproco respecto a las retenciones del expediente `{case_id}`, acordando ambas partes no repetir cargos retroactivos por los mismos conceptos.

---

### 4. SUSCRIPCIÓN Y RATIFICACIÓN

```text
POR EL PROVEEDOR:                                   POR EL COMPRADOR ({plan.account_name}):
________________________________________            ________________________________________
{operator_name}                                     Dirección de Abastecimiento & Cuentas por Pagar
SupplyMind AI Automated Settlement Unit             Comité de Conciliación de Proveedores
Fecha: {now_str}                                     Fecha: {now_str}
```
"""
        with open(minutes_path, "w", encoding="utf-8") as f:
            f.write(minutes_content)

        return minutes_content


def format_negotiation_plan_reply(plan: NegotiationPlan) -> str:
    """Formatea la propuesta de 3 escenarios en un mensaje ejecutivo Markdown para la consola de chat."""
    scenarios_cards = ""
    for s in plan.scenarios:
        badge = "⭐ RECOMENDADO" if s.scenario_id == plan.recommended_scenario else ""
        risk_emoji = "🔴" if s.friction_risk == "ALTO" else ("🟡" if s.friction_risk == "MEDIO" else "🟢")

        scenarios_cards += f"""
#### {s.title} {badge}
* **Cobro Exigible en Efectivo:** **`${s.claimable_amount:,.2f} USD`** (Recuperación: **{s.recovery_rate_pct:.1f}%**)
* **Nota de Crédito Ofrecida:** `${s.justified_amount:,.2f} USD` (Concesión: `${s.concession_amount:,.2f} USD`)
* **Riesgo de Fricción con Cliente:** {risk_emoji} `{s.friction_risk}` | **Plazo Proyectado:** `{s.expected_timeline_days} días`
* **Contraprestación Exigida al Cliente:**  
  {s.counterparty_concession_requested}
* **Instrucción para aplicar:** Escribe en el chat `Aplica el escenario {s.scenario_id.lower()}`.

---"""

    return f"""### 🤝 Propuesta Multi-Táctica de Negociación B2B
**Expediente:** `{plan.case_id}` | **Contraparte:** `{plan.account_name}` (`{plan.account_tier}`)  
**Monto Total en Disputa:** **`${plan.total_dispute_amount:,.2f} USD`**

Hemos simulado **3 escenarios determinísticos de contrapropuesta** adaptados al nivel estratégico de la cuenta:
{scenarios_cards}

💡 *Recomendación del Agente:* Para cuentas estratégicas tipo **{plan.account_tier}**, sugerimos el **Escenario {plan.recommended_scenario}** para optimizar la recuperación de flujo de efectivo sin deteriorar la relación comercial."""
