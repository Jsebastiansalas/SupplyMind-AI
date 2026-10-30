# Plan de Implementación: Sprint 6.1 — Motor Multi-Agente de Negociación Bilateral (IA vs IA)

## Resumen Ejecutivo
Construcción del motor de confrontación dialéctica autónoma de SupplyMind AI, permitiendo que el Agente Defensor SupplyMind se caree en tiempo real contra un Agente Comprador Retailer simulado (calibrado con personalidades y tácticas de Walmart, Amazon, Soriana y Costco), aplicando teoría de juegos (MCTS), límites de delegación financiera infranqueables y protocolo de 5 rondas máximas con detección de acuerdo o impasse arbitral.

---

## Decisiones de Arquitectura
1. **Desacoplamiento Aritmético Estricto:** Toda suma, concesión, retención y cálculo de spread se ejecuta con tipos Python `Decimal` ($0.00 MAE).
2. **Arquetipos de Comprador Hostil:** Modelado de comportamientos reales de grandes cadenas comerciales (`WALMART_OTIF`, `AMAZON_FC`, `SORIANA_REBATE`, `COSTCO_DEPOT`, `GENERIC_B2B`) con posturas de apertura, argumentos de desgaste y umbrales de reacción ante pruebas documentales.
3. **Control de Rondas y Anti-Bucles:** Protocolo rígido de máximo 5 rondas. Si el spread converge a cero o dentro de la tolerancia de delegación, se sella `AGREEMENT_REACHED`; si se agotan las 5 rondas sin consenso, se emite `IMPASSE_REACHED` derivando automáticamente a arbitraje ICC / CANACO.
4. **Dualidad de Inferencia:** Funciona con Grok 4.7 Direct en vivo para argumentación dialéctica rica, respaldado por un motor determinístico senior local con 100% de operatividad offline.

---

## Task List & Checkpoints

### Fase 1: Modelos de Datos & Arquetipos de Comprador
- [ ] **Task 1:** Definir esquemas Pydantic V2 en `data/models.py` (`NegotiationDuelRound`, `NegotiationDuelSession`, `RetailerArchetypeConfig`, `DuelStepRequest`, `DuelStepResponse`).
- [ ] **Task 2:** Implementar `RetailerBuyerSimulator` en `agent/core/retailer_buyer_simulator.py` con 5 arquetipos de retail y respuestas condicionadas a evidencias.

### Checkpoint: Modelos y Simulador Comprador
- [ ] Validar instanciación y cálculo de pretensiones del comprador.

### Fase 2: Motor Bilateral & Orquestador MCTS
- [ ] **Task 3:** Implementar `BilateralNegotiationEngine` en `agent/core/bilateral_negotiation_engine.py` (cálculo de contraofertas MCTS, cruce de pruebas, cálculo de spread y convergencia).
- [ ] **Task 4:** Crear rutas de API REST en `api/routes/negotiation_duel.py` (`POST /api/negotiation/duel/start`, `POST /api/negotiation/duel/step`, `GET /api/negotiation/duel/{case_id}`).

### Checkpoint: Motor y Endpoints REST
- [ ] Endpoints activos y documentados en Swagger `/docs`.

### Fase 3: Pruebas Exhaustivas y Verificación
- [ ] **Task 5:** Suite de pruebas automatizadas en `tests/test_negotiation_duel.py` cubriendo convergencia de acuerdo, detección de impasse, respeto de límites de delegación y compatibilidad con expedientes reales.

### Checkpoint: Sprint 6.1 Completado
- [ ] Todos los tests unitarios en verde (100% passing).
- [ ] Servidor FastAPI respondiendo sin errores.
