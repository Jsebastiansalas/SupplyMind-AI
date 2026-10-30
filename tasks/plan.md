# Plan de Implementación: Sprint 6.3 — Despachador Robótico a Portales B2B (Retail Link, Vendor Central, Soriana, Liverpool)

## Resumen Ejecutivo
Implementación del Despachador Robótico y Automatización de Radicación B2B de SupplyMind AI. Permite generar automáticamente un expediente probatorio pericial consolidado (CFDI 4.0, remisión sellada, ASN EDI 856, EDI 997, C-TPAT y Convenio de Finiquito ZKP) y radicar formalmente la controversia en los 4 grandes portales comerciales retail (Walmart Retail Link / Luminate, Amazon Vendor Central, Soriana B2B y Liverpool Partners), obteniendo un folio oficial de ticket y bitácora auditable de radicación.

---

## Decisiones de Arquitectura
1. **Empaquetador Forense de Evidencias (Dossier Generator):**
   - Agrupa los documentos del expediente con comprobación de integridad SHA-256.
   - Genera un archivo manifest JSON normalizado con rutas relativas, hashes y metadatos periciales.
2. **Adaptadores Específicos por Portal:**
   - `WALMART_RETAIL_LINK`: Mapea códigos de deducción (Claim Codes 21, 22, 24, 86 OTIF), DC Number, PO Number y telemetría de cita.
   - `AMAZON_VENDOR_CENTRAL`: Mapea AP Claims Engine (SHORTAGE_FC, FREIGHT_VARIANCE, ON_TIME_COMPLIANCE), código de estación/FC Dock (DAL3, PHX6), BOL y EDI 856.
   - `SORIANA_B2B`: Mapea Folio de Contra-recibo, Clave Tienda/CEDIS, Deducción de Merma/Comercial y Timbre SAT UUID.
   - `LIVERPOOL_B2B`: Mapea Pedido B2B, Folio de Cita en Patio, Remisión física sellada y Factura fiscal.
3. **Máquina de Estados de Radicación:**
   - `PREPARING_DOSSIER` -> `AUTHENTICATING_SSO` -> `UPLOADING_EVIDENCE_BUNDLE` -> `VALIDATING_CLAIM_PAYLOAD` -> `DISPATCHED_CONFIRMED` / `PORTAL_ERROR_RETRY`.
   - Generación de tickets auditables (ej: `WLMT-TK-2026-XXXX`, `AMZN-CASE-2026-XXXX`).
4. **API REST y Vinculación con Mesa de Negociación:**
   - Endpoints para generar el dossier, radicar la disputa y consultar el recibo y bitácora de eventos.
   - Conexión opcional post-convenio: una vez que el acuerdo o impasse se formaliza, el caso queda listo para despacho en 1 clic.

---

## Task List & Checkpoints

### Fase 1: Modelos Pydantic del Despachador Robótico
- [x] **Task 6.3.1:** Modelos en `data/models.py` (`PortalEvidenceManifestItem`, `PortalDispatchDossier`, `PortalAdapterPayload`, `PortalDispatchReceipt`).

### Fase 2: Empaquetador Forense y Adaptadores de Portales
- [x] **Task 6.3.2:** Empaquetador y adaptadores en `agent/portal/portal_dispatcher_engine.py` para Walmart, Amazon, Soriana y Liverpool.

### Checkpoint: Empaquetador y Adaptadores
- [x] Validar generación de dossier con hashes SHA-256 y formateo de payloads específicos.

### Fase 3: Despachador Robótico con Bitácora y Conexión Bilateral
- [x] **Task 6.3.3:** Motor de despacho con máquina de estados y registro de bitácora en `agent/portal/portal_dispatcher_engine.py`.
- [x] **Task 6.3.4:** Integración con `BilateralNegotiationEngine` y generación de tickets oficiales.

### Checkpoint: Flujo de Despacho
- [x] Validar radicación completa con ticket y registro auditable.

### Fase 4: Endpoints REST y Tests Automatizados
- [x] **Task 6.3.5:** Endpoints REST en `api/routes/portal_agent.py` y `api/routes/cases.py`.
- [x] **Task 6.3.6:** Suite de tests automatizados en `tests/test_portal_dispatcher.py` (100% passing).

### Checkpoint Final Sprint 6.3
- [x] 100% tests en verde, daemon API actualizado y verificación en vivo en rama develop.
