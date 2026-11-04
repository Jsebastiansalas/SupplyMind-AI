"""
agent/core/capa_ticket_generator.py
Generador de Tickets de Acción Correctiva y Preventiva (CAPA) (Fase 7 - Sprint 7.4).
Emite órdenes de ingeniería preventiva en formato Markdown y JSON dentro de reports/capa/
dirigidas a los responsables operativos internos (Almacén, Transporte, Sistemas EDI, Comercial)
con checklists de verificación pre-despacho para erradicar la reincidencia de deducciones B2B.
"""

from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import hashlib

from data.models import CapaPreventiveTicket
from agent.core.concession_engine import ConcessionEngine
from agent.core.retailer_buyer_simulator import RetailerBuyerSimulator
from agent.core.root_cause_analyzer import RootCauseAnalyzer

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CAPA_DIR = ROOT_DIR / "reports" / "capa"


DEPARTMENT_CAPA_CHECKLISTS: Dict[str, Dict[str, List[str]]] = {
    "WAREHOUSE_CEDIS": {
        "corrective_actions": [
            "Re-etiquetar lotes con impresora térmica calibrada a 300 DPI verificando grado ANSI 'A' en código GS1-128 / SSCC-18.",
            "Instalar báscula de patín hidráulico en andén de carga y adjuntar ticket de peso bruto de tarima al expediente POD.",
            "Capturar fotografía 360° de cada tarima emplayada antes de ingresar a la caja seca con sello visible.",
        ],
        "pre_dispatch_checklist": [
            "[ ] Escaneo exitoso de código de barras GS1-128 en las 4 caras de la tarima.",
            "[ ] Validación de patrón de estiba TI-HI acorde al manual logístico del Retailer.",
            "[ ] Certificado de peso en rampa coincidente con Packing List (±0.2 kg tolerancia).",
            "[ ] Evidencia fotográfica de emplayado y esquineros rígidos archivada en DMS.",
        ],
    },
    "TRANSPORT_LOGISTICS": {
        "corrective_actions": [
            "Activar alerta temprana GPS a 4 horas de la cita MABD para tramitar folio de reprogramación si existe siniestro vial.",
            "Exigir al operador 3PL fotografía del sello de alta seguridad ISO 17712 al salir de planta y antes de romper sello en CEDIS.",
            "Prohibir retiro de rampa sin recabar sello húmedo, nombre, número de empleado y hora de arribo en la remisión POD.",
        ],
        "pre_dispatch_checklist": [
            "[ ] Confirmación de cita en portal del Retailer (MABD / Retail Link / Vendor Central) impresa en cabina.",
            "[ ] Sello metálico de alta seguridad ISO 17712 / C-TPAT colocado y foliado en Carta Porte.",
            "[ ] Termógrafo / Data-logger calibrado y encendido (cuando aplique cadena de frío).",
            "[ ] Instrucción expresa al chofer de exigir acuse físico sellado antes de abandonar el andén.",
        ],
    },
    "SYSTEMS_EDI": {
        "corrective_actions": [
            "Configurar trigger automático en ERP para transmitir el ASN EDI 856 en el instante de cierre de embarque (mínimo 2h antes de arribo).",
            "Implementar bloqueo de salida en caseta de vigilancia si no se ha recibido el Acuse Funcional EDI 997 Status 'A' (Aceptado).",
            "Auditar y homologar la tabla de equivalencias SKU / GTIN-14 / Inner-Pack contra el catálogo EDI 832 vigente del Retailer.",
        ],
        "pre_dispatch_checklist": [
            "[ ] Transmisión ASN EDI 856 enviada con estructura jerárquica Shipment -> Order -> Tare (Pallet) -> Pack -> Item.",
            "[ ] Recepción confirmada de Acuse Funcional EDI 997 Status 'A' sin segmentos AK4 de error.",
            "[ ] Coincidencia exacta 1:1 entre SSCC-18 físico impreso en tarima y segmento MAN*GM del ASN 856.",
            "[ ] Validación de unidades de facturación (EA vs CA) sincronizada con la Orden de Compra EDI 850.",
        ],
    },
    "SALES_COMMERCIAL": {
        "corrective_actions": [
            "Bloquear en el ERP SAP / NetSuite la emisión de facturas cuyo precio unitario difiera de la Orden de Compra EDI 850 sin autorización KAM.",
            "Registrar toda promoción, rebate Co-Op o descuento por volumen en una Adenda Digital foliada antes del inicio de vigencia.",
            "Establecer tope contractual máximo de deducciones logísticas (cap del 3%) en la renovación anual del convenio comercial.",
        ],
        "pre_dispatch_checklist": [
            "[ ] Cotejo automático de precios unitarios Orden de Compra EDI 850 vs Maestro de Precios ERP (varianza $0.00).",
            "[ ] Folio de acuerdo promocional Co-Op / Rebate registrado y vinculado en el encabezado del pedido.",
            "[ ] Condiciones de pago y ventana SLA de aclaraciones validadas en el contrato marco vigente.",
            "[ ] Aprobación electrónica de Finanzas para cualquier bonificación extraordinaria fuera de factura.",
        ],
    },
}


class CapaTicketGenerator:
    """
    Generador de órdenes preventivas CAPA ancladas a expedientes reales para cerrar
    el ciclo de retroalimentación operativa (Closed-Loop RCA).
    """

    @classmethod
    def generate_capa_ticket(
        cls,
        case_id: str,
        override_department: Optional[str] = None
    ) -> CapaPreventiveTicket:
        """
        US-708: Genera y persiste en reports/capa/ un Ticket de Acción Correctiva y
        Preventiva (CAPA) con acciones específicas y checklist pre-despacho.
        """
        CAPA_DIR.mkdir(parents=True, exist_ok=True)

        report = ConcessionEngine.get_or_create_base_report(case_id)
        archetype = RetailerBuyerSimulator.resolve_archetype(case_id)
        rca_info = RootCauseAnalyzer.classify_case_root_cause(case_id, report.root_cause)

        dept_code = override_department if override_department in DEPARTMENT_CAPA_CHECKLISTS else rca_info["department_code"]
        if dept_code != rca_info["department_code"]:
            from agent.core.root_cause_analyzer import DEPARTMENT_DEFINITIONS
            meta = DEPARTMENT_DEFINITIONS[dept_code]
            dept_name = meta["department_name"]
            owner_role = meta["responsible_role"]
            anomaly_detail = meta["primary_failure_modes"][0]
        else:
            dept_name = rca_info["department_name"]
            owner_role = rca_info["responsible_role"]
            anomaly_detail = rca_info["detected_anomaly"]

        impact_usd = abs(report.difference).quantize(Decimal("0.01"))
        if impact_usd >= Decimal("20000.00"):
            severity = "CRITICAL"
            sla_hours = 24
        elif impact_usd >= Decimal("5000.00"):
            severity = "HIGH"
            sla_hours = 48
        else:
            severity = "MEDIUM"
            sla_hours = 72

        short_hash = hashlib.md5(f"{case_id}|{dept_code}".encode("utf-8")).hexdigest()[:6].upper()
        ticket_id = f"CAPA-2026-{short_hash}"
        now_iso = datetime.now(timezone.utc).isoformat()
        invoice_id = getattr(report, "invoice_id", None) or f"INV-{case_id.upper()[:12]}"

        templates = DEPARTMENT_CAPA_CHECKLISTS[dept_code]
        corrective_actions = templates["corrective_actions"]
        checklist = templates["pre_dispatch_checklist"]

        md_path = CAPA_DIR / f"capa_{case_id}.md"
        json_path = CAPA_DIR / f"capa_{case_id}.json"

        actions_md = "\n".join([f"{i + 1}. {act}" for i, act in enumerate(corrective_actions)])
        checklist_md = "\n".join([f"- {item}" for item in checklist])

        markdown_content = f"""# ORDEN DE INGENIERÍA PREVENTIVA — TICKET CAPA `{ticket_id}`
**SISTEMA DE GESTIÓN DE CALIDAD Y PREVENCIÓN DE FUGAS B2B (CLOSED-LOOP RCA)**

---
- **ID de Ticket CAPA:** `{ticket_id}`
- **Expediente Origen:** `{case_id}` (Factura: `{invoice_id}`)
- **Cliente / Retailer Afectado:** {archetype.retailer_name}
- **Departamento Interno Responsable:** **{dept_name}** (`{dept_code}`)
- **Líder Operativo Asignado:** **{owner_role}**
- **Severidad / Prioridad:** `{severity}` (SLA de Implementación: `{sla_hours} horas`)
- **Impacto Financiero en Disputa:** **${impact_usd:,.2f} USD** (Fuga Justificada: `${report.justified_amount:,.2f} USD`)
- **Fecha de Emisión UTC:** `{now_iso}`

---

### I. DIAGNÓSTICO DE CAUSA RAÍZ (HALLAZGO DE AUDITORÍA)

- **Dictamen del Agente SupplyMind:** {report.root_cause}
- **Anomalía Operativa Detectada:** {anomaly_detail}

### II. PLAN DE ACCIÓN CORRECTIVA INMEDIATA (CAPA)

{actions_md}

### III. CHECKLIST MANDATORIO PRE-DESPACHO (CANDADO DE SALIDA)

{checklist_md}

---
**Estado del Ticket:** `OPEN_ASSIGNED`  
**Generado Automáticamente por:** SupplyMind AI — Motor Preventivo RCA (Fase 7)
"""

        ticket = CapaPreventiveTicket(
            ticket_id=ticket_id,
            case_id=case_id,
            retailer_name=archetype.retailer_name,
            department_code=dept_code,
            department_name=dept_name,
            assigned_owner_role=owner_role,
            severity=severity,
            financial_impact_usd=impact_usd,
            root_cause_summary=report.root_cause,
            detected_anomaly_detail=anomaly_detail,
            corrective_actions=corrective_actions,
            pre_dispatch_checklist=checklist,
            sla_resolution_hours=sla_hours,
            status="OPEN_ASSIGNED",
            created_at=now_iso,
            markdown_content=markdown_content,
            file_path=str(md_path),
        )

        md_path.write_text(markdown_content, encoding="utf-8")
        json_path.write_text(ticket.model_dump_json(indent=2), encoding="utf-8")
        return ticket
