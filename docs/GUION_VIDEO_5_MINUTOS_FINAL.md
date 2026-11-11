# 🎬 Guion Maestro de Grabación — Video Oficial de 5 Minutos (Reto Agente Platica Track 1)

> [!TIP]
> **Por qué este guion maximiza los 100 puntos de la Rúbrica Track 1:**  
> *"Un buen agente mal explicado pierde puntos: cuida el video y el reporte."*  
> Este guion de **5:00 minutos exactos** asigna el tiempo de pantalla en proporción directa al puntaje de cada eje del jurado:
> * **Bloque 1 (0:00 – 0:50) | Impacto del Problema + Arranque en 1 Comando (25 pts)**
> * **Bloque 2 (0:50 – 2:05) | Autonomía, Herramientas Reales y OCR Multimodal (25 pts)**
> * **Bloque 3 (2:05 – 3:05) | Ingeniería Neuro-Simbólica sobre Grok-4.7 y Guardrails (20 pts)**
> * **Bloque 4 (3:05 – 4:00) | Evidencia con Datos Reales (DataCo) y Carga de 1,024 Unidades (15 pts)**
> * **Bloque 5 (4:00 – 5:00) | Viabilidad, Bitácora de Consumo y Prueba en Vivo del Harness (15 pts)**

---

## 🖥️ Preparación de Pantalla Antes de Grabar (30 Segundos)

Divide tu monitor en **dos mitades**:
1. **Mitad Izquierda (60% del ancho):** Navegador en [`http://localhost:5173`](http://localhost:5173) con **SupplyMind AI** abierto en el caso `case_005_amazon_shortage` (o `case_009_mega_retailer_dispute`).
2. **Mitad Derecha (40% del ancho):** Terminal PowerShell limpia en la raíz del proyecto (`C:\Users\USUARIO\Downloads\platica`).

---

## ⏱️ Minuto a Minuto (Guion + Acciones en Pantalla)

### 🟢 BLOQUE 1 (0:00 – 0:50): Impacto del Problema y Reproducibilidad en 1 Comando (25 Puntos)

* **Acción en pantalla:**
  * Muestra brevemente el [`README.md`](../README.md) con la insignia **MIT License** y en el navegador la interfaz principal de **SupplyMind AI** mostrando el panel financiero del expediente.
* **Voz en off (Narración):**
  > *"Hola jurado de Platica. Presentamos **SupplyMind AI**, un Analista Digital Autónomo para conciliación 3-Way Match y arbitraje de disputas comerciales B2B construido sobre el **SKYNET Framework** y **Grok-4.7**.*  
  > *En las cadenas de suministro con grandes retailers como Walmart, Amazon, Home Depot u OXXO, entre el 4% y el 9% de las facturas sufren deducciones unilaterales: multas OTIF duplicadas, faltantes alegados en muelle pese a tener acuse limpio, o descuentos no pactados. Hoy un analista humano tarda más de una hora por caso a un costo de 30 dólares, dejando perder hasta el 4% del EBITDA anual.*  
  > *SupplyMind AI se despliega con un solo comando mediante Docker o `start_app.bat` y reduce esa auditoría de 68 minutos a menos de 3 segundos con cero error aritmético."*

---

### 🔵 BLOQUE 2 (0:50 – 2:05): Autonomía de Punta a Punta, Herramientas y Salidas ERP (25 Puntos)

* **Acción en pantalla:**
  1. En la Web UI (izquierda), selecciona el expediente **`Caso 005 — Amazon Faltante Real`** (o **`Caso 008 — Home Depot Avería OCR`**) y muestra el visor de los **5 documentos cruzados** (`invoice`, `purchase_order`, `delivery`, `payment`, `contract`).
  2. Haz clic en las pestañas **Estrado Arbitral (Tribunal)**, **Duelo de Negociación B2B** y el modal de **Exportación ERP / CFDI 4.0 / EDI 812** mostrando la póliza SAP `BAPI_ACC_DOCUMENT_POST` y la Carta Legal generada.
* **Voz en off (Narración):**
  > *"A diferencia de un chatbot pasivo, SupplyMind AI ejecuta un flujo autónomo completo mediante 6 herramientas especializadas.*  
  > *Primero, ingiere expedientes multimodales: JSONs, hojas Excel, PDFs multipágina y remisiones físicas escaneadas con sellos de almacén mediante Tesseract OCR.*  
  > *Segundo, cruza partida por partida la Orden de Compra, la Factura, el Comprobante de Entrega POD, el Pago bancario y las cláusulas del Contrato Marco.*  
  > *Aquí vemos cómo distingue autónomamente qué parte del descuento del retailer sí está justificada en muelle —para la cual emite Nota de Crédito CFDI 4.0— y qué parte es una penalización unilateral improcedente, redactando automáticamente la Carta Legal de Reclamación con fundamento en el Artículo 383 del Código de Comercio y generando el payload contable listo para SAP S/4HANA, NetSuite y EDI 812."*

---

### 🟣 BLOQUE 3 (2:05 – 3:05): Ingeniería Neuro-Simbólica sobre Grok-4.7 y Guardrails (20 Puntos)

* **Acción en pantalla:**
  1. Abre en la Web UI la pestaña **`Traza Cognitiva`** o **`Calibración Humano vs Agente`** (o **`Chaos Sandbox`**).
  2. En la terminal (derecha), ejecuta:
     ```powershell
     python scripts/verify_unattended_readiness.py
     ```
* **Voz en off (Narración):**
  > *"¿Por qué diseñamos una arquitectura neuro-simbólica sobre Grok-4.7? En nuestras pruebas empíricas comprobamos que un LLM puro sin herramientas falla en el 23.3% de facturas multi-SKU por errores de punto flotante.*  
  > *Por eso en SupplyMind AI separamos estrictamente cognición y cálculo: **Grok-4.7** realiza la interpretación semántica de cláusulas contractuales, Incoterms 2020 y el careo adversarial, pero delega el 100% de las operaciones matemáticas a nuestro motor determinístico en Python `Decimal`, garantizando un Error Absoluto Medio de exactamente **cero dólares ($0.00 MAE)**.*  
  > *Además, blindamos el sistema con tres capas de resiliencia: un parser LIFO que repara JSONs truncados en 3 milisegundos, un sanitizador activo contra ataques de Prompt Injection incrustados en facturas, y el **Quad-Check Sanity Gate**, que valida invariantes matemáticos y plazos legales antes de emitir cualquier dictamen."*

---

### 🟠 BLOQUE 4 (3:05 – 4:00): Evidencia con Datos Reales, Carga 1,024 y Reconocimiento de Fallos (15 Puntos)

* **Acción en pantalla:**
  1. En la Web UI (izquierda), haz clic en la pestaña **`Carga 1,024 (12h)`** o en el botón superior **`VER AGENTE (1,024)`**.
  2. Muestra la **Tabla Dinámica de las 1,024 Unidades**, filtra o señala los casos de **DataCo Global Smart Supply Chain (Real Dataset)** y muestra el caso #10 (`work_unit_0010`) en estado de **Cuarentena Forense** + el sello criptográfico **Merkle Root SHA-256**.
  3. En la terminal (derecha), ejecuta:
     ```powershell
     python scripts/view_task_detail.py 1
     python scripts/view_task_detail.py 10
     ```
* **Voz en off (Narración):**
  > *"Validamos el agente con datos reales del dataset público **DataCo Global Smart Supply Chain** —30 expedientes multiformato en Excel, CSV y texto por más de 326 mil dólares— logrando 100% de exactitud.*  
  > *Asimismo, ejecutamos la cola masiva desatendida de **1,024 unidades de trabajo** contra la pasarela de Platica con `grok-4.7`, respaldada con cadena de hashes SHA-256 y raíz de Merkle.*  
  > *Siguiendo la filosofía de transparencia técnica, documentamos nuestros fallos y límites reales: por ejemplo, corregimos falsos positivos de polaridad negativa en frases como 'deducción no justificada', y como se observa en la unidad número 10, cuando un expediente carece físicamente de comprobante de entrega POD, el agente se niega a alucinar o inventar evidencia: bloquea el cobro y levanta un acta de Cuarentena Forense NIF C-3 para revisión humana."*

---

### 🟡 BLOQUE 5 (4:00 – 5:00): Viabilidad, Bitácora de Consumo y Ejecución para el Harness (15 Puntos)

* **Acción en pantalla:**
  1. En la terminal (derecha), ejecuta el comando oficial que usará el **Harness de Platica** para evaluar casos propios en JSON puro:
     ```powershell
     python main.py --input case_002 --json --fast
     ```
  2. Muestra la salida JSON limpia en consola (`"mae_invariant_verified": true`, `"financial_delta_mae": 0.0`, `"claimable_amount": 12500.0`, `"telemetry"`).
  3. En la Web UI, abre el modal de **Unit Economics** o haz clic en **Descargar ZIP Maestro de Auditoría** mostrando [`reports/bitacora_consumo_consola_platica.csv`](../reports/bitacora_consumo_consola_platica.csv).
* **Voz en off (Narración):**
  > *"En términos de viabilidad y Unit Economics, nuestra bitácora exportada de la pasarela oficial de Platica registra un costo real medido de **1.13 centavos de dólar por petición API ($0.01134 USD)** y entre **0.8 y 1.7 centavos de dólar por expediente completo**. Auditar mil disputas cuesta menos de 17 dólares en API frente a 30 mil dólares en horas-hombre.*  
  > *Finalmente, para que el **Harness automatizado de Platica** evalúe nuestro agente con sus propios casos inéditos, habilitamos tanto el endpoint universal `POST /api/evaluate` como el comando CLI `python main.py --input <ruta_caso> --json`, que acepta cualquier carpeta o JSON externo y devuelve en `stdout` el dictamen JSON puro con invariante matemático verificado y telemetría completa.*  
  > *Todo el código bajo licencia MIT, el reporte técnico de 3 páginas, la bitácora de consumo y las 540+ pruebas automatizadas están listos en nuestro repositorio de GitHub. ¡Muchas gracias!"*
