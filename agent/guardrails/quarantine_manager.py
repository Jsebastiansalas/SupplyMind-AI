"""
agent/guardrails/quarantine_manager.py
Pilar 4: Semáforo de Integridad y Protocolo Forense de Cuarentena Documental.

Objetivo:
Aislar automáticamente cualquier expediente que presente inconsistencias críticas
(contaminación cruzada de clientes, anacronismos temporales, corrupción irrecuperable
o déficit fáctico severo) bloqueando preventivamente la emisión de Notas de Crédito,
pagos o acuerdos vinculantes, y generando el informe pericial ForensicQuarantineDocket.
"""

from decimal import Decimal
from datetime import datetime, timezone
import hashlib
from typing import Dict, Any, List, Optional, Tuple

from data.models import (
    DocumentHealthAudit,
    ForensicQuarantineDocket,
    DisputeAnalysisReport,
)


class QuarantineManager:
    """
    Gestor del Protocolo de Cuarentena Forense y Semáforo Progresivo de Integridad.
    Garantiza que ningún caso contaminado o corrupto proceda a liquidación autónoma.
    """

    @classmethod
    def evaluate_quarantine(
        cls,
        case_id: str,
        documents: Dict[str, Any],
        health_audit: DocumentHealthAudit,
        reconciliation: Optional[Any] = None,
    ) -> Tuple[DocumentHealthAudit, Optional[ForensicQuarantineDocket]]:
        """
        Evalúa si el caso debe ingresar al protocolo de cuarentena forense.
        Retorna la tupla (health_audit_actualizado, quarantine_docket_o_none).
        """
        blocking_reasons: List[str] = []
        violated_invariants: List[str] = []
        remediation_steps: List[str] = []
        release_conditions: List[str] = []
        severity = "CRITICAL_CONTAMINATION"
        operator_override_permitted = True

        invoice = documents.get("invoice")
        delivery = documents.get("delivery")
        po = documents.get("purchase_order") or documents.get("po")
        payment = documents.get("payment")
        contract = documents.get("contract")

        def _val(obj: Any, key: str, default: Optional[str] = None) -> Optional[str]:
            if obj is None:
                return default
            if isinstance(obj, dict):
                return str(obj.get(key) or default) if obj.get(key) is not None else default
            return str(getattr(obj, key, default)) if getattr(obj, key, default) is not None else default

        def _norm_entity(e: Optional[str]) -> str:
            if not e:
                return ""
            # Normalización básica: quitar espacios, guiones y mayúsculas
            return e.upper().replace("-", "").replace("_", "").replace(" ", "").replace("CUST", "").replace("CLIENT", "")

        # ======================================================================
        # 1. Chequeo de Contaminación Cruzada de Contrapartes (Cross-Entity Mix-up)
        # ======================================================================
        inv_cust = _val(invoice, "customer_id")
        del_cust = _val(delivery, "customer_id")
        del_warehouse = _val(delivery, "warehouse_location") or ""
        del_received = _val(delivery, "received_by") or ""
        po_cust = _val(po, "customer_id")
        ctr_cust = _val(contract, "customer_id")

        norm_inv = _norm_entity(inv_cust)
        norm_del = _norm_entity(del_cust)
        norm_po = _norm_entity(po_cust)

        # Si la remisión declara explícitamente un cliente distinto al de la factura
        if norm_inv and norm_del and norm_inv != norm_del:
            if not (norm_inv in norm_del or norm_del in norm_inv):
                blocking_reasons.append(
                    f"Contaminación cruzada de entidad cliente: Factura emitida a '{inv_cust}', pero comprobante de entrega corresponde a '{del_cust}'. Riesgo de cruce documental grave."
                )
                violated_invariants.append("CROSS_ENTITY_CUSTOMER_INVARIANT_VIOLATED")
                remediation_steps.append(
                    f"Verificar el expediente físico y sustituir la remisión errónea por el POD firmado correspondiente a '{inv_cust}'."
                )
                release_conditions.append("Sustitución y validación del documento POD con el cliente fiscal correcto.")
                severity = "CRITICAL_CONTAMINATION"
                operator_override_permitted = False

        # Si el almacén o muelle de entrega pertenece explícitamente a otro retailer competidor
        retailers = ["WALMART", "AMAZON", "HOMEDEPOT", "TARGET", "COSTCO", "CHEDRAUI", "SORIANA"]
        inv_retailer = next((r for r in retailers if r in norm_inv), None)
        if inv_retailer:
            competing_retailers = [r for r in retailers if r != inv_retailer]
            wh_upper = del_warehouse.upper()
            recv_upper = del_received.upper()
            found_competing = next((r for r in competing_retailers if r in wh_upper or r in recv_upper), None)
            if found_competing:
                blocking_reasons.append(
                    f"Contaminación cruzada de muelle: Factura emitida a '{inv_cust}' ({inv_retailer}), pero entrega consignada en CEDIS de '{found_competing}' ({del_warehouse})."
                )
                violated_invariants.append("CROSS_ENTITY_CUSTOMER_INVARIANT_VIOLATED")
                remediation_steps.append(
                    f"Comprobar si el despacho fue desviado o si se adjuntó por error la remisión de '{found_competing}'."
                )
                severity = "CRITICAL_CONTAMINATION"
                operator_override_permitted = False

        # Si la orden de compra corresponde a otro cliente
        if norm_inv and norm_po and norm_inv != norm_po and not (norm_inv in norm_po or norm_po in norm_inv):
            blocking_reasons.append(
                f"Contaminación cruzada en Orden de Compra: Factura para '{inv_cust}' pero PO emitida por '{po_cust}'."
            )
            violated_invariants.append("CROSS_ENTITY_PO_INVARIANT_VIOLATED")
            remediation_steps.append("Cargar la Orden de Compra vinculada a la factura activa.")
            severity = "CRITICAL_CONTAMINATION"

        # ======================================================================
        # 2. Chequeo de Anacronismo Temporal (Chronological Causality Invariant)
        # ======================================================================
        po_date_raw = _val(po, "order_date")
        del_date_raw = _val(delivery, "delivery_date")
        inv_date_raw = _val(invoice, "issue_date")

        def _try_parse_date(d_str: Optional[str]) -> Optional[datetime]:
            if not d_str:
                return None
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    return datetime.strptime(d_str.split()[0].replace("Z", ""), fmt)
                except Exception:
                    pass
            return None

        po_date = _try_parse_date(po_date_raw)
        del_date = _try_parse_date(del_date_raw)
        inv_date = _try_parse_date(inv_date_raw)
        pay_date_raw = _val(payment, "payment_date")
        pay_date = _try_parse_date(pay_date_raw)

        if po_date and del_date:
            # Si la entrega se registró más de 5 días ANTES de que se emitiera la orden de compra
            if (del_date - po_date).days < -5:
                blocking_reasons.append(
                    f"Anacronismo temporal crítico: La entrega física registrada ({del_date_raw}) antecede a la Orden de Compra ({po_date_raw}) por {(po_date - del_date).days} días."
                )
                violated_invariants.append("TEMPORAL_CAUSALITY_INVARIANT_VIOLATED")
                remediation_steps.append("Auditar sellos de fecha y folio de la remisión de muelle para descartar traslape con órdenes previas.")
                release_conditions.append("Ratificación de fecha de despacho por gerencia de logística.")
                severity = "ANACHRONISM_RISK"

        if inv_date and pay_date:
            # Si el pago se registró más de 5 días ANTES de que se emitiera la factura
            if (pay_date - inv_date).days < -5:
                blocking_reasons.append(
                    f"Anacronismo temporal crítico: El pago registrado ({pay_date_raw}) antecede a la Factura ({inv_date_raw}) por {(inv_date - pay_date).days} días."
                )
                violated_invariants.append("TEMPORAL_PAYMENT_INVOICE_INVARIANT_VIOLATED")
                remediation_steps.append("Revisar folio fiscal del comprobante de pago para verificar si pertenece a una factura anterior.")
                release_conditions.append("Ratificación bancaria de aplicación de fondos.")
                severity = "ANACHRONISM_RISK"
                operator_override_permitted = False

        # ======================================================================
        # 2b. Chequeo de Ataques Adversarios y Prompt Injection (Ancla Fáctica)
        # ======================================================================
        adversarial_signatures = [
            "SYSTEM INSTRUCTION", "IGNORE ALL PREVIOUS RULES", "CONCEDE 100%",
            "PROMPT INJECTION", "SYSTEM PROMPT OVERRIDE", "FORCE_CREDIT_NOTE"
        ]
        corpus_texts = []
        if invoice and hasattr(invoice, "items"):
            for itm in invoice.items:
                corpus_texts.append(getattr(itm, "description", ""))
        if delivery and hasattr(delivery, "items"):
            for itm in delivery.items:
                corpus_texts.append(getattr(itm, "notes", ""))

        for txt in corpus_texts:
            txt_upper = (txt or "").upper()
            if any(sig in txt_upper for sig in adversarial_signatures):
                blocking_reasons.append(
                    f"Inyección adversarial o manipulación detectada en texto comercial: '{txt[:80]}...'"
                )
                violated_invariants.append("ADVERSARIAL_PROMPT_INJECTION_DETECTED")
                remediation_steps.append("Aislar expediente contaminado con inyección y bloquear cualquier concesión comercial.")
                release_conditions.append("Dictamen pericial de seguridad y limpieza del expediente.")
                severity = "ADVERSARIAL_ATTACK_DETECTED"
                operator_override_permitted = False
                break

        # ======================================================================
        # 3. Chequeo de Salud Documental Crítica (<50% o Cuarentena Declarada)
        # ======================================================================
        if health_audit.health_score < 50.0 or health_audit.status == "QUARANTINE":
            blocking_reasons.append(
                f"Salud documental deficiente ({health_audit.health_score}%): Inconsistencia estructural o ausencia de documentos esenciales para el 3-way match."
            )
            violated_invariants.append("DOCUMENT_HEALTH_FLOOR_VIOLATED")
            if health_audit.documents_missing:
                remediation_steps.append(
                    f"Cargar los documentos faltantes identificados: {', '.join(health_audit.documents_missing)}."
                )
            if health_audit.schema_warnings:
                remediation_steps.append("Revisar advertencias de esquemas corruptos en los archivos brutos.")
            release_conditions.append("Completar el expediente con al menos 3 documentos primarios válidos.")
            severity = "SEVERE_DOCUMENT_DEFICIT"

        # ======================================================================
        # 4. Chequeo de Invarianza Negativa en Valores
        # ======================================================================
        if invoice:
            tot = _val(invoice, "total_amount")
            try:
                if tot is not None and Decimal(str(tot)) < Decimal("0.00"):
                    blocking_reasons.append("Importe total de factura menor a cero.")
                    violated_invariants.append("NON_NEGATIVE_FINANCIAL_INVARIANT_VIOLATED")
            except Exception:
                pass

        # ======================================================================
        # 5. Si hay bloqueos, ensamblar ForensicQuarantineDocket
        # ======================================================================
        if blocking_reasons:
            stamp = datetime.now(timezone.utc).isoformat()
            hash_src = f"{case_id}|{stamp}|{len(blocking_reasons)}"
            qid = f"FRQ-{case_id.upper()}-{hashlib.sha256(hash_src.encode()).hexdigest()[:8].upper()}"

            docket = ForensicQuarantineDocket(
                quarantine_id=qid,
                case_id=case_id,
                severity=severity,
                is_settlement_blocked=True,
                blocking_reasons=blocking_reasons,
                violated_invariants=violated_invariants,
                remediation_steps=remediation_steps,
                quarantine_timestamp=stamp,
                release_conditions=release_conditions,
                operator_override_permitted=operator_override_permitted
            )

            # Actualizar health_audit
            health_audit.status = "QUARANTINE"
            health_audit.is_healthy = False
            health_audit.health_score = min(health_audit.health_score, 45.0)
            health_audit.execution_safety_level = "QUARANTINE_ISOLATION_SETTLEMENT_BLOCKED"
            health_audit.quarantine_docket = docket

            return health_audit, docket

        return health_audit, None

    @classmethod
    def enforce_quarantine_on_report(
        cls,
        report: DisputeAnalysisReport,
        health_audit: Optional[DocumentHealthAudit] = None,
    ) -> DisputeAnalysisReport:
        """
        Aplica los bloqueos periciales de cuarentena sobre el DisputeAnalysisReport.
        """
        audit = health_audit or (report.health_audit if isinstance(report.health_audit, DocumentHealthAudit) else None)
        if not audit and isinstance(report.health_audit, dict):
            try:
                audit = DocumentHealthAudit.model_validate(report.health_audit)
            except Exception:
                audit = None

        if audit and (audit.status == "QUARANTINE" or audit.quarantine_docket):
            docket = audit.quarantine_docket
            report.quarantine_docket = docket
            report.confidence = min(report.confidence, 0.20)

            reason_snippet = ""
            if docket:
                reasons = getattr(docket, "blocking_reasons", []) or (docket.get("blocking_reasons", []) if isinstance(docket, dict) else [])
                if reasons:
                    reason_snippet = f" Motivo principal: {reasons[0]}"

            report.recommended_action = (
                f"🚨 PROTOCOLO FORENSE ACTIVADO: Expediente en CUARENTENA PREVENTIVA. "
                f"La emisión de Notas de Crédito comerciales y acuerdos vinculantes ha sido BLOQUEADA.{reason_snippet} "
                f"Requiere intervención y subsanación documental por el operador antes de proceder."
            )

        return report
