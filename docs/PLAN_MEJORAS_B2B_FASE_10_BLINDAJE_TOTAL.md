# 🛡️ PLAN MAESTRO: FASE 10 — BLINDAJE TOTAL, VERDAD ÚNICA Y GRADO PRODUCCIÓN

**Proyecto:** SupplyMind AI — Autonomous B2B Revenue Recovery & Arbitration Engine
**Fase:** 10 (Tercera auditoría: consistencia entre motores, robustez del benchmark, path LLM, seguridad y operación real)
**Objetivo:** Pasar de "100% en un benchmark propio" a **cero errores demostrables** en condiciones reales: una sola fuente de verdad numérica, pruebas que no se pueden autoengañar, path LLM tan exacto como el fast-path, y todas las piezas "simuladas" claramente aisladas o reemplazadas.

---

## 🔍 1. DIAGNÓSTICO (hallazgos verificados el 2026-11-03)

### D1 — 🔴 BUG REAL: el Optimizador de Cartera cuenta casos en cuarentena
- Benchmark Crucible: reclamable total **\$400,550.00**. `WorkingCapitalPortfolioOptimizer`: **\$418,050.00**.
- Diferencia **\$17,500.00** = `case_031` (\$10,000) + `case_032` (\$4,000) + `case_033` (\$3,500), que el pipeline principal **pone en cuarentena (reclamable = \$0)** pero el optimizador sí suma.
- Impacto: el War-Room C-Level reporta capital y VaR inflados con expedientes fraudulentos/contaminados, y podría disparar `INTERRUPT_PRESCRIPTION` o `POST_ERP` sobre ellos.
- Causa raíz: cada motor (optimizer, SLA watchdog, RHI, chat, portal) **recalcula cifras por su cuenta** en vez de consumir el `DisputeAnalysisReport` canónico.

### D2 — 🔴 El benchmark puede autoengañarse
- Tolerancia `PASSED (TOL)` de **\$50** cuenta como acierto → "100% exact match" no es estrictamente exacto.
- Textos fijos en el panel: `"(0 discrepancias)"` y `"0.00% Alucinación"` se imprimen **sin medirse**.
- `arithmetic_error_rate_pct` guarda el **conteo** de errores, no un porcentaje.
- Solo se ejecuta `fast_path=True, use_cache=True` → la caché puede ocultar regresiones y el **path LLM/ReAct nunca se evalúa**.
- Los 50 casos fueron generados por el mismo equipo que escribió las reglas → riesgo de *overfitting*.

### D3 — 🟠 Cifras desalineadas entre motores (sin contrato de consistencia)
- No hay una prueba que garantice que chat, optimizer, portal RPA, courtroom, ERP y reporte digan **el mismo número** para el mismo caso.

### D4 — 🟠 Rendimiento: OCR bloqueante
- `case_008_homedepot_damaged_scanned` tarda **~30 s** (OCR sincrónico) vs ~0.5 s del resto; promedio de 1.8 s/caso inflado. Sin timeout ni caché por hash de archivo.

### D5 — 🟠 Piezas simuladas sin aislamiento explícito
- `cfdi_pac_simulator.py` (firma CSD simulada), `bank_reconciliation.py` (sello Banxico simulado con SHA-256), `skynet_runner.py:1553` ("Respuesta simulada local"). Riesgo de que un documento simulado se confunda con uno válido fiscalmente.

### D6 — 🟠 Higiene del repositorio
- Cada ejecución reescribe ~150 archivos en `reports/`, `data/vector_db/`, `data/memory/*.sqlite3` → ruido en git y estado no reproducible.
- Varios archivos de fases 7–8 siguen **sin commitear** (`capa_ticket_generator.py`, `remittance.py`, `ClosurePreventionView.jsx`, tests de fase 7 y 8, cambios en `skynet_runner.py`, `data/models.py`, `api/main.py`, frontend).

### D7 — 🟡 Seguridad y producción
- Sin autenticación/autorización por tenant en `api/routes/*` (batch execute-action puede contabilizar ERP masivamente).
- Sin idempotencia en acciones batch (doble clic = doble póliza / doble aviso).
- Sin rastro de auditoría inmutable de quién ejecutó qué acción.

### D8 — 🟡 Cobertura de casos de negocio faltantes
- Multi-moneda real con FX histórico por fecha de factura; notas de crédito parciales; pagos parciales en varias remesas; disputas que cruzan varias facturas/POs; devoluciones posteriores al pago; contracargos revertidos por el retailer.

---

## 🚀 2. PLAN DE EJECUCIÓN — 6 SPRINTS

### 🧱 SPRINT 10.1 — Fuente Única de Verdad (corrige D1, D3)
- **HU 10.1.1 `CaseLedger` canónico** (`agent/core/case_ledger.py`): una función `get_canonical_case(case_id)` que ejecuta/cachea el `DisputeAnalysisReport` y expone `claimable`, `justified`, `quarantined`, `currency`. Todos los motores la consumen.
- **HU 10.1.2 Optimizer respeta cuarentena:** casos en cuarentena → `claimable=0`, `action_type="FORENSIC_REVIEW"`, excluidos de VaR y de acciones batch.
- **HU 10.1.3 Guardas en batch:** `execute_batch_action` rechaza casos en cuarentena o con `irrefutability_grade` bajo.
- **Criterio de aceptación:** reclamable del optimizer == benchmark (\$400,550.00) al centavo; test que falla si difieren.

### 🧪 SPRINT 10.2 — Benchmark Honesto e Inviolable (corrige D2)
- Eliminar tolerancia: solo `PASSED` si error == \$0.00; mostrar `PASSED_TOL` aparte como fallo.
- Medir de verdad: error aritmético %, alucinación (vía `ZKPFinancialAuditor` sobre el texto del dictamen), citas válidas.
- Ejecutar en 3 modos: `fast_path+cache`, `fast_path sin caché`, `ReAct/LLM` (con presupuesto).
- **Holdout ciego:** 20 casos nuevos generados por un generador distinto (`scripts/generate_holdout_cases.py`) con semillas aleatorias, nunca usados para ajustar reglas.
- **Pruebas de propiedad (Hypothesis):** para cualquier caso sintético, `justified + claimable == |difference|`, montos ≥ 0, cuarentena ⇒ 0.
- Gate de CI: el benchmark falla el build si cualquier métrica baja.

### 🔗 SPRINT 10.3 — Contrato de Consistencia Cross-Motor (corrige D3)
- `tests/test_cross_engine_consistency.py`: para los 50 casos, comparar el monto reclamable reportado por reporte, chat determinístico, optimizer, portal RPA, courtroom, ERP (total póliza) y CFDI (total XML). Todos deben coincidir.
- Validar que las 18 herramientas ReAct devuelven esquemas válidos con entradas límite (caso inexistente, montos 0, moneda desconocida).

### ⚡ SPRINT 10.4 — Rendimiento y Resiliencia (corrige D4)
- Caché OCR por SHA-256 del archivo; OCR en hilo con timeout (p.ej. 15 s) y degradación controlada.
- Objetivo: **p95 < 1 s/caso** en fast-path sin caché de reportes; benchmark de 50 casos < 30 s.
- Reintentos con backoff y *circuit breaker* para llamadas LLM; fallback determinístico garantizado.

### 🔐 SPRINT 10.5 — Seguridad, Idempotencia y Auditoría (corrige D5, D7)
- Autenticación (API key / JWT) y scoping por tenant en todas las rutas mutables.
- `Idempotency-Key` en `POST /api/batch/execute-action` y endpoints ERP/CFDI.
- Bitácora inmutable encadenada por hash (`audit_log`) de cada acción ejecutada.
- Marcar todo artefacto simulado con `is_simulated=True` + marca de agua "SIN VALIDEZ FISCAL"; interfaz `PacProvider` lista para un PAC real.

### 💼 SPRINT 10.6 — Cobertura de Negocio Faltante + Higiene (corrige D6, D8)
- FX histórico por fecha (tabla Banxico FIX), pagos parciales multi-remesa, disputas multi-factura/multi-PO, devoluciones post-pago, contracargos revertidos. Un caso de prueba con ground truth por cada uno (casos 051–060).
- Mover salidas generadas a `reports/runs/<timestamp>/` y añadir `data/vector_db/`, `*.sqlite3` y reportes generados a `.gitignore`.
- Commitear o descartar el trabajo pendiente de fases 7–8 en commits atómicos.

---

## ✅ 3. DEFINICIÓN DE "CERO ERRORES" (criterios de salida de la Fase 10)

| Criterio | Meta |
| :--- | :--- |
| Exact match estricto (sin tolerancia) — 50 casos + 10 nuevos | 100% |
| Exact match en holdout ciego de 20 casos | ≥ 95%, fallos documentados con causa raíz |
| Exact match en modo ReAct/LLM | 100% de montos (texto puede variar) |
| Consistencia cross-motor | 100% de coincidencia al centavo |
| Alucinación medida (ZKP) | 0 cifras no ancladas |
| Cuarentena | 100% y 0 acciones batch sobre casos en cuarentena |
| Latencia fast-path sin caché | p95 < 1 s |
| Suite pytest completa | 100% verde en CI |
| Acciones batch | idempotentes y auditadas |

## 📌 4. ORDEN RECOMENDADO
10.1 → 10.2 → 10.3 (corrección y verdad) → 10.4 → 10.5 → 10.6. Los sprints 10.1 y 10.2 son bloqueantes: sin ellos cualquier "100%" posterior no es confiable.
