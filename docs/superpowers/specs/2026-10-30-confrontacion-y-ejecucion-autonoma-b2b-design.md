# Especificación de Diseño: Confrontación Dialéctica y Ejecución Autónoma B2B
**Fecha:** 2026-10-30  
**Proyecto:** SupplyMind AI — Superinteligencia B2B  
**Estado:** Propuesta de Diseño (Ready for Review)  
**Autor:** Antigravity Pair-Programming Agent & Operador Líder

---

## 1. Intención y Justificación Estratégica ("The Why")
SupplyMind AI cuenta actualmente con un motor de auditoría pericial exacto ($0.00 MAE), telemetría EDI ANSI X12, cadena de custodia C-TPAT, estrado dialéctico adversarial, pólizas contables NIF C-3 y un copiloto Grok 4.7 con anclaje de gobernanza.

Sin embargo, en el mundo real de la cadena de suministro B2B, **los proveedores pierden millones de dólares no porque carezcan de la razón legal o contable, sino por falta de tiempo, capacidad de negociación y recursos para confrontar a los compradores de grandes retailers** (Walmart, Amazon, Soriana, Costco, Liverpool), quienes aplican deducciones masivas y tácticas de desgaste sistemático.

El objetivo de esta fase es convertir a SupplyMind AI en el **agente B2B más completo y resolutivo del mundo**, facultándolo para **ejecutar y confrontar de forma autónoma**:
1. Sentarse a negociar en tiempo real contra un agente que emula al comprador hostil del retailer.
2. Formular contrapropuestas basadas en teoría de juegos (Monte Carlo Tree Search) protegiendo el margen del proveedor.
3. Radicar y dar seguimiento autónomo a las disputas en los portales B2B de los clientes.
4. Operar bajo una dualidad de gobernanza: **Piloto Automático** (100% independiente dentro de rangos pre-aprobados) o **Copiloto Asistido** (con visto bueno humano antes de rubricar el acuerdo).

---

## 2. Decisiones de Diseño Acordadas con el Usuario
1. **Dualidad de Gobernanza Conmutable:**
   - El operador puede seleccionar libremente entre:
     - **Modo Piloto Automático:** El agente negocia, aplica concesiones dentro del límite financiero autorizado y rubrica la minuta de acuerdo sin requerir confirmación intermedia.
     - **Modo Asistido (Human Gatekeeper):** El agente lidera todo el careo y contrapropuestas, pero al llegar a la oferta final congela la ejecución y solicita la aprobación humana con un clic.
2. **Visualización en Vivo en el Dashboard:**
   - La confrontación bilateral no se oculta en un proceso de fondo invisible; se transmite en vivo dentro del Dashboard en una nueva pestaña interactiva (`⚔️ Mesa de Negociación B2B`), permitiendo ver el intercambio dialéctico ronda por ronda, la gráfica de convergencia de ofertas y las pruebas exhibidas.
3. **Despacho Autónomo a Portales:**
   - Automatización de la radicación de la disputa con generación de paquetes foliados (ZIP/JSON con evidencias) para los 4 portales retail principales (Retail Link, Vendor Central, Soriana B2B, Liverpool Partners).

---

## 3. Metas, No-Metas y Anti-Metas

### Metas (Goals)
- **Careo Multi-Agente en Tiempo Real:** Confrontación entre el Agente Defensor SupplyMind y el Agente Comprador Retailer con personalidades configuradas por cadena comercial.
- **Negociación Táctica MCTS:** Rondas dialécticas (máximo 5) donde se intercambian posturas, argumentos legales (Art. 88 CCom, CISG) y números Decimales exactos.
- **Límites Financieros Infranqueables:** Matriz de delegación donde el CFO define el tope máximo de concesión admisible (porcentaje o monto fijo).
- **Formalización Jurídica Inmediata:** Generación y rubrica digital de la Minuta de Conciliación Extrajudicial con hash ZKP inmutable.
- **RPA & Dispatcher a Portales B2B:** Generación del paquete probatorio foliado y simulación de envío directo a portales con obtención de folio de ticket.

### No-Metas (Non-Goals)
- No busca sustituir litigios mercantiles en juzgados tradicionales; se enfoca en la resolución pre-judicial y conciliatoria directa B2B.
- No ejecuta transferencias bancarias directas de salida sin aprobación de tesorería; genera las instrucciones contables de compensación o cobro.

### Anti-Metas (Anti-Goals)
- **Cero Violación de Límites:** El agente NUNCA concederá un solo centavo por encima del tope financiero fijado por el usuario, sin importar la presión dialéctica del comprador.
- **Cero Bucles Infinitos:** La negociación no puede extenderse indefinidamente; tras 5 rondas sin acuerdo, se declara punto muerto (*impasse*) y se deriva al Tribunal Arbitral ICC / CANACO.
- **Cero Cajas Negras:** Todo argumento, oferta y cálculo del agente debe ser visible, auditable y explicable.

---

## 4. Restricciones Técnicas (Constraints)
- **Precisión Aritmética:** Exclusivamente Python `Decimal` ($0.00 MAE), libre de imprecisión IEEE 754.
- **Consistencia de Gobernanza:** Toda interacción respaldada por el `SessionAnchorManager` para evitar alucinaciones o manipulaciones de saldos.
- **Frontend Modular:** React 19 + Tailwind/CSS Obsidian Glass 3.0 en la arquitectura modular de `SupplyMind` (`frontend/src/components/`).
- **Endpoints REST FastAPI:** Integración limpia bajo `/api/negotiation/...` con esquemas Pydantic V2.

---

## 5. Plan de Sprints e Historias de Usuario

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ FASE 6: CONFRONTACIÓN DIALÉCTICA & EJECUCIÓN AUTÓNOMA B2B                        │
├──────────────────────────────────────────────────────────────────────────────────┤
│ Sprint 6.1: Motor Multi-Agente de Negociación Bilateral (IA vs IA)               │
│ Sprint 6.2: Matriz de Delegación Financiera & Dualidad de Gobernanza             │
│ Sprint 6.3: Despachador Robótico a Portales B2B (Retail Link, Vendor Central)    │
│ Sprint 6.4: Interfaz Obsidian Glass 3.0: Mesa de Negociación B2B & Careo en Vivo │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Sprint 6.1: Motor Multi-Agente de Negociación Bilateral (IA vs IA)
- **HU-6.1.1 (Simulador de Comprador Hostil):** Como auditor B2B, quiero que el sistema instancie un Agente Comprador con la personalidad y tácticas del retailer en disputa (ej. intransigente de Walmart OTIF, punitivo de Amazon FC, elusivo de Soriana) para someter el caso a una prueba de fuego real.
- **HU-6.1.2 (Motor Dialéctico MCTS y Concesiones):** Como director comercial, quiero que el Agente SupplyMind responda con contrapropuestas calibradas por teoría de juegos evaluando el impacto en el Valor Presente Neto (NPV) y la relación comercial.
- **HU-6.1.3 (Control de Rondas y Detección de Impasse):** Como CFO, quiero que la confrontación esté acotada a un máximo de 5 rondas dialécticas para evitar desgaste innecesario y derivar automáticamente a arbitraje si el comprador se niega a conciliar.

### Sprint 6.2: Matriz de Delegación Financiera & Dualidad de Gobernanza
- **HU-6.2.1 (Configurador de Límites de Delegación):** Como CFO, quiero definir parámetros estrictos de negociación (máxima concesión porcentual, monto en USD y días máximos de pago admitidos) para que el agente nunca ceda más de lo autorizado.
- **HU-6.2.2 (Selector de Modo Operativo Auto vs Gatekeeper):** Como operador de cartera, quiero poder activar el "Modo Piloto Automático" o el "Modo Asistido con Aprobación Humana" según la criticidad de la cuenta.
- **HU-6.2.3 (Rubrica Digital de Minuta Vinculante):** Como asesor legal, quiero que al cerrarse la negociación se emita y selle criptográficamente la Minuta de Conciliación Extrajudicial con efectos vinculantes bajo el Código de Comercio.

### Sprint 6.3: Despachador Robótico a Portales B2B (Portal Automation)
- **HU-6.3.1 (Empaquetador de Evidencias Periciales):** Como especialista de operaciones, quiero que el agente genere automáticamente el paquete probatorio (CFDI, remisión sellada, ASN EDI 856, C-TPAT) con índices y folios normalizados.
- **HU-6.3.2 (Adaptadores de Radicación B2B):** Como analista de cuentas por cobrar, quiero que el agente radique la disputa con el payload exacto requerido por Walmart Retail Link, Amazon Vendor Central, Soriana B2B y Liverpool Partners.
- **HU-6.3.3 (Gestor de Tickets y Notificaciones):** Como operador, quiero recibir el folio oficial de radicación y una bitácora de eventos con marcas de tiempo auditables.

### Sprint 6.4: Interfaz Obsidian Glass 3.0: Mesa de Negociación B2B
- **HU-6.4.1 (Consola de Careo Dividido Agente vs Comprador):** Como usuario, quiero ver en el dashboard una pantalla dividida donde ambos agentes debaten en tiempo real con burbujas de diálogo periciales, insignias de postura y evidencias mostradas.
- **HU-6.4.2 (Gráfica de Convergencia de Ofertas):** Como observador, quiero ver una gráfica interactiva en tiempo real que muestre la brecha entre la pretensión inicial del comprador y la oferta de SupplyMind hasta llegar al punto de equilibrio.
- **HU-6.4.3 (Controles Human-in-the-Loop):** Como operador en modo asistido, quiero botones directos para "Aprobar Acuerdo", "Exigir Mayor Recuperación" o "Romper Negociación y Derivar a Arbitraje".
- **HU-6.4.4 (Terminal de Radicación a Portales):** Como usuario, quiero ver la simulación de radicación con barras de progreso de carga de evidencias, validación de API y confirmación del ticket de disputa emitido.

---

## 6. Lo que Queda a Criterio del Desarrollador (Builder's Calls)
- Nombres exactos de las funciones de la API REST y rutas internas.
- Estructura exacta de los prompts de personalidad para los agentes compradores en OpenAI / Grok / Fallback determinístico.
- Elección de la librería de renderizado de gráficas (SVG Vanilla interactivo o Recharts) priorizando rendimiento y estética Obsidian Glass.
- Formato específico de los esquemas de empaquetado ZIP/JSON para portales retail.
