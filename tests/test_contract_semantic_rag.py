import pytest
from decimal import Decimal
from pathlib import Path

from data.models import CommercialContract, ContractClause
from tools.reconciliation_engine.engine import ReconciliationSummary, LineItemDiscrepancy
from tools.contract_analyzer.rules import evaluate_contract_compliance, ClauseMatch, ContractEvaluationResult
from tools.contract_analyzer.rag import ContractRAG, VectorContract, chromadb

CASE_004_DIR = Path("data/cases/case_004_enterprise")

def test_arbitrary_clause_ids_shortage():
    """
    Valida que una cláusula de faltante con numeración arbitraria ('CLAUSULA-14.8')
    y política libre ('CUSTOM_SHORTAGE_POLICY_XYZ') sea identificada semánticamente
    sin depender de '4.2' ni 'DEDUCTION_ALLOWED_ON_SIGNED_DISCREPANCY'.
    """
    contract = CommercialContract(
        contract_id="CTR-ARBITRARY-001",
        vendor_id="VEND-XYZ",
        customer_id="CUST-ABC",
        valid_from="2026-01-01",
        valid_to="2026-12-31",
        clauses=[
            ContractClause(
                clause_id="CLAUSULA-14.8",
                title="Ajuste por Faltantes en Muelle de Descarga",
                text="En caso de faltante físico en las cantidades recibidas respecto a lo facturado, el comprador está facultado para deducir el valor total de las unidades faltantes.",
                policy="CUSTOM_SHORTAGE_POLICY_XYZ",
                tolerance_percentage=Decimal("0.00")
            ),
            ContractClause(
                clause_id="CLAUSULA-20.1",
                title="Gobierno Corporativo y Notificaciones",
                text="Todas las comunicaciones deberán enviarse por correo certificado.",
                policy="GENERAL_COMPLIANCE",
                tolerance_percentage=Decimal("0.00")
            )
        ]
    )

    summary = ReconciliationSummary(
        billed_amount=Decimal("10000.00"),
        received_amount=Decimal("8500.00"),
        difference=Decimal("-1500.00"),
        total_deductions_applied=Decimal("1500.00"),
        primary_discrepancy_type="FALTANTE_DE_MERCANCIA",
        total_missing_amount=Decimal("1500.00"),
        total_damaged_amount=Decimal("0.00"),
        total_price_discrepancy_amount=Decimal("0.00"),
        justified_deductions_amount=Decimal("1500.00"),
        unjustified_deductions_amount=Decimal("0.00"),
        discrepancies=[
            LineItemDiscrepancy(
                item_id="ITEM-A",
                description="Caja de Componentes",
                billed_quantity=100,
                received_quantity=85,
                missing_quantity=15,
                damaged_quantity=0,
                agreed_unit_price=Decimal("100.00"),
                invoiced_unit_price=Decimal("100.00"),
                price_difference=Decimal("0.00"),
                missing_amount=Decimal("1500.00"),
                damaged_amount=Decimal("0.00"),
                total_impact=Decimal("1500.00")
            )
        ],
        evidence_trail=["Remisión con sello de 15 faltantes"]
    )

    result = evaluate_contract_compliance(contract, summary)
    assert result.contractual_justification_valid is True
    assert len(result.matches) >= 1
    match = result.matches[0]
    assert match.clause_id == "CLAUSULA-14.8"
    assert match.is_applicable is True
    assert match.is_deduction_authorized is True
    assert "autoriza" in match.explanation.lower() or "faculta" in match.explanation.lower()
    assert "justificada" in result.summary_legal_assessment.lower()
    assert "Nota de Crédito" in result.recommended_contract_action

def test_arbitrary_clause_ids_pricing():
    """
    Valida que una cláusula de precios con numeración libre ('SECCION-9.3')
    sea emparejada semánticamente ante discrepancias de tarifa en factura.
    """
    contract = CommercialContract(
        contract_id="CTR-ARBITRARY-002",
        vendor_id="VEND-XYZ",
        customer_id="CUST-ABC",
        valid_from="2026-01-01",
        valid_to="2026-12-31",
        clauses=[
            ContractClause(
                clause_id="SECCION-9.3",
                title="Prevalencia Vinculante de la Orden de Compra",
                text="Los precios acordados en la orden de compra aprobada prevalecerán con carácter vinculante. Si el proveedor factura un sobreprecio, el comprador podrá deducir de pleno derecho la diferencia.",
                policy="PO_PRICE_PREVALENCE",
                tolerance_percentage=Decimal("0.00")
            )
        ]
    )

    summary = ReconciliationSummary(
        billed_amount=Decimal("20000.00"),
        received_amount=Decimal("18000.00"),
        difference=Decimal("-2000.00"),
        total_deductions_applied=Decimal("2000.00"),
        primary_discrepancy_type="DIFERENCIA_DE_PRECIO",
        total_missing_amount=Decimal("0.00"),
        total_damaged_amount=Decimal("0.00"),
        total_price_discrepancy_amount=Decimal("-2000.00"),
        justified_deductions_amount=Decimal("2000.00"),
        unjustified_deductions_amount=Decimal("0.00"),
        discrepancies=[],
        evidence_trail=["PO fija precio a $90 vs $100 facturado"]
    )

    result = evaluate_contract_compliance(contract, summary)
    assert result.contractual_justification_valid is True
    assert any(m.clause_id == "SECCION-9.3" and m.is_deduction_authorized for m in result.matches)

def test_unilateral_penalty_clause_rejection():
    """
    Valida que cargos no autorizados (ej. mora, retención unilateral) sean evaluados
    contra cláusulas de improcedencia de penalizaciones y marcados como NO autorizados.
    """
    contract = CommercialContract(
        contract_id="CTR-ARBITRARY-003",
        vendor_id="VEND-XYZ",
        customer_id="CUST-ABC",
        valid_from="2026-01-01",
        valid_to="2026-12-31",
        clauses=[
            ContractClause(
                clause_id="ARTICULO-18",
                title="Improcedencia de Penalizaciones Unilaterales",
                text="Toda penalización, cargo por descarga o multa administrativa requiere acuerdo previo por escrito entre las partes. Las retenciones unilaterales sin adenda serán nulas de pleno derecho.",
                policy="UNILATERAL_PENALTY_FORBIDDEN",
                tolerance_percentage=Decimal("0.00")
            )
        ]
    )

    summary = ReconciliationSummary(
        billed_amount=Decimal("50000.00"),
        received_amount=Decimal("45000.00"),
        difference=Decimal("-5000.00"),
        total_deductions_applied=Decimal("5000.00"),
        primary_discrepancy_type="DEDUCCION_NO_IDENTIFICADA",
        total_missing_amount=Decimal("0.00"),
        total_damaged_amount=Decimal("0.00"),
        total_price_discrepancy_amount=Decimal("0.00"),
        justified_deductions_amount=Decimal("0.00"),
        unjustified_deductions_amount=Decimal("5000.00"),
        discrepancies=[],
        evidence_trail=["Retención unilateral de $5,000 sin comprobante"]
    )

    result = evaluate_contract_compliance(contract, summary)
    assert any(m.clause_id == "ARTICULO-18" and m.is_deduction_authorized is False for m in result.matches)
    assert "5,000.00" in result.summary_legal_assessment

def test_enterprise_rag_case_004_vector_contract():
    """
    Valida el flujo RAG con ChromaDB sobre el contrato masivo de 50 cláusulas de case_004_enterprise.
    El motor debe recuperar específicamente la CLÁUSULA 37 (Política de Averías) y extraer su ID y título.
    """
    if not CASE_004_DIR.exists() or not (CASE_004_DIR / "contract.md").exists():
        pytest.skip("case_004_enterprise no disponible")
    if chromadb is None:
        pytest.skip("ChromaDB no disponible en este entorno")

    rag = ContractRAG()
    vector_contract = rag.ingest_contract_markdown("case_004_enterprise", CASE_004_DIR / "contract.md")
    assert isinstance(vector_contract, VectorContract)
    assert vector_contract.clauses_count >= 50

    summary = ReconciliationSummary(
        billed_amount=Decimal("50000.00"),
        received_amount=Decimal("42500.00"),
        difference=Decimal("-7500.00"),
        total_deductions_applied=Decimal("7500.00"),
        primary_discrepancy_type="MERCANCIA_AVERIADA",
        total_missing_amount=Decimal("0.00"),
        total_damaged_amount=Decimal("7500.00"),
        total_price_discrepancy_amount=Decimal("0.00"),
        justified_deductions_amount=Decimal("7500.00"),
        unjustified_deductions_amount=Decimal("0.00"),
        discrepancies=[],
        evidence_trail=["Caja averiada 150% penalidad"]
    )

    result = evaluate_contract_compliance(vector_contract, summary)
    assert result.contractual_justification_valid is True
    assert len(result.matches) >= 1
    match = result.matches[0]
    # Comprobar que extrajo la cláusula 37 real en vez de un ID genérico fijo
    assert "37" in match.clause_id or "37" in match.title or "Aver" in match.title
    assert match.is_deduction_authorized is True

def test_commercial_contract_rag_ingestion():
    """
    Valida la capacidad de ContractRAG para ingerir modelos CommercialContract
    directamente en ChromaDB y realizar búsquedas ricas.
    """
    if chromadb is None:
        pytest.skip("ChromaDB no disponible en este entorno")
    rag = ContractRAG()
    contract = CommercialContract(
        contract_id="CTR-RAG-TEST-099",
        vendor_id="VEND-1",
        customer_id="CUST-1",
        valid_from="2026-01-01",
        valid_to="2026-12-31",
        clauses=[
            ContractClause(
                clause_id="CLAUSE-ALPHA",
                title="Mermas y Pérdidas en Tránsito",
                text="Las mermas en tránsito superiores al 2% serán acreditadas por el transportista.",
                policy="TRANSIT_LOSS",
                tolerance_percentage=Decimal("2.00")
            ),
            ContractClause(
                clause_id="CLAUSE-BETA",
                title="Tolerancia de Empaque Secundario",
                text="El empaque secundario debe soportar 50kg de estiba sin colapsar.",
                policy="PACKAGING_STANDARD",
                tolerance_percentage=Decimal("0.00")
            )
        ]
    )

    vc = rag.ingest_commercial_contract("test_rag_ingest", contract)
    assert isinstance(vc, VectorContract)
    assert vc.clauses_count == 2

    rich_results = rag.search_clauses_rich(vc.collection_name, "mermas en tránsito pérdida transportista", n_results=1)
    assert len(rich_results) == 1
    assert rich_results[0]["clause_id"] == "CLAUSE-ALPHA"
    assert "Mermas" in rich_results[0]["title"]
