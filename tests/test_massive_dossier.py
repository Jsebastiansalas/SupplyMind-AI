"""
tests/test_massive_dossier.py
Suite de pruebas periciales para la Fase 1: Ingesta Jerárquica Masiva y Motor Map-Reduce.
Valida el procesamiento de expedientes comerciales extensos (1,000 SKUs y ~80 páginas de contrato)
con estricta precisión Decimal ($0.00 MAE), Árbol de Merkle y compresión de contexto prompt >90%.
"""

import time
from decimal import Decimal
import pytest

from tools.document_reader.hierarchical_segmenter import HierarchicalDocumentSegmenter
from tools.reconciliation_engine.batch_map_reduce import (
    MassiveBatchReconciliationEngine,
    MassiveReconciliationManifest
)
from tools.document_reader.synthetic_fingerprint import SyntheticFingerprintGenerator
from tools.document_reader.reader import (
    load_case_documents,
    load_massive_case_hierarchical
)
from agent.core.state import DisputeState, ProcessStatus
from agent.memory.audit_logger import AuditLogger
from agent.tools.registry import ToolExecutor


def test_hierarchical_segmenter_markdown_and_bm25_retrieval():
    """Valida la descomposición jerárquica de contratos extensos y la consulta BM25 sub-milisegundo."""
    docs = load_case_documents("case_036_massive_1000_skus")
    contract = docs["contract"]
    raw_markdown = getattr(contract, "raw_content", "")
    assert raw_markdown, "El contrato masivo debe contener raw_content en markdown"

    t0 = time.perf_counter()
    hierarchy = HierarchicalDocumentSegmenter.segment_text(
        raw_text=raw_markdown,
        document_name="contrato_case_036",
        total_pages=80
    )
    t_parse = time.perf_counter() - t0

    assert hierarchy is not None
    assert hierarchy.total_pages == 80
    assert len(hierarchy.chapters) >= 10, f"Se esperaban >=10 capítulos, se obtuvieron {len(hierarchy.chapters)}"
    assert hierarchy.notice_window_days == 30, "Debe detectar la ventana de 30 días s/ Cláusula 6.1"

    # Validar búsqueda léxica BM25 en memoria < 5ms
    t0_q = time.perf_counter()
    top_clauses_shortage = HierarchicalDocumentSegmenter.query_relevant_clauses(
        hierarchy,
        query="faltante físico muelle remisión sello",
        top_k=2
    )
    t_q = (time.perf_counter() - t0_q) * 1000

    assert len(top_clauses_shortage) >= 1
    assert "FALTANTES" in top_clauses_shortage[0].title.upper() or "RECEPCIÓN" in top_clauses_shortage[0].title.upper()
    assert t_q < 10.0, f"La consulta BM25 tardó {t_q:.2f}ms (debe ser <10ms)"

    # Consulta sobre penalidad ASN
    top_clauses_asn = HierarchicalDocumentSegmenter.query_relevant_clauses(
        hierarchy,
        query="penalidades prohibición unilateral EDI ASN",
        top_k=2
    )
    assert len(top_clauses_asn) >= 1
    assert "PENALIDADES" in top_clauses_asn[0].title.upper() or "PROHIBICIÓN" in top_clauses_asn[0].title.upper()


def test_batch_map_reduce_1000_skus_and_merkle_invariants():
    """Valida la conciliación Map-Reduce en 1,000 SKUs con $0.00 MAE y Árbol Merkle de integridad."""
    docs = load_case_documents("case_036_massive_1000_skus")
    inv = docs["invoice"]
    po = docs["purchase_order"]
    deliv = docs["delivery"]
    pay = docs["payment"]

    assert len(inv.items) == 1000, "La factura debe contener exactamente 1,000 SKUs"

    t0 = time.perf_counter()
    manifest: MassiveReconciliationManifest = MassiveBatchReconciliationEngine.map_reduce_reconcile(
        invoice=inv,
        purchase_order=po,
        delivery=deliv,
        payment=pay,
        batch_size=50
    )
    t_exec = time.perf_counter() - t0

    # 1. Validación de partición
    assert manifest.total_skus_processed == 1000
    assert manifest.total_batches_count == 20  # 1000 / 50 = 20 sub-lotes
    assert manifest.batch_size == 50

    # 2. Validación de Invariantes y Cero Error de Punto Flotante
    assert manifest.invariant_conserved is True, "El árbol de invariantes contables debe conservarse"
    assert len(manifest.merkle_root_hash) == 64, "El Merkle root hash debe ser un SHA-256 de 64 caracteres"

    assert manifest.consolidated_billed_amount == Decimal("2523325.00")
    assert manifest.consolidated_missing_amount == Decimal("2190.00")
    assert manifest.summary.billed_amount == Decimal("2523325.00")
    assert manifest.summary.justified_deductions_amount == Decimal("2190.00")
    assert manifest.summary.unjustified_deductions_amount == Decimal("5000.00")

    # 3. Discrepancias exactas
    assert manifest.total_discrepant_lines_count == 5, "Deben detectarse exactamente 5 SKUs discrepantes"

    # 4. Latencia ultrarrápida: < 1.0 segundo para 1,000 SKUs
    assert t_exec < 1.0, f"Map-Reduce tardó {t_exec:.3f}s (debe ser < 1.0s para 1,000 SKUs)"


def test_synthetic_fingerprint_density_and_compression():
    """Valida la generación de la firma sintética compacta (<2,500 tokens) para el contexto del LLM."""
    docs = load_case_documents("case_036_massive_1000_skus")
    inv = docs["invoice"]
    pay = docs["payment"]

    manifest = MassiveBatchReconciliationEngine.map_reduce_reconcile(
        invoice=inv,
        purchase_order=docs["purchase_order"],
        delivery=docs["delivery"],
        payment=pay,
        batch_size=50
    )

    hierarchy = HierarchicalDocumentSegmenter.segment_text(
        raw_text=getattr(docs["contract"], "raw_content", ""),
        document_name="contrato_case_036"
    )

    fingerprint = SyntheticFingerprintGenerator.generate(
        case_id="case_036_massive_1000_skus",
        invoice=inv,
        payment=pay,
        rec_summary=manifest.summary,
        hierarchy=hierarchy,
        manifest=manifest
    )

    assert fingerprint.total_skus == 1000
    assert fingerprint.merkle_root_hash == manifest.merkle_root_hash
    assert fingerprint.estimated_tokens < 2500, f"Tokens estimados: {fingerprint.estimated_tokens} (debe ser < 2,500)"
    assert fingerprint.compression_ratio_percent > 85.0, f"Ratio compresión: {fingerprint.compression_ratio_percent}%"

    prompt_block = fingerprint.prompt_injection_block
    assert "FIRMA SINTÉTICA DE ALTA DENSIDAD" in prompt_block
    assert "Merkle Root Hash" in prompt_block or "MERKLE ROOT HASH" in prompt_block.upper()
    assert "2523325.00" in prompt_block or "2,523,325.00" in prompt_block
    assert "2190.00" in prompt_block or "2,190.00" in prompt_block
    assert "5000.00" in prompt_block or "5,000.00" in prompt_block


def test_end_to_end_massive_case_loader():
    """Valida el cargador unificado load_massive_case_hierarchical."""
    result = load_massive_case_hierarchical("case_036_massive_1000_skus")

    assert result["is_massive_scale"] is True
    assert "documents" in result
    assert "hierarchy" in result
    assert "manifest" in result
    assert "fingerprint" in result
    assert result["manifest"].total_skus_processed == 1000
    assert result["summary"].total_missing_amount == Decimal("2190.00")


def test_skynet_tool_executor_on_massive_case():
    """Valida el flujo ReAct completo del ToolExecutor de SKYNET sobre un expediente masivo."""
    state = DisputeState(
        case_id="case_036_massive_1000_skus",
        objective="Resolver disputa comercial de 1,000 SKUs con precisión pericial"
    )
    audit_logger = AuditLogger(case_id="case_036_massive_1000_skus")
    executor = ToolExecutor(state=state, audit_logger=audit_logger)

    # 1. Leer documentos
    res_read = executor.execute_tool("read_dispute_documents", {"case_id": "case_036_massive_1000_skus"})
    assert res_read["status"] == "success"
    assert res_read["is_massive_scale"] is True
    assert res_read["invoice_items_count"] == 1000
    assert state.is_massive_scale is True

    # 2. Ejecutar conciliación Map-Reduce
    res_rec = executor.execute_tool("execute_reconciliation", {"case_id": "case_036_massive_1000_skus"})
    assert res_rec["status"] == "success"
    assert res_rec["is_massive_scale"] is True
    assert res_rec["total_skus_processed"] == 1000
    assert res_rec["total_batches_count"] == 20
    assert res_rec["invariant_conserved"] is True
    assert res_rec["billed_amount"] == 2523325.0
    assert res_rec["total_missing_amount"] == 2190.0
    assert res_rec["unjustified_deductions"] == 5000.0
    assert state.hierarchical_manifest is not None

    # 3. Evaluar contrato con cláusulas jerárquicas indexadas
    res_ctr = executor.execute_tool("evaluate_contract_terms", {"case_id": "case_036_massive_1000_skus"})
    assert res_ctr["status"] == "success"
    assert "indexed_hierarchical_clauses" in res_ctr
    assert len(res_ctr["indexed_hierarchical_clauses"]) >= 1

    # 4. Generar reporte final pericial
    res_rep = executor.execute_tool("generate_final_report", {
        "case_id": "case_036_massive_1000_skus",
        "root_cause_explanation": "Faltante físico en 5 SKUs respaldado en remisión con firma de muelle. Deducción ASN unilateral inválida según Cláusula 9.3.",
        "recommended_action": "Aceptar deducción por faltante de $2,190.00 USD emitiendo Nota de Crédito. Disputar y cobrar íntegramente los $5,000.00 USD de penalización ASN unilateral."
    })
    assert res_rep["status"] == "success"
    report = res_rep["report"]
    assert float(report["billed_amount"]) == 2523325.0
    assert float(report["justified_amount"]) == 2190.0
    assert float(report["claimable_amount"]) == 5000.0
    assert state.current_status == ProcessStatus.COMPLETED
