# 🚀 Plan Maestro de Mejoras B2B — Fase 7: Superinteligencia Operativa, Prevención Causa Raíz y Cierre Financiero

**Proyecto:** SupplyMind AI Enterprise — Superinteligencia de Arbitraje y Operación B2B  
**Fase:** Fase 7 (Evolución de Frontera B2B: SLA Watchdog, Conciliación Bancaria EDI 820, Guardrail Relacional y Causa Raíz CAPA)  
**Versión:** 5.0 (SupplyMind Titan)  
**Fecha:** Noviembre 2026  
**Estado:** Listo para Implementación (Branch `develop`)  

---

## 🏛️ 1. Visión y Diagnóstico de Frontera ("The Why")

Tras consolidar en la Fase 6 la **confrontación bilateral en vivo (IA vs IA con MCTS)**, la **gobernanza con salvaguarda CFO para disputas $\ge \$10k$ USD** y el **despacho robótico a portales con sellos SHA-256**, el análisis del estado del arte empresarial (*Gartner Magic Quadrant Invoice-to-Cash*, arquitecturas de *HighRadius* y casuística real de retail en Norteamérica) reveló que los proveedores aún sufren fugas millonarias por cuatro motivos críticos:

1. **La Trampa de la Prescripción Silenciosa:** Más del 30% de los reclamos válidos son rechazados legalmente como extemporáneos porque vencen los plazos unilaterales de los portales (Amazon 30 días, Soriana 60 días, Walmart 90 días).
2. **El Agujero Negro de Tesorería:** Ganar un convenio no deposita el dinero en el banco. Los retailers pagan en remesas consolidadas (*EDI 820 / Remittance Advice*) que mezclan cientos de notas de crédito y retenciones, generando semanas de conciliación manual.
3. **El Riesgo de Ruptura Comercial:** Una confrontación excesivamente litigiosa con un comprador clave puede desencadenar represalias como reducción de órdenes de compra o des-catalogación de SKUs.
4. **La Trampa de la Fuga Recurrente:** Resolver disputas es reactivo; más del 65% de las deducciones obedecen a errores internos repetidos en el almacén (etiquetado GS1, emplaye o citas de entrega) que nadie retroalimenta en origen.

Esta **Fase 7** resuelve estos cuatro pilares para convertir a SupplyMind AI en el sistema B2B más completo, autónomo y preventivo del mercado.

---

## 🗺️ 2. Mapa de Arquitectura y Nuevos Módulos

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               SUPPLYMIND AI 5.0: PREVENCIÓN, GOBERNANZA Y CIERRE B2B                  │
├──────────────────────────────────────────┬─────────────────────────────────────────────┤
│   EJE 1: VIGILANCIA LEGAL & TESORERÍA    │   EJE 2: INTELIGENCIA RELACIONAL & CAPA     │
├──────────────────────────────────────────┼─────────────────────────────────────────────┤
│ • Watchdog de Prescripción SLA (DTP)     │ • Índice de Salud Relacional (RHI / LTV)    │
│ • Interrupción de Prescripción Art. 1041 │ • Dial Dinámico de Negociación Modulada     │
│ • Conciliador de Remesas EDI 820 / XML   │ • Motor de Diagnóstico Causa Raíz (RCA)     │
│ • Cierre Bancario y Liquidación a $0.00  │ • Generador de Tickets Preventivos CAPA     │
├──────────────────────────────────────────┴─────────────────────────────────────────────┤
│         CENTRO DE MANDO OBSIDIAN GLASS 3.0 (EXTENDED EXECUTIVE CONSOLE)                │
│ • Monitor Countdown de Vencimientos SLA  • Matriz de Fugas Operativas por Almacén    │
│ • Panel de Conciliación Bancaria 3-Way   • Visor y Exportador de Órdenes CAPA         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏃 3. Desglose de Sprints e Historias de Usuario

### ⏱️ Sprint 7.1: Watchdog de Prescripción Legal y Countdown de Vencimiento SLA
* **Objetivo:** Impedir que cualquier disputa válida expire o prescriba por falta de gestión oportuna.
* **Componentes Técnicos:** `agent/core/dispute_sla_watchdog.py`, `data/models.py`.

#### Historias de Usuario:
1. **US-701: Motor de Cuenta Regresiva de Prescripción (Days-to-Prescription - DTP):**
   - Configuración de ventanas perentorias oficiales por retailer:
     * Amazon Vendor Central: 30 días naturales (Shortage) / 60 días (Operational Chargebacks).
     * Soriana B2B: 60 días naturales desde emisión de contra-recibo.
     * Liverpool Partners: 60 días desde fecha de corte.
     * Walmart Retail Link: 90 días naturales desde fecha de factura.
     * Regla General (Código de Comercio): 120 días.
   - Cálculo dinámico de `days_to_expiration` y categorización de semáforo:
     * `CRITICAL_EXPIRED` (DTP $\le 0$): Disputa prescrita.
     * `HIGH_IMMINENT` (DTP $1 - 15$ días): Riesgo inminente de pérdida legal.
     * `MEDIUM_ATTENTION` (DTP $16 - 30$ días): Requiere careo prioritario.
     * `LOW_HEALTHY` (DTP $> 30$ días): Ventana operativa segura.
2. **US-702: Generador de Aviso de Interrupción de Prescripción Mercantil:**
   - Emisión formal de notificación mercantil basada en el **Artículo 1041 del Código de Comercio**.
   - Notificación preventiva con hash forense del expediente que congela e interrumpe el cómputo de la prescripción ante el retailer.

---

### 💳 Sprint 7.2: Motor de Conciliación de Remesas Bancarias y Cierre Order-to-Cash (EDI 820)
* **Objetivo:** Cerrar el ciclo financiero uniendo el convenio finiquito con el pago bancario real recibido, eliminando semanas de conciliación en tesorería.
* **Componentes Técnicos:** `agent/core/bank_remittance_reconciler.py`, `api/routes/remittance.py`.

#### Historias de Usuario:
1. **US-703: Parser de Remesas Masivas Consolidadas (EDI 820 / CAMT.053 / CSV Bancario):**
   - Extracción de depósitos brutos, retenciones aplicadas, notas de crédito descontadas y referencias de pago bancario.
2. **US-704: Motor de Conciliación Tripartita (3-Way Settlement Matcher):**
   - Cruce algorítmico exacto:
     $$\text{Factura Original} - \text{Deducción Retailer} + \text{Monto Recuperado Convenio} = \text{Depósito Neto Bancario}$$
   - Tolerancia de centavos: $0.00 MAE (Aritmética `Decimal` estricta).
   - Generación del **Certificado de Cierre y Liquidación de Cartera** con saldo residual cero, liberando el expediente en el ERP.

---

### 🤝 Sprint 7.3: Guardrail de Salud Relacional y Riesgo de Deserción (LTV & Churn Index)
* **Objetivo:** Evitar que el agente dañe relaciones comerciales estratégicas al litigar contra compradores clave de los que depende la empresa.
* **Componentes Técnicos:** `agent/core/relational_health_engine.py`.

#### Historias de Usuario:
1. **US-705: Índice de Salud Relacional (Relationship Health Index - RHI):**
   - Ponderación de 4 factores:
     * *Customer Lifetime Value (LTV):* Volumen de ventas anual del cliente.
     * *Concentración de Cartera (% Share of Wallet):* Dependencia económica del proveedor.
     * *Margen Comercial Bruto:* Rentabilidad de la cuenta.
     * *Historial de Reciprocidad:* Tasa de cumplimiento en acuerdos pasados.
2. **US-706: Modulación Dinámica de la Agresividad Negociadora:**
   - **Modo Diplomático / Preservativo (RHI Alto > 80 pts):** Concesiones moderadas a cambio de volumen futuro o compromisos de órdenes de compra; lenguaje formal y colaborativo.
   - **Modo Firme / Comercial (RHI Medio 50 - 80 pts):** Negociación equilibrada 50/50 respaldada por precedentes y evidencia de muelle.
   - **Modo Asertivo / Litigioso (RHI Bajo < 50 pts):** Cero concesiones en faltantes injustificados; máxima firmeza legal e invocación de cláusulas de incumplimiento.

---

### 🛡️ Sprint 7.4: Inteligencia Preventiva de Causa Raíz y Alertas CAPA (Closed-Loop RCA)
* **Objetivo:** Detener la sangría financiera en origen diagnosticando qué departamento interno generó la deducción y emitiendo acciones correctivas.
* **Componentes Técnicos:** `agent/core/root_cause_analyzer.py`, `agent/core/capa_ticket_generator.py`.

#### Historias de Usuario:
1. **US-707: Motor de Diagnóstico de Causa Raíz Longitudinal (RCA Engine):**
   - Análisis de patrones a través de toda la base de expedientes (los 50 casos del benchmark).
   - Atribución causal de cuatro frentes:
     * *Almacén / CEDIS:* Empaque deficiente, tarima no normalizada, etiqueta GS1-128 ilegible.
     * *Transporte / Logística:* Cita incumplida (OTIF tardío), rotura de frío, sello violentado.
     * *Sistemas / EDI:* Desfase en envío de ASN 856 vs arribo de camión, error en catálogo de SKUs.
     * *Ventas / Comercial:* Descuentos promocionales no registrados o precios desfasados en OC.
2. **US-708: Generador de Tickets Preventivos y Correctivos (CAPA):**
   - Emisión automática de órdenes de mejora dirigidas al responsable (ej. "Jefe de Almacén - Turno B", "Coordinador de Línea Transportista").
   - Checklist operativo para evitar multas repetidas en los próximos embarques.

---

### 💻 Sprint 7.5: Consola Ejecutiva Obsidian Glass 3.0 (Módulo de Tesorería & Prevención)
* **Objetivo:** Proporcionar al CFO y al equipo de operaciones visibilidad en tiempo real de vencimientos, conciliación de remesas y causa raíz en React 19 y Streamlit.
* **Componentes Técnicos:** `frontend/src/components/`, `dashboard.py`.

#### Historias de Usuario:
1. **US-709: Monitor de Vencimientos SLA y Tesorería:**
   - Semáforo interactivo con cuenta regresiva en días para prescripción de cada cliente.
   - Botón de disparo rápido: *"Emitir Notificación de Interrupción Art. 1041 CCom"*.
2. **US-710: Centro de Causa Raíz y Banco de Acciones CAPA:**
   - Gráfico de torta/barras de fugas de dinero por departamento responsable.
   - Visor y descargador de planes de acción CAPA en PDF/Markdown.

---

## 📊 4. Matriz de Entregables, Criterios de Aceptación y DoD

| Sprint | Módulo Central | Criterio de Aceptación Clave | DoD (Definición de Hecho) |
| :--- | :--- | :--- | :--- |
| **7.1** | SLA Watchdog | Identifica con 100% de exactitud días a prescripción por retailer y emite aviso Art. 1041. | Tests unitarios de cálculo DTP pasando; generador de aviso validado. |
| **7.2** | Conciliador EDI 820 | Conciliación de remesa con diferencia de $0.00 centavos (`Decimal` exacto). | Parser EDI 820 funcional y certificado de liquidación generado. |
| **7.3** | Guardrail Relacional | Ajusta dinámicamente la agresividad del careo según el LTV y margen de la cuenta. | Matriz RHI documentada y acoplada al motor de negociación. |
| **7.4** | Causa Raíz & CAPA | Clasifica el origen de deducciones de 50 casos en los 4 departamentos e imprime ticket. | Motor RCA clustering y tickets CAPA generados en `reports/capa/`. |
| **7.5** | Obsidian Glass UI | Vistas en React 19 y Streamlit que permiten operar y auditar todo el nuevo pipeline. | Compilación sin errores (`npm run build`), diseño responsive y fluido. |

---

## 🔒 5. Principios Inquebrantables de Ingeniería

1. **Aritmética Cero-Alucinación:** Toda suma, resta o liquidación financiera debe usar `Decimal` de Python ($0.00 MAE). Queda prohibido el uso de flotantes `IEEE 754` en conciliación.
2. **Gobernanza y Separación de Ramas:** Todo el desarrollo se realizará en la rama `develop`, validando con pruebas unitarias y compilación antes del merge final a `main`.
3. **Cero Dependencias Huérfanas:** Cada ticket CAPA o aviso de prescripción debe estar estrictamente anclado al expediente físico y contractual del caso correspondiente.
