# 🚀 Plan Maestro — Semana 3: SupplyMind AI Enterprise
**Objetivo:** Consolidar la madurez de producción con **Datos Reales**, un **Set de Evaluación Propio de 30+ Casos (Benchmark Suite)** con Ground Truth pericial, y un **Reporte Detallado de Costo por Tarea (Unit Economics)**.

---

## 🏛️ 1. Estructura de Sprints de la Semana 3

```
┌────────────────────────────────────────────────────────────────────────┐
│                      CRONOGRAMA DE SPRINTS SEMANA 3                    │
├────────────────────────────────────────────────────────────────────────┤
│ Sprint 3.1: Ingesta de Datos Reales & Topología B2B Auténtica           │
│   ├── US-301: Generador de Casos con Datos Comerciales Reales          │
│   └── US-302: Catálogo de Retailers y Matriz de Deducciones Reales     │
│                                                                        │
│ Sprint 3.2: Set de Evaluación Propio de 30+ Casos (Benchmark Suite)    │
│   ├── US-303: Matriz de Ground Truth Pericial y 35 Casos Tipológicos   │
│   └── US-304: Runner Automatizado de Benchmark y Métricas Estadísticas │
│                                                                        │
│ Sprint 3.3: Reporte de Costos por Tarea (Unit Economics)               │
│   ├── US-305: Telemetría Granular de Costos y Tokens por Tarea ReAct   │
│   └── US-306: Reporte Financiero Comparativo (Humano vs SupplyMind AI) │
│                                                                        │
│ Sprint 3.4: Visualización Ejecutiva en Frontend y Terminal             │
│   ├── US-307: Componente de Benchmark Scoreboard en React              │
│   └── US-308: Comando CLI de Benchmark Masivo (`python main.py bench`) │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🏃 SPRINT 3.1: Ingesta de Datos Reales & Topología B2B Auténtica
**Meta del Sprint:** Dotar al sistema de datos comerciales indistinguibles de una operación B2B real (formatos CFDI 4.0 con UUIDs válidos, remisiones con firmas autógrafas de muelle, penalizaciones logísticas EDI 856, contratos marco con cláusulas reales y variación FX).

### 📋 Historia de Usuario 301: Generador de Casos con Datos Comerciales Reales
* **Identificador:** `US-301`
* **Como:** Auditor Contable y Especialista en Conciliación B2B,
* **Quiero:** Que el sistema cuente con expedientes que repliquen transacciones reales de la industria de retail, consumo masivo, tecnología y farmacéutica,
* **Para:** Evaluar el comportamiento del agente frente a la complejidad, ruido, códigos de barras, SKUs largos y deducciones auténticas de grandes compradores.

#### Criterios de Aceptación (Gherkin):
* **Escenario 1: Consistencia de documentos comerciales interrelacionados**
  - **Dado** un caso generado con datos de retail real (ej. Walmart o Amazon),
  - **Cuando** el agente procese la Orden de Compra, Factura CFDI, Remisión de Entrega y Comprobante de Pago,
  - **Entonces** los números de parte, descripciones comerciales, impuestos (IVA 16%), retenciones y sellos de muelle deben coincidir exactamente con los estándares fiscales y logísticos de México y Norteamérica.
* **Escenario 2: Variabilidad de tipologías documentales**
  - **Dado** un caso con discrepancia mixta (faltante + merma + penalización ASN),
  - **Cuando** se cargue el expediente,
  - **Entonces** cada documento debe contener los metadatos reales correspondientes (UUID fiscal SAT de 36 caracteres, número de folio de muelle, hora exacta de entrega y sello de recibidor).

#### Definición de Hecho (DoD):
- [ ] Generador paramétrico en Python capaz de sintetizar expedientes completos con estructura física y contractual real.
- [ ] Soporte para JSON y PDF con visualización de remisiones firmadas.
- [ ] Validación Pydantic estricta de todos los documentos generados.

---

### 📋 Historia de Usuario 302: Catálogo de Retailers y Matriz de Deducciones Reales
* **Identificador:** `US-302`
* **Como:** Gerente de Cuentas por Cobrar,
* **Quiero:** Contar con reglas de deducción específicas para los principales compradores de la región (Amazon, Walmart, OXXO, Mercado Libre, Liverpool, Chedraui, Home Depot, Cisco),
* **Para:** Identificar de forma automática deducciones abusivas basadas en los manuales de proveedores de cada comprador.

#### Criterios de Aceptación:
* **Escenario 1: Detección de penalizaciones logísticas típicas**
  - **Dado** un pago de Amazon con código de retención `ASN-LATE-EDI856`,
  - **Cuando** el agente evalúe el contrato comercial,
  - **Entonces** debe dictaminar si la penalización es procedente según los plazos estipulados o improcedente por falta de notificación previa en menos de 48 horas.
* **Escenario 2: Descuentos financieros de pronto pago extemporáneos**
  - **Dado** una retención de pronto pago (`EARLY-PAY-2%`) aplicada por Walmart a los 45 días,
  - **Cuando** la factura estipule pago a 15 días para aplicar descuento,
  - **Entonces** el agente debe declarar extemporáneo e improcedente el descuento del 2% y marcarlo como 100% reclamable.

---

## 🏃 SPRINT 3.2: Set de Evaluación Propio de 30+ Casos (Benchmark Suite)
**Meta del Sprint:** Crear un benchmark representativo con **35 casos exhaustivos**, cada uno con su Ground Truth verificado, cubriendo el 100% de las tipologías de discrepancia comercial B2B.

### 📊 Matriz de los 35 Casos del Benchmark

| ID del Caso | Empresa Compradora | Giro / Industria | Monto Disputa | Tipología Principal de Discrepancia | Ground Truth (Reclamable) |
| :--- | :--- | :--- | :---: | :--- | :---: |
| `case_001` | Retail General | Consumo Masivo | $800.00 | Faltante Físico Acordado en Muelle | **$300.00** |
| `case_002` | Cadena Departamental | Ropa y Calzado | $16,500.00 | Dañado no probado + Multa ilegal | **$12,500.00** |
| `case_003` | Distribuidor Mayorista | Alimentos Secos | $3,000.00 | Discrepancia de Precio Factura vs PO | **$0.00** |
| `case_004` | Enterprise B2B | Electrónica | $12,000.00 | Penalización Extemporánea OTIF | **$8,500.00** |
| `case_005` | Amazon México | E-Commerce / Fulfillment | $7,500.00 | Dock Shortage y Multa ASN EDI 856 | **$2,500.00** |
| `case_006` | Walmart México | Supermercados | $8,000.00 | Descuento Pronto Pago Extemporáneo | **$4,000.00** |
| `case_007` | Cisco Systems | Infraestructura IT | $27,000.00 | Bundle Complejo 25 Partes con Licencias | **$12,000.00** |
| `case_008` | Home Depot | Construcción / Ferretería | $10,500.00 | Avería Parcial con Remisión Escaneada | **$6,500.00** |
| `case_009` | Mega Retailer S.A. | Cadena Nacional | $75,000.00 | Mega Expediente Masivo de 40 SKUs | **$22,500.00** |
| `case_010` | Mercado Libre | Marketplace / Envíos Full | $5,400.00 | Extravío en Cross-Docking Logístico | **$5,400.00** |
| `case_011` | OXXO / FEMSA | Conveniencia | $3,200.00 | Merma por Caducidad Corta no Pactada | **$3,200.00** |
| `case_012` | Liverpool | Tiendas Departamentales | $18,400.00 | Cargo por Etiquetado y Colgado Incompleto| **$11,000.00** |
| `case_013` | Chedraui | Autoservicio | $6,100.00 | Diferencia en Tarifa de Flete Compartido | **$3,800.00** |
| `case_014` | Soriana | Autoservicio | $9,800.00 | Rebate Comercial no Acordado por Escrito | **$9,800.00** |
| `case_015` | Costco Wholesale | Club de Precios | $14,200.00 | Tarima Rechazada por Daño en Embalaje | **$4,200.00** |
| `case_016` | Nestlé Alimentos | Proveedor / Copacker | $21,000.00 | Lote Parcial Retenido por Cuarentena Lab | **$7,000.00** |
| `case_017` | Unilever México | Cuidado Personal | $11,500.00 | Penalización por Despacho Fuera de Cita | **$5,500.00** |
| `case_018` | Farmacias del Ahorro| Sector Farmacéutico | $8,900.00 | Diferencia en Tasa de Descuento Especial | **$4,900.00** |
| `case_019` | Sanborns | Retail Mixto | $4,500.00 | Deducción por Devolución de Temporada | **$4,500.00** |
| `case_020` | Grupo Modelo | Bebidas / Consumo | $32,000.00 | Discrepancia en Envase Retornable y Tarimas| **$18,000.00** |
| `case_021` | Samsung Electronics | Tecnología / Displays | $45,000.00 | Varianza Cambiaria FX DOF vs Factura | **$15,000.00** |
| `case_022` | LG Electronics | Línea Blanca / Electro | $28,000.00 | Venta Incoterm FOB con Merma en Alta Mar | **$28,000.00** |
| `case_023` | Apple Retail MX | Tecnología de Consumo | $52,000.00 | Retención por Garantías de Usuario Final | **$34,000.00** |
| `case_024` | PepsiCo Alimentos | Botanas y Bebidas | $13,600.00 | Cargo de Cooperación Publicitaria No Pactada| **$13,600.00** |
| `case_025` | Miniso México | Retail Variedades | $7,800.00 | Faltante en Contenedor Marítimo CIF | **$2,800.00** |
| `case_026` | Truper Herramientas | Ferretero Mayorista | $19,500.00 | Devolución Extemporánea a los 90 Días | **$19,500.00** |
| `case_027` | Biofarma Labs | Farma / Insumos | $16,800.00 | Termo-registro Roto en Transporte Frío | **$0.00** (Justificado) |
| `case_028` | Zara / Inditex | Textil Fast Fashion | $22,300.00 | Discrepancia de Tallas y Colores en Matriz | **$8,300.00** |
| `case_029` | Sony Intermédica | Dispositivos Médicos | $38,000.00 | Retención por Calibración en Destino | **$24,000.00** |
| `case_030` | Petco México | Mascotas / Retail | $5,900.00 | Multa por Código UPC No Escaneable | **$2,900.00** |
| `case_031` | Retail Desconocido | Caso Adversario | $50,000.00 | Inyección de Monto Falso en Descripción | **Rechazado (Ancla)** |
| `case_032` | Bodega Aurrerá | Caso Cuarentena | $9,000.00 | Contaminación Cruzada: Remisión de Soriana | **Bloqueo Cuarentena** |
| `case_033` | Cedis Monterrey | Caso Fecha Anacrónica | $15,000.00 | Pago realizado 3 meses antes de Factura | **Bloqueo Cuarentena** |
| `case_034` | Distribuidora Norte | Caso JSON Corrupto | $8,200.00 | Comas colgantes y comillas rotas | **Auto-Reparado** |
| `case_035` | Mega Distribución | Caso Mega Lote 60 SKUs| $120,000.00 | Operación Masiva Multimodal 60 SKUs | **$35,000.00** |

---

### 📋 Historia de Usuario 303: Suite de Benchmark Automatizada de 35 Casos
* **Identificador:** `US-303`
* **Como:** Jurado Evaluador y Líder Técnico de Supply Chain,
* **Quiero:** Ejecutar una suite automatizada que corra los 35 casos y compare el dictamen del agente contra el Ground Truth matemático,
* **Para:** Medir con rigor científico la precisión, el recall, la tasa de error aritmético y la tasa de alucinación cero.

#### Criterios de Aceptación:
* **Escenario 1: Precisión Aritmética 100%**
  - **Dado** el set de 35 casos del benchmark,
  - **Cuando** se ejecute `python scripts/benchmark_30_cases.py`,
  - **Entonces** la discrepancia matemática entre Facturado, Recibido, Justificado y Reclamable debe ser de $0.00 en el 100% de los casos evaluados (conservación estricta de la ecuación contable).
* **Escenario 2: Cuarentena y Casos Adversarios**
  - **Dado** los casos 31, 32 y 33 (adversarios y contaminados),
  - **Cuando** el agente procese los expedientes,
  - **Entonces** debe activar el Protocolo de Cuarentena Forense y bloquear la emisión de notas de crédito en el 100% de ellos.

---

## 🏃 SPRINT 3.3: Reporte de Costos por Tarea (Unit Economics)
**Meta del Sprint:** Desglosar y certificar el costo financiero real de inferencia por cada tarea del agente, comparándolo contra el costo de un equipo de analistas humanos.

### 📋 Historia de Usuario 304: Auditoría y Telemetría de Costo por Tarea
* **Identificador:** `US-304`
* **Como:** Director Financiero (CFO),
* **Quiero:** Un reporte granular de costo en dólares y consumo de tokens desglosado por cada tarea que ejecuta el agente,
* **Para:** Conocer con exactitud el costo unitario de auditar expedientes simples vs complejos vs masivos de 60 SKUs.

#### Criterios de Aceptación:
* **Escenario 1: Desglose por fases operativas**
  - **Dado** un expediente auditado por el agente,
  - **Cuando** se genere el reporte de telemetría contable,
  - **Entonces** debe especificar tokens de entrada, tokens de salida, costo USD de Platica Gateway (Grok 4.7) y latencia en milisegundos para:
    * Ingesta y normalización documental
    * Conciliación matemática y matching de SKUs
    * Evaluación pericial de cláusulas contractuales
    * Síntesis de dictamen y prueba ZKP
    * Generación de póliza ERP y CFDI 4.0

```
┌────────────────────────────────────────────────────────────────────────┐
│                   DESGLOSE DE COSTO POR TAREA (USD)                   │
├──────────────────────────────┬──────────────┬─────────────┬────────────┤
│ Tarea Operativa              │ Tokens In    │ Tokens Out  │ Costo USD  │
├──────────────────────────────┼──────────────┼─────────────┼────────────┤
│ 1. Ingesta y OCR Documental  │ 650 tokens   │ 80 tokens   │ $0.00080   │
│ 2. Conciliación Matemática   │ Python Local │ Decimal     │ $0.00000   │
│ 3. Evaluación Contractual    │ 850 tokens   │ 220 tokens  │ $0.00175   │
│ 4. Síntesis y Prueba ZKP     │ 450 tokens   │ 180 tokens  │ $0.00095   │
│ 5. Póliza ERP y CFDI 4.0     │ Python Local │ Asiento NIF │ $0.00000   │
├──────────────────────────────┼──────────────┼─────────────┼────────────┤
│ TOTAL POR CASO COMPLETO      │ 1,950 tokens │ 480 tokens  │ $0.00350   │
└──────────────────────────────┴──────────────┴─────────────┴────────────┘
```

---

## 🏃 SPRINT 3.4: Visualización Ejecutiva en Frontend y Terminal
**Meta del Sprint:** Presentar el Benchmark de 35 casos y el Reporte de Costos tanto en la interfaz React Obsidian Glass como en la consola interactiva CLI.

### 📋 Historia de Usuario 305: Pantalla de Benchmark & Unit Economics en React
* **Identificador:** `US-305`
* **Como:** Evaluador o Usuario Enterprise,
* **Quiero:** Una pestaña en la plataforma web que despliegue la matriz de los 35 casos, sus puntuaciones periciales, y el análisis comparativo financiero humano vs agente,
* **Para:** Auditar el desempeño del sistema de forma interactiva y visual.

---

## 🎯 Criterios Globales de Éxito de la Semana 3
1. **35 de 35 casos evaluados** con Ground Truth verificado.
2. **Cero alucinación matemática:** Error cuadrático de saldos = 0.00 centavos.
3. **Costo promedio por caso:** Menor a $0.005 USD.
4. **Tiempo de ejecución suite completa:** Menor a 45 segundos.
5. **Cobertura de pruebas:** Batería pytest ampliada a más de 45 pruebas unitarias y de estrés.
