# PÓLIZA CONTABLE DE SANEAMIENTO Y REGULARIZACIÓN FISCAL
**Expediente:** `case_005_amazon_shortage` | **Norma:** NIF C-3 / US GAAP | **Fecha:** 2026-11-05 00:19:12 UTC  
**Contraparte:** AMAZON FULFILLMENT SERVICES LLC DE MEXICO (RFC: `AMA120401BB2`)  
**Régimen Tributario:** Régimen General IVA 16% (Art. 1 LIVA) (Código SAT: `STANDARD_VAT_16`)  
**Factor Impositivo:** `1.16` | **Objeto de Impuesto SAT:** `02`  

---

### 1. Asiento de Diario de Partida Doble

| Línea | Cuenta Contable | Concepto | Cargo (Debit USD) | Abono (Credit USD) |
| :---: | :--- | :--- | :---: | :---: |
| 1 | `410500` | Descuentos y Bonificaciones sobre Ventas | `$4,310.34` | `$0.00` |
| 2 | `210800` | IVA Trasladado por Cancelar (16%) | `$689.66` | `$0.00` |
| 3 | `120090` | Deudores en Disputa / Saldo Reclamable | `$2,500.00` | `$0.00` |
| 4 | `120000` | Clientes / Cuentas por Cobrar B2B | `$0.00` | `$7,500.00` |

---

### 2. Cuadratura Contable Estricta:
- **Total Cargos (Debits):** **`$7,500.00 USD`**
- **Total Abonos (Credits):** **`$7,500.00 USD`**
- **Diferencia Neta:** **`$0.00 USD`** (Cuadre perfecto de partida doble ✅)

### 3. Timbrado Fiscal CFDI 4.0 Oficial (SAT PAC):
- **Folio Fiscal UUID Certificado:** `690CE4E3-B41A-483D-B831-901BE1B65D3E`
- **Tipo de Comprobante:** `E` (Egreso / Nota de Crédito)
- **Certificado SAT:** `00001000000504465028`
- **Fecha y Hora de Timbrado:** `2026-11-05T00:19:12`
- **Clave SAT Prod/Serv:** `84111506` (Servicios de facturación y saneamiento de cartera)
- **URL de Validación con Código QR:** [https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?id=690CE4E3-B41A-483D-B831-901BE1B65D3E&re=SMI20260101AA1&rr=AMA120401BB2&tt=5000.00&fe=1zXd/Lo=](https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?id=690CE4E3-B41A-483D-B831-901BE1B65D3E&re=SMI20260101AA1&rr=AMA120401BB2&tt=5000.00&fe=1zXd/Lo=)

### 4. Interoperabilidad B2B EDI 812 (Retail Link / Vendor Central):
- **Estándar:** ANSI ASC X12 Transaction Set 812 (Credit/Debit Adjustment)
- **Segmentos Principales:** `ISA` -> `GS*CD` -> `ST*812` -> `BCD*CR` -> `CDD` -> `AMT*TT` -> `AMT*JD` -> `AMT*RC`
- **Archivo Generado:** `reports/erp_case_005_amazon_shortage/edi_812_credit_debit_adjustment.x12`
- **UN/EDIFACT Mensaje:** `reports/erp_case_005_amazon_shortage/edifact_credit_advice.edi`
