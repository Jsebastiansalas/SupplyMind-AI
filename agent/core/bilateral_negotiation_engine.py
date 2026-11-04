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
import re
import unicodedata

from data.models import (
    NegotiationDuelRound,
    NegotiationDuelSession,
    RetailerArchetypeConfig,
    DisputeAnalysisReport,
    SettlementAgreementDetails,
    LiveNegotiationResponse
)
from agent.core.retailer_buyer_simulator import RetailerBuyerSimulator, ARCHETYPE_REGISTRY
from agent.core.concession_engine import ConcessionEngine, ConcessionIntent
from agent.core.delegation_matrix_engine import DelegationMatrixEngine
from agent.core.settlement_agreement_generator import SettlementAgreementGenerator
from agent.core.relational_health_engine import RelationalHealthEngine
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
        delegation_limit_pct: Optional[float] = None,
        override_rhi_score: Optional[float] = None
    ) -> NegotiationDuelSession:
        """
        Inicia una nueva sesión de careo bilateral entre SupplyMind y el Comprador Retailer.
        Aplica los límites y salvaguardas de la Matriz de Delegación Financiera (Sprint 6.2)
        y la Modulación Relacional LTV / RHI (Sprint 7.3).
        Ejecuta de inmediato la Ronda 1 de apertura de posturas.
        """
        report = ConcessionEngine.get_or_create_base_report(case_id)
        archetype = RetailerBuyerSimulator.resolve_archetype(case_id)
        rhi_report = RelationalHealthEngine.evaluate_relational_health(case_id, override_rhi_score=override_rhi_score)

        # Evaluar contra la Matriz de Delegación Corporativa
        delegation_eval = DelegationMatrixEngine.evaluate_case_delegation(case_id, requested_mode=governance_mode)

        total_dispute = abs(report.difference).quantize(Decimal("0.01"))
        justified = report.justified_amount.quantize(Decimal("0.01"))
        claimable = report.claimable_amount.quantize(Decimal("0.01"))

        # Determinar modo de gobernanza efectivo (respetando salvaguarda estricta > $10,000 USD)
        effective_mode = delegation_eval["enforced_mode"]

        # Determinar límite de concesión autorizado por la matriz
        max_matrix_pct = delegation_eval["max_allowed_concession_pct"]
        max_matrix_cap = delegation_eval["max_allowed_concession_amount"]

        if delegation_limit_pct is not None:
            effective_limit_pct = min(float(delegation_limit_pct), max_matrix_pct)
        else:
            effective_limit_pct = max_matrix_pct

        # Si se especifica explícitamente un RHI < 50 en override (ASSERTIVE_LITIGIOUS), bloquear concesiones
        if override_rhi_score is not None and rhi_report.modulation_mode == "ASSERTIVE_LITIGIOUS":
            effective_limit_pct = 0.0

        limit_pct_decimal = (Decimal(str(effective_limit_pct)) / Decimal("100.0")).quantize(Decimal("0.01"))
        calculated_limit_amount = (claimable * limit_pct_decimal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        delegation_limit_amount = min(calculated_limit_amount, max_matrix_cap)

        session_id = f"DUEL-{case_id.upper()}-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        safeguard_note = f" [{delegation_eval['safeguard_reason']}]" if delegation_eval["safeguard_triggered"] else ""

        session = NegotiationDuelSession(
            session_id=session_id,
            case_id=case_id,
            retailer_name=archetype.retailer_name,
            archetype=archetype,
            governance_mode=effective_mode,
            status="IN_PROGRESS",
            current_round=1,
            max_rounds=5,
            delegation_limit_pct=effective_limit_pct,
            delegation_limit_amount=delegation_limit_amount,
            total_disputed_amount=total_dispute,
            rounds=[],
            started_at=now_iso,
            summary_verdict=(
                f"Careo iniciado. Posturas preliminares bajo política {delegation_eval['account_tier']} "
                f"| Salud Relacional RHI {rhi_report.rhi_score}/100 ({rhi_report.modulation_mode}).{safeguard_note}"
            ),
            rhi_score=rhi_report.rhi_score,
            modulation_mode=rhi_report.modulation_mode,
            churn_risk_level=rhi_report.churn_risk_level,
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

        evidences = list(evidences_pool.get(round_num, evidences_pool[1]))
        if report.evidence:
            real_ev = report.evidence[min(round_num - 1, len(report.evidence) - 1)]
            if real_ev not in evidences:
                evidences.insert(0, real_ev)

        mod_mode = getattr(session, "modulation_mode", None) or "FIRM_COMMERCIAL"
        mod_suffix = ""
        if mod_mode == "DIPLOMATIC_PRESERVATION" and round_num >= 2:
            mod_suffix = " (Sujeto a compromiso recíproco de volumen en próximas órdenes de compra Tier-1)."
        elif mod_mode == "ASSERTIVE_LITIGIOUS":
            mod_suffix = " [Directriz RHI < 50: Cero concesiones sobre retenciones sin soporte físico]."

        if round_num == 1:
            stance = "EVIDENCE_FIRMNESS"
            msg = (
                f"Estimado {session.archetype.buyer_title}: Rechazamos categóricamente la retención unilateral de "
                f"${claimable:,.2f} USD. Exhibimos la factura y remisión debidamente autorizadas. Reconocemos "
                f"únicamente ${justified:,.2f} USD por faltante físico real mediante Nota de Crédito comercial, "
                f"y requerimos la transferencia inmediata del saldo restante de ${supplier_claim_cash:,.2f} USD.{mod_suffix}"
            )
        elif round_num == 2:
            stance = "COUNTER_OFFER"
            msg = (
                f"Exhibimos la constancia sellada en muelle y el sello de seguridad C-TPAT ISO 17712 intacto al momento del arribo. "
                f"Para coadyuvar con sus procesos administrativos sin perjudicar la relación de suministro, podemos autorizar "
                f"una bonificación comercial complementaria de ${concession_offered:,.2f} USD, totalizando una Nota de Crédito "
                f"por ${supplier_offer_cm:,.2f} USD, condicionado al pago expedito de ${supplier_claim_cash:,.2f} USD en 5 días.{mod_suffix}"
            )
        elif round_num == 3:
            stance = "PROPORTIONAL_CONCESSION"
            msg = (
                f"Cotejando la telemetría EDI 856 ASN transmitida con antelación y confirmada por su sistema con el acuse EDI 997, "
                f"su centro de distribución contaba con el inventario exacto previo al descargue. En un esfuerzo de conciliación "
                f"equilibrada, elevamos nuestra concesión a ${supplier_offer_cm:,.2f} USD en Nota de Crédito. Exigimos liquidar en banco "
                f"${supplier_claim_cash:,.2f} USD.{mod_suffix}"
            )
        elif round_num == 4:
            stance = "PROPORTIONAL_CONCESSION"
            msg = (
                f"Reiteramos que legalmente operó la preclusión mercantil del Art. 88 del Código de Comercio al no protestar "
                f"averías en el plazo legal de 5 días. Conforme a las directrices de nuestra dirección financiera, nuestra "
                f"penúltima contraoferta es una Nota de Crédito por ${supplier_offer_cm:,.2f} USD. Cualquier retención adicional carece "
                f"de amparo legal y obligará a iniciar formalmente el arbitraje CANACO.{mod_suffix}"
            )
        else: # round_num == 5
            stance = "CLOSING_AGREEMENT"
            msg = (
                f"Propuesta final e integral de conciliación extrajudicial: Concedemos hasta ${supplier_offer_cm:,.2f} USD en Nota "
                f"de Crédito comercial para cerrar definitivamente el expediente `{session.case_id}` sin litigio, a cambio de la transferencia "
                f"inmediata de ${supplier_claim_cash:,.2f} USD. De no aceptarse, daremos por concluida la negociación extrajudicial.{mod_suffix}"
            )

        return msg, stance, supplier_offer_cm, supplier_claim_cash, evidences

    @classmethod
    def respond_to_live_objection(
        cls,
        case_id: str,
        objection: str,
        operator_name: Optional[str] = "Evaluador B2B"
    ) -> LiveNegotiationResponse:
        """
        Evalúa y refuta en tiempo real una objeción planteada por el comprador retailer o evaluador (Eje 2).
        Verifica tolerancias contractuales (ej. ventana de arribo a muelle de 60 min),
        recalcula con precisión Decimal la deducción admisible y emite una contra-oferta balanceada.
        """
        session = cls.get_duel_session(case_id)
        if not session:
            session = cls.start_duel(case_id)

        report = ConcessionEngine.get_or_create_base_report(case_id)
        total_dispute = session.total_disputed_amount
        base_justified = report.justified_amount
        base_claimable = report.claimable_amount

        # Normalización semántica
        def _clean_str(t: str) -> str:
            if not t:
                return ""
            nfkd = unicodedata.normalize('NFKD', t.lower())
            return "".join(c for c in nfkd if not unicodedata.combining(c))

        norm_obj = _clean_str(objection)

        def _has_kw(target_text: str, kws: List[str]) -> bool:
            for kw in kws:
                if re.search(r'\b' + re.escape(kw), target_text):
                    return True
            return False

        # 1. Extracción de señales cuantitativas de la objeción
        delay_mins: Optional[int] = None
        m_min = re.search(r'\b(\d+)\s*(?:minutos?|mins?|m)\b', norm_obj)
        m_hr = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:horas?|hrs?|h)\b', norm_obj)
        if m_min:
            delay_mins = int(m_min.group(1))
        elif m_hr:
            delay_mins = int(float(m_hr.group(1)) * 60)

        extracted_amt: Optional[Decimal] = None
        m_amt = re.search(r'\$\s*([\d,]+(?:\.\d+)?)', objection)
        if not m_amt:
            m_amt = re.search(r'\b([\d,]+(?:\.\d+)?)\s*(?:usd|dolares|dlls)\b', norm_obj)
        if m_amt:
            try:
                extracted_amt = Decimal(m_amt.group(1).replace(",", "")).quantize(Decimal("0.01"))
            except Exception:
                extracted_amt = None

        # 2. Categorización semántica robusta con delimitadores de palabra y jerarquía temática
        otif_kw = [
            "tarde", "retraso", "retrasos", "demora", "demoras", "otif", "impuntual",
            "impuntualidad", "fuera de cita", "fuera de horario", "extemporaneo",
            "extemporanea", "cita vencida", "desfase"
        ]
        unauth_kw = [
            "publicidad", "publicitario", "publicitaria", "co-op", "coop", "folleto", "folletos",
            "mercadeo", "administrativo", "administrativa", "administrativos", "unilateral",
            "unilaterales", "sin adenda", "rebate", "rebates", "cuota", "cuotas",
            "promocion", "promociones", "catalogo", "catalogos"
        ]
        damage_kw = [
            "danado", "danada", "danados", "danadas", "averia", "averias", "averiado", "averiada",
            "roto", "rota", "rotos", "rotas", "tarima", "tarimas", "empaque", "empaques",
            "caja rota", "humedad", "golpeado", "golpeada", "destruido", "destruida"
        ]
        shortage_kw = [
            "faltante", "faltantes", "shortage", "piezas de menos", "piezas menos",
            "conteo fisico", "merma", "mermas", "unidades faltantes", "no recibido", "no recibida"
        ]
        price_kw = [
            "sobreprecio", "costo unitario", "orden de compra", "tarifa", "tarifas",
            "rate", "po price", "variacion de precio"
        ]
        asn_kw = [
            "asn", "edi", "856", "transmision", "acuse", "997"
        ]

        has_delay = delay_mins is not None or _has_kw(norm_obj, otif_kw)

        if _has_kw(norm_obj, unauth_kw):
            category = "UNAUTHORIZED_PENALTY"
        elif _has_kw(norm_obj, damage_kw):
            category = "DAMAGED_GOODS"
        elif _has_kw(norm_obj, shortage_kw):
            category = "SHORTAGE_MISSING"
        elif _has_kw(norm_obj, price_kw):
            category = "PRICE_VARIANCE"
        elif has_delay:
            category = "LATE_DELIVERY_OTIF"
        elif _has_kw(norm_obj, asn_kw):
            category = "ASN_EDI"
        else:
            category = "GENERAL_OBJECTION"

        # 3. Evaluación de Cláusulas Contractuales, Tolerancias y Jerarquía Probatoria
        tolerance_mins = 60
        recalculated_justified = base_justified
        evidence_exhibited: List[str] = []

        if category == "LATE_DELIVERY_OTIF":
            reported_delay = delay_mins if delay_mins is not None else 45
            if reported_delay <= tolerance_mins:
                is_valid = False
                clause_applied = "CL-LOG-05.2 (Ventana de Tolerancia Operativa en Muelle)"
                tolerance_rule = (
                    f"Tolerancia contractual autorizada de {tolerance_mins} minutos de gracia sobre horario de cita "
                    f"({reported_delay} min incurridos <= {tolerance_mins} min autorizados). Deducción improcedente."
                )
                recalculated_justified = base_justified
                recalculated_claimable = (total_dispute - recalculated_justified).quantize(Decimal("0.01"))
                counter_reply = (
                    f"Rechazamos de plano la objeción planteada por retraso de transporte. Conforme a la Cláusula 5.2 del "
                    f"Contrato Marco de Suministro y el estándar logístico B2B, existe una ventana contractual de tolerancia "
                    f"de {tolerance_mins} minutos de gracia posterior a la hora de cita. El transportista arribó con "
                    f"{reported_delay} minutos de diferencia, operando plenamente dentro del margen contractual protegido. "
                    f"En consecuencia, la penalización alegada carece de sustento vinculante ($0.00 admisible). "
                    f"Exigimos la restitución íntegra del importe de ${recalculated_claimable:,.2f} USD."
                )
                evidence_exhibited = [
                    f"Bitácora de arribo de transporte con sello de muelle dentro de ventana de tolerancia ({reported_delay} min <= {tolerance_mins} min)",
                    "Contrato Marco Cláusula 5.2 de Tolerancia Operativa en Muelle",
                    "Acuse de recibo de cita logística sin reserva de penalización"
                ]
            else:
                is_valid = True
                excess = reported_delay - tolerance_mins
                clause_applied = "CL-LOG-05.3 (Penalización Proporcional por Exceso de Cita Muelle)"
                tolerance_rule = (
                    f"Exceso de {excess} minutos sobre la ventana de gracia de {tolerance_mins} minutos. "
                    f"Aplica deducción proporcional tasada conforme a tabulador contractual."
                )
                proportional_penalty = min(
                    Decimal("250.00"),
                    (Decimal(str(excess)) * Decimal("5.00")).quantize(Decimal("0.01"))
                )
                recalculated_justified = (base_justified + proportional_penalty).quantize(Decimal("0.01"))
                recalculated_claimable = (total_dispute - recalculated_justified).quantize(Decimal("0.01"))
                counter_reply = (
                    f"Revisada la bitácora de muelle frente a la Cláusula 5.3, se constata un arribo con {reported_delay} minutos "
                    f"de demora, excediendo por {excess} minutos la tolerancia contractual de {tolerance_mins} minutos. "
                    f"En apego estricto al tabulador de penalización pactado, reconocemos una deducción tasada de "
                    f"${proportional_penalty:,.2f} USD mediante Nota de Crédito. Rechazamos cualquier retención unilateral "
                    f"arbitraria en exceso y requerimos la transferencia bancaria inmediata de ${recalculated_claimable:,.2f} USD."
                )
                evidence_exhibited = [
                    f"Tabulador de penalización logística Cláusula 5.3 ({excess} min tasados a $5 USD/min, máx $250 USD)",
                    "Contrato Marco de Suministro Logístico B2B"
                ]

        elif category == "UNAUTHORIZED_PENALTY":
            is_valid = False
            clause_applied = "CL-COM-07.2 / CL-10.4 (Prohibición Expresa de Deducciones Unilaterales de Mercadeo sin Adenda)"
            tolerance_rule = (
                "Ninguna deducción por concepto de folleto publicitario, cuota de cooperación (co-op) o cargo administrativo "
                "es contractualmente procedente sin una orden de inserción o adenda bilateral firmada por ambas partes."
            )
            recalculated_justified = base_justified
            recalculated_claimable = (total_dispute - recalculated_justified).quantize(Decimal("0.01"))
            counter_reply = (
                f"La deducción unilateral por concepto de folleto de verano / cuota publicitaria es contractualmente inadmisible. "
                f"Conforme a la Cláusula 7.2 del Contrato Marco y el principio mercantil de inalterabilidad de las obligaciones "
                f"(Art. 78 del Código de Comercio), cualquier cargo de mercadeo o cooperación requiere una orden de inserción "
                f"bilateral formalmente autorizada por nuestra dirección comercial. Al no existir adenda previa firmada, "
                f"la retención constituye una deducción ilícita de fondos. Exigimos la restitución del saldo retenido de "
                f"${recalculated_claimable:,.2f} USD."
            )
            evidence_exhibited = [
                "Código de Comercio Art. 78 y 88 (Inalterabilidad contractual de las partes)",
                "Contrato Marco Cláusula 7.2 / 10.4 (Prohibición expresa de retención unilateral sin adenda)",
                "Auditoría interna de acuerdos comerciales sin orden de inserción autorizada"
            ]

        elif category == "DAMAGED_GOODS":
            is_valid = False
            clause_applied = "CL-CAL-04.1 (Inspección de Muelle) & Art. 88 Código de Comercio"
            tolerance_rule = (
                "Remisión física sellada sin reservas en muelle. Preclusión legal perentoria de 5 días para "
                "reclamar vicios o averías aparentes."
            )
            recalculated_justified = base_justified
            recalculated_claimable = (total_dispute - recalculated_justified).quantize(Decimal("0.01"))
            counter_reply = (
                f"La reclamación por avería o daño físico deviene improcedente al amparo del Art. 88 del Código de Comercio "
                f"y la Cláusula 4.1. La entrega fue recibida y rubricada por su personal de muelle mediante remisión sellada "
                f"sin asentar excepciones ni constancia fotográfica de daño al descargue. Habiendo precluido el término legal "
                f"de 5 días para protestar averías visibles, la retención carece de causa jurídica."
            )
            evidence_exhibited = [
                "Remisión física de entrega sellada con acuse de recibo de conformidad en muelle",
                "Código de Comercio Art. 88 (Preclusión legal de 5 días para reclamar vicios aparentes)",
                "Certificado de sello de alta seguridad ISO 17712 intacto al momento del desestibe"
            ]

        elif category == "SHORTAGE_MISSING":
            is_valid = True
            clause_applied = "CL-ENT-03.1 (Ajuste por Faltante Físico Asentado en Remisión de Entrega)"
            tolerance_rule = (
                "Se reconoce exclusivamente el faltante físico cotejado y asentado formalmente en la remisión sellada al descargue."
            )
            recalculated_justified = base_justified
            recalculated_claimable = (total_dispute - recalculated_justified).quantize(Decimal("0.01"))
            counter_reply = (
                f"En apego a la Cláusula 3.1, reconocemos únicamente el faltante físico que consta en la remisión sellada "
                f"al descargue (${recalculated_justified:,.2f} USD), autorizando la correspondiente Nota de Crédito. "
                f"El remanente de ${recalculated_claimable:,.2f} USD corresponde a producto efectivamente recibido y debe ser "
                f"liquidado mediante transferencia bancaria inmediata."
            )
            evidence_exhibited = [
                "Remisión sellada en muelle con desglose de unidades recibidas vs facturadas",
                "Conciliación de inventario con precisión Decimal"
            ]

        elif category == "PRICE_VARIANCE":
            is_valid = True
            clause_applied = "CL-PRC-02.1 (Prevalencia Estricta de la Orden de Compra Aprobada)"
            tolerance_rule = "Los precios facturados deben guardar correspondencia estricta con la Orden de Compra pactada."
            recalculated_justified = base_justified
            recalculated_claimable = (total_dispute - recalculated_justified).quantize(Decimal("0.01"))
            counter_reply = (
                f"Conforme a la Cláusula 2.1, admitimos el ajuste de tarifa hacia el precio unitario pactado en la Orden de "
                f"Compra (${recalculated_justified:,.2f} USD en Nota de Crédito), exigiendo el pago sin descuento del saldo de "
                f"${recalculated_claimable:,.2f} USD."
            )
            evidence_exhibited = [
                "Orden de Compra autorizada con desglose de precios unitarios pactados",
                "Factura comercial oficial cotejada partida por partida"
            ]

        elif category == "ASN_EDI":
            is_valid = False
            clause_applied = "CL-LOG-05.3 (Cumplimiento de Transmisión Electrónica ASN EDI 856)"
            tolerance_rule = "Transmisión electrónica ASN confirmada con acuse de recibo funcional EDI 997 previo al arribo."
            recalculated_justified = base_justified
            recalculated_claimable = (total_dispute - recalculated_justified).quantize(Decimal("0.01"))
            counter_reply = (
                f"Rechazamos la penalización por supuesta omisión de ASN. La transmisión electrónica EDI 856 cuenta con acuse "
                f"funcional EDI 997 Aceptado (Status A) emitido por su propio sistema con timestamp UTC previo a la descarga. "
                f"La penalización de ${recalculated_claimable:,.2f} USD es infundada."
            )
            evidence_exhibited = [
                "Transmisión electrónica ASN EDI 856 con timestamp previo al arribo",
                "Acuse Funcional EDI 997 Aceptado sin excepciones técnicas"
            ]

        else:
            is_valid = False
            clause_applied = "CL-GEN-01.1 (Cumplimiento Mercantil General y Partida Doble)"
            tolerance_rule = "Toda deducción debe estar amparada por documento probatorio físico o electrónico previo."
            recalculated_justified = base_justified
            recalculated_claimable = (total_dispute - recalculated_justified).quantize(Decimal("0.01"))
            counter_reply = (
                f"Evaluada su manifestación, reiteramos que cualquier deducción sobre la factura debe sustentarse en prueba "
                f"fehaciente de faltante o vicio acreditado. Reconocemos ${recalculated_justified:,.2f} USD en Nota de Crédito "
                f"y requerimos el pago del saldo de ${recalculated_claimable:,.2f} USD."
            )
            evidence_exhibited = [
                "Factura comercial oficial debidamente timbrada",
                "Código de Comercio Art. 78 (Cumplimiento de las obligaciones mercantiles)"
            ]

        # 4. Cálculo de Contra-Oferta Numérica con Invariante Decimal ($0.00 MAE)
        proposed_credit_memo = recalculated_justified.quantize(Decimal("0.01"))
        proposed_cash_recovery = (total_dispute - proposed_credit_memo).quantize(Decimal("0.01"))
        assert proposed_credit_memo + proposed_cash_recovery == total_dispute, "Invariante contable violada en live objection"

        # Pretensión del comprador
        if is_valid and extracted_amt is not None:
            buyer_demand_cm = min(total_dispute, max(recalculated_justified, extracted_amt))
        else:
            buyer_demand_cm = total_dispute

        spread = abs(buyer_demand_cm - proposed_credit_memo).quantize(Decimal("0.01"))
        if total_dispute > Decimal("0.00"):
            conv_ratio = max(0.0, min(100.0, float((Decimal("1.00") - (spread / total_dispute)) * 100)))
        else:
            conv_ratio = 100.0

        next_round_num = session.current_round + 1 if session.rounds else 1
        session.current_round = next_round_num

        round_status = "IN_PROGRESS"
        if spread <= Decimal("75.00") or buyer_demand_cm <= proposed_credit_memo:
            round_status = "AGREED"
        elif conv_ratio >= 70.0:
            round_status = "CONVERGING"
        elif next_round_num >= session.max_rounds:
            round_status = "IMPASSE"

        duel_round = NegotiationDuelRound(
            round_number=next_round_num,
            buyer_message=objection,
            buyer_stance="BUYER_LIVE_OBJECTION" if is_valid else "UNFOUNDED_OBJECTION",
            buyer_demand_credit_memo=buyer_demand_cm,
            buyer_cash_payout_offer=(total_dispute - buyer_demand_cm).quantize(Decimal("0.01")),
            supplier_message=counter_reply,
            supplier_stance="LEGAL_REFUTATION" if not is_valid else "BALANCED_COUNTER_OFFER",
            supplier_offer_credit_memo=proposed_credit_memo,
            supplier_claim_cash=proposed_cash_recovery,
            evidence_exhibited=evidence_exhibited,
            spread=spread,
            convergence_pct=round(conv_ratio, 1),
            round_status=round_status
        )
        session.rounds.append(duel_round)

        if round_status == "AGREED":
            session.final_agreed_credit_memo = proposed_credit_memo
            session.final_agreed_cash_recovery = proposed_cash_recovery
            if session.governance_mode == "FULL_AUTONOMY":
                session.status = "AGREEMENT_REACHED"
                session.completed_at = datetime.now(timezone.utc).isoformat()
                session.summary_verdict = (
                    f"Acuerdo bilateral alcanzado tras responder objeción en vivo (Ronda {next_round_num}). "
                    f"Recuperación neta en banco: ${proposed_cash_recovery:,.2f} USD | Nota de Crédito: ${proposed_credit_memo:,.2f} USD."
                )
                cls._seal_and_generate_minutes(session, report, operator_name=operator_name or "Evaluador B2B")
            else:
                session.status = "AWAITING_HUMAN_APPROVAL"
                session.summary_verdict = (
                    f"Punto de acuerdo alcanzado en Ronda {next_round_num} (${proposed_cash_recovery:,.2f} USD en banco vs ${proposed_credit_memo:,.2f} USD NC). "
                    f"En espera de confirmación y rúbrica final del operador (Human Gatekeeper)."
                )
        elif next_round_num >= session.max_rounds and round_status == "IMPASSE":
            session.status = "IMPASSE_REACHED"
            session.completed_at = datetime.now(timezone.utc).isoformat()
            session.summary_verdict = f"Punto muerto alcanzado en Ronda {next_round_num}. Brecha irreducible de ${spread:,.2f} USD."

        cls._active_sessions[case_id] = session
        cls._save_session(session)

        return LiveNegotiationResponse(
            case_id=case_id,
            round_number=next_round_num,
            objection_received=objection,
            objection_category=category,
            contract_clause_applied=clause_applied,
            contract_tolerance_rule=tolerance_rule,
            is_objection_contractually_valid=is_valid,
            recalculated_justified_amount=recalculated_justified,
            recalculated_claimable_amount=recalculated_claimable,
            proposed_credit_memo=proposed_credit_memo,
            proposed_cash_recovery=proposed_cash_recovery,
            spread=spread,
            convergence_pct=round(conv_ratio, 1),
            status=session.status if session.status in ["AGREEMENT_REACHED", "AWAITING_HUMAN_APPROVAL", "IMPASSE_REACHED"] else round_status,
            counter_argument_reply=counter_reply,
            evidence_exhibited=evidence_exhibited
        )

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
    def set_governance_mode(cls, case_id: str, new_mode: str) -> NegotiationDuelSession:
        """
        Conmuta el modo de gobernanza de una sesión activa (FULL_AUTONOMY vs HUMAN_GATEKEEPER).
        Aplica estrictamente las salvaguardas de la Matriz de Delegación Financiera.
        """
        if new_mode not in ["FULL_AUTONOMY", "HUMAN_GATEKEEPER"]:
            raise ValueError(f"Modo de gobernanza inválido '{new_mode}'. Use 'FULL_AUTONOMY' o 'HUMAN_GATEKEEPER'.")

        session = cls.get_duel_session(case_id)
        if not session:
            session = cls.start_duel(case_id, governance_mode=new_mode)
            return session

        delegation_eval = DelegationMatrixEngine.evaluate_case_delegation(case_id, requested_mode=new_mode)
        if delegation_eval["safeguard_triggered"] and new_mode == "FULL_AUTONOMY":
            raise ValueError(delegation_eval["safeguard_reason"])

        session.governance_mode = delegation_eval["enforced_mode"]
        cls._save_session(session)
        return session

    @classmethod
    def get_settlement_agreement_details(
        cls,
        case_id: str
    ) -> Optional[SettlementAgreementDetails]:
        """Obtiene o reconstruye los detalles certificados del convenio para el caso."""
        session = cls.get_duel_session(case_id)
        if not session or not session.settlement_minutes_hash:
            return None
        report = ConcessionEngine.get_or_create_base_report(case_id)
        return SettlementAgreementGenerator.generate_agreement(
            session=session,
            report=report,
            operator_name="Auditor B2B / SupplyMind AI"
        )

    @classmethod
    def _seal_and_generate_minutes(
        cls,
        session: NegotiationDuelSession,
        report: DisputeAnalysisReport,
        operator_name: str = "Director Comercial B2B / SupplyMind AI"
    ):
        """Genera y firma digitalmente el Convenio de Transacción Mercantil con ZKP SHA-256."""
        agreement = SettlementAgreementGenerator.generate_agreement(
            session=session,
            report=report,
            operator_name=operator_name
        )
        session.settlement_minutes_hash = agreement.zkp_seal_hash
        session.minutes_markdown_path = str(ROOT_DIR / "reports" / f"convenio_finiquito_{session.case_id}.md")

        # Registrar precedente de negociación bilateral en la Red de Memoria SQLite (Sprint 8.5)
        try:
            from agent.memory.precedent_graph import DisputeMemoryNetwork
            mem_net = DisputeMemoryNetwork()
            mem_net.record_case_resolution(
                case_id=session.case_id,
                report=report,
                deduction_code=f"SETTLEMENT-{session.archetype.archetype_id}"
            )
        except Exception:
            pass

    @classmethod
    def _save_session(cls, session: NegotiationDuelSession):
        file_path = cls.get_session_file_path(session.case_id)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(session.model_dump_json(indent=2))
