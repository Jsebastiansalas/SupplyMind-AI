# Plan de Implementación: Sprint 6.2 — Matriz de Delegación Financiera & Dualidad de Gobernanza

## Resumen Ejecutivo
Implementación del marco de gobernanza financiera y jurídica vinculante de SupplyMind AI. Permite a los directores financieros (CFO) establecer una Matriz de Delegación con límites infranqueables por nivel de cuenta (Tier 1 Estratégica, Tier 2 Regular, Tier 3 Alto Riesgo), reglas de reciprocidad comercial obligatoria (exención de multas futuras por pronto acuerdo), umbrales de forzado a Human Gatekeeper para disputas de alto volumen y generación de convenios de finiquito mercantil certificados con sellos criptográficos ZKP SHA-256.

---

## Decisiones de Arquitectura
1. **Matriz Jerárquica de Delegación:**
   - `TIER_1_STRATEGIC`: Hasta 50% de concesión de lo reclamable si hay compromiso de volumen o exención de multas.
   - `TIER_2_REGULAR`: Hasta 25% de concesión máxima.
   - `TIER_3_HIGH_RISK`: 0% de concesión (Cobro íntegro estricto sin tolerancia).
   - Umbral de Salvaguarda: Disputas > $10,000 USD activan obligatoriamente el modo `HUMAN_GATEKEEPER` para requerir rúbrica del CFO.
2. **Reciprocidad Comercial Vinculante:** Ninguna concesión económica se otorga de forma unilateral. El convenio exige automáticamente al comprador:
   - Compromiso de pago bancario en menos de 5 días hábiles.
   - Cláusula de no-penalización logística por 2 pedidos consecutivos.
   - Eliminación de cargos de reprogramación en muelle.
3. **Finiquito Legal Mercantil Certificado:**
   - Redacción formal conforme a los Artículos 2944 y 2953 del Código Civil y Art. 1054 del Código de Comercio (autoridad de cosa juzgada entre las partes).
   - Sello criptográfico SHA-256 HMAC inmutable que une el folio, las partes, los montos y la fecha UTC.
4. **API REST y Gobernanza Dinámica:**
   - Endpoints para consultar/calibrar la matriz de delegación y conmutar el modo operativo del expediente en caliente.

---

## Task List & Checkpoints

### Fase 1: Modelos de Gobernanza y Matriz de Delegación
- [x] **Task 6.2.1:** Esquemas Pydantic V2 en `data/models.py` (`DelegationTierPolicy`, `FinancialDelegationMatrix`, `SettlementAgreementDetails`).
- [x] **Task 6.2.2:** Motor de Gobernanza en `agent/core/delegation_matrix_engine.py` (auditoría de límites, forzado automático de Gatekeeper para casos > $10,000 USD, inyección de reciprocidad).

### Checkpoint: Motor de Gobernanza
- [x] Validar que ninguna concesión viole los topes de la matriz y que el forzado de Gatekeeper opere en casos de alto valor.

### Fase 2: Redacción y Certificación de Convenios Mercantiles
- [x] **Task 6.2.3:** Generador de Convenios y Minutas Formales en `agent/core/settlement_agreement_generator.py` con cláusulas de cosa juzgada, reciprocidad comercial y sellos ZKP.
- [x] **Task 6.2.4:** Integrar el validador de gobernanza y generador de convenios en `agent/core/bilateral_negotiation_engine.py`.

### Checkpoint: Generador de Convenios
- [x] Validar generación de convenios certificados con hash SHA-256 e invariantes contables $0.00 MAE.

### Fase 3: Endpoints REST y Tests Automatizados
- [x] **Task 6.2.5:** Endpoints REST en `api/routes/negotiation.py` (`GET/POST /api/negotiation/delegation-matrix`, `POST /api/cases/{case_id}/negotiation/duel/governance`, `GET /api/cases/{case_id}/negotiation/duel/minutes`).
- [x] **Task 6.2.6:** Suite completa de tests en `tests/test_delegation_matrix.py` (100% passing).

### Checkpoint Final Sprint 6.2
- [x] Tests en verde, servidor API activo y actualización de documentación maestra.
