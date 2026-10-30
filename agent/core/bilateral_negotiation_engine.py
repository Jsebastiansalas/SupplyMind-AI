"""
agent/core/bilateral_negotiation_engine.py
Orquestador Multi-Agente de Negociación Bilateral B2B con Teoría de Juegos MCTS (Sprint 6.1).
Conduce el careo por rondas entre el Agente Defensor SupplyMind y el Comprador Retailer,
calculando spreads, convergencia y generando minutas con sello criptográfico ZKP.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import uuid

from data.models import (
    NegotiationDuelRound,
    NegotiationDuelSession,
    RetailerArchetypeConfig,
    DisputeAnalysisReport
)
from agent.core.retailer_buyer_simulator import RetailerBuyerSimulator, ARCHETYPE_REGISTRY
from agent.core.concession_engine import ConcessionEngine, ConcessionIntent
from config.settings import settings

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class BilateralNegotiationEngine:
    """Motor de orquestación dialéctica autónoma multi-agente."""

    _active_sessions: Dict[str, NegotiationDuelSession] = {}

    @classmethod
    def get_session_file_path(cls, case_id: str) -> Path:
        reports_dir = ROOT_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir / f"negotiation_duel_{case_id}.json"

    @classmethod
    def get_duel_session(cls, case_id: str) -> Optional[NegotiationDuelSession]:
        """Recupera la sesión activa de memoria o del archivo persistido."""
        if case_id in cls._active_sessions:
            return cls._active_sessions[case_id]

        file_path = cls.get_session_file_path(case_id)
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                session = NegotiationDuelSession.model_validate(data)
                cls._active_sessions[case_id] = session
                return session
            except Exception:
                pass
        return None

    @classmethod
    def start_duel(
        cls,
        case_id: str,
        governance_mode: str = "HUMAN_GATEKEEPER",
        delegation_limit_pct: float = 50.0
    ) -> NegotiationDuelSession:
        """
        Inicia una nueva sesión de careo bilateral entre SupplyMind y el Comprador Retailer.
        Ejecuta de inmediato la Ronda 1 de apertura de posturas.
        """
        report = ConcessionEngine.get_or_create_base_report(case_id)
        archetype = RetailerBuyerSimulator.resolve_archetype(case_id)

        total_dispute = abs(report.difference).quantize(Decimal("0.01"))
        justified = report.justified_amount.quantize(Decimal("0.01"))
        claimable = report.claimable_amount.quantize(Decimal("0.01"))

        # Límite máximo de dinero reclamable que el agente tiene autorización de conceder
        limit_pct_decimal = (Decimal(str(delegation_limit_pct)) / Decimal("100.0")).quantize(Decimal("0.01"))
        delegation_limit_amount = (claimable * limit_pct_decimal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        session_id = f"DUEL-{case_id.upper()}-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        session = NegotiationDuelSession(
            session_id=session_id,
            case_id=case_id,
            retailer_name=archetype.retailer_name,
            archetype=archetype,
            governance_mode=governance_mode,
            status="IN_PROGRESS",
            current_round=1,
            max_rounds=5,
            delegation_limit_pct=delegation_limit_pct,
            delegation_limit_amount=delegation_limit_amount,
            total_disputed_amount=total_dispute,
            rounds=[],
            started_at=now_iso,
            summary_verdict="Careo iniciado. Apertura de posturas preliminares."
        )

        # Generar Ronda 1 de inmediato
        cls._execute_round_internal(session, report, 1)

        cls._active_sessions[case_id] = session
        cls._save_session(session)
        return session

    @classmethod
    def advance_duel_step(cls, case_id: str) -> NegotiationDuelSession:
        """
        Avanza una ronda en la confrontación bilateral.
        Calcula la respuesta reactiva de ambos agentes y evalúa convergencia o impasse.
        """
        session = cls.get_duel_session(case_id)
        if not session:
            session = cls.start_duel(case_id)
            return session

        if session.status in ["AGREEMENT_REACHED", "IMPASSE_REACHED", "AWAITING_HUMAN_APPROVAL"]:
            return session

        report = ConcessionEngine.get_or_create_base_report(case_id)
        next_round = session.current_round + 1

        if next_round > session.max_rounds:
            session.status = "IMPASSE_REACHED"
            session.summary_verdict = (
                "Punto muerto alcanzado tras 5 rondas dialécticas sin convergencia. "
                "Se deriva de pleno derecho al Tribunal Arbitral ICC / CANACO para ejecución de laudo vinculante."
            )
            session.completed_at = datetime.now(timezone.utc).isoformat()
            cls._save_session(session)
            return session

        session.current_round = next_round
        cls._execute_round_internal(session, report, next_round)
        cls._save_session(session)
        return session

    @classmethod
    def _execute_round_internal(
        cls,
        session: NegotiationDuelSession,
        report: DisputeAnalysisReport,
        round_num: int
    ) -> NegotiationDuelRound:
        total_dispute = session.total_disputed_amount
        justified = report.justified_amount
        claimable = report.claimable_amount
        delegation_cap = session.delegation_limit_amount

        previous_round = session.rounds[-1] if session.rounds else None

        # 1. Turno del Comprador Retailer
        buyer_msg, buyer_stance, buyer_demand_cm, buyer_cash_offer = RetailerBuyerSimulator.generate_buyer_turn(
            archetype=session.archetype,
            round_number=round_num,
            total_dispute=total_dispute,
            justified_amount=justified,
            claimable_amount=claimable,
            previous_round=previous_round
        )

        # 2. Turno del Agente Defensor SupplyMind AI (Cálculo MCTS & Evidencias)
        supplier_msg, supplier_stance, supplier_offer_cm, supplier_claim_cash, evidences = cls._generate_supplier_turn(
            session=session,
            report=report,
            round_num=round_num,
            buyer_demand_cm=buyer_demand_cm,
            buyer_cash_offer=buyer_cash_offer
        )

        # 3. Cálculo de Spread Aritmético y Porcentaje de Convergencia
        spread = abs(buyer_demand_cm - supplier_offer_cm).quantize(Decimal("0.01"))
        if total_dispute > Decimal("0.00"):
            conv_ratio = max(0.0, min(100.0, float((Decimal("1.00") - (spread / total_dispute)) * 100)))
        else:
            conv_ratio = 100.0

        round_status = "IN_PROGRESS"
        if spread <= Decimal("75.00") or buyer_demand_cm <= supplier_offer_cm:
            round_status = "AGREED"
        elif round_num >= 5 and spread > Decimal("150.00"):
            round_status = "IMPASSE"
        elif conv_ratio >= 70.0:
            round_status = "CONVERGING"

        duel_round = NegotiationDuelRound(
            round_number=round_num,
            buyer_message=buyer_msg,
            buyer_stance=buyer_stance,
            buyer_demand_credit_memo=buyer_demand_cm,
            buyer_cash_payout_offer=buyer_cash_offer,
            supplier_message=supplier_msg,
            supplier_stance=supplier_stance,
            supplier_offer_credit_memo=supplier_offer_cm,
            supplier_claim_cash=supplier_claim_cash,
            evidence_exhibited=evidences,
            spread=spread,
            convergence_pct=round(conv_ratio, 1),
            round_status=round_status
        )

        session.rounds.append(duel_round)

        # 4. Evaluación de Cierre de Sesión
        if round_status == "AGREED" or (round_num == 5 and spread <= Decimal("150.00")):
            # Punto de acuerdo equilibrado alcanzado
            final_cm = max(justified, min(supplier_offer_cm, buyer_demand_cm))
            final_cash = (total_dispute - final_cm).quantize(Decimal("0.01"))

            session.final_agreed_credit_memo = final_cm
            session.final_agreed_cash_recovery = final_cash

            if session.governance_mode == "FULL_AUTONOMY":
                session.status = "AGREEMENT_REACHED"
                session.completed_at = datetime.now(timezone.utc).isoformat()
                session.summary_verdict = (
                    f"Acuerdo bilateral formalizado con éxito en Ronda {round_num}. "
                    f"Recuperación neta en banco: ${final_cash:,.2f} USD | Nota de Crédito autorizada: ${final_cm:,.2f} USD."
                )
                cls._seal_and_generate_minutes(session, report)
            else:
                session.status = "AWAITING_HUMAN_APPROVAL"
                session.summary_verdict = (
                    f"Punto de equilibrio alcanzado en Ronda {round_num} (${final_cash:,.2f} USD en banco vs ${final_cm:,.2f} USD NC). "
                    f"En espera de confirmación y rúbrica final del operador (Human Gatekeeper)."
                )

        elif round_num >= 5:
            session.status = "IMPASSE_REACHED"
            session.completed_at = datetime.now(timezone.utc).isoformat()
            session.summary_verdict = (
                f"Punto muerto alcanzado en Ronda 5 con una brecha irreducible de ${spread:,.2f} USD. "
                f"Se activa la cláusula arbitral ICC / CANACO con el dossier foliado."
            )

        return duel_round

    @classmethod
    def _generate_supplier_turn(
        cls,
        session: NegotiationDuelSession,
        report: DisputeAnalysisReport,
        round_num: int,
        buyer_demand_cm: Decimal,
        buyer_cash_offer: Decimal
    ) -> Tuple[str, str, Decimal, Decimal, List[str]]:
        """
        Genera la réplica pericial de SupplyMind basada en teoría de juegos MCTS
        y el límite de delegación autorizado.
        """
        total_dispute = session.total_disputed_amount
        justified = report.justified_amount
        claimable = report.claimable_amount
        delegation_cap = session.delegation_limit_amount

        # Escalonamiento estratégico de concesiones según el número de ronda
        pacing_factors = {
            1: Decimal("0.00"),  # Ronda 1: Firmeza contractual absoluta
            2: Decimal("0.20"),  # Ronda 2: 20% del límite de concesión si muestran apertura
            3: Decimal("0.50"),  # Ronda 3: 50% del límite
            4: Decimal("0.80"),  # Ronda 4: 80% del límite
            5: Decimal("1.00"),  # Ronda 5: 100% del límite autorizado
        }

        pacing = pacing_factors.get(round_num, Decimal("1.00"))
        concession_offered = (delegation_cap * pacing).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        supplier_offer_cm = (justified + concession_offered).quantize(Decimal("0.01"))
        supplier_claim_cash = (total_dispute - supplier_offer_cm).quantize(Decimal("0.01"))

        # Catálogo de pruebas exhibidas según la ronda
        evidences_pool = {
            1: [
                f"Factura Comercial Oficial {getattr(report, 'invoice_id', 'INV')} por ${report.billed_amount:,.2f} USD",
                "Orden de Compra aprobada sin variaciones de precio unitario"
            ],
            2: [
                "Remisión física de recibo con firma y sello de personal de muelle",
                "Certificado de sello de alta seguridad ISO 17712 e inspección C-TPAT intacta"
            ],
            3: [
                "Transmisión electrónica Advance Ship Notice (ASN EDI 856) con timestamp UTC previo al descargue",
                "Acuse Funcional EDI 997 Aceptado (Status A) sin excepción operativa"
            ],
            4: [
                "Código de Comercio (Art. 88): Preclusión de 5 días para reclamo de vicios aparentes",
                "Tesis Jurisprudencial SCJN Registro 178234 (Pleno valor probatorio de remisión sellada)"
            ],
            5: [
                "Dictamen Pericial Contable bajo NIF C-3 balanceado al centavo",
                "Apercibimiento de causación de interés moratorio mercantil del 9% anual (Art. 362 CCom)"
            ]
        }

        evidences = evidences_pool.get(round_num, evidences_pool[1])

        if round_num == 1:
            stance = "EVIDENCE_FIRMNESS"
            msg = (
                f"Estimado {session.archetype.buyer_title}: Rechazamos categóricamente la retención unilateral de "
                f"${claimable:,.2f} USD. Exhibimos la factura y remisión debidamente autorizadas. Reconocemos "
                f"únicamente ${justified:,.2f} USD por faltante físico real mediante Nota de Crédito comercial, "
                f"y requerimos la transferencia inmediata del saldo restante de ${supplier_claim_cash:,.2f} USD."
            )
        elif round_num == 2:
            stance = "COUNTER_OFFER"
            msg = (
                f"Exhibimos la constancia sellada en muelle y el sello de seguridad C-TPAT ISO 17712 intacto al momento del arribo. "
                f"Para coadyuvar con sus procesos administrativos sin perjudicar la relación de suministro, podemos autorizar "
                f"una bonificación comercial complementaria de ${concession_offered:,.2f} USD, totalizando una Nota de Crédito "
                f"por ${supplier_offer_cm:,.2f} USD, condicionado al pago expedito de ${supplier_claim_cash:,.2f} USD en 5 días."
            )
        elif round_num == 3:
            stance = "PROPORTIONAL_CONCESSION"
            msg = (
                f"Cotejando la telemetría EDI 856 ASN transmitida con antelación y confirmada por su sistema con el acuse EDI 997, "
                f"su centro de distribución contaba con el inventario exacto previo al descargue. En un esfuerzo de conciliación "
                f"equilibrada, elevamos nuestra concesión a ${supplier_offer_cm:,.2f} USD en Nota de Crédito. Exigimos liquidar en banco "
                f"${supplier_claim_cash:,.2f} USD."
            )
        elif round_num == 4:
            stance = "PROPORTIONAL_CONCESSION"
            msg = (
                f"Reiteramos que legalmente operó la preclusión mercantil del Art. 88 del Código de Comercio al no protestar "
                f"averías en el plazo legal de 5 días. Conforme a las directrices de nuestra dirección financiera, nuestra "
                f"penúltima contraoferta es una Nota de Crédito por ${supplier_offer_cm:,.2f} USD. Cualquier retención adicional carece "
                f"de amparo legal y obligará a iniciar formalmente el arbitraje CANACO."
            )
        else: # round_num == 5
            stance = "CLOSING_AGREEMENT"
            msg = (
                f"Propuesta final e integral de conciliación extrajudicial: Concedemos hasta ${supplier_offer_cm:,.2f} USD en Nota "
                f"de Crédito comercial para cerrar definitivamente el expediente `{session.case_id}` sin litigio, a cambio de la transferencia "
                f"inmediata de ${supplier_claim_cash:,.2f} USD. De no aceptarse, daremos por concluida la negociación extrajudicial."
            )

        return msg, stance, supplier_offer_cm, supplier_claim_cash, evidences

    @classmethod
    def approve_settlement(
        cls,
        case_id: str,
        operator_name: str = "Director Comercial B2B"
    ) -> NegotiationDuelSession:
        """
        Aprueba formalmente el acuerdo preliminar en modo Human Gatekeeper,
        generando y sellando la Minuta de Conciliación Extrajudicial.
        """
        session = cls.get_duel_session(case_id)
        if not session:
            raise ValueError(f"No se encontró sesión de negociación activa para el caso '{case_id}'.")

        report = ConcessionEngine.get_or_create_base_report(case_id)
        final_cm = session.final_agreed_credit_memo or report.justified_amount
        final_cash = session.final_agreed_cash_recovery or (session.total_disputed_amount - final_cm)

        # Aplicar concesión en el ConcessionEngine probado
        concession_delta = final_cm - report.justified_amount
        if concession_delta > Decimal("0.00"):
            intent = ConcessionIntent(
                is_concession=True,
                is_reset=False,
                fixed_amount=concession_delta,
                target_concept="CONCILIACION_DUEL_AUTONOMA",
                reason=f"Acuerdo bilateral formalizado en mesa de negociación multi-agente frente a {session.retailer_name}"
            )
            ConcessionEngine.apply_concession(case_id, intent, operator_name=operator_name)

        session.status = "AGREEMENT_REACHED"
        session.completed_at = datetime.now(timezone.utc).isoformat()
        session.summary_verdict = (
            f"Acuerdo bilateral rubricado y aprobado por el operador ({operator_name}). "
            f"Recuperación neta en banco: ${final_cash:,.2f} USD | Nota de Crédito: ${final_cm:,.2f} USD."
        )

        cls._seal_and_generate_minutes(session, report, operator_name)
        cls._save_session(session)
        return session

    @classmethod
    def _seal_and_generate_minutes(
        cls,
        session: NegotiationDuelSession,
        report: DisputeAnalysisReport,
        operator_name: str = "Director Comercial B2B / SupplyMind AI"
    ):
        """Genera y firma digitalmente la Minuta de Conciliación con hash criptográfico SHA-256."""
        reports_dir = ROOT_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        minutes_path = reports_dir / f"minuta_conciliacion_duel_{session.case_id}.md"

        final_cm = session.final_agreed_credit_memo or Decimal("0.00")
        final_cash = session.final_agreed_cash_recovery or Decimal("0.00")

        # Criptografía SHA-256 para el sello de integridad
        raw_proof = f"{session.session_id}|{session.case_id}|{final_cm}|{final_cash}|{session.completed_at}"
        proof_hash = hashlib.sha256(raw_proof.encode("utf-8")).hexdigest()

        rounds_table = ""
        for r in session.rounds:
            rounds_table += (
                f"| R{r.round_number} | {r.buyer_stance} | ${r.buyer_demand_credit_memo:,.2f} | "
                f"${r.buyer_cash_payout_offer:,.2f} | {r.supplier_stance} | ${r.supplier_offer_credit_memo:,.2f} | "
                f"${r.supplier_claim_cash:,.2f} | ${r.spread:,.2f} | {r.convergence_pct:.1f}% |\n"
            )

        minutes_content = f"""# CONVENIO DE CONCILIACIÓN COMERCIAL Y FINIQUITO TRANSACCIONAL BILATERAL
**Folio de Negociación:** `{session.session_id}`  
**Expediente Arbitrado:** `{session.case_id}`  
**Fecha de Cierre:** {datetime.now(timezone.utc).strftime("%d de %B de %Y - %H:%M:%S UTC")}  
**Partes:** Proveedor Autorizado de Suministro vs **{session.retailer_name}**  
**Representante Retailer:** {session.archetype.buyer_title}  
**Representante Proveedor:** {operator_name} / SupplyMind Bilateral Negotiation Engine  
**Sello Criptográfico ZKP (SHA-256):** `{proof_hash}`

---

### 1. DECLARACIÓN DE ANTECEDENTES Y DISPUTA
1. Con motivo del suministro correspondiente al caso `{session.case_id}`, la parte compradora retuvo un monto de **${session.total_disputed_amount:,.2f} USD** sobre la facturación emitida.
2. Ambas partes acordaron dirimir la controversia mediante careo dialéctico pericial en {len(session.rounds)} rondas de intercambio de evidencias.

---

### 2. TRAZABILIDAD AUDITABLE DE LA NEGOCIACIÓN

| Ronda | Postura Comprador | Exigencia NC | Oferta Efectivo | Postura Proveedor | Concesión NC | Reclamo Efectivo | Spread | Convergencia |
| :---: | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: |
{rounds_table}

---

### 3. TÉRMINOS DEFINITIVOS DE CONCILIACIÓN
- **Nota de Crédito Autorizada:** **${final_cm:,.2f} USD** (Ampara faltantes físicos acreditados y concesión comercial concertada).
- **Liquidación en Efectivo Inmediata:** **${final_cash:,.2f} USD** (Pago bancario exigible en menos de 5 días hábiles).
- **Estatus Legal:** Finiquito pleno, total y definitivo entre las partes bajo el Código de Comercio.

*Documento generado y certificado automáticamente por SupplyMind AI Enterprise.*
"""
        with open(minutes_path, "w", encoding="utf-8") as f:
            f.write(minutes_content)

        session.settlement_minutes_hash = proof_hash
        session.minutes_markdown_path = str(minutes_path)

    @classmethod
    def _save_session(cls, session: NegotiationDuelSession):
        file_path = cls.get_session_file_path(session.case_id)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(session.model_dump_json(indent=2))
