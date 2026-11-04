# ORDEN DE INGENIERÍA PREVENTIVA — TICKET CAPA `CAPA-2026-203D55`
**SISTEMA DE GESTIÓN DE CALIDAD Y PREVENCIÓN DE FUGAS B2B (CLOSED-LOOP RCA)**

---
- **ID de Ticket CAPA:** `CAPA-2026-203D55`
- **Expediente Origen:** `dataco_real_001_caguas_pelican_kayak` (Factura: `INV-DATACO_REAL_`)
- **Cliente / Retailer Afectado:** Cadena Comercial Mayorista B2B
- **Departamento Interno Responsable:** **Sistemas / Integración EDI B2B** (`SYSTEMS_EDI`)
- **Líder Operativo Asignado:** **Arquitecto Senior de Integración EDI X12 / ERP**
- **Severidad / Prioridad:** `MEDIUM` (SLA de Implementación: `72 horas`)
- **Impacto Financiero en Disputa:** **$1,099.97 USD** (Fuga Justificada: `$599.97 USD`)
- **Fecha de Emisión UTC:** `2026-11-04T11:53:21.531516+00:00`

---

### I. DIAGNÓSTICO DE CAUSA RAÍZ (HALLAZGO DE AUDITORÍA)

- **Dictamen del Agente SupplyMind:** Discrepancia mixta en expediente dataco_real_001_caguas_pelican_kayak: Faltante físico comprobado de $599.97 USD amparado en remisión firmada con sello, y retenciones no autorizadas por $500.00 USD sin sustento contractual ni documental.
- **Anomalía Operativa Detectada:** Desfase entre la confirmación del ASN EDI 856 y el escaneo automatizado en muelle del Fulfillment Center, aunado a discrepancia de unidad de medida Master Case.

### II. PLAN DE ACCIÓN CORRECTIVA INMEDIATA (CAPA)

1. Configurar trigger automático en ERP para transmitir el ASN EDI 856 en el instante de cierre de embarque (mínimo 2h antes de arribo).
2. Implementar bloqueo de salida en caseta de vigilancia si no se ha recibido el Acuse Funcional EDI 997 Status 'A' (Aceptado).
3. Auditar y homologar la tabla de equivalencias SKU / GTIN-14 / Inner-Pack contra el catálogo EDI 832 vigente del Retailer.

### III. CHECKLIST MANDATORIO PRE-DESPACHO (CANDADO DE SALIDA)

- [ ] Transmisión ASN EDI 856 enviada con estructura jerárquica Shipment -> Order -> Tare (Pallet) -> Pack -> Item.
- [ ] Recepción confirmada de Acuse Funcional EDI 997 Status 'A' sin segmentos AK4 de error.
- [ ] Coincidencia exacta 1:1 entre SSCC-18 físico impreso en tarima y segmento MAN*GM del ASN 856.
- [ ] Validación de unidades de facturación (EA vs CA) sincronizada con la Orden de Compra EDI 850.

---
**Estado del Ticket:** `OPEN_ASSIGNED`  
**Generado Automáticamente por:** SupplyMind AI — Motor Preventivo RCA (Fase 7)
