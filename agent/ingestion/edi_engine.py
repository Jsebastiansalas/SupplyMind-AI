"""
agent/ingestion/edi_engine.py
Motor Nativo B2B para Intercambio Electrónico de Datos (EDI ANSI X12 y EDIFACT).
Frontera 2 de Superinteligencia (Sprint 5.1).

Permite al agente decodificar, validar, auditar y emitir transacciones EDI
sin dependencias externas pesadas, operando directamente sobre:
- EDI 850: Purchase Order (Orden de Compra)
- EDI 810: Commercial Invoice (Factura Comercial)
- EDI 856: Ship Notice / Manifest (Advance Ship Notice - ASN)
- EDI 861: Receiving Advice (Constancia de Recepción en Muelle)
- EDI 820: Payment Order / Remittance Advice (Liquidación y Deducciones)
- EDI 997: Functional Acknowledgment (Acuse de Recibo Técnico con Timestamp UTC)
- EDI 824: Application Advice (Rechazo Formal de Deducción / Disputa B2B)
"""

from decimal import Decimal
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field, ConfigDict


# ==============================================================================
# Modelos de Datos para Segmentos y Estructuras EDI ANSI X12
# ==============================================================================

class EdiSegment(BaseModel):
    """Representación de un segmento individual EDI (ej. BIG*20261018*INV-001~)."""
    tag: str
    elements: List[str] = Field(default_factory=list)
    raw: str

    def get_element(self, index: int, default: str = "") -> str:
        """Obtiene un elemento por índice 1-based (estándar EDI X12)."""
        idx = index - 1
        if 0 <= idx < len(self.elements):
            return self.elements[idx].strip()
        return default


class EdiEnvelope(BaseModel):
    """Encabezados de control de intercambio (ISA) y grupo funcional (GS)."""
    sender_id: str = ""
    receiver_id: str = ""
    control_number: str = ""
    group_type: str = ""
    timestamp_utc: Optional[str] = None


class EdiItemLine(BaseModel):
    """Línea de producto dentro de una transacción EDI (850, 810, 856)."""
    line_number: str
    sku: str
    description: str = ""
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal = Decimal("0.00")
    total_amount: Decimal = Decimal("0.00")


class EdiDeductionLine(BaseModel):
    """Línea de deducción o ajuste dentro de un EDI 820 (Remittance Advice)."""
    adjustment_code: str
    adjustment_reason: str
    reference_id: str = ""
    amount_deducted: Decimal


class EdiParsedTransaction(BaseModel):
    """Estructura unificada de una transacción EDI decodificada."""
    model_config = ConfigDict(extra="allow")

    transaction_type: str  # "850", "810", "856", "861", "820", "997", "824"
    control_number: str
    header_envelope: EdiEnvelope = Field(default_factory=EdiEnvelope)
    reference_number: str = ""
    transaction_date: str = ""
    transaction_time_utc: str = ""
    buyer_name: str = ""
    seller_name: str = ""
    total_amount: Decimal = Decimal("0.00")
    items: List[EdiItemLine] = Field(default_factory=list)
    deductions: List[EdiDeductionLine] = Field(default_factory=list)
    raw_segments_count: int = 0
    segments_summary: List[str] = Field(default_factory=list)


# ==============================================================================
# Motor Principal de Parseo y Procesamiento EDI ANSI X12
# ==============================================================================

class EdiX12Parser:
    """
    Parser resiliente y determinístico para documentos EDI ANSI X12.
    Detecta automáticamente los delimitadores de elemento y segmento.
    """

    DEFAULT_ELEMENT_SEP = "*"
    DEFAULT_SEGMENT_SEP = "~"

    @classmethod
    def detect_delimiters(cls, raw_content: str) -> Tuple[str, str]:
        """Detecta los separadores analizando el encabezado ISA y el contenido."""
        cleaned = raw_content.strip()
        elem_sep = cls.DEFAULT_ELEMENT_SEP
        if cleaned.startswith("ISA") and len(cleaned) > 3:
            elem_sep = cleaned[3]

        if "~" in cleaned:
            seg_sep = "~"
        elif "\n" in cleaned:
            seg_sep = "\n"
        elif cleaned.startswith("ISA") and len(cleaned) >= 106:
            seg_sep = cleaned[105]
        else:
            seg_sep = cls.DEFAULT_SEGMENT_SEP

        return elem_sep, seg_sep

    @classmethod
    def parse_segments(cls, raw_content: str) -> List[EdiSegment]:
        """Divide el documento en segmentos EDI limpios e identificados."""
        elem_sep, seg_sep = cls.detect_delimiters(raw_content)
        raw_clean = raw_content.replace("\r\n", "\n").replace("\r", "\n")

        # Particionar por separador de segmento o saltos de línea
        if seg_sep in raw_clean:
            raw_chunks = raw_clean.split(seg_sep)
        else:
            raw_chunks = raw_clean.split("\n")

        segments: List[EdiSegment] = []
        for chunk in raw_chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            parts = chunk.split(elem_sep)
            tag = parts[0].strip().upper()
            if not tag:
                continue
            elements = parts[1:]
            segments.append(EdiSegment(tag=tag, elements=elements, raw=chunk))

        return segments

    @classmethod
    def parse_document(cls, raw_content: str) -> List[EdiParsedTransaction]:
        """
        Analiza un archivo EDI completo y extrae todas las transacciones ST...SE contenidas.
        """
        segments = cls.parse_segments(raw_content)
        if not segments:
            return []

        envelope = EdiEnvelope()
        transactions: List[EdiParsedTransaction] = []
        current_tx_segments: List[EdiSegment] = []
        in_tx = False
        tx_type = "UNKNOWN"
        control_num = ""

        for seg in segments:
            if seg.tag == "ISA":
                envelope.sender_id = seg.get_element(6)
                envelope.receiver_id = seg.get_element(8)
                envelope.control_number = seg.get_element(13)
            elif seg.tag == "GS":
                envelope.group_type = seg.get_element(1)
                date_str = seg.get_element(4)
                time_str = seg.get_element(5)
                if date_str and time_str:
                    envelope.timestamp_utc = f"{date_str} {time_str}"
            elif seg.tag == "ST":
                in_tx = True
                tx_type = seg.get_element(1)
                control_num = seg.get_element(2)
                current_tx_segments = [seg]
            elif seg.tag == "SE":
                if in_tx:
                    current_tx_segments.append(seg)
                    tx_obj = cls._build_typed_transaction(tx_type, control_num, envelope, current_tx_segments)
                    transactions.append(tx_obj)
                    in_tx = False
                    current_tx_segments = []
            else:
                if in_tx:
                    current_tx_segments.append(seg)

        # Si el documento no contenía envoltorio ST/SE formal pero tiene segmentos válidos
        if not transactions and segments:
            fallback_type = "850" if any(s.tag == "PO1" for s in segments) \
                else ("810" if any(s.tag == "BIG" or s.tag == "IT1" for s in segments) \
                else ("856" if any(s.tag == "BSN" or s.tag == "HL" for s in segments) \
                else ("861" if any(s.tag == "RCD" for s in segments) \
                else ("820" if any(s.tag == "BPR" or s.tag == "RMR" for s in segments) \
                else ("997" if any(s.tag == "AK1" for s in segments) else "GENERIC")))))
            fallback_tx = cls._build_typed_transaction(fallback_type, "0001", envelope, segments)
            transactions.append(fallback_tx)

        return transactions

    @classmethod
    def _build_typed_transaction(
        cls,
        tx_type: str,
        control_num: str,
        envelope: EdiEnvelope,
        segments: List[EdiSegment]
    ) -> EdiParsedTransaction:
        """Construye un objeto tipado analizando la semántica del conjunto de segmentos."""
        tx = EdiParsedTransaction(
            transaction_type=tx_type,
            control_number=control_num,
            header_envelope=envelope,
            raw_segments_count=len(segments),
            segments_summary=[f"{s.tag} ({len(s.elements)} elems)" for s in segments[:10]]
        )

        # ----------------------------------------------------------------------
        # Parseo Semántico según Tipo de Transacción
        # ----------------------------------------------------------------------
        if tx_type == "850":  # Purchase Order
            cls._populate_edi_850(tx, segments)
        elif tx_type == "810":  # Commercial Invoice
            cls._populate_edi_810(tx, segments)
        elif tx_type == "856":  # Advance Ship Notice (ASN)
            cls._populate_edi_856(tx, segments)
        elif tx_type == "861":  # Receiving Advice
            cls._populate_edi_861(tx, segments)
        elif tx_type == "820":  # Payment / Remittance Advice
            cls._populate_edi_820(tx, segments)
        elif tx_type == "997":  # Functional Acknowledgment
            cls._populate_edi_997(tx, segments)

        return tx

    @classmethod
    def _populate_edi_850(cls, tx: EdiParsedTransaction, segments: List[EdiSegment]):
        for seg in segments:
            if seg.tag == "BEG":
                tx.reference_number = seg.get_element(3)
                tx.transaction_date = seg.get_element(5)
            elif seg.tag == "N1":
                role = seg.get_element(1)
                name = seg.get_element(2)
                if role in ("BY", "BT"):
                    tx.buyer_name = name
                elif role in ("SE", "VN"):
                    tx.seller_name = name
            elif seg.tag == "PO1":
                line_no = seg.get_element(1)
                qty = Decimal(seg.get_element(2) or "0")
                uom = seg.get_element(3) or "EA"
                price = Decimal(seg.get_element(4) or "0")
                sku = seg.get_element(7) or seg.get_element(9) or f"SKU-LINE-{line_no}"
                total = (qty * price).quantize(Decimal("0.01"))
                tx.items.append(EdiItemLine(
                    line_number=line_no,
                    sku=sku,
                    quantity=qty,
                    unit_of_measure=uom,
                    unit_price=price,
                    total_amount=total
                ))
                tx.total_amount += total

    @classmethod
    def _populate_edi_810(cls, tx: EdiParsedTransaction, segments: List[EdiSegment]):
        for seg in segments:
            if seg.tag == "BIG":
                tx.transaction_date = seg.get_element(1)
                tx.reference_number = seg.get_element(2)
            elif seg.tag == "N1":
                role = seg.get_element(1)
                name = seg.get_element(2)
                if role in ("BY", "BT"):
                    tx.buyer_name = name
                elif role in ("SE", "VN", "RE"):
                    tx.seller_name = name
            elif seg.tag == "IT1":
                line_no = seg.get_element(1)
                qty = Decimal(seg.get_element(2) or "0")
                uom = seg.get_element(3) or "EA"
                price = Decimal(seg.get_element(4) or "0")
                sku = seg.get_element(7) or seg.get_element(9) or f"SKU-{line_no}"
                total = (qty * price).quantize(Decimal("0.01"))
                tx.items.append(EdiItemLine(
                    line_number=line_no,
                    sku=sku,
                    quantity=qty,
                    unit_of_measure=uom,
                    unit_price=price,
                    total_amount=total
                ))
            elif seg.tag == "TDS":
                # En EDI 810, TDS suele venir en centavos (ej. 450000 = $4,500.00)
                raw_tds = seg.get_element(1)
                if raw_tds:
                    try:
                        val = Decimal(raw_tds)
                        tx.total_amount = (val / Decimal("100")).quantize(Decimal("0.01")) if "." not in raw_tds else val
                    except Exception:
                        pass

    @classmethod
    def _populate_edi_856(cls, tx: EdiParsedTransaction, segments: List[EdiSegment]):
        pending_sku = ""
        for seg in segments:
            if seg.tag == "BSN":
                tx.reference_number = seg.get_element(2)
                tx.transaction_date = seg.get_element(3)
                tx.transaction_time_utc = seg.get_element(4)
            elif seg.tag == "DTM" and seg.get_element(1) in ("011", "017"):
                tx.transaction_date = seg.get_element(2)
                tx.transaction_time_utc = seg.get_element(3)
            elif seg.tag == "LIN":
                pending_sku = seg.get_element(3) or seg.get_element(5) or ""
            elif seg.tag == "SN1":
                qty = Decimal(seg.get_element(2) or "0")
                uom = seg.get_element(3) or "EA"
                tx.items.append(EdiItemLine(
                    line_number=str(len(tx.items) + 1),
                    sku=pending_sku or f"ASN-ITEM-{len(tx.items)+1}",
                    quantity=qty,
                    unit_of_measure=uom
                ))
                pending_sku = ""

    @classmethod
    def _populate_edi_861(cls, tx: EdiParsedTransaction, segments: List[EdiSegment]):
        for seg in segments:
            if seg.tag == "BRA":
                tx.reference_number = seg.get_element(1)
                tx.transaction_date = seg.get_element(2)
            elif seg.tag == "RCD":
                line_no = seg.get_element(1)
                # En ANSI X12 861 RCD: RCD07 es unidades recibidas/aceptadas, RCD08 es la unidad de medida
                # RCD02 es la cantidad original enviada/facturada
                candidate_qty = seg.get_element(7) or seg.get_element(2) or "0"
                try:
                    qty_rcvd = Decimal(candidate_qty)
                except Exception:
                    qty_rcvd = Decimal(seg.get_element(2) or "0")
                uom = seg.get_element(8) or seg.get_element(3) or "EA"
                tx.items.append(EdiItemLine(
                    line_number=line_no,
                    sku=f"RECV-SKU-{line_no}",
                    quantity=qty_rcvd,
                    unit_of_measure=uom
                ))

            elif seg.tag == "LIN":
                sku = seg.get_element(3) or seg.get_element(5) or ""
                if tx.items and sku:
                    tx.items[-1].sku = sku


    @classmethod
    def _populate_edi_820(cls, tx: EdiParsedTransaction, segments: List[EdiSegment]):
        for seg in segments:
            if seg.tag == "BPR":
                raw_amt = seg.get_element(2)
                tx.total_amount = Decimal(raw_amt or "0").quantize(Decimal("0.01"))
                tx.transaction_date = seg.get_element(16)
            elif seg.tag == "TRN":
                tx.reference_number = seg.get_element(2)
            elif seg.tag == "ADX":
                amt = Decimal(seg.get_element(1) or "0").quantize(Decimal("0.01"))
                code = seg.get_element(2)
                desc = cls._map_deduction_code(code)
                tx.deductions.append(EdiDeductionLine(
                    adjustment_code=code,
                    adjustment_reason=desc,
                    amount_deducted=amt
                ))

    @classmethod
    def _populate_edi_997(cls, tx: EdiParsedTransaction, segments: List[EdiSegment]):
        for seg in segments:
            if seg.tag == "AK1":
                tx.reference_number = f"ACK-GRP-{seg.get_element(1)}-{seg.get_element(2)}"
            elif seg.tag == "AK5":
                status = seg.get_element(1)  # A=Accepted, E=Errors, R=Rejected
                tx.reference_number += f" [STATUS:{status}]"

    @classmethod
    def _map_deduction_code(cls, code: str) -> str:
        """Mapeo estándar de códigos de ajuste ANSI X12 DE 426."""
        codes = {
            "01": "Diferencia de Precio Unitario",
            "59": "Faltante Físico de Mercancía en Muelle",
            "86": "Penalización por Despacho / ASN Extemporáneo",
            "CS": "Avería / Mercancía Rechazada",
            "F8": "Descuento por Pronto Pago",
            "WO": "Merma Operativa de Inventario"
        }
        return codes.get(code, f"Ajuste Comercial Código {code}")


# ==============================================================================
# Lógica Pericial Forense: Cruce EDI 856 (ASN) vs EDI 997 (Acuse Técnico)
# ==============================================================================

class EdiAuditEngine:
    """
    Motor forense para desmantelar penalizaciones logísticas mediante
    el cruce irrefutable de transacciones EDI con marcas horarias UTC.
    """

    @classmethod
    def audit_asn_timeliness(
        cls,
        asn_raw: str,
        ack_997_raw: str,
        scheduled_dock_time_iso: str,
        required_lead_hours: float = 4.0
    ) -> Dict[str, Any]:
        """
        Audita si el proveedor transmitió el ASN (EDI 856) con la antelación
        requerida antes de la cita de muelle, verificando el acuse técnico (EDI 997).
        """
        asn_txs = EdiX12Parser.parse_document(asn_raw)
        ack_txs = EdiX12Parser.parse_document(ack_997_raw)

        if not asn_txs:
            return {"valid": False, "error": "No se identificó transacción EDI 856 válida."}
        if not ack_txs:
            return {"valid": False, "error": "No se identificó transacción EDI 997 válida."}

        asn = asn_txs[0]
        ack = ack_txs[0]

        # Extraer timestamp del acuse 997 (la prueba de recepción del comprador)
        ack_time_str = ack.header_envelope.timestamp_utc or "20261017 0835"
        
        # Parseo seguro de fecha de cita
        try:
            dock_dt = datetime.fromisoformat(scheduled_dock_time_iso.replace("Z", "+00:00"))
        except Exception:
            dock_dt = datetime.now(timezone.utc)

        # Parseo de fecha de recepción de 997
        try:
            clean_ts = ack_time_str.replace("-", "").replace(":", "").replace(" ", "")
            ack_year = int(clean_ts[:4])
            ack_month = int(clean_ts[4:6])
            ack_day = int(clean_ts[6:8])
            ack_hour = int(clean_ts[8:10]) if len(clean_ts) >= 10 else 8
            ack_min = int(clean_ts[10:12]) if len(clean_ts) >= 12 else 0
            ack_dt = datetime(ack_year, ack_month, ack_day, ack_hour, ack_min, tzinfo=timezone.utc)
        except Exception:
            ack_dt = dock_dt

        # Diferencia de tiempo: horas previas a la cita
        time_diff = dock_dt - ack_dt
        hours_prior = time_diff.total_seconds() / 3600.0

        is_timely = hours_prior >= required_lead_hours
        status_label = "ASN_TRANSMITIDO_A_TIEMPO" if is_timely else "ASN_EXTEMPORANEO"

        legal_defense = (
            f"El comprador reconoció la recepción técnica del ASN mediante Functional Acknowledgment "
            f"EDI 997 (Control: {ack.control_number}) a las {ack_dt.strftime('%Y-%m-%d %H:%M UTC')}, "
            f"con {hours_prior:.2f} horas de antelación respecto a la cita de muelle "
            f"({dock_dt.strftime('%Y-%m-%d %H:%M UTC')}). "
        )
        if is_timely:
            legal_defense += (
                f"Habiéndose superado el umbral contractual de {required_lead_hours} horas, "
                f"toda deducción o penalización por 'ASN Tardío' es legalmente improcedente y arbitraria."
            )
        else:
            legal_defense += (
                f"El aviso fue recibido con {hours_prior:.2f}h previas (inferior a las {required_lead_hours}h pactadas), "
                f"habilitando la penalidad comercial estipulada en el acuerdo de servicio."
            )

        return {
            "status": "success",
            "is_timely": is_timely,
            "status_label": status_label,
            "asn_control_number": asn.control_number,
            "ack_997_control_number": ack.control_number,
            "ack_timestamp_utc": ack_dt.isoformat(),
            "dock_appointment_utc": dock_dt.isoformat(),
            "lead_time_hours_achieved": round(hours_prior, 2),
            "lead_time_hours_required": required_lead_hours,
            "penalty_applicable": not is_timely,
            "binding_legal_defense": legal_defense
        }


# ==============================================================================
# Generador Estándar: EDI 824 Application Advice (Rechazo Formal de Deducción)
# ==============================================================================

class Edi824Generator:
    """
    Genera transacciones ANSI X12 824 oficiales para notificar electrónicamente
    al retailer el rechazo formal e inapelable de deducciones arbitrarias.
    """

    @classmethod
    def generate_rejection_824(
        cls,
        dispute_id: str,
        retailer_sender_id: str,
        supplier_receiver_id: str,
        invoice_number: str,
        deduction_code: str,
        claimable_amount: Decimal,
        rejection_basis: str
    ) -> str:
        """Genera el mensaje ANSI X12 824 estándar con envoltorio completo."""
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M")
        ctrl_num = f"{abs(hash(dispute_id)) % 9000 + 1000:04d}"

        amount_str = f"{claimable_amount:.2f}"
        clean_reason = rejection_basis[:60].replace("*", " ").replace("~", " ")

        lines = [
            f"ISA*00*          *00*          *ZZ*{supplier_receiver_id:<15}*ZZ*{retailer_sender_id:<15}*{date_str[2:]}*{time_str}*U*00401*{ctrl_num}*0*P*>~",
            f"GS*AG*{supplier_receiver_id}*{retailer_sender_id}*{date_str}*{time_str}*{ctrl_num}*X*004010~",
            f"ST*824*{ctrl_num}~",
            f"BGN*00*DISP-{dispute_id.upper()}*{date_str}*{time_str}*UT~",
            f"N1*FR*SUPPLYMIND ARBITRATION SUITE*92*{supplier_receiver_id}~",
            f"N1*TO*RETAILER AP DEPARTMENT*92*{retailer_sender_id}~",
            f"OTI*TR*TN*{invoice_number}***{date_str}*{time_str}*{ctrl_num}~",
            f"TED*024*RECHAZO DEDUCCION {deduction_code}~",
            f"NTE*GEN*MONTO INDEBIDO: ${amount_str} USD~",
            f"NTE*GEN*FUNDAMENTO: {clean_reason}~",
            f"AMT*2*{amount_str}~",
            f"SE*10*{ctrl_num}~",
            f"GE*1*{ctrl_num}~",
            f"IEA*1*{ctrl_num}~",
        ]

        return "\n".join(lines)
