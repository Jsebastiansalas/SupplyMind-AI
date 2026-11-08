# 🛰️ Radar de Fuga de Capital y Perfilado de Retailers (Eje 4)
## SupplyMind AI Enterprise — Inteligencia de Cartera y Prevención Pre-Despacho
**Fecha de Emisión:** 2026-11-05T00:19:15.746931+00:00  
**Expedientes Totales Auditados:** 82 casos  
**Tasa de Efectividad Proyectada (Win Rate):** 57.3%  

---

### 💰 1. Métricas Consolidadas de Capital de la Cartera

| Métrica Financiera | Monto (USD) | Interpretación Operativa |
| :--- | :---: | :--- |
| **Volumen Total Disputado** | **$798,216.54 USD** | Monto retenido o descontado unilateralmente en remesas |
| **Capital Recuperable (Ganable)** | **$457,707.31 USD** | Fondos recuperables con sustento documental y legal |
| **Fuga Neta en Riesgo** | **$340,509.23 USD** | Capital expuesto a pérdida si no se actúa dentro del plazo |
| **Ratio de Recuperación Global** | **57.3%** | Eficiencia defensiva calculada en partida doble |

---

### 🏢 2. Ranking de Riesgo y Perfilado por Retailer

| Retailer / Cadena Comercial | Nivel de Riesgo | Win Rate | Vol. Disputado | Capital Recuperable | Patrón Sistemático Principal | Incoterm Sugerido |
| :--- | :---: | :---: | :---: | :---: | :--- | :---: |
| **Amazon Fulfillment Services (CUST-RETAIL-AMZN)** | 🟠 ALTO | 92.4% | $14,800.00 | $8,695.08 | Penalización Automatizada de ASN EDI 856 | `FCA` |
| **Walmart Inc. & Retail Link (CUST-RETAIL-WMT)** | 🔴 PREDATORIO | 89.1% | $460,540.00 | $284,488.50 | Deducción Extemporánea de Pronto Pago (Fin de Mes) | `FOB` |
| **Cisco Systems Global Supply (CUST-RETAIL-CSCO)** | 🟡 MEDIO | 95.0% | $42,949.88 | $28,650.00 | Deducción de Margen por Desglose de Bundles | `CIP` |
| **The Home Depot Supply Chain (CUST-RETAIL-HD)** | 🟡 MEDIO | 91.5% | $11,349.95 | $7,149.95 | Rechazo por Daño Cosmético de Empaque Exterior | `FOB` |
| **Mega Retailer Global Corp (CUST-RETAIL-MEGA)** | 🟠 ALTO | 94.8% | $187,500.00 | $70,500.00 | Retención Cautelar por Auditoría Masiva Multi-SKU | `FOB` |
| **Organización Soriana S.A.B. de C.V. (CUST-RETAIL-SOR)** | 🟠 ALTO | 88.5% | $16,850.00 | $15,850.00 | Deducción Unilateral de Rebate Extracontractual | `FOB` |
| **Grupo Comercial Chedraui S.A.B. de C.V. (CUST-RETAIL-CHED)** | 🟡 MEDIO | 92.0% | $14,699.98 | $12,399.98 | Retención por Flete Compartido en Maniobra | `FCA` |
| **El Puerto de Liverpool S.A.B. de C.V. (CUST-RETAIL-LIV)** | 🟡 MEDIO | 93.4% | $23,649.99 | $15,950.00 | Multa por Defecto Óptico en Etiqueta de Colgado | `FOB` |
| **DataCo Global Smart Supply Chain (Real Dataset Benchmark)** | 🟡 MEDIO | 94.0% | $25,876.74 | $14,023.80 | Penalización por Retraso Transfronterizo no Imputable | `FOB` |

---

### 🚛 3. Centros de Distribución (CEDIS) y Hubs de Alta Fricción

| Hub / Muelle Logístico | Ubicación | Calificación Riesgo | Tasa Merma Histórica | Tipologías Frecuentes | Salvaguarda Mandatoria |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Walmart México (WALMART_DC_6014)** | San Martín Obispo / Cuautitlán | 🔴 CRÍTICO | 4.8% | OTIF_LATE_DELIVERY, ASN_EXTEMPORANEO | Ventana de muelle estricta de 2 horas. Si el transportista llega 15 minutos tarde, cancelan cita y aplican multa del 3%. |
| **Amazon Fulfillment Services (AMAZON_FC_DFW)** | Dallas-Fort Worth FC (DFW) | 🟠 ALTO | 3.8% | RECEIVING_SHORTAGE, BARCODE_UNREADABLE | Escaneo automatizado por bandas transportadoras. Alta tasa de falsos faltantes en tarimas multi-SKU. |
| **Tiendas Soriana (SORIANA_DC_TULTITLAN)** | Tultitlán, Edo. Mex. | 🟠 ALTO | 4.2% | REBATE_UNILATERAL, MERMA_OPERATIVA_NO_PACTADA | Rechazo de tarimas por astillamiento leve o falta de precinto térmico. |
| **El Puerto de Liverpool (LIVERPOOL_CUAUTITLAN)** | Cuautitlán Izcalli | 🟡 MODERADO | 2.5% | ETIQUETA_COLGADO_ERRONEA, DESCUENTO_FINANCIERO_ABUSIVO | Penalización por código de barras GS1 no centrado o fuera de altura reglamentaria. |

---

### 🛡️ 4. Protocolo Operativo Pre-Despacho (Salvagardas Obligatorias)

1. **Protocolo Fotográfico 4 Ángulos:** Registro obligatorio de estiba y precinto C-TPAT antes de cierre de remolque.
2. **Transmisión Anticipada EDI 856:** Emisión del ASN al menos 4 a 6 horas antes de la cita de muelle con acuse EDI 997.
3. **Sello Limpio de Caseta (Gate-In Time):** Registrar hora de arribo a patio para invalidar penalizaciones OTIF indebidas.
4. **Certificación de Tarimas CHEP Grado A:** Cero astillamiento y sin salientes de caja (Zero Pallet Overhang).
5. **Leyenda Contractual Anti-Extemporánea:** Cláusula expresa de caducidad de descuento por pronto pago al día 10 natural.

---

### ⚖️ 5. Directivas Ejecutivas para Dirección de Finanzas y Cobranza

- **Directiva 1:** Migrar términos de contratación con retailers de nivel PREDATORIO (ej. Walmart) hacia Incoterm FOB/FCA en origen.
- **Directiva 2:** Blindar el 57.3% de tasa de recuperación mediante contestación legal inmediata dentro de los primeros 15 días.
- **Directiva 3:** Instalar escaneo RFID de tarima completa para anular la deducción por auditoría masiva en órdenes multi-SKU.
- **Directiva 4:** Exigir a transportistas el sellado de la carta porte bajo el Art. 88 del Código de Comercio.
