"""
agent/core/concession_engine.py
Motor Determinístico Human-in-the-Loop para Concesiones Comerciales y Recálculo Dinámico.
Permite que un operador humano ordene ajustes estratégicos en lenguaje natural
(ej. "Acepta el 50% de la penalidad ASN de $2,500 y concilia el resto"),
recalculando los balances contables en Decimal en menos de 1 segundo con trazabilidad auditable.
"""

import re
import json
import time
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Optional, Dict, Any, List

from data.models import DisputeAnalysisReport, CommercialConcession
from agent.core.skynet_runner import SkynetRunner
from config.settings import settings

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class ConcessionIntent:
    """Intención de concesión comercial o recálculo extraída de lenguaje natural."""
    def __init__(
        self,
        is_concession: bool = False,
        is_reset: bool = False,
        percentage: Optional[Decimal] = None,
        fixed_amount: Optional[Decimal] = None,
        target_concept: str = "PENALIZACION",
        reason: str = "Concesión estratégica autorizada por Human-in-the-Loop para preservar la cuenta"
    ):
        self.is_concession = is_concession
        self.is_reset = is_reset
        self.percentage = percentage
        self.fixed_amount = fixed_amount
        self.target_concept = target_concept
        self.reason = reason


def parse_concession_intent(text: str) -> Optional[ConcessionIntent]:
    """
    Analiza un mensaje en lenguaje natural para detectar si el operador solicita
    una concesión comercial o el reinicio de la auditoría estricta.
    """
    t = text.lower().strip()

    # 1. Detección de reinicio / reset
    if any(k in t for k in ["restaurar", "revertir", "deshacer concesion", "deshacer concesión", "reset", "revertir ajuste", "auditoria original", "auditoría original", "sin concesion", "sin concesión"]):
        return ConcessionIntent(
            is_concession=True,
            is_reset=True,
            reason="Reversión a auditoría contractual estricta solicitada por operador"
        )

    # 2. Detección de porcentaje: ej. "acepta el 50%", "condonar 50% de la multa", "absorber 30%"
    # Busca patrones tipo "50%", "50 %", "la mitad"
    pct_match = re.search(r"(\d{1,3}(?:\.\d+)?)\s*%", t)
    half_match = any(k in t for k in ["la mitad", "50 por ciento", "cincuenta por ciento"])
    all_match = any(k in t for k in ["todo", "el 100%", "toda la penalidad", "toda la multa", "condonar la penalidad", "condonar la multa", "absorber la penalidad"])

    percentage: Optional[Decimal] = None
    if pct_match:
        percentage = Decimal(pct_match.group(1))
    elif half_match:
        percentage = Decimal("50.0")
    elif all_match:
        percentage = Decimal("100.0")

    # 3. Detección de importe monetario fijo: ej. "acepta $1,000", "absorber 1250 usd", "conceder $500"
    amt_match = re.search(
        r"(?:aceptar|acepta|absorber|absorbe|condonar|condona|conceder|concede|ceder|cede)\s+(?:por\s+)?(?:\$\s*)?([0-9]{1,3}(?:[,\.][0-9]{3})*(?:[\.,][0-9]{1,2})?|[0-9]+(?:[\.,][0-9]{1,2})?)\s*(?:usd|dolares|dólares)?",
        t
    )
    fixed_amount: Optional[Decimal] = None
    if amt_match and not pct_match and not half_match:
        raw_num = amt_match.group(1)
        if "," in raw_num and "." in raw_num:
            raw_num = raw_num.replace(",", "")
        elif "," in raw_num:
            parts = raw_num.split(",")
            if len(parts[-1]) == 3:
                raw_num = raw_num.replace(",", "")
            else:
                raw_num = raw_num.replace(",", ".")
        try:
            fixed_amount = Decimal(raw_num)
        except Exception:
            fixed_amount = None

    # Si se detectó porcentaje o importe fijo, o verbos claros de concesión
    triggers = ["acepta", "aceptar", "condona", "condonar", "absorbe", "absorber", "concede", "conceder", "cede", "ceder", "bonifica", "bonificar", "perdonar", "perdona"]
    has_trigger = any(trig in t for trig in triggers)

    if (percentage is not None or fixed_amount is not None) and (has_trigger or "penaliz" in t or "multa" in t or "asn" in t or "pronto pago" in t or "deducci" in t):
        # Determinar concepto objetivo
        concept = "PENALIZACION_OPERATIVA"
        if "asn" in t:
            concept = "PENALIDAD_EDI_ASN"
        elif "pronto pago" in t or "financier" in t:
            concept = "DESCUENTO_PRONTO_PAGO"
        elif "averia" in t or "avería" in t or "daño" in t:
            concept = "AVERIA_MERCANCIA"
        elif "precio" in t:
            concept = "AJUSTE_PRECIO"

        return ConcessionIntent(
            is_concession=True,
            is_reset=False,
            percentage=percentage,
            fixed_amount=fixed_amount,
            target_concept=concept,
            reason=f"Ajuste estratégico de {concept} ordenado por operador Human-in-the-Loop"
        )

    return None


class ConcessionEngine:
    """Motor central de cálculo y persistencia de concesiones comerciales."""

    _cached_reports: Dict[str, DisputeAnalysisReport] = {}

    @classmethod
    def get_or_create_base_report(cls, case_id: str) -> DisputeAnalysisReport:
        """Obtiene el reporte base determinístico puro sin concesiones."""
        runner = SkynetRunner(case_id=case_id, fast_path=True, use_cache=True)
        return runner.run()

    @classmethod
    def apply_concession(
        cls,
        case_id: str,
        intent: ConcessionIntent,
        operator_name: str = "Operador Comercial Senior"
    ) -> DisputeAnalysisReport:
        """
        Ejecuta el recálculo contable determinístico aplicando la concesión
        sin alterar la conciliación física real de muelle.
        """
        base_report = cls.get_or_create_base_report(case_id)

        # Si es reset, restaurar valores base
        if intent.is_reset:
            restored_report = DisputeAnalysisReport(
                case_id=case_id,
                currency=base_report.currency,
                billed_amount=base_report.billed_amount,
                received_amount=base_report.received_amount,
                difference=base_report.difference,
                root_cause=base_report.root_cause,
                evidence=base_report.evidence,
                justified_amount=base_report.justified_amount,
                claimable_amount=base_report.claimable_amount,
                confidence=base_report.confidence,
                recommended_action=base_report.recommended_action,
                concessions=[]
            )
            cls._cached_reports[case_id] = restored_report
            cls._persist_report_files(case_id, restored_report)
            return restored_report

        # Cálculo exacto del monto de concesión en Decimal
        base_claimable = base_report.claimable_amount
        base_justified = base_report.justified_amount

        if intent.percentage is not None:
            pct_clamped = min(Decimal("100.0"), max(Decimal("0.0"), intent.percentage))
            concession_amount = (base_claimable * (pct_clamped / Decimal("100.0"))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        elif intent.fixed_amount is not None:
            concession_amount = min(base_claimable, intent.fixed_amount).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            concession_amount = (base_claimable * Decimal("0.50")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        new_justified = (base_justified + concession_amount).quantize(Decimal("0.01"))
        new_claimable = (base_claimable - concession_amount).quantize(Decimal("0.01"))

        # Registro auditable
        concession_record = CommercialConcession(
            concession_id=f"CONCESS-{case_id.upper()}-{int(time.time())}",
            applied_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            operator=operator_name,
            concession_type="PERCENTAGE_PENALTY" if intent.percentage else "FIXED_AMOUNT",
            target=intent.target_concept,
            original_claimable=base_claimable,
            concession_amount=concession_amount,
            new_claimable=new_claimable,
            new_justified=new_justified,
            reason=intent.reason
        )

        pct_label = f" ({intent.percentage:.0f}%)" if intent.percentage is not None else ""
        new_root_cause = (
            f"{base_report.root_cause} | [HUMAN-IN-THE-LOOP] Se aplicó concesión comercial autorizada de "
            f"${concession_amount:,.2f} USD{pct_label} sobre el saldo de penalización disputado."
        )

        if new_claimable > Decimal("0.00"):
            new_action = (
                f"Resolución Comercial Ajustada con Human-in-the-Loop: Emitir Nota de Crédito global por "
                f"${new_justified:,.2f} USD (incluyendo ${base_justified:,.2f} USD de faltante físico comprobado y "
                f"${concession_amount:,.2f} USD de concesión comercial acordada para preservar la relación de cuenta). "
                f"Exigir el pago bancario inmediato del saldo neto reclamable de ${new_claimable:,.2f} USD."
            )
        else:
            new_action = (
                f"Resolución Comercial con Acuerdo Pleno (Human-in-the-Loop): Emitir Nota de Crédito por el 100% "
                f"del saldo disputado (${new_justified:,.2f} USD) absorbiendo la penalización por política comercial. "
                f"Partida de cartera cerrada satisfactoriamente sin saldo reclamable pendiente."
            )

        updated_report = DisputeAnalysisReport(
            case_id=case_id,
            currency=base_report.currency,
            billed_amount=base_report.billed_amount,
            received_amount=base_report.received_amount,
            difference=base_report.difference,
            root_cause=new_root_cause,
            evidence=base_report.evidence + [
                f"Autorización Human-in-the-Loop: Concesión de ${concession_amount:,.2f} USD ({intent.reason}) s/ ID {concession_record.concession_id}"
            ],
            justified_amount=new_justified,
            claimable_amount=new_claimable,
            confidence=0.99,
            recommended_action=new_action,
            concessions=[concession_record]
        )

        cls._cached_reports[case_id] = updated_report
        cls._persist_report_files(case_id, updated_report, concession_record)
        return updated_report

    @classmethod
    def _persist_report_files(
        cls,
        case_id: str,
        report: DisputeAnalysisReport,
        concession: Optional[CommercialConcession] = None
    ) -> None:
        """Persiste el reporte actualizado en JSON y regenera la carta de reclamación formal."""
        reports_dir = ROOT_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # 1. Guardar reporte JSON
        json_path = reports_dir / f"dispute_report_{case_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

        # 2. Guardar carta de reclamación formal actualizada
        letter_path = reports_dir / f"carta_reclamacion_{case_id}.md"
        conc_clause = ""
        if concession:
            conc_clause = f"""
### 🤝 ACUERDO COMERCIAL Y CONCESIÓN MUTUA (HUMAN-IN-THE-LOOP)
- **Folio de Concesión:** `{concession.concession_id}`
- **Importe Concedido:** **${concession.concession_amount:,.2f} USD**
- **Fundamento Operativo:** {concession.reason}
- **Saldo Original en Litigio:** `${concession.original_claimable:,.2f} USD`
- **Saldo Neto Exigible:** **`${concession.new_claimable:,.2f} USD`**
"""

        letter_content = f"""# CARTA FORMAL DE RECLAMACIÓN Y CONCILIACIÓN COMERCIAL
**Ref: Expediente de Cartera {case_id}**  
**Fecha:** {datetime.now(timezone.utc).strftime("%d de %B de %Y")}  
**Autorización:** Dirección de Crédito y Cobranza / Human-in-the-Loop  

---

### Estimado Departamento de Cuentas por Pagar:

Acusamos recibo de la liquidación bancaria de la factura correspondiente al expediente **`{case_id}`**, por un importe facturado de **${report.billed_amount:,.2f} USD** y un monto recibido de **${report.received_amount:,.2f} USD**, registrando una retención neta de **${abs(report.difference):,.2f} USD**.

Tras la auditoría técnica y la instrucción de la dirección comercial, comunicamos la resolución ejecutiva de la partida:

1. **Partidas Aceptadas para Nota de Crédito (${report.justified_amount:,.2f} USD):**  
   Emitiremos de forma inmediata la **Nota de Crédito comercial por ${report.justified_amount:,.2f} USD**, la cual ampara las deducciones operativas legítimas y las concesiones comerciales autorizadas de común acuerdo para preservar la continuidad de la relación de suministro.

2. **Saldo Exigible e Incondicional de Cartera (${report.claimable_amount:,.2f} USD):**  
   Rechazamos formalmente las restantes retenciones que carecen de soporte documental y legal. Solicitamos la transferencia complementaria por el importe de **${report.claimable_amount:,.2f} USD** en un plazo perentorio de 10 días hábiles.
{conc_clause}
**Acción Recomendada:**  
{report.recommended_action}

Atentamente,  
**Dirección General de Cuentas por Cobrar y Conciliación Arbitral**  
*SupplyMind AI Enterprise Platform*
"""
        with open(letter_path, "w", encoding="utf-8") as lf:
            lf.write(letter_content)


def format_concession_reply(
    report: DisputeAnalysisReport,
    intent: ConcessionIntent,
    concession: Optional[CommercialConcession] = None
) -> str:
    """Genera una respuesta ejecutiva en Markdown formateada para la consola del chat."""
    if intent.is_reset:
        return f"""### 🔄 Auditoría Contractual Restaurada a Términos Originales

Se han revertido todas las concesiones previas para el expediente **`{report.case_id}`**:

| Concepto Financiero | Importe Original (USD) | Estado Contable |
| :--- | :---: | :--- |
| **Total Facturado** | `${report.billed_amount:,.2f}` | Emitido s/ Factura |
| **Total Pagado** | `${report.received_amount:,.2f}` | Liquidación Bancaria |
| **Diferencia Neta** | `${abs(report.difference):,.2f}` | Retención Aplicada |
| **Deducción Justificada** | `${report.justified_amount:,.2f}` | Faltante físico comprobado con sello |
| **Saldo Reclamable Íntegro** | **`${report.claimable_amount:,.2f}`** | **Cobro formal sin concesiones** |

**Dictamen:**  
{report.recommended_action}"""

    conc = concession or (report.concessions[0] if report.concessions else None)
    c_amt = conc.concession_amount if conc else Decimal("0.00")
    orig_claim = conc.original_claimable if conc else report.claimable_amount
    orig_just = (report.justified_amount - c_amt) if conc else report.justified_amount

    return f"""### ⚡ Concesión Comercial Human-in-the-Loop Aplicada con Éxito

Se ha recalculado el balance contable del expediente **`{report.case_id}`** conforme a tu instrucción:

| Parámetro Contable | Antes de Concesión | Concesión Aprobada | Saldo Ajustado (Ahora) |
| :--- | :---: | :---: | :---: |
| **Deducción Justificada (Nota de Crédito)** | `${orig_just:,.2f}` | `+${c_amt:,.2f}` | **`${report.justified_amount:,.2f} USD`** 🟢 |
| **Saldo Reclamable (Cobranza)** | `${orig_claim:,.2f}` | `-${c_amt:,.2f}` | **`${report.claimable_amount:,.2f} USD`** 🟡 |
| **Total Retención Conciliada** | `${abs(report.difference):,.2f}` | `$0.00` | **`${abs(report.difference):,.2f} USD`** ⚖️ |

---

#### 📋 Impacto Estratégico y Operativo:
1. **Nota de Crédito Comercial:** Se expande a **`${report.justified_amount:,.2f} USD`**, absorbiendo la penalización para salvaguardar la relación comercial con la cuenta.
2. **Reclamación Formal Restante:** Se ajusta a **`${report.claimable_amount:,.2f} USD`**, emitiendo un requerimiento formal por el saldo neto improcedente.
3. **Trazabilidad:** Folio `{conc.concession_id if conc else 'CONCESS-MANUAL'}` sellado en la bitácora con precisión estricta al centavo en `Decimal`.

*(Los paneles financieros, la Carta de Reclamación y el expediente han sido actualizados en tiempo real).*"""
