# PLAN MAESTRO DE ARQUITECTURA — FASE 8: SUPERAGENTE B2B AUTÓNOMO (CLOSED-LOOP & ZERO-BLINDSPOT)

**Proyecto:** SupplyMind AI — Plataforma Enterprise de Conciliación, Negociación y Prevención B2B  
**Fase:** 8 (Unificación de Súper-Herramientas ReAct, Topología Multi-Entrega N:M, Conversión UoM, Topes Contractuales, Auto-Curación Algebraica OCR y Aprendizaje Episódico Continuo)  
**Rama de Trabajo:** `develop`  
**Estándar de Precisión:** `Decimal("0.00")` MAE — Cero Alucinación Financiera

---

## 1. Objetivo Ejecutivo de la Fase 8

Eliminar los **7 puntos ciegos estructurales** detectados en la auditoría forense de código, transformando a **SupplyMind AI** de un conjunto de motores especializados en un **Superagente B2B Autónomo Unificado** capaz de:
1. Invocar las **15 herramientas determinísticas de las Fases 1 a 7** directamente desde su bucle de razonamiento ReAct.
2. Conciliar expedientes complejos con **entregas parciales múltiples (Split Shipments `N:M`)**, **códigos SKU cruzados** y **conversión automática de Unidades de Medida (`CA` $\leftrightarrow$ `EA` $\leftrightarrow$ `PLT`)**.
3. Auditar **topes porcentuales y franquicias contractuales** (ej. tolerancia de merma del 2% o multa OTIF máxima del 3%), dividiendo al centavo la porción procedente del exceso abusivo.
4. Auto-corregir errores ópticos de OCR en facturas y remisiones escaneadas mediante **despeje algebraico determinístico (`Self-Healing Optical Math`)**.
5. Retroalimentar automáticamente su **Red de Memoria de Precedentes en SQLite (`DisputeMemoryNetwork`)** cada vez que resuelve una auditoría o cierra un convenio bilateral.
6. Soportar **argumentación dialéctica contextual anclada a cláusulas reales del expediente** en la Mesa de Careo Bilateral.

---

## 2. Desglose por Sprints e Historias de Usuario

### Sprint 8.1: Unificación de Súper-Herramientas en el Bucle ReAct (15 Tools Nativas)
- **US-801 (Catálogo Unificado de 15 Herramientas ReAct):** Expandir `TOOL_DEFINITIONS` y `ToolExecutor` en `agent/tools/registry.py` para que el agente pueda invocar autónomamente los motores de FX/Incoterms 2020, Auditoría EDI 856/820, Watchdog SLA Art. 1041 CCom, Salud Relacional RHI, Tickets Preventivos CAPA, Careo Bilateral MCTS, Despacho Robótico a Portales y Pólizas Contables ERP SAP/NetSuite/CFDI 4.0.
- **US-802 (Trazabilidad Forense de Súper-Herramientas):** Registrar cada invocación de las 15 herramientas en `AuditLogger` con tiempos, argumentos y resultados estructurados.

### Sprint 8.2: Conciliación Multi-Entrega (`N:M`), Conversor UoM y Homologación Cross-SKU
- **US-803 (Consolidador de Entregas Parciales / Split Shipments):** Implementar `consolidate_partial_deliveries()` en `tools/document_reader/reader.py` para detectar y fusionar múltiples remisiones parciales (`delivery_01`, `delivery_02`, etc.) asociadas a una misma Orden de Compra sin generar falsos faltantes.
- **US-804 (Conversor de Unidades de Medida `CA` $\leftrightarrow$ `EA` y Cross-Reference SKU):** Implementar `UnitOfMeasureNormalizer` en `tools/sku_matcher.py` e integrarlo en `tools/reconciliation_engine/engine.py` para homologar códigos SKU alternos y convertir automáticamente Cajas Master (`CA` / `Pack xN`) a Piezas individuales (`EA`) antes de calcular discrepancias físicas y de precio.

### Sprint 8.3: Auditor de Topes Porcentuales y Franquicias Contractuales (`ContractualCapEnforcer`)
- **US-805 (Extracción Determinística de Topes Contractuales):** Implementar `ContractualCapEnforcer` en `tools/contract_analyzer/rules.py` capaz de extraer límites porcentuales y topes monetarios (ej. *"tope máximo del 3%"*, *"tolerancia de merma hasta el 2%"*) del texto de las cláusulas.
- **US-806 (Partición Matemática de Excesos de Deducción):** Cuando un retailer aplique una penalización o cargo que supere el tope contractual pactado, particionar con precisión `Decimal` la fracción amparada por el contrato (`justified_portion`) y el excedente abusivo 100% reclamable (`unjustified_excess`).

### Sprint 8.4: Auto-Corrección Algebraica de OCR y PDFs Escaneados (`OpticalMathHealer`)
- **US-807 (Despeje Algebraico de Renglones con Ruido Óptico):** Implementar `OpticalMathHealer` en `tools/document_reader/pdf_parser.py` y `tools/ocr_engine/vision.py` para verificar en cada línea extraída que $\text{Cantidad} \times \text{Precio Unitario} = \text{Importe Línea}$ y $\sum \text{Líneas} = \text{Subtotal}$. Si un dígito fue degradado por un sello o mancha en el escaneo, reconstruir el valor exacto por despeje algebraico en `Decimal`.
- **US-808 (Sanidad de Ecuación Física en Remisiones OCR):** Verificar y reparar en `DeliveryItem` la ecuación física $\text{Recibido} + \text{Faltante} + \text{Averiado} = \text{Despachado}$.

### Sprint 8.5: Memoria Episódica Auto-Evolutiva (`Closed-Loop Precedent Learning`)
- **US-809 (Auto-Registro de Precedentes Post-Auditoría y Post-Careo):** Implementar `record_case_resolution_automatically()` en `agent/memory/precedent_graph.py` y conectarlo al cierre de `SkynetRunner.run()` y `BilateralNegotiationEngine` para que cada caso resuelto o convenio rubricado actualice en tiempo real la base SQLite `precedents.sqlite3` y los perfiles de éxito por retailer.

### Sprint 8.6: Careo Adversarial Contextual Anclado a Cláusulas del Expediente
- **US-810 (Inyección de Cláusulas y Evidencias Reales del Caso en Careo Bilateral):** Enriquecer `BilateralNegotiationEngine` y `RetailerBuyerSimulator` para extraer y citar las cláusulas reales del contrato del expediente activo, las referencias exactas de factura/PO/POD y las directrices del modo RHI (`DIPLOMATIC_PRESERVATION`, `FIRM_COMMERCIAL`, `ASSERTIVE_LITIGIOUS`).
