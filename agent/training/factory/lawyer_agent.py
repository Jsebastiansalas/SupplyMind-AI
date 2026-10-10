"""
Corporate Lawyer Agent (Abogado Corporativo).

Agente adversarial que redacta y modula las cláusulas del contrato comercial
(CommercialContract), fijando ventanas perentorias de notificación, reglas de
jerarquía de evidencia probatoria, prohibiciones de penalizaciones unilaterales
y márgenes de tolerancia de merma permitida.
"""

from decimal import Decimal
from typing import List, Optional
from data.models import CommercialContract, ContractClause


class CorporateLawyerAgent:
    """
    Genera contratos mercantiles complejos con cláusulas de protección patrimonial
    y reglas probatorias estrictas para desafiar el análisis contractual del agente.
    """

    def __init__(self, legal_firm: str = "Bufete Jurídico Corporativo & Asociados"):
        self.legal_firm = legal_firm

    def build_clause_3_1_price_precedence(self) -> ContractClause:
        """Cláusula 3.1: Prelación de Precios de la Orden de Compra sobre listas o facturas."""
        return ContractClause(
            clause_id="CLAUSE-3.1",
            title="Condiciones de Precios y Prevalencia de la Orden de Compra",
            text=(
                "Los precios unitarios facturados deben coincidir estrictamente con los precios "
                "pactados en la Orden de Compra respectiva. En caso de discrepancia entre la factura "
                "y la Orden de Compra, prevalecerá en todo momento el precio pactado en la Orden de Compra. "
                "El comprador queda autorizado a deducir cualquier sobreprecio no pactado."
            ),
            policy="STRICT_MATCH",
            tolerance_percentage=Decimal("0.00")
        )

    def build_clause_4_2_signed_pod_shortage(self) -> ContractClause:
        """Cláusula 4.2: Faltantes físicos requieren POD firmado con sello de muelle."""
        return ContractClause(
            clause_id="CLAUSE-4.2",
            title="Faltantes Físicos en Recepción y Prueba Plena",
            text=(
                "En caso de que las cantidades recibidas en bodega sean inferiores a las facturadas "
                "y esto conste de manera fehaciente en la remisión de entrega debidamente firmada "
                "por el transportista y con sello oficial de recepción de muelle, el comprador está "
                "facultado para deducir automáticamente del pago el valor unitario de las unidades faltantes. "
                "Cualquier remisión no firmada o sin sello carece de valor probatorio y no autoriza deducción alguna."
            ),
            policy="DEDUCTION_ALLOWED_ON_SIGNED_DISCREPANCY",
            tolerance_percentage=Decimal("0.00")
        )

    def build_clause_5_1_damage_notice_window(self) -> ContractClause:
        """Cláusula 5.1: Ventana perentoria de 48 horas y evidencia fotográfica para averías."""
        return ContractClause(
            clause_id="CLAUSE-5.1",
            title="Mercancía Averiada y Plazo Perentorio de Notificación",
            text=(
                "Toda mercancía dañada o averiada detectada durante el descargue debe notificarse por escrito "
                "al proveedor dentro de un plazo perentorio de cuarenta y ocho (48) horas siguientes a la entrega, "
                "acompañando acta circunstanciada suscrita y reporte fotográfico de las estibas. "
                "Cualquier notificación posterior a dicho plazo o carente de fotografías se considerará extemporánea "
                "e improcedente, perdiendo el comprador todo derecho a deducción o retención sobre el pago."
            ),
            policy="PHOTO_EVIDENCE_REQUIRED",
            tolerance_percentage=Decimal("0.00")
        )

    def build_clause_6_1_volume_tolerance(self, tolerance_pct: Decimal = Decimal("2.00")) -> ContractClause:
        """Cláusula 6.1: Franquicia o ventana de tolerancia para merma o faltante en volumen."""
        return ContractClause(
            clause_id="CLAUSE-6.1",
            title="Tolerancia Comercial en Volumen y Mermas",
            text=(
                f"Para entregas de productos empacados a granel o de alta rotación, se establece una franquicia de "
                f"tolerancia de hasta el {tolerance_pct:.2f}% sobre el volumen total ordenado. Las variaciones o faltantes "
                f"que se ubiquen dentro de dicho porcentaje serán absorbidas por el comprador sin derecho a retención de pago "
                f"ni emisión forzosa de notas de crédito."
            ),
            policy="TOLERANCE_WINDOW_2PCT",
            tolerance_percentage=tolerance_pct
        )

    def build_clause_7_3_no_unilateral_penalties(self) -> ContractClause:
        """Cláusula 7.3: Prohibición absoluta de penalizaciones o cobros administrativos unilaterales."""
        return ContractClause(
            clause_id="CLAUSE-7.3",
            title="Prohibición de Penalizaciones y Descuentos Unilaterales",
            text=(
                "Queda estrictamente prohibida la aplicación unilateral de descuentos administrativos, cargos por "
                "incumplimiento de citas de muelle (late slot), cargos de aviso anticipado de embarque (ASN) o penalidades "
                "operativas no pactadas expresamente. Toda deducción por penalización requerirá un addendum firmado por los "
                "representantes legales de ambas partes previo a cualquier retención en los avisos de pago."
            ),
            policy="NO_UNILATERAL_PENALTIES",
            tolerance_percentage=Decimal("0.00")
        )

    def build_clause_8_2_evidence_hierarchy(self) -> ContractClause:
        """Cláusula 8.2: Jerarquía probatoria de documentos comerciales."""
        return ContractClause(
            clause_id="CLAUSE-8.2",
            title="Jerarquía Probatoria y Conciliación de Cuentas",
            text=(
                "La remisión de entrega debidamente firmada constituye prueba plena de primer nivel (Nivel 1) respecto a las "
                "cantidades efectivamente entregadas. El contrato y la orden de compra rigen los términos y precios pactados "
                "(Nivel 2). Los comprobantes bancarios y avisos de pago representan declaraciones unilaterales (Nivel 3). "
                "Ninguna deducción unilateral en Nivel 3 podrá prevalecer sobre la verdad probada de los Niveles 1 y 2."
            ),
            policy="EVIDENCE_HIERARCHY",
            tolerance_percentage=Decimal("0.00")
        )

    def generate_standard_contract(
        self,
        contract_id: str = "CTR-RETAIL-2026",
        vendor_id: str = "VEN-001",
        customer_id: str = "CUST-RETAIL-101",
        valid_from: str = "2026-01-01",
        valid_to: str = "2026-12-31",
        custom_clauses: Optional[List[ContractClause]] = None
    ) -> CommercialContract:
        """Genera un contrato mercantil completo con las 6 cláusulas rectoras de la industria."""
        if custom_clauses:
            clauses = custom_clauses
        else:
            clauses = [
                self.build_clause_3_1_price_precedence(),
                self.build_clause_4_2_signed_pod_shortage(),
                self.build_clause_5_1_damage_notice_window(),
                self.build_clause_6_1_volume_tolerance(),
                self.build_clause_7_3_no_unilateral_penalties(),
                self.build_clause_8_2_evidence_hierarchy()
            ]

        return CommercialContract(
            contract_id=contract_id,
            vendor_id=vendor_id,
            customer_id=customer_id,
            valid_from=valid_from,
            valid_to=valid_to,
            clauses=clauses
        )
