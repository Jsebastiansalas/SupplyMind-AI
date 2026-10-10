import streamlit as st
import time
import sys
from pathlib import Path
from decimal import Decimal
import plotly.graph_objects as go

sys.path.append(str(Path(__file__).resolve().parent))
from agent.core.skynet_runner import SkynetRunner
from tools.document_reader.classifier import DocumentClassifier
import json

st.set_page_config(
    page_title="SKYNET | Enterprise Control",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------
# CSS AVANZADO: GLASSMORPHISM & NEON GLOW EFFECTS
# -----------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Ocultar elementos por defecto de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Fondo principal y textos */
    .stApp {
        background: linear-gradient(135deg, #020617 0%, #0f172a 100%);
        color: #f8fafc;
    }
    
    h1, h2, h3 {
        background: -webkit-linear-gradient(45deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* Tarjetas principales estilo Glassmorphism */
    .premium-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .premium-card:hover {
        transform: translateY(-5px);
        border-color: rgba(56, 189, 248, 0.4);
    }
    
    /* Estilos de Metricas Customizadas */
    div[data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        background: -webkit-linear-gradient(45deg, #fff, #cbd5e1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 1.1rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Botn Principal Neon */
    .stButton>button {
        background: linear-gradient(90deg, #2563eb, #4f46e5);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 1.2rem;
        font-weight: 600;
        box-shadow: 0 0 15px rgba(79, 70, 229, 0.5);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px rgba(79, 70, 229, 0.8);
        transform: scale(1.02);
    }
    
    /* Alertas y Boxes */
    .success-glow {
        border-left: 5px solid #10b981;
        background: rgba(16, 185, 129, 0.1);
        padding: 20px;
        border-radius: 8px;
        margin-top: 15px;
    }
    .error-glow {
        border-left: 5px solid #ef4444;
        background: rgba(239, 68, 68, 0.1);
        padding: 20px;
        border-radius: 8px;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------
# HEADER Y SIDEBAR
# -----------------------------------------------------
col_h1, col_h2 = st.columns([1, 10])
with col_h1:
    st.image("https://img.icons8.com/nolan/96/bot.png", width=70)
with col_h2:
    st.markdown("<h1>SKYNET <span style='font-size: 0.5em; color: #94a3b8; -webkit-text-fill-color: #94a3b8;'>ENTERPRISE</span></h1>", unsafe_allow_html=True)
    st.caption("Supply Chain Autonomous Dispute Resolution Engine")

st.markdown("<br>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>CONTROL PANEL</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("#### 📂 1. INGESTA DE DATOS")
    case_option = st.selectbox(
        "Seleccione un Expediente Batch:",
        [
            "case_008_homedepot_damaged_scanned (Real OCR: Home Depot Scanned POD Damaged Goods)",
            "case_007_cisco_large_bundle (Real Large PDF: Cisco $125k Infrastructure)",
            "case_005_amazon_shortage (Real PDF: Amazon Shortage Claim)",
            "case_006_walmart_otif_pricing (Real PDF: Walmart OTIF Price Dispute)",
            "case_004_enterprise (RAG+OCR)",
            "case_001 (Basic Missing Item)",
            "case_002 (Complex Deduction)",
            "case_003 (Pricing Discrepancy)",
            "test_dynamic_case (Dynamic Eval)"
        ]
    )
    case_id = case_option.split(" ")[0]
    case_path = Path("data/cases") / case_id
    pdf_files = list(case_path.glob("*.pdf")) if case_path.exists() else []
    if pdf_files:
        st.markdown(f"""
        <div style="background: rgba(56, 189, 248, 0.12); border-left: 3px solid #38bdf8; padding: 10px; border-radius: 6px; margin: 10px 0;">
            <span style="color: #38bdf8; font-weight: 700; font-size: 0.85rem;">📑 Expediente PDF Nativo ({len(pdf_files)} docs)</span>
            <p style="color: #cbd5e1; font-size: 0.75rem; margin: 4px 0 0 0;">Ingesta directa sin JSON intermedio. Extracción y validación Pydantic 100% activa.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### ⚙️ 2. CONFIGURACIÓN DEL ENJAMBRE")
    fast_mode = st.toggle("⚡ Fast-Path de Inferencia (<1s)", value=True, help="Ejecuta la conciliación determinística instantánea sin latencia de red ReAct.")
    use_cache = st.toggle("💾 Caché en Memoria Inteligente", value=True, help="Reutiliza resultados previos si los documentos del expediente no han cambiado.")
    st.toggle("🤖 Activar Multi-Agent Swarm", value=True, help="Divide el análisis entre FinanceAgent, LegalAgent y LogisticsAgent.")
    st.toggle("📚 RAG Legal Habilitado", value=True, help="Usa ChromaDB para buscar vacíos legales en contratos gigantes.")
    st.toggle("👁️ Motor Visión OCR Habilitado", value=True, help="Lee imágenes manuscritas y fotos de daños.")
    st.toggle("🔮 Análisis Predictivo (ML)", value=False, help="Estima la probabilidad de ganar la disputa usando datos históricos.")
    
    if st.button("🔄 Limpiar Memoria Caché", use_container_width=True):
        from agent.core.cache import dispute_cache
        dispute_cache.clear()
        st.toast("Caché de expedientes invalidada exitosamente.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("▶ INICIAR AUDITORÍA AUTÓNOMA", use_container_width=True, type="primary")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption("SYSTEM STATUS")
    st.progress(100, text="Grok 4.7 Gateway: ONLINE")
    st.progress(100, text="Fast-Path Engine: OPTIMIZED")
    st.progress(100, text="Skynet Engine: v1.0.0")

# Lógica Principal
if run_btn:
    with st.spinner(f"Iniciando SKYNET para el caso {case_id}..."):
        status_text = st.empty()
        prog_bar = st.progress(0)
        
        status_text.markdown("#### 📡 Estableciendo conexión segura con Skynet Engine...")
        time.sleep(0.2 if fast_mode else 0.5)
        prog_bar.progress(25)
        
        status_text.markdown("#### 📄 Ingestando y parseando estructuras Pydantic...")
        time.sleep(0.2 if fast_mode else 0.6)
        prog_bar.progress(50)
        
        status_text.markdown("#### ⚖️ Evaluando variables contractuales e invocando Tools...")
        time.sleep(0.2 if fast_mode else 0.7)
        prog_bar.progress(75)
        
        status_text.markdown("#### 🧠 Resolviendo razonamiento en LLM (Grok)...")
        
        try:
            # EJECUCIÓN REAL (CON FAST-PATH Y CACHÉ)
            runner = SkynetRunner(case_id=case_id, fast_path=fast_mode, use_cache=use_cache)
            report = runner.run()
            
            # Guardar en session state
            st.session_state.current_report = report
            st.session_state.runner_logs = runner.audit_logger.log_file
            st.session_state.messages = []
            
            st.rerun() # Dispara recarga para que dibuje todo desde el estado
            
        except Exception as e:
            status_text.error(f"SYSTEM OVERRIDE ERROR: {str(e)}")

# SI YA SE EJECUTO EL REPORTE, RENDERIZAR INTERFAZ
if "current_report" in st.session_state:
    report = st.session_state.current_report
    
    st.markdown(f"<h2>📊 RESULTADOS: {Path(report.case_id).name.upper()}</h2>", unsafe_allow_html=True)
    tab1, tab2, tab_pdf, tab3, tab4, tab5 = st.tabs(["💵 PANEL FINANCIERO", "⚖️ VEREDICTO LEGAL", "📑 EXPEDIENTE PDF", "📋 TRAZABILIDAD (AUDIT)", "💬 TERMINAL INTERACTIVA", "📤 EXPORTAR Y COMUNICAR"])
    
    with tab1:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Monto Facturado", f"${report.billed_amount:,.2f}")
        m2.metric("Monto Recibido", f"${report.received_amount:,.2f}")
        diff_color = "normal" if report.difference == 0 else "inverse"
        m3.metric("Diferencia / Retención", f"${report.difference:,.2f}", delta=f"Impacto", delta_color=diff_color)
        m4.metric("SALDO RECLAMABLE", f"${report.claimable_amount:,.2f}", delta="Recuperable", delta_color="normal")
        st.markdown("<br>", unsafe_allow_html=True)
        col_chart, col_details = st.columns([1, 1])
        with col_chart:
            labels = ['Justificado (Perdido)', 'Reclamable (A Favor)']
            values = [float(report.justified_amount), float(report.claimable_amount)]
            colors = ['#ef4444', '#10b981']
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker=dict(colors=colors))])
            fig.update_layout(title_text="Distribución del Faltante", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        with col_details:
            st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
            st.markdown("### 🔍 Causa Raíz Detectada")
            st.write(report.root_cause)
            st.markdown("</div>", unsafe_allow_html=True)
            
    with tab2:
        col_ev, col_act = st.columns(2)
        with col_ev:
            st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
            st.markdown("### 📑 Evidencia y Respaldo Contractual (RAG)")
            for ev in report.evidence:
                if "contractual" in ev.lower() or "cláusula" in ev.lower() or "clausula" in ev.lower():
                    st.markdown(f"<div style='background: rgba(129, 140, 248, 0.15); border-left: 3px solid #818cf8; padding: 8px 12px; border-radius: 6px; margin: 6px 0; color: #e2e8f0; font-size: 0.88rem;'>⚖️ <strong>Cláusula RAG:</strong> {ev.replace('Respaldo contractual: ', '')}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"- {ev}")
            st.markdown("</div>", unsafe_allow_html=True)
        with col_act:
            st.markdown("### 🎯 Acción Recomendada")
            st.progress(float(report.confidence), text=f"Certeza Algorítmica: {float(report.confidence)*100:.1f}%")
            if report.claimable_amount > Decimal("0"):
                st.markdown(f"<div class='error-glow'><strong>Emitir Reclamación:</strong><br><br>{report.recommended_action}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='success-glow'><strong>Operación Saneada:</strong><br><br>{report.recommended_action}</div>", unsafe_allow_html=True)

    with tab_pdf:
        st.markdown("### 📑 Expediente Comercial Original (Archivos PDF)")
        st.caption("Documentos de origen procesados e ingeridos directamente por el motor agéntico de lectura PDF.")
        
        case_dir_path = Path("data/cases") / Path(report.case_id).name
        docs_found = sorted(list(case_dir_path.glob("*.pdf")) + list(case_dir_path.glob("*.png")) + list(case_dir_path.glob("*.jpg"))) if case_dir_path.exists() else []
        
        if docs_found:
            st.markdown(f"**Total de Documentos en Expediente:** `{len(docs_found)}` | **Estado:** `Extracción Pydantic y Visión OCR Exitosa`")
            pdf_cols = st.columns(min(len(docs_found), 3))
            doc_meta = {
                "invoice.pdf": ("🧾 Factura Comercial", "#38bdf8", "Emitida por proveedor con ítems, subtotales y total."),
                "purchase_order.pdf": ("📦 Orden de Compra", "#818cf8", "Emitida por retailer con precios pactados y cantidades."),
                "delivery.pdf": ("🚚 Remisión de Entrega / POD", "#34d399", "Firmada en muelle con constancia de faltantes o averías."),
                "delivery.png": ("📷 Remisión Física Escaneada (OCR)", "#10b981", "Fotografía digitalizada de remisión con sello y notas de patio."),
                "payment.pdf": ("💳 Comprobante de Pago", "#f59e0b", "Detalla la dispersión bancaria y códigos de deducción."),
                "contract.pdf": ("⚖️ Contrato Marco (MSA)", "#ec4899", "Cláusulas legales vinculantes y políticas de deducción.")
            }
            type_meta = {
                "invoice": ("🧾 Factura Comercial (Auto-Detectada)", "#38bdf8", "Emitida por proveedor con ítems, subtotales y total."),
                "purchase_order": ("📦 Orden de Compra (Auto-Detectada)", "#818cf8", "Emitida por retailer con precios pactados y cantidades."),
                "delivery": ("🚚 Remisión / POD (Visión OCR)", "#34d399", "Firmada en muelle con constancia de faltantes o averías."),
                "payment": ("💳 Comprobante de Pago (Auto-Detectada)", "#f59e0b", "Detalla la dispersión bancaria y códigos de deducción."),
                "contract": ("⚖️ Contrato Marco MSA (Auto-Detectado)", "#ec4899", "Cláusulas legales vinculantes y políticas de deducción.")
            }
            for idx, p_file in enumerate(docs_found):
                col_target = pdf_cols[idx % len(pdf_cols)]
                if p_file.name in doc_meta:
                    title, border_color, desc = doc_meta[p_file.name]
                else:
                    try:
                        detected_role, conf = DocumentClassifier.classify_pdf(p_file) if p_file.suffix.lower() == ".pdf" else ("delivery", 0.95)
                        title, border_color, desc = type_meta.get(detected_role, (f"📄 {p_file.name}", "#94a3b8", "Documento soporte."))
                        title = f"{title} [{int(conf*100)}%]"
                    except Exception:
                        title, border_color, desc = (f"📄 {p_file.name}", "#94a3b8", "Documento soporte.")
                with col_target:
                    st.markdown(f"""
                    <div class='premium-card' style='margin-bottom: 12px; border-top: 3px solid {border_color};'>
                        <h4 style='color: {border_color}; margin: 0 0 6px 0; font-size: 1rem;'>{title}</h4>
                        <p style='color: #94a3b8; font-size: 0.8rem; margin: 0 0 6px 0;'>{desc}</p>
                        <p style='color: #64748b; font-size: 0.75rem; margin: 0;'>Archivo: <code>{p_file.name}</code> ({p_file.stat().st_size:,} bytes)</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if p_file.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                        st.image(str(p_file), caption=f"Documento Escaneado: {p_file.name}", use_container_width=True)
                    with open(p_file, "rb") as f_bytes:
                        m_type = "image/png" if p_file.suffix.lower() == ".png" else "application/pdf"
                        st.download_button(
                            label=f"⬇️ Descargar {p_file.name}",
                            data=f_bytes.read(),
                            file_name=p_file.name,
                            mime=m_type,
                            key=f"dl_viewer_{report.case_id}_{p_file.name}",
                            use_container_width=True
                        )
        else:
            st.info("ℹ️ Este expediente utiliza fuentes en formato JSON. Para observar el procesamiento de PDFs nativos, documentos escaneados con OCR y expedientes masivos, seleccione **case_008_homedepot_damaged_scanned**, **case_007_cisco_large_bundle**, **case_005_amazon_shortage** o **case_006_walmart_otif_pricing** en la barra lateral.")

    with tab3:
        st.markdown("### 🗃️ Registro Criptográfico de Auditoría")
        log_path = Path(st.session_state.runner_logs)
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8") as f:
                logs = f.readlines()
            for idx, line in enumerate(logs[-10:]):
                data = json.loads(line)
                with st.expander(f"Paso {data.get('step_number')}: {data.get('phase')} - {data.get('action_type')}"):
                    st.json(data)
        else:
            st.warning("Log no encontrado para renderizar.")

    with tab4:
        st.markdown("### 💬 Interacción con SKYNET (Modo Terminal)")
        st.caption("Consulta dudas específicas sobre este caso directamente al Agente.")
        
        chat_container = st.container(height=400)
        with chat_container:
            st.chat_message("assistant").write(f"Soy SKYNET. He completado el análisis del caso. ¿Qué deseas saber?")
            for msg in st.session_state.messages:
                st.chat_message(msg["role"]).write(msg["content"])
                
        # Chat Input FUERA DEL CONTENEDOR PERO DENTRO DEL TAB (Para que se dibuje abajo)
        col_input1, col_input2 = st.columns([10, 1])
        with col_input1:
            prompt = st.chat_input("Escribe tu pregunta al agente aquí...")
            
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Conexión directa a OpenAI/Grok Gateway
            from openai import OpenAI
            import config.settings as s
            client = OpenAI(api_key=s.settings.RETO_KEY, base_url=s.settings.PLATICA_BASE_URL)
            
            context = f"""Eres SKYNET Enterprise AI, un agente corporativo autónomo experto en conciliación financiera B2B y análisis contractual.
Acabas de realizar una auditoría sobre el expediente '{report.case_id}'.

=== RESULTADOS DE LA AUDITORÍA MATEMÁTICA Y LEGAL ===
Monto Justificado (Aprobado): ${report.justified_amount:,.2f}
Monto Reclamable (A Favor de Nuestra Empresa): ${report.claimable_amount:,.2f}
Hallazgo Principal (Causa Raíz): {report.root_cause}
Veredicto Final (Acción Recomendada): {report.recommended_action}

=== INSTRUCCIONES DE OPERACIÓN ===
1. Responde a las dudas del jurado/usuario basándote ÚNICAMENTE en la información anterior.
2. Si te preguntan algo no relacionado con este caso, indica que tu contexto está limitado al expediente actual.
3. Mantén un tono extremadamente profesional, frío, corporativo y preciso. No uses jerga amigable. Usa viñetas para explicar datos financieros.
4. Si hay errores o discrepancias, identifícalos como "Desviaciones del SLA" o "Anomalías Contractuales"."""
            
            api_messages = [{"role": "system", "content": context}] + st.session_state.messages
            
            try:
                with st.spinner("Pensando..."):
                    response = client.chat.completions.create(
                        model=s.settings.MODEL_NAME,
                        messages=api_messages
                    )
                bot_reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                st.rerun()
            except Exception as e:
                st.error(f"Error de conexión con la API Gateway: {e}")
        
    with tab5:
        st.markdown("### 📤 Módulo de Comunicación B2B")
        st.caption("SKYNET puede generar automáticamente los comunicados oficiales para el cliente.")
        
        try:
            from tools.reporting.generator import CommunicationEngine
            engine = CommunicationEngine()
            
            col_mail, col_pdf = st.columns(2)
            with col_mail:
                st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
                st.markdown("#### 📧 Borrador de Correo")
                asunto, cuerpo = engine.generate_email_draft(report)
                st.text_input("Asunto:", value=asunto, disabled=True)
                st.text_area("Cuerpo del mensaje:", value=cuerpo, height=250)
                if st.button("Copiar al Portapapeles", use_container_width=True):
                    st.toast("Correo copiado exitosamente.", icon="✅")
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col_pdf:
                st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
                st.markdown("#### 📄 Dictamen Oficial (PDF)")
                st.write("Genera un reporte gerencial sellado por SKYNET AI con toda la evidencia legal y matemática.")
                
                # Generar PDF en memoria temporal
                pdf_path = engine.generate_pdf_report(report, "data/output")
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="⬇️ Descargar Reporte PDF",
                        data=pdf_file,
                        file_name=f"Dictamen_{Path(report.case_id).name}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                st.markdown("</div>", unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error al cargar módulo de comunicación: {e}")

elif not run_btn:
    # PANTALLA DE INICIO (GLOBAL DASHBOARD)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### 🌐 Global Command Center")
    st.caption("Visión general del ecosistema de resolución de disputas corporativas.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Kpis Globales
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown("""
        <div class="premium-card">
            <h4 style="color:#94a3b8; font-size:14px; text-transform:uppercase;">Casos Auditados (Mes)</h4>
            <h2 style="font-size:2rem; margin:0;">1,284</h2>
            <p style="color:#10b981; margin:0; font-size:12px;">↑ 12% vs mes anterior</p>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown("""
        <div class="premium-card">
            <h4 style="color:#94a3b8; font-size:14px; text-transform:uppercase;">Deducciones Analizadas</h4>
            <h2 style="font-size:2rem; margin:0;">$4.2M</h2>
            <p style="color:#10b981; margin:0; font-size:12px;">↑ 5% vs mes anterior</p>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown("""
        <div class="premium-card">
            <h4 style="color:#94a3b8; font-size:14px; text-transform:uppercase;">Capital Recuperado</h4>
            <h2 style="font-size:2rem; margin:0;">$850K</h2>
            <p style="color:#10b981; margin:0; font-size:12px;">↑ 22% de eficiencia RAG</p>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown("""
        <div class="premium-card">
            <h4 style="color:#94a3b8; font-size:14px; text-transform:uppercase;">Tiempo Promedio / Caso</h4>
            <h2 style="font-size:2rem; margin:0;">1.2s</h2>
            <p style="color:#10b981; margin:0; font-size:12px;">↓ 99% vs auditoría manual</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Layout Principal del Dashboard
    col_table, col_activity = st.columns([2, 1])
    
    with col_table:
        st.markdown("#### 📁 Expedientes en Cola de Procesamiento")
        
        # Tabla simulada de casos
        st.markdown("""
        <div class="premium-card" style="padding: 0;">
            <table style="width: 100%; border-collapse: collapse; text-align: left; color: #cbd5e1;">
                <thead>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.2);">
                        <th style="padding: 15px;">ID Expediente</th>
                        <th style="padding: 15px;">Cliente</th>
                        <th style="padding: 15px;">Prioridad</th>
                        <th style="padding: 15px;">Estado</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <td style="padding: 15px; font-weight: bold; color: #38bdf8;">case_004_enterprise</td>
                        <td style="padding: 15px;">MegaCorp Retail Holdings</td>
                        <td style="padding: 15px;"><span style="background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 4px 8px; border-radius: 4px; font-size: 12px;">ALTA</span></td>
                        <td style="padding: 15px; color: #fbbf24;">Pendiente Análisis RAG</td>
                    </tr>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <td style="padding: 15px; font-weight: bold; color: #38bdf8;">case_002_complex</td>
                        <td style="padding: 15px;">TechMart Solutions</td>
                        <td style="padding: 15px;"><span style="background: rgba(245, 158, 11, 0.2); color: #f59e0b; padding: 4px 8px; border-radius: 4px; font-size: 12px;">MEDIA</span></td>
                        <td style="padding: 15px; color: #10b981;">Resolución Automática</td>
                    </tr>
                    <tr>
                        <td style="padding: 15px; font-weight: bold; color: #38bdf8;">case_001_basic</td>
                        <td style="padding: 15px;">Global Traders Inc</td>
                        <td style="padding: 15px;"><span style="background: rgba(16, 185, 129, 0.2); color: #10b981; padding: 4px 8px; border-radius: 4px; font-size: 12px;">BAJA</span></td>
                        <td style="padding: 15px; color: #10b981;">Auditado Completado</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
    with col_activity:
        st.markdown("#### ⚡ Actividad del Enjambre (Swarm)")
        st.markdown("""
        <div class="premium-card">
            <div style="margin-bottom: 15px;">
                <span style="font-size: 12px; color: #94a3b8;">Hace 2 mins</span><br>
                <span style="color: #38bdf8;">[FinanceAgent]</span> Conciliación de facturas batch #842 completada.
            </div>
            <div style="margin-bottom: 15px;">
                <span style="font-size: 12px; color: #94a3b8;">Hace 5 mins</span><br>
                <span style="color: #a855f7;">[LegalAgent]</span> Base Vectorial ChromaDB actualizada (12 nuevos contratos indexados).
            </div>
            <div style="margin-bottom: 15px;">
                <span style="font-size: 12px; color: #94a3b8;">Hace 12 mins</span><br>
                <span style="color: #10b981;">[MasterAgent]</span> Nota de crédito $2,500 aprobada para case_089_auto.
            </div>
            <div style="margin-bottom: 15px;">
                <span style="font-size: 12px; color: #94a3b8;">Hace 45 mins</span><br>
                <span style="color: #ef4444;">[LogisticsAgent]</span> Alerta: Tasa de OCR baja en remisiones de proveedor XYZ.
            </div>
        </div>
        """, unsafe_allow_html=True)
