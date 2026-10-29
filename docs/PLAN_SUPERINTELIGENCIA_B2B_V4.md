# ⚡ PLAN MAESTRO SUPERINTELIGENCIA B2B 4.0 (SUPPLYMIND TITAN)
> **Objetivo:** Expandir SupplyMind AI hacia la autonomía operativa total con dos capacidades de frontera:
> 1. **RPA Autónomo de Portales B2B:** Extracción y carga desatendida de disputas en portales de Retailers (Walmart, Amazon, Soriana, Liverpool).
> 2. **Visión Multimodal en Muelle:** Peritaje fotográfico de tarimas, lectura OCR de precintos C-TPAT y emisión de Certificados Criptográficos de Carga Intacta.

---

## 🏛️ ARQUITECTURA GENERAL — SUPPLYMIND TITAN (V4.0)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      SUPPLYMIND AI 4.0: ARQUITECTURA DE FRONTERA                        │
├───────────────────────────────────────────┬────────────────────────────────────────────┤
│         FRONTERA 1: RPA DE PORTALES       │       FRONTERA 2: VISIÓN MULTIMODAL        │
│   (Extracción & Disputa Desatendida)      │     (Peritaje C-TPAT & Certificación)      │
├───────────────────────────────────────────┼────────────────────────────────────────────┤
│ • Conector Walmart Retail Link / Luminate │ • Auditoría de Precintos C-TPAT / ISO 17712│
│ • Conector Amazon Vendor Central (AP)     │ • Detección de Bounding Boxes en Tarimas   │
│ • Conector Soriana B2B / Liverpool        │ • Conteo Volumétrico & Alerta de Emplaye   │
│ • Auto-Upload de Dossiers de Reclamación  │ • Certificado Criptográfico SHA-256 + GPS │
├───────────────────────────────────────────┴────────────────────────────────────────────┤
│            CENTRO DE COMANDO OBSIDIAN GLASS 3.0 (V4 EXTENDED INTERFACE)                │
│ • Monitor en Vivo de Bots de Portales      • Laboratorio Interactivo de Visión Muelle │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 DIMENSIÓN 1: RPA Autónomo & Conector de Portales Retailer
> **Módulo:** `agent/portal/retailer_portal_agent.py`  
> **Rutas API:** `api/routes/portal_agent.py`

### 1.1 Conectores Soportados
1. **Walmart Retail Link / Luminate Portal:**
   - Descarga automática de notas de débito diarias (Códigos 21, 22, 24, 25, 28, 86).
   - Inyección automática de cartas de objeción y remisiones selladas en el módulo de AP Dispute Management.
2. **Amazon Vendor Central:**
   - Rastreo de deducciones por *Shortage Claim* y multas operativas de *Vendor Performance*.
   - Generación y carga del archivo de apelación con evidencia vinculada.
3. **Soriana B2B / Liverpool B2B:**
   - Conciliación de contra-recibos vs facturas pendientes de liquidación.

### 1.2 Modos de Operación
* **Modo Acelerado Simulado (`SIMULATED_RETAILER_PORTAL`):** Simulación estocástica y determinística de navegación de portal para pruebas continuas, CI/CD y demostraciones seguras sin exponer credenciales corporativas reales.
* **Modo Navegador Activo (`LIVE_BROWSER_AUTOMATION`):** Ejecución mediante agente headless con capacidad de captura de pantalla de evidencia de carga y descarga de archivos.

---

## 👁️ DIMENSIÓN 2: Visión Multimodal en Muelle & Peritaje C-TPAT
> **Módulo:** `agent/vision/pallet_vision_auditor.py`  
> **Rutas API:** `api/routes/vision_inspection.py`

### 2.1 Capacidades Periciales
1. **Lectura y Validación de Precintos C-TPAT (ISO 17712):**
   - Extracción OCR del número de serie troquelado en el precinto de perno metálico del contenedor.
   - Confrontación automática contra el campo `seal_number` de la Carta Porte, Remisión o EDI 856 (ASN).
   - Detección de sellos manipulados o rotos (`SEAL_INTACT` vs `SEAL_TAMPERED`).
2. **Inspección de Tarimas y Estiba:**
   - Verificación de integridad del emplaye plástico (`FILM_WRAPPED_SECURE` vs `FILM_TORN`).
   - Verificación de flejes de seguridad plásticos/metálicos.
   - Detección y conteo de cajas estibadas con generación de Bounding Boxes.
3. **Certificado Criptográfico de Carga Intacta (`CargoIntegrityCertificate`):**
   - Folio único institucional (ej. `CERT-CTPAT-2026-WM8841`).
   - Timbre UTC con coordenadas GPS simuladas de origen/destino.
   - Hashes SHA-256 de las imágenes periciales.
   - Conclusión probatoria inexpugnable para anular reclamos por mermas posteriores en muelle.

---

## 💎 DIMENSIÓN 3: Interfaz Obsidian Glass V4
> **Componentes Frontend:**
> - `frontend/src/components/PortalCrawlerView.jsx`: Monitor de sincronización de portales con logs en tiempo real, selector de retailer y botón de auto-disputa desatendida.
> - `frontend/src/components/PalletVisionView.jsx`: Laboratorio de visión artificial con carga de fotos, visualización de Bounding Boxes de cajas y precintos, y descarga del Certificado Pericial.

---

## 🗓️ CRONOGRAMA DE SPRINTS — SUPPLYMIND TITAN 4.0

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CRONOGRAMA DE SPRINTS SUPPLYMIND 4.0                 │
├────────────────────────────────────────────────────────────────────────┤
│ Sprint 6.1: RPA Autónomo & Conector de Portales Retailer               │ [COMPLETADO ✅]
│   - Motor de Navegación y Extracción (RetailerPortalAgent)             │
│   - Conectores Walmart, Amazon, Soriana y Liverpool                    │
│   - Auto-Carga y Apelación Desatendida de Notas de Débito              │
│   - API REST (/api/portal/catalog, sync-retailer, upload-dispute)      │
│   - Tests Unitarios e Integración en Verde                             │
│ Sprint 6.2: Visión Multimodal en Muelle & Certificación C-TPAT        │ [COMPLETADO ✅]
│   - Analizador Forense de Imágenes (PalletVisionAuditor)               │
│   - OCR de Precinto C-TPAT y Detección de Bounding Boxes               │
│   - Emisor de Certificado Criptográfico de Carga Intacta (SHA-256)     │
│   - API REST (/api/vision/inspect-pallet, samples)                     │
│   - Tests Unitarios e Integración en Verde                             │
│ Sprint 6.3: Componentes Visuales Obsidian Glass 4.0                    │ [COMPLETADO ✅]
│   - Monitor de Bots de Portales (PortalCrawlerView.jsx)                │
│   - Visor de Bounding Boxes y Certificados (PalletVisionView.jsx)      │
│   - Integración de Pestañas y Atajos de Teclado (7 y 8) en App.jsx     │
│   - 63/63 Tests Unitarios e Integración en Verde (100% Passing)        │
│   - Frontend Vite Production Build & Verificación Completa             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🏆 Criterios de Aceptación Innegociables
1. **$0.00 MAE:** Las deducciones extraídas por los bots de portales se concilian sin alucinaciones aritméticas.
2. **Validación Pericial C-TPAT:** Todo precinto inspeccionado produce un certificado foliado con hashes criptográficos inalterables.
3. **100% de Pruebas Automatizadas en Verde:** Cobertura de tests unitarios e integración para cada conector y analizador de visión.
4. **Build de Producción Limpio:** Vite compila sin advertencias ni errores en el frontend.
