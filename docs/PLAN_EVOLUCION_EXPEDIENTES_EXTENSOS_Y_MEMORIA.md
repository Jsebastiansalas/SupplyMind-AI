# Plan Maestro de Evolución Arquitectónica: Ingesta Masiva & Memoria de Precedentes
## SupplyMind AI — Del Agente Transaccional al Cerebro Cognitivo B2B

---

## 🎯 Visión y Objetivos Estratégicos
Convertir a **SupplyMind AI** en el sistema pericial más potente del mercado corporativo mediante la transición de un agente que evalúa disputas de forma reactiva e individual a un **sistema cognitivo autónomo** capaz de:
1. **Digerir expedientes masivos de 100+ páginas y miles de SKUs** sin desbordar el contexto LLM ni perder un solo centavo de precisión aritmética.
2. **Aprender continuamente del historial de disputas (*Dispute Memory Network*)**, recordando precedentes ganados por cada retailer para usarlos como jurisprudencia vinculante en nuevas reclamaciones.
3. **Autoblindarse mediante debate dialéctico multi-agente** antes de emitir cualquier carta formal.
4. **Predecir la probabilidad de cobro** de cada partida antes de iniciar la gestión.

---

## 🏛️ PILAR 1: Ingesta Jerárquica Masiva (*Chunking Map-Reduce Engine*)
> **Objetivo:** Auditar contratos marco de 100+ páginas, adendas complejas y facturas/remisiones con más de 2,000 SKUs con latencia menor a 3 segundos.

### 1.1 Arquitectura del Pipeline de Ingesta
```
┌────────────────────────────────────────────────────────────────────────┐
│                   EXPEDIENTE MASIVO (100+ PÁGINAS)                     │
│  [Contrato Marco 80 pág]  [Factura 2,000 SKUs]  [Remisión 50 Tarimas]   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
       [Contratos & Adendas]               [Facturas & Remisiones]
   Segmentador Semántico por Cláusulas   Particionador de Lotes (50 SKUs)
                  │                                   │
                  ▼                                   ▼
      [Índice Vectorial Local]             [Motor Map-Reduce Local]
   Búsqueda Semántica de Párrafos          Cálculo Matricial Python Decimal
                  │                                   │
                  └─────────────────┬─────────────────┘
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │     FIRMA SINTÉTICA DEL EXPEDIENTE (Context Injection)  │
       │  • Resumen Jerárquico Condensado (<3,000 tokens)        │
       │  • Árbol de Invariantes Cuadradas ($0.00 MAE)           │
       │  • Punteros de Evidencia Exactos (Pág / Párrafo / Fila) │
       └─────────────────────────────────────────────────────────┘
```

### 1.2 Componentes Técnicos a Implementar
1. **`tools/document_reader/hierarchical_segmenter.py`:**
   - Parser estructural de PDFs de gran extensión con detección de jerarquía documental: Títulos, Capítulos, Secciones de Penalización, Anexos Técnicos y Fechas de Vigencia.
2. **`tools/reconciliation_engine/batch_map_reduce.py`:**
   - Algoritmo que procesa facturas de 2,000+ renglones en lotes de 50 partidas.
   - Cada sub-lote se concilia con precisión `Decimal` en memoria CPU ($0.00 costo de inferencia).
   - Generación del *Árbol de Invariantes Merkle*, asegurando que la sumatoria de todos los bloques coincida al centavo con el total facturado.
3. **`tools/document_reader/synthetic_fingerprint.py`:**
   - Genera una "Firma de Evidencia" comprimida con las anomalías detectadas y sus coordenadas documentales exactas, lista para inyectarse al LLM (Grok 4.7) sin truncamiento.

---

## 🧠 PILAR 2: Red de Memoria Corporativa & Historial de Precedentes (*Dispute Memory Graph*)
> **Objetivo:** Que el agente nunca empiece de cero, sino que consulte el historial de casos resueltos con cada retailer para invocar antecedentes jurídicos y comerciales que fuercen el pago inmediato.

### 2.1 Esquema de la Red de Memoria por Retailer
```
┌────────────────────────────────────────────────────────────────────────┐
│                   DISPUTE MEMORY NETWORK (POR BUYER)                   │
├────────────────────────────────────────────────────────────────────────┤
│ Retailer: WALMART MÉXICO (RFC: WME6502099T1)                           │
│ Historial: 142 disputas auditadas | Tasa de Éxito: 91.4%              │
│                                                                        │
│ • Patrón Recurrente Detectado:                                         │
│   Deducción sistemática por ASN tardío en semanas 48-52 (Fin de Año).  │
│                                                                        │
│ • Precedente Vinculante Ganado (CASE-006):                             │
│   Walmart aceptó rembolsar $2,400 USD tras demostrarse que el retraso │
│   fue originado por saturación en su propio muelle de Cuautitlán.      │
│                                                                        │
│ • Cláusula de Oro:                                                     │
│   Cláusula 14.2 del Convenio 2026 prevalece sobre guías operativas.   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │     INYECCIÓN AUTOMÁTICA DE PRECEDENTE EN LA CARTA      │
       │ "Conforme al precedente formal resuelto en el caso      │
       │ CASE-006 el pasado 15 de Septiembre, donde Walmart     │
       │ acordó la restitución del cargo por saturación de       │
       │ muelle, exigimos idéntico criterio contable..."         │
       └─────────────────────────────────────────────────────────┘
```

### 2.2 Componentes Técnicos a Implementar
1. **`agent/memory/precedent_graph.py`:**
   - Almacenamiento estructurado persistente en `data/memory/precedents/`.
   - Indexación multidimensional: `retailer_id`, `deduction_code`, `governing_clause`, `resolution_outcome` (`WON`, `PARTIAL_CONCESSION`, `LOST`).
2. **`agent/memory/precedent_matcher.py`:**
   - Al recibir una deducción en un caso nuevo, busca en el historial los 3 precedentes más similares y exitosos.
3. **`agent/planner/precedent_prompts.py`:**
   - Enriquecimiento del generador de Cartas de Reclamación y Minutas de Negociación incorporando las referencias históricas citadas como antecedentes firmes.

---

## ⚖️ PILAR 3: Debate Dialéctico Multi-Agente (*Adversarial Courtroom*)
> **Objetivo:** Someter cada dictamen a una prueba de fuego interna entre dos roles adversarios antes de emitir la postura oficial.

### 3.1 Flujo Dialéctico
1. **Agente 1 — Fiscal Forense del Retailer (*The Auditor*):**
   - Ataca el expediente buscando vacíos probatorios: *"El POD carece de hora de salida de rampa", "La fecha del reclamo supera los 15 días de la política interna"*.
2. **Agente 2 — Abogado Defensor del Proveedor (*The Advocate*):**
   - Responde con fundamentos jurídicos y contractuales: *"El Art. 88 del Código de Comercio invalida términos leoninos", "Existe termo-registro de temperatura sellado por el operador"*.
3. **Agente 3 — Magistrado Sentenciador (*The Magistrate*):**
   - Pesa ambos alegatos, descarta reclamos débiles y emite el dictamen final irrefutable.

---

## 📈 PILAR 4: Motor Predictivo de Recuperación & Simulación de Cobro
> **Objetivo:** Estimar la probabilidad matemática de cobro (0% a 100%) y recomendar la ruta operativa más rentable.

### 4.1 Matriz de Scoring de Recuperabilidad
- **Score > 85%:** Reclamación directa formal vía portal B2B (recuperación en 7 días).
- **Score 55% - 85%:** Oferta de Concesión Parcial / Nota de Crédito por merma y compensación del remanente en siguiente pedido.
- **Score < 55%:** Escalamiento a cobranza corporativa con póliza contable NIF C-3 y aviso formal de controversia.

---

## 🗓️ Hoja de Ruta de Implementación (Fases de Desarrollo)

### Fase 1: Ingesta Jerárquica Masiva (Sprints 4.1 y 4.2) — ✅ COMPLETADA (Commit `fe4774c`)
- [x] Implementar `hierarchical_segmenter.py` para parseo de documentos de 50+ a 200+ páginas.
- [x] Desarrollar motor `batch_map_reduce.py` para conciliación de lotes masivos de 1,000+ partidas en CPU local con Merkle tree SHA-256.
- [x] Construir prueba de estrés con expediente sintético de 80 páginas y 1,000 SKUs (`tests/test_massive_dossier.py` — 5/5 PASSED).

### Fase 2: Red de Memoria & Historial de Precedentes (Sprints 4.3 y 4.4) — ✅ COMPLETADA (Commit `24c5be9`)
- [x] Diseñar el modelo de datos `RetailerPrecedentProfile` y repositorio dual SQLite/JSON (`agent/memory/precedent_graph.py`).
- [x] Implementar pipeline de aprendizaje: tras resolver un caso, el dictamen se archiva automáticamente como antecedente vinculante.
- [x] Inyectar citas de precedentes en cartas de reclamación (`reports/carta_reclamacion_*.md` y `exporter.py`).
- [x] Crear suite de pruebas de memoria y recall de precedentes (`tests/test_precedent_network.py` — 6/6 PASSED).

### Fase 3: Debate Dialéctico & Motor Predictivo (Sprint 4.5) — ✅ COMPLETADA (Commit `c65adaf`)
- [x] Integrar el debate dialéctico multi-agente Auditor vs Defensor vs Magistrado (`agent/courtroom/adversarial_engine.py`).
- [x] Implementar algoritmo predictivo de probabilidad de cobro y 3 escenarios financieros (`agent/predictive/recovery_scorer.py`).
- [x] Enriquecer reporte formal de disputa con Secciones 4.1 (Debate Dialéctico) y 5.1 (Scoring Predictivo).
- [x] Exponer rutas API REST (`/api/cases/{case_id}/adversarial-courtroom`, `/api/cases/{case_id}/recovery-prediction`).
- [x] Validar con suite de pruebas `tests/test_adversarial_courtroom.py` (6/6 PASSED, 17/17 total).
