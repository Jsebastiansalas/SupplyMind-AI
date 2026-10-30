# Plan de Implementación: Sprint 6.4 — Interfaz Obsidian Glass 3.0: Mesa de Negociación B2B & Careo en Vivo

## Resumen Ejecutivo
Implementación de la experiencia visual y operativa Obsidian Glass 3.0 para la confrontación dialéctica autónoma (Mesa de Negociación B2B) y la radicación desatendida en portales retail. Dota a los analistas y directores financieros de una consola interactiva en tiempo real donde pueden presenciar el debate IA vs Retailer ronda a ronda, monitorear la curva de convergencia de ofertas, intervenir con controles Human-in-the-Loop o conmutar al modo 100% autónomo, y supervisar el despacho pericial con folios de ticket.

---

## Decisiones de Arquitectura de UI
1. **Consola Dividida (Split-Screen Dialéctico):**
   - Lado Izquierdo: Agente Defensor SupplyMind AI con desglose de reclamo en banco, concesión ofrecida, argumentos periciales y catálogo de pruebas exhibidas en la ronda.
   - Centro: Stepper de rondas 1 a 5, indicador visual de Spread ($0.00 MAE) y barra de convergencia animada. Botones de avance de ronda, auto-careo y reinicio.
   - Lado Derecho: Comprador Retailer con arquetipo (Walmart, Amazon, Soriana, Costco, Liverpool), nivel de resistencia (1-10), postura y demandas comerciales.
2. **Barra de Gobernanza y Salvaguardas:**
   - Conmutador en caliente de gobernanza: `Piloto Automático` vs `Human Gatekeeper`.
   - Insignia de salvaguarda financiera para controversias $\ge \$10,000$ USD (bloquea el cierre autónomo para exigir rúbrica del CFO).
   - Indicador del tope máximo autorizado por la Matriz de Delegación Financiera.
3. **Visor de Finiquito y Transacción Mercantil:**
   - Modal interactivo con el texto del Convenio de Finiquito en Markdown formal (Arts. 1054 CCom / 2944 CCF), sello ZKP SHA-256 copiable en 1 clic y reciprocidad comercial.
4. **Terminal Integrada de Despacho Robótico (RPA):**
   - Botón directo para radicar en el portal B2B del retailer.
   - Bitácora de micro-pasos en vivo y confirmación de ticket oficial (ej. `WLMT-TK-2026-XXXXXX`, `AMZN-CASE-2026-XXXXXX`).

---

## Task List & Checkpoints

### Fase 1: Componente Core de Careo y Navegación
- [x] **Task 6.4.1:** Componente `NegotiationDuelView.jsx` en `frontend/src/components/NegotiationDuelView.jsx`.
- [x] **Task 6.4.2:** Métodos API de negociación y despacho en `frontend/src/api/client.js`.

### Fase 2: Integración en Aplicación Principal
- [x] **Task 6.4.3:** Integración del Tab `Mesa Careo` y selector de herramientas en `frontend/src/App.jsx`.
- [x] **Task 6.4.4:** Integración complementaria en Streamlit `dashboard.py` (Tab `⚔️ MESA DE CAREO & DESPACHO`).

### Checkpoint Final Sprint 6.4
- [x] Compilación de producción Vite `npm run build` en verde (3.99s, 0 errores).
- [x] 14/14 tests automatizados de backend pasando.
- [x] Commits y push en rama `develop`.
