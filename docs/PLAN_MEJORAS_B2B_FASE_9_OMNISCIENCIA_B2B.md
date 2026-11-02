# 🌐 PLAN MAESTRO DE ARQUITECTURA: FASE 9 — OMNISCIENCIA B2B, TRIBUTACIÓN MULTIRRÉGIMEN, CHAT TOOL-CALLING Y OPTIMIZACIÓN DE CAPITAL DE TRABAJO (WACC/NPV)

**Proyecto:** SupplyMind AI — The Autonomous B2B Revenue Recovery & Arbitration Engine  
**Fase:** 9 (Segunda Auditoría Profunda de Sub-Sistemas: Guardrails, Fiscal/ERP, MCTS Financiero, Courtroom, Visión, Portales RPA y Copiloto Conversacional Omnisciente)  
**Objetivo:** Erradicar los **9 puntos ciegos de segundo orden** detectados en los subsistemas periféricos y de orquestación (`api/routes/chat.py`, `agent/guardrails/`, `agent/core/erp_engine.py`, `agent/fiscal/`, `agent/planner/mcts_negotiator.py`, `agent/courtroom/`, `agent/vision/`, `agent/portal/` y `agent/predictive/`), logrando que todos los motores trabajen como un **único organismo conectado en tiempo real**.

---

## 🔍 1. DIAGNÓSTICO DE DEBILIDADES DE SEGUNDO ORDEN (AUDITORÍA PROFUNDA DE SUBSISTEMAS)

Tras completar las Fases 7 y 8 en el núcleo de ejecución (`SkynetRunner`, `registry.py`, `reconciliation_engine`, `pdf_parser` y `precedent_graph`), auditamos línea por línea los subsistemas restantes del repositorio e identificamos **9 debilidades estructurales**:

### Debilidad 1: El Copiloto Conversacional (`api/routes/chat.py`) no usa Tool-Calling ReAct ni conoce los motores de Fase 7 y 8
- **Diagnóstico técnico:** En `api/routes/chat.py` (líneas 677–1235), el endpoint `POST /api/cases/{case_id}/chat` opera con un árbol estático de `if/elif` por palabras clave y, cuando invoca a Grok 4.7 en vivo (`client.chat.completions.create`), **no le pasa `tools=TOOL_DEFINITIONS`**. Además, ni `_extract_case_full_context()` ni `_deterministic_chat_response()` incluyen información sobre:
  - Prescripción SLA (`DisputeSlaWatchdog` / DTP / Art. 1041 CCom),
  - Salud Relacional (`RelationalHealthEngine` / RHI),
  - Conciliación Bancaria 3-Way (`BankRemittanceReconciler`),
  - Causa Raíz 80/20 y Tickets CAPA (`RootCauseAnalyzer`),
  - Topes Contractuales de Responsabilidad (`ContractualCapEnforcer`).
- **Riesgo B2B:** Si un ejecutivo pregunta en el chat *"¿Cuántos días quedan antes de que prescriba este reclamo?"*, *"¿Cuál es el índice RHI de esta cuenta?"*, o *"¿Existe un tope máximo de penalización en el contrato?"*, el chat no puede ejecutar la herramienta correspondiente ni tiene el contexto precargado. Tampoco puede responder preguntas transversales de portafolio (*"¿Cuáles son los 5 casos más urgentes de toda la cartera?"*).

### Debilidad 2: `ContractualCapEnforcer` no está conectado en línea con `reconcile_dispute_data()` ni `SanityGateEngine`
- **Diagnóstico técnico:** Aunque `ContractualCapEnforcer` fue creado en `tools/contract_analyzer/rules.py` y expuesto en `agent/tools/registry.py`, el flujo automático de `reconcile_dispute_data()` (`tools/reconciliation_engine/engine.py`) y `SanityGateEngine.audit_and_reinforce_case()` (`agent/guardrails/sanity_gate.py`) aún no trunca automáticamente las multas que exceden el porcentaje máximo pactado en el contrato marco.
- **Riesgo B2B:** Cuando una cláusula contractual limita las multas logísticas (ej. tope del 3% sobre el valor de la PO) y el retailer deduce el 8%, el motor debe dividir automáticamente la deducción en dos: la porción contractualmente admisible (si hubo incumplimiento probado) y el **exceso ilegal sobre el tope (`excess_over_cap`)** como 100% reclamable.

### Debilidad 3: Rigidez Fiscal en `ErpEngine` y `CfdiPacSimulator` (IVA 16% fijo vs. Tasa 0% Alimentos/Medicinas, Región Fronteriza 8%, IEPS y Exportación)
- **Diagnóstico técnico:** En `agent/core/erp_engine.py` (líneas 105 y 297), el desglose contable divide siempre entre `Decimal("1.16")` asumiendo IVA general del 16%. Asimismo, `CfdiPacSimulator.stamp_credit_note()` (`agent/fiscal/cfdi_pac_simulator.py`) iguala `total = subtotal` sin desglosar el nodo `<cfdi:Impuestos>` según el régimen tributario del producto.
- **Riesgo B2B:** En cadenas de suministro de supermercados y retail (Walmart, Soriana, Chedraui), existen múltiples regímenes fiscales:
  1. **Tasa 0% IVA (Art. 2-A LIVA):** Alimentos básicos, agroindustria y medicinas de patente.
  2. **Tasa 8% IVA:** Estímulo fiscal de la Región Fronteriza Norte/Sur.
  3. **IEPS (8% / 26.5% / 53%):** Bebidas saborizadas, alimentos de alta densidad calórica, vinos y licores.
  4. **Exportación T-MEC / US Sales Tax (0% IVA):** Operaciones transfronterizas en USD.
  Aplicar `1.16` fijo descuadra la contabilidad fiscal del proveedor ante el SAT.

### Debilidad 4: `MCTSNegotiator` ignora el Valor del Dinero en el Tiempo (WACC / TIIE / SOFR / NPV) y la Salud Relacional (`RHI`)
- **Diagnóstico técnico:** En `agent/planner/mcts_negotiator.py`, la simulación Monte Carlo evalúa `expected_payoff = claimable * recovery_pct` en valores nominales estáticos, sin descontar el flujo de efectivo futuro mediante una tasa de costo de capital (**WACC** o **TIIE/SOFR**) ni restar los costos legales directos del litigio arbitral. Además, no consume el `rhi_score` de `RelationalHealthEngine`.
- **Riesgo B2B:** Para un CFO, cobrar \$100,000 USD dentro de 120 días tras pagar \$5,000 USD de costas arbitrales con un WACC anual del 14% tiene un **Valor Presente Neto (NPV)** de \$90,520 USD, que es financieramente **inferior** a una Liquidación Express del 92% (\$92,000 USD) cobrada en 5 días hábiles. Sin NPV ni WACC, el agente puede recomendar litigios destructivos de valor.

### Debilidad 5: `AdversarialCourtroomEngine` y `PalletVisionAuditor` operan con plantillas fijas en vez de inspeccionar las pruebas reales del expediente
- **Diagnóstico técnico:**
  - `AdversarialCourtroomEngine.conduct_debate()` (`agent/courtroom/adversarial_engine.py`) genera sólo 2 argumentos genéricos sin citar los códigos reales de deducción (`pay.deductions`), los SKUs con diferencias (`reconciliation.discrepancies`), las cláusulas reales (`ctr.clauses`), ni los hallazgos de `SanityGateEngine` (doble penalización, extemporaneidad, topes contractuales).
  - `PalletVisionAuditor.inspect_pallet()` (`agent/vision/pallet_vision_auditor.py`) devuelve siempre `total_boxes_detected=48` y `PO-994820` en lugar de sincronizarse con los bultos, SKUs, bodega (`warehouse_location`) y averías/faltantes reales del expediente `case_id`.

### Debilidad 6: `RetailerPortalAgent` desconectado del Benchmark Real y del `DisputeSlaWatchdog`
- **Diagnóstico técnico:** `RetailerPortalAgent.sync_retailer_portal()` (`agent/portal/retailer_portal_agent.py`) devuelve una lista fija de 5 deducciones simuladas que no corresponden a los 50 expedientes reales de `data/cases/`, ni dispara alertas automáticas en `DisputeSlaWatchdog` para las partidas extraídas cuyo `dispute_deadline` está por vencer.

### Debilidad 7: `PreDispatchLeakageRadar` (DVI) estático y aislado del aprendizaje de `RootCauseAnalyzer` y `DisputeMemoryNetwork`
- **Diagnóstico técnico:** `PreDispatchLeakageRadar.evaluate_purchase_order()` (`agent/predictive/leakage_radar.py`) calcula el índice `DVI` usando únicamente un diccionario fijo de 4 CEDIS (`HIGH_RISK_DC_PROFILES`), sin consultar la incidencia real de defectos por CEDIS/SKU calculada por `RootCauseAnalyzer` ni los precedentes históricos de `DisputeMemoryNetwork`.

### Debilidad 8: `ZKPFinancialAuditor` (`arithmetic_verifier.py`) limitado a USD y sin soporte para cifras derivadas (Intereses Art. 362, Topes, NPV y FX)
- **Diagnóstico técnico:** `extract_monetary_figures()` sólo detecta `USD|dólares` y `collect_valid_ground_truth_figures()` no registra en el conjunto de cifras válidas (`valid_set`) los intereses moratorios legales (9% anual Art. 362 CCom), los montos de topes contractuales (`cap_amount`), los equivalentes en `MXN` ni los flujos descontados `NPV`. Esto puede provocar penalizaciones falsas (`HALLUCINATION_INTERCEPTED`) cuando el dictamen incluye cálculos financieros avanzados legítimos.

### Debilidad 9: Falta de un Optimizador C-Level de Portafolio y Capital de Trabajo (`WorkingCapitalPortfolioOptimizer`)
- **Diagnóstico técnico:** No existe un motor que consolide los 50+ expedientes para responder la pregunta ejecutiva más importante de un Director de Finanzas (CFO): *"Si mi equipo y mis bots tienen capacidad para ejecutar hoy las 10 acciones de mayor retorno ajustado por riesgo, ¿en qué orden exacto debemos atacar la cartera considerando DTP (prescripción), NPV (valor presente neto), RHI (riesgo relacional) y probabilidad de éxito?"*.

---

## 🚀 2. ARQUITECTURA DE SOLUCIÓN — PLAN DE EJECUCIÓN EN 6 SPRINTS (FASE 9)

### 🛠️ SPRINT 9.1: Copiloto Conversacional Omnisciente con Tool-Calling ReAct y Consultas de Portafolio
**Objetivo:** Transformar `api/routes/chat.py` para que el chat interactivo tenga acceso total a las 15+ herramientas ReAct en vivo, contexto 360° de las Fases 7 y 8, y soporte para consultas transversales de portafolio.

- **Historia de Usuario 9.1.1 (Native Tool-Calling en Chat Interactivo):**
  - En `api/routes/chat.py`, habilitar el bucle de *Function Calling* con `tools=TOOL_DEFINITIONS` y `ToolExecutor` cuando Grok 4.7 está activo, permitiendo que el copiloto ejecute en tiempo real cualquier herramienta durante la conversación.
- **Historia de Usuario 9.1.2 (Inyección de Contexto Fase 7/8 y Respuestas Determinísticas):**
  - Enriquecer `_extract_case_full_context()` y `_deterministic_chat_response()` en `api/routes/chat.py` con:
    1. Auditoría de Prescripción SLA (`DisputeSlaWatchdog.evaluate_case_sla(case_id)`),
    2. Salud Relacional RHI (`RelationalHealthEngine.evaluate_case_relationship(case_id)`),
    3. Conciliación Bancaria 3-Way (`BankRemittanceReconciler.reconcile_case(case_id)`),
    4. Causa Raíz 80/20 y CAPA (`RootCauseAnalyzer` / `CapaTicketGenerator`),
    5. Topes Contractuales (`ContractualCapEnforcer`) y Simulación Financiera NPV/WACC.
- **Historia de Usuario 9.1.3 (Cross-Portfolio Intelligence Query Handler):**
  - Permitir que el usuario consulte en el chat métricas globales de los 50 casos (ej. *"¿Qué casos están en riesgo de prescripción?"*, *"¿Cuál es el ranking del portafolio por valor presente neto?"*).

---

### ⚖️ SPRINT 9.2: Conexión en Línea de `ContractualCapEnforcer`, `SanityGateEngine` y `ZKPFinancialAuditor`
**Objetivo:** Integrar los topes contractuales, las divisas múltiples y las cifras financieras derivadas directamente en el pipeline de conciliación y en el auditor criptográfico ZKP.

- **Historia de Usuario 9.2.1 (Auto-Truncamiento de Topes en `reconcile_dispute_data` y `SanityGateEngine`):**
  - Conectar `ContractualCapEnforcer.enforce_caps()` dentro de `tools/reconciliation_engine/engine.py` y `agent/guardrails/sanity_gate.py` (Filtro 5: *Auditoría de Topes de Responsabilidad Contractual*), asegurando que cualquier penalización que rebase el límite contractual sea truncada con precisión `Decimal` y su excedente pase a `claimable_amount`.
- **Historia de Usuario 9.2.2 (Expansión Multi-Divisa y Cifras Derivadas en `ZKPFinancialAuditor`):**
  - Actualizar `agent/guardrails/arithmetic_verifier.py` para soportar `MXN`, `USD`, `EUR` y registrar automáticamente en `collect_valid_ground_truth_figures()` las cifras legítimas derivadas: intereses moratorios Art. 362 CCom (9% anual), topes contractuales, subtotales/IVA desglosados y Valor Presente Neto (NPV), manteniendo `$0.00 MAE` y 0 falsos positivos.

---

### 🏛️ SPRINT 9.3: Motor Tributario Multirrégimen (IVA 16% / 0% / 8%, IEPS, Exportación) en `ErpEngine` y `CfdiPacSimulator`
**Objetivo:** Dotar a `agent/core/erp_engine.py` y `agent/fiscal/cfdi_pac_simulator.py` de inteligencia fiscal real adaptable al tipo de producto y ubicación de la operación.

- **Historia de Usuario 9.3.1 (Detector de Régimen Fiscal por Caso y SKU — `FiscalRegimeResolver`):**
  - Crear `FiscalRegimeResolver` en `agent/core/erp_engine.py` que clasifique automáticamente el perfil tributario del expediente:
    - `STANDARD_VAT_16` (IVA General 16%),
    - `ZERO_RATED_FOOD_PHARMA_0` (Tasa 0% Art. 2-A LIVA para alimentos/agro/medicinas),
    - `BORDER_REGION_VAT_8` (Estímulo Frontera Norte 8%),
    - `IEPS_HIGH_CALORIE_BEVERAGE` (IVA 16% + IEPS 8%),
    - `EXPORT_USMCA_0` (Exportación T-MEC 0% / ObjetoImp `01`).
- **Historia de Usuario 9.3.2 (Pólizas SAP/NetSuite y XML CFDI 4.0 con Nodo `<cfdi:Impuestos>` Exacto):**
  - Actualizar `ErpEngine.build_erp_posting_lines()`, `ErpEngine.generate_cfdi_40_xml()` y `CfdiPacSimulator.stamp_credit_note()` para calcular al centavo (`Decimal`) el `SubTotal`, los impuestos trasladados (`IVA`, `IEPS`) y el `Total`, garantizando cuadratura contable perfecta (`sum(debits) == sum(credits)`).

---

### 📈 SPRINT 9.4: `MCTSNegotiator` Financiero con WACC, DSO, Valor Presente Neto (NPV) y Acoplamiento RHI
**Objetivo:** Evolucionar `agent/planner/mcts_negotiator.py` hacia un simulador financiero corporativo digno de un CFO.

- **Historia de Usuario 9.4.1 (Descuento de Flujos de Efectivo por WACC y Costos de Litigio en `Decimal`):**
  - Incorporar en `MCTSNegotiator.simulate_negotiation()` el cálculo exacto en `Decimal` de:
    $$\text{NPV} = \frac{\text{Monto Recuperado Nominal}}{\left(1 + \frac{\text{WACC}}{365}\right)^{\text{Días Proyectados}}} - \text{Costos Legales Directos} + \text{Interés Moratorio Esperado}$$
  - Añadir los campos `npv_payoff`, `capital_cost_Drag`, `wacc_annual_pct` y `dso_savings_days` a `NegotiationTrajectory` y `MCTSPlanResult`.
- **Historia de Usuario 9.4.2 (Acoplamiento Dinámico con `RelationalHealthEngine`):**
  - Hacer que `MCTSNegotiator` consulte automáticamente el `rhi_score` del caso (cuando no se le pase manualmente) para ajustar los pesos de utilidad (`w_cash`, `w_rel`, `w_time`, `w_fric`) de forma coherente con el motor de negociación bilateral.

---

### 🔬 SPRINT 9.5: Dinamización Forense de `AdversarialCourtroomEngine`, `PalletVisionAuditor`, `RetailerPortalAgent` y `PreDispatchLeakageRadar`
**Objetivo:** Eliminar los datos estáticos en los 4 motores especializados para que operen al 100% con la evidencia real de cada expediente del benchmark y la telemetría histórica viva.

- **Historia de Usuario 9.5.1 (Careo Judicial Específico por Evidencia en `AdversarialCourtroomEngine`):**
  - Mejorar `AdversarialCourtroomEngine.conduct_debate()` para que el Fiscal y la Defensora debatan citando las partidas reales con diferencias (`reconciliation.discrepancies`), los folios exactos de factura/remisión/pago, las cláusulas del contrato (`ctr.clauses`), las violaciones detectadas por `SanityGateEngine` (extemporaneidad, doble cobro, topes) y el riesgo SLA (`DisputeSlaWatchdog`).
- **Historia de Usuario 9.5.2 (Inspección Visual Sincronizada por Caso en `PalletVisionAuditor`):**
  - Dotar a `PalletVisionAuditor.inspect_pallet_for_case(case_id)` de la capacidad de leer los documentos reales del expediente (`delivery`, `invoice`, `purchase_order`) para reflejar el conteo exacto de cajas facturadas vs. recibidas, cajas dañadas, ubicación del muelle (`warehouse_location`) y sello C-TPAT del caso.
- **Historia de Usuario 9.5.3 (Sincronización de Portales RPA con Casos Reales y `PreDispatchLeakageRadar` Conectado):**
  - Hacer que `RetailerPortalAgent.sync_retailer_portal()` incluya las deducciones reales de los expedientes del retailer en `data/cases/` junto con su semáforo `DisputeSlaWatchdog`, y que `PreDispatchLeakageRadar.evaluate_purchase_order()` ajuste dinámicamente el puntaje `DVI` consultando la tasa de defectos histórica de `RootCauseAnalyzer` y `DisputeMemoryNetwork`.

---

### 💼 SPRINT 9.6: `WorkingCapitalPortfolioOptimizer` (War-Room de Capital de Trabajo y Ejecución Batch) & Suite de Regresión Fase 9
**Objetivo:** Construir el motor C-Level de optimización de cartera y exponer las nuevas capacidades en el Registro de Herramientas ReAct (`18 herramientas`), API y pruebas automatizadas.

- **Historia de Usuario 9.6.1 (`WorkingCapitalPortfolioOptimizer` en `agent/core/portfolio_optimizer.py`):**
  - Crear el optimizador de portafolio que audita los 50 expedientes combinando:
    1. `claimable_amount` y `NPV` (WACC 12% anual),
    2. `days_remaining` y nivel de urgencia `DTP` (`DisputeSlaWatchdog`),
    3. `rhi_score` y estrategia recomendada (`RelationalHealthEngine`),
    4. `irrefutability_grade` (`SanityGateEngine`),
    calculando un **Priority Execution Score (0–100)** y el **Valor Económico en Riesgo Inminente (VaR Prescripción)**, con soporte de **Batch Action Execution** (emisión masiva de avisos de interrupción de prescripción y paquetes ERP).
- **Historia de Usuario 9.6.2 (Expansión a 18 Super-Herramientas ReAct y Endpoints API):**
  - Registrar 3 nuevas herramientas en `agent/tools/registry.py` (llevando el arsenal ReAct de 15 a **18 herramientas nativas**):
    16. `optimize_working_capital_portfolio` (`WorkingCapitalPortfolioOptimizer`),
    17. `simulate_mcts_npv_strategy` (`MCTSNegotiator` con WACC/NPV),
    18. `resolve_fiscal_regime_and_erp` (`FiscalRegimeResolver` + `ErpEngine` multirrégimen).
- **Historia de Usuario 9.6.3 (Suite de Pruebas `tests/test_phase9_omniscience.py`):**
  - Crear pruebas unitarias y de integración exhaustivas verificando las 6 mejoras de Fase 9 y manteniendo el 100% de la suite previa en verde.
