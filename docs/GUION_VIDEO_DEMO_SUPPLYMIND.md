# 🎬 Guion de Grabación de Video Demo (4 Minutos) — SupplyMind AI B2B

Este documento contiene la secuencia exacta de comandos y explicación técnica para grabar el video demostrativo consolidado (S1 a S4), respondiendo directamente a cada punto de retroalimentación del jurado evaluador.

---

## ⏱️ Minuto 0:00 – 0:50 | 1. Enrutamiento Cognitivo Neuro-Simbólico (`Grok-4.7` vs. `Python Tools`)

### Qué mostrar en pantalla:
Ejecutar en la terminal interactiva de PowerShell una demostración en vivo de cómo [`CognitiveRouter`](../agent/planner/cognitive_router.py) decide cuándo usar ejecución simbólica en Python (`SYMBOLIC_PYTHON`) y cuándo activar el modo híbrido con `grok-4.7` (`HYBRID_NEURO_SYMBOLIC`):

```powershell
python -c "from agent.planner.cognitive_router import CognitiveRouter; d1 = CognitiveRouter.evaluate_routing('dataco_real_001_caguas_pelican_kayak'); print('CASO 1:', d1.mode.value, '| Triggers:', d1.triggers, '| Costo Est:', d1.estimated_cost_usd); d2 = CognitiveRouter.evaluate_routing('case_001', force_symbolic=True); print('CASO 2:', d2.mode.value, '| Costo Est:', d2.estimated_cost_usd)"
```

### Qué explicar con voz:
> *"En SupplyMind AI el agente no usa una tabla estática: cuenta con un Enrutador Cognitivo (`CognitiveRouter`) que inspecciona los documentos de cada expediente antes de actuar. Cuando los archivos son tabulares estructurados con códigos de deducción estándar, el agente elige `SYMBOLIC_PYTHON` para conciliar con precisión `Decimal` exacta y costo `$0.00`. Cuando detecta textos no estructurados (`.txt`), escaneos de muelle (`.png`) o consultas legales complejas, activa `HYBRID_NEURO_SYMBOLIC`, donde `grok-4.7` interpreta la semántica contractual pero delega obligatoriamente toda la aritmética a las herramientas de Python."*

---

## ⏱️ Minuto 0:50 – 1:55 | 2. Datos Reales Abiertos (`DataCo Dataset`) e Ingesta Multiformato (`.xlsx`, `.csv`, `.txt`, `.json`)

### Qué mostrar en pantalla:
1. Mostrar los archivos reales dentro de `data/real_supply_chain_cases/` y el dataset fuente:
```powershell
Get-ChildItem data/real_supply_chain_cases -Recurse | Select-Object FullName
```
2. Ejecutar el benchmark sobre los 5 expedientes reales multiformato de **DataCo Global Smart Supply Chain Dataset** (`DOI: 10.17632/8gx2fvg2k6.5`):
```powershell
python scripts/benchmark_50_cases.py --cases-dir data/real_supply_chain_cases --mode fast_no_cache
```

### Qué explicar con voz:
> *"Atendiendo la retroalimentación de la Semana 3, además de nuestra batería sintética de estrés, integramos expedientes construidos sobre el dataset público real **DataCo Global Smart Supply Chain** (Mendeley Data, DOI `10.17632/8gx2fvg2k6.5`), con órdenes reales de los centros logísticos de Caguas, Cleveland, Los Ángeles, Chicago y Miami. Como se observa en pantalla, cada expediente combina diferentes formatos empresariales: hojas de cálculo Excel OpenXML (`.xlsx`), manifiestos de almacén en `.csv`, avisos bancarios y contratos en `.txt` y `.json`. Nuestro `MultiFormatParser` y `DocumentClassifier` los procesan de forma nativa con `$0.00 USD` de error absoluto medio (MAE)."*

---

## ⏱️ Minuto 1:55 – 2:55 | 3. Costo Real Medido de Pasarela (`$10.66 / 940 peticiones`) y Guardarraíl Presupuestario (`TaskBudgetGuard`)

### Qué mostrar en pantalla:
Ejecutar en consola la prueba de calibración de costo real y corte duro presupuestario:
```powershell
pytest tests/test_cognitive_router_and_budget.py -v
```

### Qué explicar con voz:
> *"Para que ninguna tarea consuma más presupuesto de lo debido en el LLM, implementamos `TaskBudgetGuard` calibrado exactamente con nuestro consumo medido en la pasarela de Platica: **USD \$10.66 en 940 peticiones**, equivalente a **\$0.011340 USD por petición**. Cada expediente tiene un tope duro configurable (por defecto `\$0.05 USD` o máximo 4 llamadas a Grok). Si una tarea compleja alcanza ese límite, `TaskBudgetGuard` corta las llamadas adicionales al LLM (`THROTTLED_CAP_REACHED`) y cierra el expediente de forma determinística con las herramientas de Python, impidiendo cualquier sobrecosto."*

---

## ⏱️ Minuto 2:55 – 4:00 | 4. Transparencia de Fallos Corregidos, Invariantes SHA-256 y Suite Completa en Verde

### Qué mostrar en pantalla:
Ejecutar todas las suites de verificación de ingeniería (Consistencia Cross-Motor, Rendimiento `<1s`, Multiformato DataCo, Enrutador Cognitivo y Holdout Ciego):
```powershell
pytest tests/test_cognitive_router_and_budget.py tests/test_multiformat_real_cases.py tests/test_phase10_case_ledger.py tests/test_benchmark_invariants.py tests/test_cross_engine_consistency.py tests/test_performance_and_resilience.py -v
```

### Qué explicar con voz:
> *"Finalmente, documentamos en nuestro reporte consolidado los errores reales detectados y corregidos durante el desarrollo —como la falsa activación del tope contractual de `0%` en cláusulas de avería de DataCo y el bloqueo de hilos en OCR cuando el gateway tardaba en responder, resuelto con un `CircuitBreaker` y caché SHA-256 que redujo el tiempo de `case_008` de 45 segundos a 0.58 segundos. Asimismo, reemplazamos términos inflados por descripciones matemáticas exactas: nuestro `CryptographicInvariantAuditor` verifica la conservación de partida doble sellada con `SHA-256`. Las 36 pruebas de invariantes, multiformato, presupuesto real y consistencia cross-motor pasan al 100%."*
