"""
agent/core/retailer_buyer_simulator.py
Simulador de Comprador Hostil Retail para Confrontación Bilateral Multi-Agente (Sprint 6.1).
Emula los perfiles psicológicos, tácticas de desgaste y contrapropuestas de los 5 grandes arquetipos de retail:
- Walmart OTIF (Compliance estricto de entregas a tiempo)
- Amazon FC (Algoritmos punitivos de Fulfillment Center)
- Soriana Rebate (Deducciones unilaterales de merma y fin de año)
- Costco Depot (Rechazos de tarima en patio sin acta)
- Generic B2B (Comprador comercial tradicional)
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json

from data.models import RetailerArchetypeConfig, NegotiationDuelRound, NegotiationDuelSession
from config.settings import settings

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


ARCHETYPE_REGISTRY: Dict[str, RetailerArchetypeConfig] = {
    "WALMART_OTIF": RetailerArchetypeConfig(
        archetype_id="WALMART_OTIF",
        retailer_name="Walmart Inc. Retail Operations",
        buyer_title="Lic. Roberto Garza (Director de Compras & Compliance OTIF)",
        initial_demand_pct=100.0,
        concession_resistance_score=9.0,
        key_pressure_points=["Degradación de Scorecard OTIF", "Pérdida de ventana de cita prioritaria", "Retención de pedidos futuros"],
        evidence_vulnerability="ASN_EDI_856_AND_SEAL",
        tone="Intransigente, corporativo, escudado en métricas de logística"
    ),
    "AMAZON_FC": RetailerArchetypeConfig(
        archetype_id="AMAZON_FC",
        retailer_name="Amazon Fulfillment Services LLC",
        buyer_title="Marcus Vance (Vendor Chargeback Resolution Manager)",
        initial_demand_pct=100.0,
        concession_resistance_score=9.5,
        key_pressure_points=["Bloqueo de Buy-Box en Vendor Central", "Cobro automático de tarifa de discrepancia", "Suspensión de POs semanales"],
        evidence_vulnerability="EDI_997_AND_C_TPAT",
        tone="Frío, algorítmico, automatizado y despersonalizado"
    ),
    "SORIANA_REBATE": RetailerArchetypeConfig(
        archetype_id="SORIANA_REBATE",
        retailer_name="Organización Soriana S.A.B. de C.V.",
        buyer_title="Ing. Carlos Villalobos (Gerente de Liquidaciones y Cartera Comercial)",
        initial_demand_pct=100.0,
        concession_resistance_score=7.5,
        key_pressure_points=["Revisión de acuerdos verbales de volumen", "Retención de pagos en mesa de control", "Condonación de merma anual"],
        evidence_vulnerability="CCOM_ART88_PRECLUSION",
        tone="Burocrático, negociador clásico, apela a la continuidad de la relación"
    ),
    "COSTCO_DEPOT": RetailerArchetypeConfig(
        archetype_id="COSTCO_DEPOT",
        retailer_name="Costco Wholesale Corporation",
        buyer_title="Laura Santander (Auditora de Recibo en Plataforma y Muelle)",
        initial_demand_pct=100.0,
        concession_resistance_score=8.0,
        key_pressure_points=["Rechazo de tarimas completas en patio", "Cargo administrativo por reprogramación", "Pérdida de membrecía como vendor preferente"],
        evidence_vulnerability="DELIVERY_SLIP_AND_SEAL",
        tone="Pragmático, tajante sobre especificaciones de tarima y empaque"
    ),
    "GENERIC_B2B": RetailerArchetypeConfig(
        archetype_id="GENERIC_B2B",
        retailer_name="Cadena Comercial Mayorista B2B",
        buyer_title="Lic. Fernando Mora (Gerente de Cuentas por Pagar y Abastecimiento)",
        initial_demand_pct=100.0,
        concession_resistance_score=6.5,
        key_pressure_points=["Retraso de programaciones de pago", "Reasignación de cuotas de mercado a la competencia"],
        evidence_vulnerability="CONTRACT_CLAUSES_AND_ARITHMETIC",
        tone="Comercial tradicional, busca maximizar margen de fin de mes"
    )
}


class RetailerBuyerSimulator:
    """Motor que emula el comportamiento autónomo del comprador retail en el careo bilateral."""

    @classmethod
    def resolve_archetype(cls, case_id: str) -> RetailerArchetypeConfig:
        """Determina el arquetipo correspondiente a partir del ID del caso o la factura."""
        cid = case_id.lower()
        if "walmart" in cid:
            return ARCHETYPE_REGISTRY["WALMART_OTIF"]
        if "amazon" in cid:
            return ARCHETYPE_REGISTRY["AMAZON_FC"]
        if "soriana" in cid:
            return ARCHETYPE_REGISTRY["SORIANA_REBATE"]
        if "costco" in cid:
            return ARCHETYPE_REGISTRY["COSTCO_DEPOT"]

        # Inspección rápida de factura
        inv_path = ROOT_DIR / "data" / "cases" / case_id / "invoice.json"
        if inv_path.exists():
            try:
                with open(inv_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cust = (data.get("customer_id") or data.get("customer_name") or "").lower()
                    if "walmart" in cust:
                        return ARCHETYPE_REGISTRY["WALMART_OTIF"]
                    if "amazon" in cust:
                        return ARCHETYPE_REGISTRY["AMAZON_FC"]
                    if "soriana" in cust:
                        return ARCHETYPE_REGISTRY["SORIANA_REBATE"]
                    if "costco" in cust:
                        return ARCHETYPE_REGISTRY["COSTCO_DEPOT"]
            except Exception:
                pass

        return ARCHETYPE_REGISTRY["GENERIC_B2B"]

    @classmethod
    def generate_buyer_turn(
        cls,
        archetype: RetailerArchetypeConfig,
        round_number: int,
        total_dispute: Decimal,
        justified_amount: Decimal,
        claimable_amount: Decimal,
        previous_round: Optional[NegotiationDuelRound] = None
    ) -> Tuple[str, str, Decimal, Decimal]:
        """
        Genera la postura dialéctica y oferta numérica del comprador retail.
        Retorna: (buyer_message, buyer_stance, buyer_demand_credit_memo, buyer_cash_payout_offer)
        """
        total_dispute = total_dispute.quantize(Decimal("0.01"))
        justified_amount = justified_amount.quantize(Decimal("0.01"))
        claimable_amount = claimable_amount.quantize(Decimal("0.01"))

        # Ronda 1: Postura de máxima exigencia (100% deducción)
        if round_number == 1 or not previous_round:
            demand_cm = total_dispute
            cash_offer = Decimal("0.00")
            stance = "INTRANSIGENT"

            if archetype.archetype_id == "WALMART_OTIF":
                msg = (
                    f"Buenas tardes. Nuestra mesa de control validó que su entrega incumplió los parámetros de cita OTIF "
                    f"y presenta incidencias de recibo. Conforme a las políticas de Vendor Performance, no podemos liberar el pago de "
                    f"${claimable_amount:,.2f} USD. Exigimos la emisión inmediata de una Nota de Crédito por ${demand_cm:,.2f} USD "
                    f"para desbloquear la colocación de sus siguientes órdenes de compra."
                )
            elif archetype.archetype_id == "AMAZON_FC":
                msg = (
                    f"Notificación de Vendor Central: Se generó un Chargeback automático de recepción en CEDIS por ${total_dispute:,.2f} USD "
                    f"debido a discrepancias en el escaneo de bultos. El algoritmo retuvo el saldo de forma definitiva. Para proceder a "
                    f"conciliar el estatus de su cuenta, solicitamos formalizar la Nota de Crédito por ${demand_cm:,.2f} USD."
                )
            elif archetype.archetype_id == "SORIANA_REBATE":
                msg = (
                    f"Estimado proveedor: Como es de su conocimiento, las deducciones aplicadas por ${total_dispute:,.2f} USD corresponden "
                    f"al acuerdo de merma operativa y ajuste comercial acordado con la dirección de compras. No procede el reclamo de "
                    f"${claimable_amount:,.2f} USD. Requerimos la Nota de Crédito por el monto total para continuar con la relación regular."
                )
            elif archetype.archetype_id == "COSTCO_DEPOT":
                msg = (
                    f"El reporte de muelle arrojó rechazo por tarimas en condiciones no aptas para rack de alta densidad. "
                    f"La retención de ${total_dispute:,.2f} USD está debidamente fundada en el reglamento de patio. Esperamos la "
                    f"Nota de Crédito por ${demand_cm:,.2f} USD para dar por saldada la partida."
                )
            else:
                msg = (
                    f"Hemos revisado la factura y confirmamos las retenciones contables por ${total_dispute:,.2f} USD. "
                    f"Nuestra postura de cierre es mantener la deducción íntegra mediante Nota de Crédito por ${demand_cm:,.2f} USD."
                )

            return msg, stance, demand_cm, cash_offer

        # Rondas 2 a 5: Respuesta reactiva a las pruebas de SupplyMind
        ev_shown = previous_round.evidence_exhibited
        supplier_offer_cm = previous_round.supplier_offer_credit_memo

        # Evaluar la contundencia de las pruebas exhibidas
        has_seal_or_deliv = any("remisión" in e.lower() or "sello" in e.lower() or "c-tpat" in e.lower() or "del-" in e.lower() for e in ev_shown)
        has_edi = any("edi" in e.lower() or "856" in e.lower() or "997" in e.lower() or "asn" in e.lower() for e in ev_shown)
        has_law = any("artículo 88" in e.lower() or "preclusión" in e.lower() or "código de comercio" in e.lower() or "scjn" in e.lower() for e in ev_shown)

        # Grado de concesión del comprador según ronda y pruebas
        if round_number == 2:
            # Comprador pasa de intransigente a defensivo
            stance = "DEFENSIVE"
            # Cede 25% de lo reclamable si hay pruebas contundentes
            if has_seal_or_deliv or has_edi:
                concession_from_claim = (claimable_amount * Decimal("0.25")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                demand_cm = (total_dispute - concession_from_claim).quantize(Decimal("0.01"))
                cash_offer = concession_from_claim
                msg = (
                    f"Tomamos nota de la remisión y telemetría electrónica que exhiben. Sin embargo, nuestros registros de patio "
                    f"aún indican demoras y gastos operativos de descarga. Como muestra de buena fe, estamos dispuestos a liberar "
                    f"${cash_offer:,.2f} USD en transferencia si aceptan una Nota de Crédito por ${demand_cm:,.2f} USD."
                )
            else:
                demand_cm = (total_dispute * Decimal("0.90")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                cash_offer = (total_dispute - demand_cm).quantize(Decimal("0.01"))
                msg = (
                    f"Sus argumentos carecen de respaldo técnico contundente en nuestro sistema. A lo sumo podemos liberar "
                    f"${cash_offer:,.2f} USD si formalizan la Nota de Crédito por ${demand_cm:,.2f} USD."
                )

        elif round_number == 3:
            # Comprador evalúa preclusión legal o pruebas irrefutables
            stance = "PARTIAL_CONCESSION"
            if has_law or (has_seal_or_deliv and has_edi):
                # Comprador se ve obligado a ceder 50% de lo reclamable
                concession_from_claim = (claimable_amount * Decimal("0.50")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                demand_cm = (justified_amount + (claimable_amount - concession_from_claim)).quantize(Decimal("0.01"))
                cash_offer = concession_from_claim
                msg = (
                    f"Tras consultar con nuestra área legal sobre la preclusión del Art. 88 del Código de Comercio y el sello C-TPAT, "
                    f"reconocemos que no hubo protesta oportuna en muelle de ciertas partidas. Proponemos un punto medio: les liquidamos "
                    f"${cash_offer:,.2f} USD en banco a cambio de una Nota de Crédito por ${demand_cm:,.2f} USD."
                )
            else:
                concession_from_claim = (claimable_amount * Decimal("0.35")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                demand_cm = (total_dispute - concession_from_claim).quantize(Decimal("0.01"))
                cash_offer = concession_from_claim
                msg = (
                    f"Aceptamos reconsiderar parcialmente las partidas objetadas. Nuestra contraoferta es liquidar ${cash_offer:,.2f} USD "
                    f"si ustedes absorben ${demand_cm:,.2f} USD mediante Nota de Crédito."
                )

        elif round_number == 4:
            # Comprador busca cerrar ante riesgo de arbitraje
            stance = "PARTIAL_CONCESSION"
            # Cede hasta el 75% de lo reclamable si el proveedor insiste con firmeza
            concession_from_claim = (claimable_amount * Decimal("0.75")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            demand_cm = (justified_amount + (claimable_amount - concession_from_claim)).quantize(Decimal("0.01"))
            cash_offer = concession_from_claim
            msg = (
                f"Para evitar elevar esta controversia a un arbitraje comercial formal bajo reglas ICC, nuestra gerencia autoriza "
                f"un desembolso bancario de ${cash_offer:,.2f} USD. Únicamente requerimos la Nota de Crédito por el faltante real en muelle "
                f"y una deducción administrativa reducida por ${demand_cm:,.2f} USD."
            )

        else: # round_number >= 5: Oferta final de liquidación
            stance = "FINAL_SETTLEMENT"
            # Comprador se allana al monto estrictamente justificado en remisión más mínimo residual
            demand_cm = justified_amount
            cash_offer = claimable_amount
            msg = (
                f"Posición final e inamovible de la mesa de compras: Aceptamos liberar la totalidad del saldo reclamable en efectivo "
                f"por ${cash_offer:,.2f} USD en un plazo de 3 días bancarios, condicionada a que ustedes emitan la Nota de Crédito "
                f"por el faltante físico real de ${demand_cm:,.2f} USD constatado en la remisión de muelle. Solicitamos la rúbrica del acuerdo."
            )

        return msg, stance, demand_cm, cash_offer
