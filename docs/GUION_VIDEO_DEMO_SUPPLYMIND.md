# 🎬 Guion de Grabación de Video Demo (2 Minutos Exactos) — SupplyMind AI B2B
> **Hitos S1, S2 y S3 — Reto Agente 2026 (Platica.mx × Campuslands)**  
> **Estructura oficial:** Problema en 1 frase → Agente en vivo con 3 herramientas reales → Error y auto-recuperación → Datos reales del dominio y costo medido.

---

## ⏱️ Bloque 1 (0:00 – 0:15) | El Problema de Negocio en una Frase

### Qué mostrar en pantalla:
Terminal o portada con el título **SupplyMind AI** y un expediente comercial abierto mostrando una factura con pago recortado.

### Qué decir en voz alta (15 segundos):
> *"En las cadenas de suministro B2B, los proveedores pierden millones de dólares cada mes cuando los retailers aplican deducciones arbitrarias y faltantes de mercancía que los analistas humanos tardan días en auditar."*

---

## ⏱️ Bloque 2 (0:15 – 0:50) | Agente Corriendo en Vivo con Herramientas Reales

### Qué mostrar en pantalla:
Lanzar la ejecución en vivo del agente contra Grok-4.7:
```powershell
python -c "from agent.core.skynet_runner import SkynetRunner; r = SkynetRunner('dataco_real_001_caguas_pelican_kayak', fast_path=False); r.run()"
```
Mostrar en la consola a **Grok-4.7 decidiendo pasos solo** a través de tool calling e invocando sus herramientas reales:
1. `read_dispute_documents` (lectura multiformato).
2. `execute_reconciliation` (conciliación aritmética en `Decimal` con cero alucinación).
3. `evaluate_contract_terms` (revisión de cláusulas y ventanas perentorias).
4. `generate_final_report` (dictamen pericial y carta formal de reclamación).

### Qué decir en voz alta (35 segundos):
> *"Aquí vemos a SupplyMind AI corriendo en vivo contra Grok-4.7 mediante la pasarela de Platica. El agente analiza el objetivo y decide de forma 100% autónoma qué herramientas invocar: primero extrae los documentos de la orden, ejecuta la conciliación matemática determinística en Python con precisión Decimal para no alucinar números, valida las cláusulas contractuales y emite el dictamen final con la carta legal de reclamo."*

---

## ⏱️ Bloque 3 (0:50 – 1:25) | Manejo de Errores y Auto-Recuperación en Vivo

### Qué mostrar en pantalla:
Ejecutar el script de auto-recuperación:
```powershell
python scripts/demo_error_recovery.py
```
Se observa en consola la inyección de un comprobante de pago severamente truncado con comentarios ilegales, el fallo de `json.loads` estándar, y la auto-reparación agéntica en 3 milisegundos sin abortar la ejecución.

### Qué decir en voz alta (35 segundos):
> *"La verdadera autonomía se demuestra ante fallos. Inyectamos a propósito un archivo de pago comercial corrupto y truncado. Python estándar colapsa con JSONDecodeError. SupplyMind AI intercepta la anomalía, activa su parser resiliente con balance LIFO de delimitadores, repara la estructura en solo tres milisegundos y completa la auditoría financiera sin detenerse ni requerir intervención humana."*

---

## ⏱️ Bloque 4 (1:25 – 2:00) | Datos Reales del Dominio (DataCo), Costo Medido y Cierre Concreto

### Qué mostrar en pantalla:
1. Ejecutar el benchmark sobre los 30 casos reales de DataCo:
```powershell
python scripts/benchmark_50_cases.py --cases-dir data/real_supply_chain_cases --mode fast_no_cache
```
2. Mostrar el manifiesto oficial de las 10 ejecuciones registradas:
```powershell
Get-Content reports/live_executions_manifest.md -TotalCount 25
```

### Qué decir en voz alta (35 segundos):
> *"Operamos sobre datos reales del dominio tomados de la base abierta DataCo Global Smart Supply Chain con 30 expedientes multiformato. La suite alcanza cien por ciento de acierto exacto con cero dólares de error aritmético. Medimos el costo real con la telemetría oficial de la pasarela: diez punto sesenta y seis dólares en novecientas cuarenta peticiones, lo que da un centavo de dólar por solicitud. En estos diez expedientes registrados recuperamos más de siete mil trescientos dólares indebidamente retenidos. Con SupplyMind AI, la cobranza B2B pasa de días a segundos con evidencia matemática irrefutable."*

---

## 📋 Resumen de Comandos del Video (Copiar y Pegar en Grabación)

| Segundo | Paso | Comando PowerShell |
|---|---|---|
| **0:15** | Agente en vivo contra Grok | `python -c "from agent.core.skynet_runner import SkynetRunner; r = SkynetRunner('dataco_real_001_caguas_pelican_kayak', fast_path=False); r.run()"` |
| **0:50** | Error y Auto-Recuperación | `python scripts/demo_error_recovery.py` |
| **1:25** | Benchmark 30 Casos DataCo | `python scripts/benchmark_50_cases.py --cases-dir data/real_supply_chain_cases --mode fast_no_cache` |
| **1:45** | 10 Ejecuciones Registradas | `Get-Content reports/live_executions_manifest.md -TotalCount 27` |
