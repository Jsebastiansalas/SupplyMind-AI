"""
tools/batch_processor/batch_audit_sealer.py
Sellador Criptográfico e Inmutabilidad Forense de Bitácoras (SHA-256 Hash Chain + Merkle Root).

Certifica ante evaluadores y auditores que los registros de la jornada desatendida:
1. Mantienen integridad criptográfica secuencial (Hash Chain ininterrumpida desde el bloque génesis).
2. Poseen una raíz de Merkle (Merkle Root SHA-256) verificable sobre el total de unidades.
3. Cumplen al 100% el invariante contable estricto ($0.00 MAE) sin alteración manual.
4. Vinculan las sumas de verificación SHA-256 de los archivos físicos CSV, JSON y JSONL en disco.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


GENESIS_HASH = "0" * 64


@dataclass
class TaskHashEntry:
    """Entrada individual en la cadena de bloques de auditoría del lote."""
    unit_index: int
    task_id: str
    case_id: str
    status: str
    disputed_amount: float
    recovered_amount: float
    cost_usd: float
    record_hash: str
    previous_chain_hash: str
    chain_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BatchIntegrityVerificationResult:
    """Resultado de la auditoría de verificación criptográfica y contable del lote."""
    is_valid: bool
    total_records_verified: int
    merkle_root_expected: str
    merkle_root_computed: str
    tip_chain_hash_expected: str
    tip_chain_hash_computed: str
    mae_zero_invariant_passed: bool
    files_digest_passed: bool
    tampered_tasks: List[str]
    file_mismatches: List[str]
    verification_timestamp: str
    summary_message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BatchAuditSealer:
    """
    Motor de sellado criptográfico SHA-256 y verificación de integridad para la bitácora de carga.
    """

    CANONICAL_FIELDS = [
        "unit_index",
        "task_id",
        "case_id",
        "source_origin",
        "retailer_id",
        "category",
        "status",
        "billed_amount",
        "received_amount",
        "disputed_amount",
        "recovered_amount",
        "justified_amount",
        "financial_delta",
        "tokens_prompt",
        "tokens_completion",
        "tokens_total",
        "cost_usd",
    ]

    def __init__(self, reports_dir: Optional[Path] = None):
        self.workspace_root = Path(__file__).resolve().parent.parent.parent
        self.reports_dir = reports_dir or (self.workspace_root / "reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.manifest_json_path = self.reports_dir / "unattended_batch_audit_manifest.json"
        self.manifest_sha256_path = self.reports_dir / "unattended_batch_audit_manifest.sha256"

    @classmethod
    def compute_record_hash(cls, record: Dict[str, Any]) -> str:
        """Calcula el hash SHA-256 canónico de una unidad de trabajo."""
        canonical_payload: Dict[str, Any] = {}
        for field in cls.CANONICAL_FIELDS:
            val = record.get(field)
            if isinstance(val, float):
                # Normalizar flotantes a 6 decimales para determinismo entre plataformas
                canonical_payload[field] = f"{val:.6f}"
            elif isinstance(val, Decimal):
                canonical_payload[field] = f"{float(val):.6f}"
            else:
                canonical_payload[field] = val

        serialized = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_chain_step(prev_chain_hash: str, record_hash: str) -> str:
        """Calcula el eslabón de la cadena de hashes: SHA256(prev_chain_hash + ':' + record_hash)."""
        combined = f"{prev_chain_hash}:{record_hash}".encode("utf-8")
        return hashlib.sha256(combined).hexdigest()

    @staticmethod
    def compute_merkle_root(hashes: List[str]) -> str:
        """Calcula la raíz del árbol de Merkle binario SHA-256 sobre la lista de hashes."""
        if not hashes:
            return GENESIS_HASH

        current_layer = list(hashes)
        while len(current_layer) > 1:
            next_layer: List[str] = []
            for i in range(0, len(current_layer), 2):
                left = current_layer[i]
                right = current_layer[i + 1] if (i + 1) < len(current_layer) else left
                combined = hashlib.sha256(f"{left}:{right}".encode("utf-8")).hexdigest()
                next_layer.append(combined)
            current_layer = next_layer

        return current_layer[0]

    @staticmethod
    def compute_file_sha256(file_path: Path) -> Optional[str]:
        """Calcula el digest SHA-256 del contenido binario de un archivo en disco."""
        if not file_path.exists() or not file_path.is_file():
            return None
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def seal_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Genera el manifiesto criptográfico completo para una lista de registros de ejecución
        y guarda tanto el JSON estructurado como el archivo .sha256 en disco.
        """
        chain_entries: List[TaskHashEntry] = []
        record_hashes: List[str] = []
        prev_hash = GENESIS_HASH
        mae_violations = 0

        for r in records:
            rec_hash = self.compute_record_hash(r)
            record_hashes.append(rec_hash)
            curr_chain_hash = self.compute_chain_step(prev_hash, rec_hash)

            billed = Decimal(str(round(float(r.get("billed_amount", 0.0)), 2)))
            received = Decimal(str(round(float(r.get("received_amount", 0.0)), 2)))
            recovered = Decimal(str(round(float(r.get("recovered_amount", 0.0)), 2)))
            justified = Decimal(str(round(float(r.get("justified_amount", 0.0)), 2)))
            if abs(billed - (received + recovered + justified)) > Decimal("0.01"):
                mae_violations += 1

            entry = TaskHashEntry(
                unit_index=int(r.get("unit_index", 0)),
                task_id=str(r.get("task_id", "")),
                case_id=str(r.get("case_id", "")),
                status=str(r.get("status", "UNKNOWN")),
                disputed_amount=float(r.get("disputed_amount", 0.0)),
                recovered_amount=float(r.get("recovered_amount", 0.0)),
                cost_usd=float(r.get("cost_usd", 0.0)),
                record_hash=rec_hash,
                previous_chain_hash=prev_hash,
                chain_hash=curr_chain_hash,
            )
            chain_entries.append(entry)
            prev_hash = curr_chain_hash

        merkle_root = self.compute_merkle_root(record_hashes)
        tip_chain_hash = prev_hash

        # Calcular digests de archivos de bitácora si existen
        tracked_files = [
            "unattended_batch_execution_log.csv",
            "unattended_batch_execution_log.json",
            "unattended_batch_execution_stream.jsonl",
            "unattended_batch_executive_summary.md",
            "work_unit_queue_manifest_1024.json",
        ]
        file_digests: Dict[str, str] = {}
        for fname in tracked_files:
            fpath = self.reports_dir / fname
            digest = self.compute_file_sha256(fpath)
            if digest:
                file_digests[fname] = digest

        manifest_data = {
            "seal_metadata": {
                "sealed_at": datetime.now(timezone.utc).isoformat(),
                "algorithm": "SHA-256 (Sequential Hash Chain + Binary Merkle Tree)",
                "total_units_sealed": len(records),
                "genesis_hash": GENESIS_HASH,
                "tip_chain_hash": tip_chain_hash,
                "merkle_root": merkle_root,
                "mae_zero_invariant_verified": (mae_violations == 0),
                "mae_violations_count": mae_violations,
            },
            "file_digests": file_digests,
            "hash_chain": [e.to_dict() for e in chain_entries],
        }

        with open(self.manifest_json_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)

        # Generar archivo .sha256 estándar compatible con herramientas de auditoría
        sha_lines = [
            f"# SupplyMind AI - Cryptographic Audit Seal (SHA-256)",
            f"# Sealed At: {manifest_data['seal_metadata']['sealed_at']}",
            f"# Total Units Sealed: {len(records)}",
            f"# Merkle Root: {merkle_root}",
            f"# Tip Chain Hash: {tip_chain_hash}",
            f"# Financial Invariant ($0.00 MAE): {'VERIFIED' if mae_violations == 0 else 'VIOLATION'}",
            "",
        ]
        for fname, digest in file_digests.items():
            sha_lines.append(f"{digest}  {fname}")

        with open(self.manifest_sha256_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sha_lines) + "\n")

        return {
            "manifest_json": str(self.manifest_json_path),
            "manifest_sha256": str(self.manifest_sha256_path),
            "merkle_root": merkle_root,
            "tip_chain_hash": tip_chain_hash,
            "total_units_sealed": len(records),
        }

    def verify_batch_integrity(
        self,
        records: Optional[List[Dict[str, Any]]] = None,
    ) -> BatchIntegrityVerificationResult:
        """
        Audita y verifica criptográficamente que ni la bitácora ni los archivos hayan sido alterados.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        if not self.manifest_json_path.exists():
            return BatchIntegrityVerificationResult(
                is_valid=False,
                total_records_verified=0,
                merkle_root_expected="MISSING",
                merkle_root_computed="NONE",
                tip_chain_hash_expected="MISSING",
                tip_chain_hash_computed="NONE",
                mae_zero_invariant_passed=False,
                files_digest_passed=False,
                tampered_tasks=[],
                file_mismatches=["unattended_batch_audit_manifest.json no encontrado"],
                verification_timestamp=now_iso,
                summary_message="Manifiesto criptográfico no encontrado en disco.",
            )

        with open(self.manifest_json_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        meta = manifest.get("seal_metadata", {})
        expected_merkle = meta.get("merkle_root", "")
        expected_tip = meta.get("tip_chain_hash", "")
        stored_chain = manifest.get("hash_chain", [])
        expected_files = manifest.get("file_digests", {})

        # Cargar registros desde log JSON si no se pasaron explícitamente
        if records is None:
            json_log_path = self.reports_dir / "unattended_batch_execution_log.json"
            stream_path = self.reports_dir / "unattended_batch_execution_stream.jsonl"
            records = []
            if json_log_path.exists():
                with open(json_log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    records = data.get("records", [])
            elif stream_path.exists():
                with open(stream_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            records.append(json.loads(line))

        tampered_tasks: List[str] = []
        computed_record_hashes: List[str] = []
        prev_hash = GENESIS_HASH
        mae_ok = True

        # Mapear chain guardada por task_id
        stored_by_task = {item["task_id"]: item for item in stored_chain}

        for r in records:
            tid = str(r.get("task_id", ""))
            rec_hash = self.compute_record_hash(r)
            computed_record_hashes.append(rec_hash)
            curr_chain = self.compute_chain_step(prev_hash, rec_hash)

            # Validar contra entrada sellada
            stored_entry = stored_by_task.get(tid)
            if not stored_entry:
                tampered_tasks.append(f"{tid} (registro no sellado)")
            elif stored_entry.get("record_hash") != rec_hash or stored_entry.get("chain_hash") != curr_chain:
                tampered_tasks.append(tid)

            # Validar invariante financiero
            billed = Decimal(str(round(float(r.get("billed_amount", 0.0)), 2)))
            received = Decimal(str(round(float(r.get("received_amount", 0.0)), 2)))
            recovered = Decimal(str(round(float(r.get("recovered_amount", 0.0)), 2)))
            justified = Decimal(str(round(float(r.get("justified_amount", 0.0)), 2)))
            if abs(billed - (received + recovered + justified)) > Decimal("0.01"):
                mae_ok = False
                if tid not in tampered_tasks:
                    tampered_tasks.append(f"{tid} (violación MAE)")

            prev_hash = curr_chain

        computed_merkle = self.compute_merkle_root(computed_record_hashes)
        computed_tip = prev_hash

        # Verificar digests de archivos físicos
        file_mismatches: List[str] = []
        for fname, exp_digest in expected_files.items():
            fpath = self.reports_dir / fname
            actual_digest = self.compute_file_sha256(fpath)
            if actual_digest != exp_digest:
                file_mismatches.append(fname)

        files_ok = len(file_mismatches) == 0
        merkle_ok = (computed_merkle == expected_merkle)
        tip_ok = (computed_tip == expected_tip)
        count_ok = (len(records) == meta.get("total_units_sealed", 0))

        is_valid = (
            merkle_ok
            and tip_ok
            and count_ok
            and mae_ok
            and files_ok
            and len(tampered_tasks) == 0
        )

        if is_valid:
            msg = (
                f"INTEGRIDAD CRIPTOGRÁFICA VERIFICADA: {len(records):,} unidades intactas, "
                f"Merkle Root {computed_merkle[:16]}... válida y $0.00 MAE confirmado."
            )
        else:
            msg = (
                f"ALERTA DE INTEGRIDAD: Merkle={'OK' if merkle_ok else 'MISMATCH'}, "
                f"Tareas alteradas={len(tampered_tasks)}, Archivos modificados={len(file_mismatches)}."
            )

        return BatchIntegrityVerificationResult(
            is_valid=is_valid,
            total_records_verified=len(records),
            merkle_root_expected=expected_merkle,
            merkle_root_computed=computed_merkle,
            tip_chain_hash_expected=expected_tip,
            tip_chain_hash_computed=computed_tip,
            mae_zero_invariant_passed=mae_ok,
            files_digest_passed=files_ok,
            tampered_tasks=tampered_tasks,
            file_mismatches=file_mismatches,
            verification_timestamp=now_iso,
            summary_message=msg,
        )
