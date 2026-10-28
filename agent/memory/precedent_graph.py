"""
agent/memory/precedent_graph.py
Red de Memoria de Precedentes Comerciales & Perfiles de Retailer (Pilar 2).

Proporciona almacenamiento persistente dual (JSON y SQLite) de resoluciones
históricas, jurisprudencia interna de controversias B2B y perfiles analíticos
de comportamiento por cadena comercial (Walmart, Amazon, Soriana, Chedraui, etc.).
"""

from decimal import Decimal
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field

from data.models import DisputeAnalysisReport


class DisputePrecedentRecord(BaseModel):
    """Registro individual de un precedente comercial o resolución previa vinculante."""
    model_config = ConfigDict(extra="allow")

    precedent_id: str
    case_id: str
    date_resolved: str
    retailer_id: str
    retailer_name: str
    dispute_type: str
    deduction_code: str
    governing_clause: str
    billed_amount: Decimal
    disputed_amount: Decimal
    justified_amount: Decimal
    recovered_amount: Decimal
    outcome: str  # "WON" | "PARTIAL_CONCESSION" | "LOST"
    success_rate_ratio: float  # recovered_amount / disputed_amount
    key_evidence_cited: List[str] = Field(default_factory=list)
    binding_argument: str
    precedent_summary: str


class RetailerPrecedentProfile(BaseModel):
    """Perfil consolidado de comportamiento de cartera por retailer / cliente corporativo."""
    model_config = ConfigDict(extra="allow")

    retailer_id: str
    retailer_name: str
    rfc_or_tax_id: Optional[str] = None
    total_cases_analyzed: int = 0
    cases_won: int = 0
    cases_partial: int = 0
    cases_lost: int = 0
    overall_success_rate_pct: float = 0.0
    total_disputed_usd: Decimal = Decimal("0.00")
    total_recovered_usd: Decimal = Decimal("0.00")
    average_recovery_rate_pct: float = 0.0
    common_dispute_patterns: List[str] = Field(default_factory=list)
    precedent_ids: List[str] = Field(default_factory=list)
    last_dispute_date: Optional[str] = None


class DisputeMemoryNetwork:
    """
    Motor central de la Red de Memoria de Precedentes B2B.
    Gestiona la persistencia en JSON y base relacional SQLite, asegurando
    consultas ultrarrápidas y trazabilidad inmutable entre sesiones del agente.
    """

    DEFAULT_DATA_DIR = Path("data/memory/precedents")

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else self.DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.json_file = self.data_dir / "precedents_store.json"
        self.db_file = self.data_dir / "precedents.sqlite3"
        self._init_sqlite()

    def _init_sqlite(self) -> None:
        """Inicializa las tablas de SQLite para indexación pericial."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS precedents (
                    precedent_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    date_resolved TEXT NOT NULL,
                    retailer_id TEXT NOT NULL,
                    retailer_name TEXT NOT NULL,
                    dispute_type TEXT NOT NULL,
                    deduction_code TEXT NOT NULL,
                    governing_clause TEXT NOT NULL,
                    billed_amount TEXT NOT NULL,
                    disputed_amount TEXT NOT NULL,
                    justified_amount TEXT NOT NULL,
                    recovered_amount TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    success_rate_ratio REAL NOT NULL,
                    key_evidence_json TEXT NOT NULL,
                    binding_argument TEXT NOT NULL,
                    precedent_summary TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_precedents_retailer ON precedents(retailer_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_precedents_type ON precedents(dispute_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_precedents_code ON precedents(deduction_code)")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS retailer_profiles (
                    retailer_id TEXT PRIMARY KEY,
                    retailer_name TEXT NOT NULL,
                    rfc_or_tax_id TEXT,
                    total_cases INTEGER NOT NULL,
                    cases_won INTEGER NOT NULL,
                    cases_partial INTEGER NOT NULL,
                    cases_lost INTEGER NOT NULL,
                    success_rate_pct REAL NOT NULL,
                    total_disputed_usd TEXT NOT NULL,
                    total_recovered_usd TEXT NOT NULL,
                    avg_recovery_rate_pct REAL NOT NULL,
                    patterns_json TEXT NOT NULL,
                    last_date TEXT
                )
            """)
            conn.commit()

    def register_precedent(self, precedent: DisputePrecedentRecord) -> None:
        """Registra un precedente en SQLite y actualiza el almacenamiento JSON y el perfil."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO precedents (
                    precedent_id, case_id, date_resolved, retailer_id, retailer_name,
                    dispute_type, deduction_code, governing_clause, billed_amount,
                    disputed_amount, justified_amount, recovered_amount, outcome,
                    success_rate_ratio, key_evidence_json, binding_argument, precedent_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                precedent.precedent_id,
                precedent.case_id,
                precedent.date_resolved,
                precedent.retailer_id.upper(),
                precedent.retailer_name,
                precedent.dispute_type,
                precedent.deduction_code,
                precedent.governing_clause,
                str(precedent.billed_amount),
                str(precedent.disputed_amount),
                str(precedent.justified_amount),
                str(precedent.recovered_amount),
                precedent.outcome,
                float(precedent.success_rate_ratio),
                json.dumps(precedent.key_evidence_cited, ensure_ascii=False),
                precedent.binding_argument,
                precedent.precedent_summary
            ))
            conn.commit()

        self._recalculate_retailer_profile(precedent.retailer_id.upper(), precedent.retailer_name)
        self._sync_json_store()

    def _recalculate_retailer_profile(self, retailer_id: str, retailer_name: str) -> None:
        """Recalcula las métricas estadísticas del perfil del retailer tras un nuevo fallo."""
        precedents = self.get_precedents_by_retailer(retailer_id)
        if not precedents:
            return

        total_cases = len(precedents)
        won = sum(1 for p in precedents if p.outcome == "WON")
        partial = sum(1 for p in precedents if p.outcome == "PARTIAL_CONCESSION")
        lost = sum(1 for p in precedents if p.outcome == "LOST")

        total_disputed = sum(p.disputed_amount for p in precedents)
        total_recovered = sum(p.recovered_amount for p in precedents)

        success_rate = round(((won + partial) / total_cases) * 100.0, 2) if total_cases > 0 else 0.0
        avg_recovery = round(float((total_recovered / total_disputed) * Decimal("100.00")), 2) if total_disputed > 0 else 0.0

        # Identificar patrones comunes de discrepancia
        type_counts: Dict[str, int] = {}
        for p in precedents:
            type_counts[p.dispute_type] = type_counts.get(p.dispute_type, 0) + 1

        common_patterns = [
            f"Frecuente controversia en {dtype} ({cnt} casos registrados)"
            for dtype, cnt in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        ]

        last_date = max(p.date_resolved for p in precedents)

        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO retailer_profiles (
                    retailer_id, retailer_name, total_cases, cases_won, cases_partial,
                    cases_lost, success_rate_pct, total_disputed_usd, total_recovered_usd,
                    avg_recovery_rate_pct, patterns_json, last_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                retailer_id,
                retailer_name,
                total_cases,
                won,
                partial,
                lost,
                success_rate,
                str(total_disputed),
                str(total_recovered),
                avg_recovery,
                json.dumps(common_patterns, ensure_ascii=False),
                last_date
            ))
            conn.commit()

    def _sync_json_store(self) -> None:
        """Sincroniza la base SQLite con el archivo JSON legible para portabilidad."""
        all_precedents = self.get_all_precedents()
        data_to_save = [p.model_dump(mode="json") for p in all_precedents]
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)

    def get_all_precedents(self) -> List[DisputePrecedentRecord]:
        """Recupera la totalidad de precedentes de la red."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM precedents ORDER BY date_resolved DESC")
            rows = cursor.fetchall()

        results = []
        for r in rows:
            results.append(DisputePrecedentRecord(
                precedent_id=r[0],
                case_id=r[1],
                date_resolved=r[2],
                retailer_id=r[3],
                retailer_name=r[4],
                dispute_type=r[5],
                deduction_code=r[6],
                governing_clause=r[7],
                billed_amount=Decimal(r[8]),
                disputed_amount=Decimal(r[9]),
                justified_amount=Decimal(r[10]),
                recovered_amount=Decimal(r[11]),
                outcome=r[12],
                success_rate_ratio=r[13],
                key_evidence_cited=json.loads(r[14]),
                binding_argument=r[15],
                precedent_summary=r[16]
            ))
        return results

    def get_precedents_by_retailer(self, retailer_id: str) -> List[DisputePrecedentRecord]:
        """Filtra precedentes vinculados a un retailer específico."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM precedents WHERE UPPER(retailer_id) = ? ORDER BY date_resolved DESC", (retailer_id.upper(),))
            rows = cursor.fetchall()

        results = []
        for r in rows:
            results.append(DisputePrecedentRecord(
                precedent_id=r[0],
                case_id=r[1],
                date_resolved=r[2],
                retailer_id=r[3],
                retailer_name=r[4],
                dispute_type=r[5],
                deduction_code=r[6],
                governing_clause=r[7],
                billed_amount=Decimal(r[8]),
                disputed_amount=Decimal(r[9]),
                justified_amount=Decimal(r[10]),
                recovered_amount=Decimal(r[11]),
                outcome=r[12],
                success_rate_ratio=r[13],
                key_evidence_cited=json.loads(r[14]),
                binding_argument=r[15],
                precedent_summary=r[16]
            ))
        return results

    def get_retailer_profile(self, retailer_id: str) -> Optional[RetailerPrecedentProfile]:
        """Retorna el perfil consolidado del retailer o None si no tiene historial."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM retailer_profiles WHERE UPPER(retailer_id) = ?", (retailer_id.upper(),))
            row = cursor.fetchone()

        if not row:
            return None

        precedents = self.get_precedents_by_retailer(retailer_id)
        return RetailerPrecedentProfile(
            retailer_id=row[0],
            retailer_name=row[1],
            rfc_or_tax_id=row[2],
            total_cases_analyzed=row[3],
            cases_won=row[4],
            cases_partial=row[5],
            cases_lost=row[6],
            overall_success_rate_pct=row[7],
            total_disputed_usd=Decimal(row[8]),
            total_recovered_usd=Decimal(row[9]),
            average_recovery_rate_pct=row[10],
            common_dispute_patterns=json.loads(row[11]),
            precedent_ids=[p.precedent_id for p in precedents],
            last_dispute_date=row[12]
        )

    def get_all_retailer_profiles(self) -> List[RetailerPrecedentProfile]:
        """Retorna la lista de todos los perfiles de retailers registrados."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT retailer_id FROM retailer_profiles ORDER BY total_disputed_usd DESC")
            rows = cursor.fetchall()

        profiles = []
        for (rid,) in rows:
            prof = self.get_retailer_profile(rid)
            if prof:
                profiles.append(prof)
        return profiles

    def record_case_resolution(
        self,
        case_id: str,
        report: DisputeAnalysisReport,
        docs: Optional[Dict[str, Any]] = None,
        deduction_code: Optional[str] = None
    ) -> DisputePrecedentRecord:
        """
        Extrae y archiva de manera autónoma el precedente de un caso resuelto exitosamente.
        """
        docs = docs or {}
        inv = docs.get("invoice")
        pay = docs.get("payment")
        ctr = docs.get("contract")

        # Inferencia de Retailer
        raw_ret = getattr(inv, "customer_id", None) or "RETAIL_B2B_CORP"
        retailer_name = str(raw_ret).replace("_", " ").title()
        retailer_id = str(raw_ret).upper()

        # Inferencia de Código de Deducción y Cláusula
        code = deduction_code
        if not code and pay and hasattr(pay, "deductions") and pay.deductions:
            code = pay.deductions[0].code
        if not code:
            code = "DED-COMMERCIAL-VARIANCE"

        clause = "CTR-GENERAL-TERMS"
        if ctr and hasattr(ctr, "clauses") and ctr.clauses:
            clause = ctr.clauses[0].clause_id

        disputed = abs(report.difference)
        recovered = report.claimable_amount
        justified = report.justified_amount

        if recovered > 0 and justified == 0:
            outcome = "WON"
            ratio = 1.0
        elif recovered > 0 and justified > 0:
            outcome = "PARTIAL_CONCESSION"
            ratio = float(recovered / disputed) if disputed > 0 else 0.5
        else:
            outcome = "LOST"
            ratio = 0.0

        prec_id = f"PREC-{retailer_id[:4]}-{case_id.upper()}"
        now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        binding_arg = (
            f"En el caso {case_id}, se acreditó la improcedencia de la deducción '{code}' "
            f"conforme a {clause}, logrando la restitución de ${recovered:,.2f} USD."
        )

        prec = DisputePrecedentRecord(
            precedent_id=prec_id,
            case_id=case_id,
            date_resolved=now_date,
            retailer_id=retailer_id,
            retailer_name=retailer_name,
            dispute_type=report.root_cause[:80],
            deduction_code=code,
            governing_clause=clause,
            billed_amount=report.billed_amount,
            disputed_amount=disputed,
            justified_amount=justified,
            recovered_amount=recovered,
            outcome=outcome,
            success_rate_ratio=ratio,
            key_evidence_cited=report.evidence[:4],
            binding_argument=binding_arg,
            precedent_summary=f"Resolución {outcome}: ${recovered:,.2f} USD recuperados de ${disputed:,.2f} USD disputados."
        )

        self.register_precedent(prec)
        return prec
