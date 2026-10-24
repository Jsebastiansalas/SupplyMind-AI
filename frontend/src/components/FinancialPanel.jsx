import React, { useState } from 'react';
import { 
  Scale, 
  Copy, 
  Check, 
  FileText, 
  TrendingUp,
  ShieldCheck,
  ChevronRight,
  Package,
  Calendar,
  Layers,
  FileCheck2,
  Printer,
  AlertTriangle,
  Handshake,
  Globe,
  ShieldAlert,
  ListChecks,
  CheckSquare,
  Square,
  ArrowRightLeft
} from 'lucide-react';

export default function FinancialPanel({ 
  report, 
  activeSubTab: externalSubTab, 
  onSubTabChange, 
  onOpenOfficialDossier,
  onApplyScenario
}) {
  const [localSubTab, setLocalSubTab] = useState('summary');
  const activeSubTab = externalSubTab || localSubTab;
  const setActiveSubTab = (tab) => {
    if (onSubTabChange) onSubTabChange(tab);
    setLocalSubTab(tab);
  };
  const [copiedHash, setCopiedHash] = useState(false);

  // Estados interactivos para Motor Cambiario FX & Incoterms 2020 (Pilar 5)
  const [selectedIncoterm, setSelectedIncoterm] = useState('FOB');
  const [invoiceFxRate, setInvoiceFxRate] = useState(18.50);
  const [paymentFxRate, setPaymentFxRate] = useState(17.85);
  const [targetCurrency, setTargetCurrency] = useState('MXN');

  // Estados interactivos para Perfilador de Fugas de Retailers & Checklist (Pilar 3)
  const defaultRetailer = report?.case_id?.includes('005') || report?.case_id?.includes('amazon') ? 'AMAZON'
    : (report?.case_id?.includes('006') || report?.case_id?.includes('walmart') ? 'WALMART'
    : (report?.case_id?.includes('007') || report?.case_id?.includes('cisco') ? 'CISCO'
    : (report?.case_id?.includes('008') || report?.case_id?.includes('homedepot') ? 'HOMEDEPOT' : 'MEGA_RETAILER')));
  
  const [selectedRetailer, setSelectedRetailer] = useState(defaultRetailer);
  const [checklistCompleted, setChecklistCompleted] = useState({});

  const toggleChecklistItem = (id) => {
    setChecklistCompleted(prev => ({ ...prev, [id]: !prev[id] }));
  };

  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center h-80 text-center p-8 text-zinc-500 ledger-card">
        <Scale className="w-10 h-10 mb-3 text-zinc-600" />
        <h3 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider font-mono">
          Ningún Expediente Seleccionado
        </h3>
        <p className="text-xs text-zinc-500 mt-1 max-w-sm">
          Seleccione un expediente para desplegar la conciliación y el dictamen de arbitraje.
        </p>
      </div>
    );
  }

  const billed = Number(report.billed_amount || 0);
  const received = Number(report.received_amount || 0);
  const diff = Number(report.difference || 0);
  const justified = Number(report.justified_amount || 0);
  const claimable = Number(report.claimable_amount || 0);
  const confidence = Number(report.confidence || 0.95);
  const executionTime = Number(report.execution_time_seconds || 0.15);

  const skuMatching = report.sku_matching || null;
  const noticeWindow = report.notice_window_audit || null;

  const isClaimable = claimable > 0;
  const isTechnicalError = confidence === 0 || (report.root_cause && report.root_cause.includes("TECHNICAL_ERROR"));
  const totalDeduction = Math.abs(diff);

  const auditChecksum = `SM-AUDIT-${Math.abs(Math.round(billed * 100)).toString(16)}-${Math.abs(Math.round(claimable * 100)).toString(16)}-${Math.abs(Math.round(justified * 100)).toString(16)}`.toUpperCase();

  const handleCopyHash = () => {
    navigator.clipboard?.writeText(auditChecksum);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const formatCurrency = (val) => {
    return val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  return (
    <div className="space-y-6">
      
      {/* 1. HORIZONTAL EQUATION STRIP (Clean Sovereign Ledger Ribbon) */}
      <div className="p-4 rounded-lg bg-[#0e0f14] border border-[#1b1c24] flex flex-wrap items-baseline justify-between gap-4 shadow-subtle select-none">
        <div className="flex flex-wrap items-baseline gap-6 sm:gap-9">
          <div>
            <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
              Facturado Bruto
            </div>
            <div className="text-xl font-bold font-mono tabular-nums text-zinc-100 mt-0.5">
              ${formatCurrency(billed)}
            </div>
          </div>

          <div className="text-zinc-600 font-mono text-base hidden sm:block">—</div>

          <div>
            <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
              Cobrado en Banco
            </div>
            <div className="text-xl font-bold font-mono tabular-nums text-zinc-300 mt-0.5">
              ${formatCurrency(received)}
            </div>
          </div>

          <div className="text-zinc-600 font-mono text-base hidden sm:block">=</div>

          <div>
            <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
              Retención / Deducción
            </div>
            <div className="text-xl font-bold font-mono tabular-nums text-zinc-200 mt-0.5">
              ${formatCurrency(diff)}
            </div>
          </div>
        </div>

        <div className="text-right">
          <div className="text-[10px] font-mono uppercase tracking-widest text-[#d4af37] font-bold">
            Saldo Recuperable Exigible
          </div>
          <div className="text-2xl font-black font-mono tabular-nums text-[#eed98d] mt-0.5">
            ${formatCurrency(claimable)} <span className="text-xs font-semibold text-zinc-400">USD</span>
          </div>
        </div>
      </div>

      {/* 2. HERO RESOLUTION BANNER (Institutional Forensic Docket) */}
      <div className={`border rounded-lg p-5 relative overflow-hidden shadow-subtle ${
        isTechnicalError 
          ? 'bg-[#140f10] border-rose-900/50' 
          : 'bg-[#101117] border-[#1e202b]'
      }`}>
        <div className={`absolute top-0 left-0 right-0 h-[2px] ${
          isTechnicalError 
            ? 'bg-rose-500' 
            : 'bg-[#d4af37]'
        }`} />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center space-x-2">
              <span className={`text-[10px] font-mono uppercase tracking-wider font-semibold px-2 py-0.5 rounded border ${
                isTechnicalError
                  ? 'bg-rose-950/60 text-rose-300 border-rose-800/60 flex items-center'
                  : 'bg-[#1b1910] text-[#eed98d] border-[#d4af37]/40'
              }`}>
                {isTechnicalError ? (
                  <span className="flex items-center space-x-1">
                    <AlertTriangle className="w-3 h-3 text-rose-400 mr-1" />
                    <span>Degradación Controlada: Error Contenido</span>
                  </span>
                ) : (
                  <span>Dictamen Pericial de Conciliación</span>
                )}
              </span>
              {!isTechnicalError && noticeWindow && (
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                  noticeWindow.is_timely ? 'bg-[#15161d] text-zinc-400 border-[#222430]' : 'bg-rose-950 text-rose-300 border-rose-900'
                }`}>
                  {noticeWindow.status_label}
                </span>
              )}
            </div>

            <h2 className="text-lg lg:text-xl font-bold text-white tracking-tight">
              {isTechnicalError 
                ? 'Anomalía de Integridad: Cuarentena Documental' 
                : (isClaimable ? 'Recuperación Formal Exigible' : 'Retención 100% Justificada')}
            </h2>

            <p className="text-xs text-zinc-300 leading-relaxed font-sans">
              {report.root_cause}
            </p>
          </div>

          <div className="flex-shrink-0 bg-[#0e0f14] border border-[#1d1f29] rounded p-3 min-w-[220px]">
            <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider block">
              Acción Operativa Inmediata
            </span>
            <div className="text-xs font-semibold text-zinc-200 mt-1">
              {isTechnicalError 
                ? 'Cuarentena Documental & Auditoría' 
                : (isClaimable ? 'Carta Formal de Objeción' : 'Emisión de Nota de Crédito')}
            </div>
            <div className="mt-2 pt-2 border-t border-[#1a1c24] text-[10px] text-zinc-500 flex justify-between font-mono tabular-nums">
              <span>Tiempo de Resolución</span>
              <span className={isTechnicalError ? "text-rose-400" : "text-[#eed98d]"}>
                {executionTime.toFixed(2)}s • Determinístico
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. SUB-VIEWS SEGMENTED TABS (Institutional Precision) */}
      <div className="space-y-4">
        
        <div className="flex flex-wrap gap-1.5 border-b border-[#1b1c24] pb-2 select-none">
          <button
            onClick={() => setActiveSubTab('summary')}
            className={`btn-tactile px-3 py-1.5 rounded text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
              activeSubTab === 'summary'
                ? 'bg-[#171822] text-white border border-[#2b2e3e] shadow-tactile'
                : 'text-zinc-400 hover:text-white hover:bg-[#121319]'
            }`}
          >
            <FileText className="w-3.5 h-3.5 text-[#d4af37]" />
            <span>Resumen & Fundamento Legal</span>
          </button>

          <button
            onClick={() => setActiveSubTab('negotiation')}
            className={`btn-tactile px-3 py-1.5 rounded text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
              activeSubTab === 'negotiation'
                ? 'bg-[#171822] text-[#eed98d] border border-[#d4af37]/60 shadow-tactile font-bold'
                : 'text-zinc-400 hover:text-white hover:bg-[#121319]'
            }`}
          >
            <Handshake className="w-3.5 h-3.5 text-[#d4af37]" />
            <span>🤝 Negociación B2B (3 Escenarios)</span>
          </button>

          {skuMatching && (
            <button
              onClick={() => setActiveSubTab('sku')}
              className={`btn-tactile px-3 py-1.5 rounded text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
                activeSubTab === 'sku'
                  ? 'bg-[#171822] text-white border border-[#2b2e3e] shadow-tactile'
                  : 'text-zinc-400 hover:text-white hover:bg-[#121319]'
              }`}
            >
              <Package className="w-3.5 h-3.5 text-[#d4af37]" />
              <span>Auditoría SKU por SKU ({skuMatching.total_skus_audited})</span>
            </button>
          )}

          <button
            onClick={() => setActiveSubTab('ledger')}
            className={`btn-tactile px-3 py-1.5 rounded text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
              activeSubTab === 'ledger'
                ? 'bg-[#171822] text-white border border-[#2b2e3e] shadow-tactile'
                : 'text-zinc-400 hover:text-white hover:bg-[#121319]'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-zinc-400" />
            <span>Libro Contable (Partida Doble)</span>
          </button>

          <button
            onClick={() => setActiveSubTab('certificate')}
            className={`btn-tactile px-3 py-1.5 rounded text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
              activeSubTab === 'certificate'
                ? 'bg-[#171822] text-white border border-[#2b2e3e] shadow-tactile'
                : 'text-zinc-400 hover:text-white hover:bg-[#121319]'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5 text-zinc-400" />
            <span>Certificado Digital NIF C-3</span>
          </button>

          <button
            onClick={() => setActiveSubTab('erp')}
            className={`btn-tactile px-3 py-1.5 rounded text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
              activeSubTab === 'erp'
                ? 'bg-[#171822] text-[#eed98d] border border-[#d4af37]/60 shadow-tactile font-bold'
                : 'text-zinc-400 hover:text-white hover:bg-[#121319]'
            }`}
          >
            <FileCheck2 className="w-3.5 h-3.5 text-[#d4af37]" />
            <span>🏦 Pólizas ERP & CFDI 4.0</span>
          </button>

          <button
            onClick={() => setActiveSubTab('fx_incoterms')}
            className={`btn-tactile px-3 py-1.5 rounded text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
              activeSubTab === 'fx_incoterms'
                ? 'bg-[#171822] text-[#eed98d] border border-[#d4af37]/60 shadow-tactile font-bold'
                : 'text-zinc-400 hover:text-white hover:bg-[#121319]'
            }`}
          >
            <Globe className="w-3.5 h-3.5 text-[#d4af37]" />
            <span>🌐 FX & Incoterms 2020</span>
          </button>

          <button
            onClick={() => setActiveSubTab('retailer_leakage')}
            className={`btn-tactile px-3 py-1.5 rounded text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
              activeSubTab === 'retailer_leakage'
                ? 'bg-[#171822] text-[#eed98d] border border-[#d4af37]/60 shadow-tactile font-bold'
                : 'text-zinc-400 hover:text-white hover:bg-[#121319]'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5 text-[#d4af37]" />
            <span>🛡️ Fugas Retailers & Checklist</span>
          </button>

          {onOpenOfficialDossier && (
            <button
              onClick={onOpenOfficialDossier}
              className="btn-tactile ml-auto flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#1f1d14] hover:bg-[#282518] border border-[#d4af37]/60 text-xs font-mono text-[#eed98d] font-semibold transition-colors shadow-tactile"
              title="Descargar Dictamen Pericial Oficial con Validez Probatoria"
            >
              <Printer className="w-3.5 h-3.5 text-[#d4af37]" />
              <span>Dictamen Pericial Oficial PDF</span>
            </button>
          )}
        </div>

        {/* SUB-TAB 1: RESUMEN EJECUTIVO & FUNDAMENTO LEGAL */}
        {activeSubTab === 'summary' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-[#121317] border border-[#23242c] rounded-xl p-5 space-y-3">
              <div className="flex items-center space-x-2 text-zinc-300">
                <FileText className="w-4 h-4 text-[#d4af37]" />
                <h3 className="text-xs font-mono font-semibold uppercase tracking-wider">
                  Causa Raíz & Citas Documentales
                </h3>
              </div>
              <div className="p-3.5 rounded-lg bg-[#0e0f12] border border-[#1e2027] text-zinc-300 text-xs leading-relaxed font-sans">
                {report.root_cause}
              </div>
              {noticeWindow && (
                <div className="p-3 rounded-lg bg-[#15161e] border border-[#242633] text-[11px] text-zinc-400 font-sans space-y-1">
                  <div className="font-semibold text-zinc-200 font-mono text-[10px] uppercase">
                    Auditoría de Caducidad Contractual:
                  </div>
                  <div>{noticeWindow.legal_basis}</div>
                </div>
              )}
            </div>

            <div className="bg-[#121317] border border-[#23242c] rounded-xl p-5 space-y-3">
              <div className="flex items-center space-x-2 text-zinc-300">
                <TrendingUp className="w-4 h-4 text-zinc-400" />
                <h3 className="text-xs font-mono font-semibold uppercase tracking-wider">
                  Ruta de Acción Comercial B2B
                </h3>
              </div>
              <div className="p-3.5 rounded-lg bg-[#0e0f12] border border-[#1e2027] text-zinc-300 text-xs leading-relaxed font-sans">
                {report.recommended_action}
              </div>
              <div className="p-3 rounded-lg bg-[#15161e] border border-[#242633] text-[11px] text-zinc-400 font-mono flex items-center justify-between">
                <span>Estrategia:</span>
                <span className="text-[#eed98d] font-bold">
                  {isClaimable ? 'Objeción con Copia de Remisión Sellada' : 'Aceptación y Nota de Crédito'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* SUB-TAB: NEGOCIACIÓN B2B Y 3 ESCENARIOS */}
        {activeSubTab === 'negotiation' && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-[#121319] border border-[#232533] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <div className="flex items-center space-x-2">
                  <Handshake className="w-4 h-4 text-[#d4af37]" />
                  <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                    Matriz de Negociación B2B Bilateral (Fase 2)
                  </h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1f1d14] border border-[#d4af37]/50 text-[#eed98d]">
                    Multi-Táctico
                  </span>
                </div>
                <p className="text-xs text-zinc-400 mt-1">
                  Contrapropuestas determinísticas con cálculo estricto en Decimal, estimación de fricción y contraprestaciones del comprador.
                </p>
              </div>

              {report.active_scenario && (
                <div className="px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-500/50 text-emerald-300 text-xs font-mono flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span>Escenario Activo: <strong>{report.active_scenario}</strong></span>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* ESCENARIO 1: AGRESIVO */}
              <div className="p-4 rounded-xl bg-[#0f1015] border border-[#262836] hover:border-sky-500/50 transition-all flex flex-col justify-between space-y-4">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-sky-950/60 text-sky-400 border border-sky-800/50">
                      LEGAL STRICT
                    </span>
                    <span className="text-[10px] font-mono text-rose-400">Riesgo Alto 🔴</span>
                  </div>
                  <h4 className="text-sm font-bold text-white mt-2">1. Cobro Contractual Íntegro</h4>
                  <p className="text-[11px] text-zinc-400 mt-1 leading-relaxed">
                    Exigencia extrajudicial del 100% del saldo retenido bajo amparo estricto de cláusulas contractuales.
                  </p>

                  <div className="mt-4 p-3 rounded-lg bg-[#14151e] border border-[#1e202c] space-y-2 font-mono text-xs">
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Cobro en Efectivo:</span>
                      <span className="text-sky-300 font-bold">${formatCurrency(claimable + (report.concessions?.[0]?.concession_amount ? Number(report.concessions[0].concession_amount) : 0))}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Nota de Crédito:</span>
                      <span className="text-zinc-300">${formatCurrency(justified - (report.concessions?.[0]?.concession_amount ? Number(report.concessions[0].concession_amount) : 0))}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Recuperación:</span>
                      <span className="text-emerald-400 font-bold">100%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Plazo Esperado:</span>
                      <span className="text-zinc-300">25 días</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => onApplyScenario && onApplyScenario('AGGRESSIVE')}
                  className="w-full btn-tactile py-2 rounded-lg bg-[#181a24] hover:bg-sky-950/60 border border-[#2a2d3e] hover:border-sky-500/60 text-xs font-mono text-sky-300 font-semibold transition-all"
                >
                  ⚡ Aplicar Cobro Íntegro
                </button>
              </div>

              {/* ESCENARIO 2: EQUILIBRADO (RECOMENDADO) */}
              <div className="p-4 rounded-xl bg-[#0f1015] border-2 border-[#d4af37]/60 shadow-[0_0_20px_rgba(212,175,55,0.12)] flex flex-col justify-between space-y-4 relative">
                <div className="absolute -top-2.5 right-3 px-2 py-0.5 rounded bg-[#d4af37] text-black font-mono text-[9px] font-bold tracking-wider uppercase">
                  ⭐ Recomendado
                </div>
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/50">
                      WIN-WIN RECÍPROCO
                    </span>
                    <span className="text-[10px] font-mono text-amber-400">Riesgo Medio 🟡</span>
                  </div>
                  <h4 className="text-sm font-bold text-white mt-2">2. Conciliación Táctica</h4>
                  <p className="text-[11px] text-zinc-400 mt-1 leading-relaxed">
                    Concesión del 50% de la penalidad condicionada a pago inmediato en 5 días y exención de multas en siguientes pedidos.
                  </p>

                  <div className="mt-4 p-3 rounded-lg bg-[#14151e] border border-[#1e202c] space-y-2 font-mono text-xs">
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Cobro en Efectivo:</span>
                      <span className="text-emerald-300 font-bold">50% Saldo Neto</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Nota de Crédito:</span>
                      <span className="text-[#eed98d] font-bold">50% Concesión</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Reciprocidad Exigida:</span>
                      <span className="text-zinc-300">2 POs sin multas</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Plazo Esperado:</span>
                      <span className="text-emerald-400 font-bold">7 días</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => onApplyScenario && onApplyScenario('BALANCED')}
                  className="w-full btn-tactile py-2 rounded-lg bg-[#242013] hover:bg-[#332b17] border border-[#d4af37] text-xs font-mono text-[#eed98d] font-bold transition-all shadow-tactile"
                >
                  🤝 Aplicar Conciliación Táctica
                </button>
              </div>

              {/* ESCENARIO 3: CONSERVADOR */}
              <div className="p-4 rounded-xl bg-[#0f1015] border border-[#262836] hover:border-purple-500/50 transition-all flex flex-col justify-between space-y-4">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-purple-950/60 text-purple-400 border border-purple-800/50">
                      TIER-1 RETENTION
                    </span>
                    <span className="text-[10px] font-mono text-emerald-400">Riesgo Bajo 🟢</span>
                  </div>
                  <h4 className="text-sm font-bold text-white mt-2">3. Conservación Estratégica</h4>
                  <p className="text-[11px] text-zinc-400 mt-1 leading-relaxed">
                    Absorción total de la retención vía Nota de Crédito blindando la cuenta a cambio de compromiso de volumen anual +15%.
                  </p>

                  <div className="mt-4 p-3 rounded-lg bg-[#14151e] border border-[#1e202c] space-y-2 font-mono text-xs">
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Cobro en Efectivo:</span>
                      <span className="text-zinc-400">$0.00</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Nota de Crédito:</span>
                      <span className="text-purple-300 font-bold">100% Saldo</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Contraprestación:</span>
                      <span className="text-zinc-300">+15% Volumen Q</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Plazo Esperado:</span>
                      <span className="text-emerald-400 font-bold">2 días</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => onApplyScenario && onApplyScenario('CONSERVATIVE')}
                  className="w-full btn-tactile py-2 rounded-lg bg-[#181a24] hover:bg-purple-950/60 border border-[#2a2d3e] hover:border-purple-500/60 text-xs font-mono text-purple-300 font-semibold transition-all"
                >
                  🛡️ Aplicar Conservación
                </button>
              </div>
            </div>
          </div>
        )}

        {/* SUB-TAB 2: AUDITORÍA SKU POR SKU & FISCAL */}
        {activeSubTab === 'sku' && skuMatching && (
          <div className="bg-[#101116] border border-[#1b1c24] rounded-lg overflow-hidden shadow-subtle">
            <div className="p-3.5 border-b border-[#1b1c24] bg-[#12131a] flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                  Auditoría Analítica por Partida / SKU
                </h3>
                <p className="text-[11px] text-zinc-400 font-sans mt-0.5">
                  Cotejo cruzado de Factura vs Remisión vs Orden de Compra y desglose de IVA (16%).
                </p>
              </div>
              <div className="text-xs font-mono text-zinc-300 flex gap-4 tabular-nums">
                <span>Partidas Auditadas: <strong className="text-white">{skuMatching.total_skus_audited}</strong></span>
                <span>Con Discrepancia: <strong className="text-[#eed98d]">{skuMatching.skus_with_discrepancies}</strong></span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono tabular-nums">
                <thead>
                  <tr className="border-b border-[#1b1c24] text-zinc-500 text-[10px] uppercase bg-[#0d0e13]">
                    <th className="py-2.5 px-4 font-semibold">SKU / Descripción</th>
                    <th className="py-2.5 px-4 font-semibold text-center">Facturado</th>
                    <th className="py-2.5 px-4 font-semibold text-center">Recibido</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Precio Unitario</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Impacto Bruto</th>
                    <th className="py-2.5 px-4 font-semibold text-right">IVA 16%</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Dictamen</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#181922] text-zinc-300">
                  {skuMatching.line_items.map((line, idx) => (
                    <tr key={idx} className="audit-row transition-colors">
                      <td className="py-2.5 px-4">
                        <div className="font-bold text-white tracking-tight">{line.item_id}</div>
                        <div className="text-[10px] text-zinc-400 font-sans truncate max-w-xs">{line.description}</div>
                      </td>
                      <td className="py-2.5 px-4 text-center tabular-nums">{line.quantity_billed}</td>
                      <td className="py-2.5 px-4 text-center tabular-nums">{line.quantity_received}</td>
                      <td className="py-2.5 px-4 text-right tabular-nums">${formatCurrency(line.unit_price_invoiced)}</td>
                      <td className="py-2.5 px-4 text-right font-bold text-white tabular-nums">
                        ${formatCurrency(line.line_total_discrepancy)}
                      </td>
                      <td className="py-2.5 px-4 text-right text-zinc-400 tabular-nums">
                        ${formatCurrency(line.vat_impact_16)}
                      </td>
                      <td className="py-2.5 px-4 text-right">
                        <span className={`text-[10px] px-2 py-0.5 rounded font-mono ${
                          line.is_fully_reconciled
                            ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/60'
                            : 'bg-[#221f15] text-[#eed98d] border border-[#d4af37]/40'
                        }`}>
                          {line.status_label}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-[#121319] border-t border-[#1e2029] text-white">
                    <td className="py-3 px-4 uppercase text-zinc-400 font-semibold" colSpan={4}>
                      Impacto Neto Total por Discrepancia de Líneas
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-sm font-bold text-[#eed98d] tabular-nums">
                      ${formatCurrency(skuMatching.net_line_discrepancy)}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-zinc-400 tabular-nums">
                      ${formatCurrency(skuMatching.total_vat_impact_16)}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-[10px] text-zinc-400 tabular-nums">
                      NC TOTAL: ${formatCurrency(skuMatching.credit_note_recommended_total)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        )}

        {/* SUB-TAB 3: LIBRO CONTABLE (PARTIDA DOBLE) */}
        {activeSubTab === 'ledger' && (
          <div className="bg-[#101116] border border-[#1b1c24] rounded-lg overflow-hidden shadow-subtle">
            <div className="px-4 py-3 border-b border-[#1b1c24] bg-[#12131a] flex items-center justify-between">
              <span className="text-xs font-mono font-semibold text-zinc-200 uppercase tracking-wider">
                Balance de Liquidación Contable NIF C-3 / GAAP
              </span>
              <span className="text-[10px] font-mono text-zinc-400">
                Precisión Decimal Determinística
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono tabular-nums">
                <thead>
                  <tr className="border-b border-[#1b1c24] text-zinc-500 text-[10px] uppercase bg-[#0d0e13]">
                    <th className="py-2.5 px-4 font-semibold">Concepto Contable</th>
                    <th className="py-2.5 px-4 font-semibold">Naturaleza</th>
                    <th className="py-2.5 px-4 font-semibold">Sustento Probatorio</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Importe (USD)</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Estatus</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#181922] text-zinc-300">
                  <tr className="audit-row transition-colors">
                    <td className="py-2.5 px-4 font-medium text-white">Factura Original Emitida</td>
                    <td className="py-2.5 px-4 text-zinc-400">(+) Crédito</td>
                    <td className="py-2.5 px-4 text-zinc-400">CFDI / Comprobante Comercial</td>
                    <td className="py-2.5 px-4 text-right font-medium text-white tabular-nums">${formatCurrency(billed)}</td>
                    <td className="py-2.5 px-4 text-right text-zinc-400">Exigible Base</td>
                  </tr>

                  <tr className="audit-row transition-colors">
                    <td className="py-2.5 px-4 font-medium text-white">Dispersión Bancaria Recibida</td>
                    <td className="py-2.5 px-4 text-zinc-400">(-) Débito</td>
                    <td className="py-2.5 px-4 text-zinc-400">Comprobante SPEI / Transferencia</td>
                    <td className="py-2.5 px-4 text-right font-medium text-zinc-300 tabular-nums">-${formatCurrency(received)}</td>
                    <td className="py-2.5 px-4 text-right text-zinc-400">Liquidado</td>
                  </tr>

                  {justified > 0 && (
                    <tr className="audit-row transition-colors bg-[#171415]/30">
                      <td className="py-2.5 px-4 font-medium text-zinc-300">Deducción Contractual Procedente</td>
                      <td className="py-2.5 px-4 text-zinc-500">(-) Ajuste</td>
                      <td className="py-2.5 px-4 text-zinc-400">Remisión Sellada con Faltante Físico</td>
                      <td className="py-2.5 px-4 text-right font-medium text-zinc-300 tabular-nums">-${formatCurrency(justified)}</td>
                      <td className="py-2.5 px-4 text-right text-zinc-400">Emitir Nota de Crédito</td>
                    </tr>
                  )}

                  {claimable > 0 && (
                    <tr className="audit-row transition-colors bg-[#1b1910]/30">
                      <td className="py-2.5 px-4 font-medium text-[#eed98d]">Retención Sin Soporte Legal</td>
                      <td className="py-2.5 px-4 text-[#d4af37]">(+) Reclamo</td>
                      <td className="py-2.5 px-4 text-zinc-300">Remisión Conforme sin Observación</td>
                      <td className="py-2.5 px-4 text-right font-bold text-[#eed98d] tabular-nums">+${formatCurrency(claimable)}</td>
                      <td className="py-2.5 px-4 text-right text-[#d4af37] font-semibold">Exigir Restitución</td>
                    </tr>
                  )}
                </tbody>
                <tfoot>
                  <tr className="bg-[#121319] border-t border-[#1e2029] text-white">
                    <td className="py-3 px-4 uppercase text-zinc-400 font-semibold" colSpan={3}>
                      Conciliación Neta Final
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-sm font-bold text-[#eed98d] tabular-nums">
                      ${formatCurrency(claimable)}
                    </td>
                    <td className="py-3 px-4 text-right text-[11px] font-mono text-zinc-300">
                      SALDO EXIGIBLE
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        )}

        {/* SUB-TAB 4: CERTIFICADO DIGITAL */}
        {activeSubTab === 'certificate' && (
          <div className="p-5 bg-[#101115] border border-[#20222a] rounded-xl space-y-3">
            <div className="flex items-center space-x-2 text-zinc-300">
              <ShieldCheck className="w-5 h-5 text-[#d4af37]" />
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider">
                Certificado Digital de Conciliación Determinística
              </h3>
            </div>
            <p className="text-xs text-zinc-400 font-sans leading-relaxed">
              Este informe cuenta con un sello criptográfico inmutable generado a partir de los datos exactos del expediente.
              Garantiza auditoría de partida doble y ausencia total de alucinaciones matemáticas mediante el motor Python Decimal.
            </p>
            <div className="flex items-center space-x-2 pt-2">
              <span className="text-xs font-mono text-zinc-300 bg-[#16171d] px-3 py-1.5 rounded-md border border-[#22242c]">
                {auditChecksum}
              </span>
              <button
                onClick={handleCopyHash}
                className="p-1.5 hover:text-white transition-colors text-zinc-400 rounded bg-[#16171d] border border-[#22242c]"
                title="Copiar Sello Criptográfico"
              >
                {copiedHash ? <Check className="w-3.5 h-3.5 text-[#d4af37]" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>
        )}

        {/* SUB-TAB 5: INTEGRACIÓN ERP Y TIMBRADO FISCAL CFDI 4.0 */}
        {activeSubTab === 'erp' && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-[#121319] border border-[#232533] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <div className="flex items-center space-x-2">
                  <FileCheck2 className="w-4 h-4 text-[#d4af37]" />
                  <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                    Integración Contable ERP & Timbrado CFDI 4.0 (Fase 3)
                  </h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 font-bold">
                    ERP Ready
                  </span>
                </div>
                <p className="text-xs text-zinc-400 mt-1">
                  Pólizas de diario para SAP S/4HANA (BAPI / IDoc), Oracle NetSuite y XML CFDI 4.0 (Tipo E).
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <a
                  href={`/api/cases/${report.case_id}/erp/sap`}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-tactile px-3 py-1.5 rounded bg-[#181a24] hover:bg-[#202330] border border-[#2a2d3e] text-xs font-mono text-sky-300 font-semibold transition-all flex items-center space-x-1"
                >
                  <span>📥 SAP BAPI</span>
                </a>
                <a
                  href={`/api/cases/${report.case_id}/erp/netsuite`}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-tactile px-3 py-1.5 rounded bg-[#181a24] hover:bg-[#202330] border border-[#2a2d3e] text-xs font-mono text-purple-300 font-semibold transition-all flex items-center space-x-1"
                >
                  <span>📥 NetSuite CSV</span>
                </a>
                <a
                  href={`/api/cases/${report.case_id}/erp/cfdi`}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-tactile px-3 py-1.5 rounded bg-[#242013] hover:bg-[#332b17] border border-[#d4af37] text-xs font-mono text-[#eed98d] font-bold transition-all flex items-center space-x-1 shadow-tactile"
                >
                  <span>📥 CFDI 4.0 XML</span>
                </a>
              </div>
            </div>

            {/* Asiento Contable NIF C-3 */}
            <div className="bg-[#101116] border border-[#1b1c24] rounded-lg overflow-hidden shadow-subtle">
              <div className="p-3.5 border-b border-[#1b1c24] bg-[#12131a] flex justify-between items-center">
                <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                  Asiento Contable de Saneamiento (NIF C-3 / US GAAP)
                </span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
                  Cuadre de Partida Doble: $0.00 Diferencia
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono tabular-nums">
                  <thead>
                    <tr className="border-b border-[#1b1c24] text-zinc-500 text-[10px] uppercase bg-[#0d0e13]">
                      <th className="py-2.5 px-4 font-semibold">Línea</th>
                      <th className="py-2.5 px-4 font-semibold">Cuenta Contable</th>
                      <th className="py-2.5 px-4 font-semibold">Concepto / Glosa</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Cargo (Debit USD)</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Abono (Credit USD)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#181922] text-zinc-300">
                    <tr className="audit-row transition-colors">
                      <td className="py-2.5 px-4">1</td>
                      <td className="py-2.5 px-4 text-sky-400 font-bold">410500</td>
                      <td className="py-2.5 px-4 text-zinc-200">Descuentos y Bonificaciones sobre Ventas (Nota de Crédito Base)</td>
                      <td className="py-2.5 px-4 text-right text-emerald-400 font-bold">${formatCurrency(justified > 0 ? (justified / 1.16) : 0)}</td>
                      <td className="py-2.5 px-4 text-right text-zinc-500">$0.00</td>
                    </tr>
                    <tr className="audit-row transition-colors">
                      <td className="py-2.5 px-4">2</td>
                      <td className="py-2.5 px-4 text-sky-400 font-bold">210800</td>
                      <td className="py-2.5 px-4 text-zinc-200">IVA Trasladado por Cancelar (16% Nota de Crédito)</td>
                      <td className="py-2.5 px-4 text-right text-emerald-400 font-bold">${formatCurrency(justified > 0 ? (justified - (justified / 1.16)) : 0)}</td>
                      <td className="py-2.5 px-4 text-right text-zinc-500">$0.00</td>
                    </tr>
                    <tr className="audit-row transition-colors">
                      <td className="py-2.5 px-4">3</td>
                      <td className="py-2.5 px-4 text-sky-400 font-bold">120090</td>
                      <td className="py-2.5 px-4 text-zinc-200">Deudores en Disputa / Saldo Reclamable en Cobranza Legal</td>
                      <td className="py-2.5 px-4 text-right text-[#eed98d] font-bold">${formatCurrency(claimable)}</td>
                      <td className="py-2.5 px-4 text-right text-zinc-500">$0.00</td>
                    </tr>
                    <tr className="audit-row transition-colors">
                      <td className="py-2.5 px-4">4</td>
                      <td className="py-2.5 px-4 text-amber-400 font-bold">120000</td>
                      <td className="py-2.5 px-4 text-zinc-200">Clientes / Cuentas por Cobrar B2B (Cancelación de Partida Retenida)</td>
                      <td className="py-2.5 px-4 text-right text-zinc-500">$0.00</td>
                      <td className="py-2.5 px-4 text-right text-rose-400 font-bold">${formatCurrency(totalDeduction)}</td>
                    </tr>
                  </tbody>
                  <tfoot>
                    <tr className="bg-[#121319] border-t border-[#1e2029] text-white">
                      <td className="py-3 px-4 font-bold" colSpan={3}>
                        TOTALES DE BALANCE (PARTIDA DOBLE BALANCES EQUAL)
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-sm font-bold text-emerald-400">
                        ${formatCurrency(totalDeduction)}
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-sm font-bold text-rose-400">
                        ${formatCurrency(totalDeduction)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* SUB-TAB: MOTOR CAMBIARIO FX & INCOTERMS 2020 (Pilar 5) */}
        {activeSubTab === 'fx_incoterms' && (() => {
          const rateInv = Number(invoiceFxRate) || 18.50;
          const ratePay = Number(paymentFxRate) || 17.85;
          const billedMxn = billed * rateInv;
          const receivedMxn = received * ratePay;
          const totalNominalDiffMxn = billedMxn - receivedMxn;
          const fxVarianceMxn = billed * (rateInv - ratePay);
          const commercialDeductionMxn = totalDeduction * ratePay;
          const isFxLoss = fxVarianceMxn > 0;

          const incotermData = {
            FOB: {
              name: 'Free on Board (Franco a Bordo)',
              point: 'Bordo del buque / Terminal de carga en origen',
              riskParty: 'BUYER (Retailer / Comprador)',
              verdict: 'IMPROCEDENTE_POR_INCOTERM',
              verdictColor: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40',
              basis: 'ICC Incoterms 2020 Regla FOB Art. A4/B4 y A10/B10. Riesgo de tránsito y muelle asumido por el comprador en origen.',
              rec: 'Exigir el 100% del pago. El comprador asumió el riesgo de tránsito; las deducciones por daño o faltante en su CEDIS son improcedentes.'
            },
            FCA: {
              name: 'Free Carrier (Franco Porteador)',
              point: 'Entrega al transportista designado por el comprador en origen',
              riskParty: 'BUYER (Retailer / Comprador)',
              verdict: 'IMPROCEDENTE_POR_INCOTERM',
              verdictColor: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40',
              basis: 'ICC Incoterms 2020 Regla FCA Art. A4/B4. Mercancía entregada al porteador del comprador.',
              rec: 'El retailer debe reclamar la merma a su propia línea de transporte, no retener contra el proveedor.'
            },
            DDP: {
              name: 'Delivered Duty Paid (Entregada Derechos Pagados)',
              point: 'Muelle de descarga en CEDIS del comprador (destino)',
              riskParty: 'SELLER (Proveedor)',
              verdict: 'PROCEDENTE_EN_DESTINO',
              verdictColor: 'text-rose-400 bg-rose-950/40 border-rose-800/40',
              basis: 'ICC Incoterms 2020 Regla DDP Art. A4/B4. El vendedor soporta los riesgos hasta la entrega en destino.',
              rec: 'La merma física debidamente documentada en el muelle de descarga es deducible según contrato.'
            },
            DAP: {
              name: 'Delivered at Place (Entregada en Lugar)',
              point: 'Puesta a disposición en el vehículo de llegada sin descargar',
              riskParty: 'SELLER (Proveedor)',
              verdict: 'PROCEDENTE_EN_DESTINO',
              verdictColor: 'text-rose-400 bg-rose-950/40 border-rose-800/40',
              basis: 'ICC Incoterms 2020 Regla DAP Art. A4/B4. Vendedor responsable hasta punto acordado en destino.',
              rec: 'Riesgo del vendedor hasta la llegada al CEDIS del comprador.'
            },
            CIF: {
              name: 'Cost, Insurance and Freight (Coste, Seguro y Flete)',
              point: 'A bordo del buque en origen con póliza de seguro marítimo',
              riskParty: 'BUYER (Respaldado por póliza contratada por vendedor)',
              verdict: 'REQUERIDO_RECLAMO_ASEGURADORA',
              verdictColor: 'text-amber-400 bg-amber-950/40 border-amber-800/40',
              basis: 'ICC Incoterms 2020 Regla CIF Art. A5/B5. Mercancía asegurada bajo póliza marítima transferible.',
              rec: 'El comprador no puede retener la factura; debe activar formalmente la póliza de seguro marítimo con el endoso del certificado.'
            },
            CIP: {
              name: 'Carriage and Insurance Paid to (Transporte y Seguro Pagados)',
              point: 'Custodia del primer porteador con cobertura Todo Riesgo Cláusula A',
              riskParty: 'BUYER (Respaldado por seguro Todo Riesgo)',
              verdict: 'REQUERIDO_RECLAMO_ASEGURADORA',
              verdictColor: 'text-amber-400 bg-amber-950/40 border-amber-800/40',
              basis: 'ICC Incoterms 2020 Regla CIP Art. A5/B5. Cobertura obligatoria Institute Cargo Clauses (A).',
              rec: 'Reclamo directo a la aseguradora con el certificado de seguro Cláusula A provisto al despacho.'
            },
            EXW: {
              name: 'Ex Works (En Fábrica)',
              point: 'Fábrica / Almacén del proveedor',
              riskParty: 'BUYER (Retailer / Comprador)',
              verdict: 'IMPROCEDENTE_POR_INCOTERM',
              verdictColor: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40',
              basis: 'ICC Incoterms 2020 Regla EXW Art. A4/B4. Cumplimiento al poner la carga en instalaciones del vendedor.',
              rec: 'Toda pérdida posterior a la recolección en planta es riesgo exclusivo del comprador.'
            }
          };

          const curInco = incotermData[selectedIncoterm] || incotermData.FOB;

          return (
            <div className="space-y-4">
              {/* Barra de parámetros de simulación */}
              <div className="bg-[#121317] border border-[#23242c] rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="text-xs font-mono text-zinc-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
                    <Globe className="w-3.5 h-3.5 text-[#d4af37]" />
                    Parámetros Transfronterizos:
                  </span>
                  
                  <div className="flex items-center space-x-1.5 bg-[#0e0f13] border border-[#1e2029] rounded px-2.5 py-1">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase">Incoterm ICC:</span>
                    <select
                      value={selectedIncoterm}
                      onChange={(e) => setSelectedIncoterm(e.target.value)}
                      className="bg-transparent text-xs font-mono font-bold text-[#eed98d] focus:outline-none cursor-pointer"
                    >
                      <option value="FOB" className="bg-[#121317] text-white">FOB (Puerto Origen)</option>
                      <option value="FCA" className="bg-[#121317] text-white">FCA (Carrier Origen)</option>
                      <option value="DDP" className="bg-[#121317] text-white">DDP (Muelle Destino)</option>
                      <option value="DAP" className="bg-[#121317] text-white">DAP (Destino s/ Descargar)</option>
                      <option value="CIF" className="bg-[#121317] text-white">CIF (Seguro Marítimo)</option>
                      <option value="CIP" className="bg-[#121317] text-white">CIP (Seguro Todo Riesgo)</option>
                      <option value="EXW" className="bg-[#121317] text-white">EXW (En Fábrica)</option>
                    </select>
                  </div>

                  <div className="flex items-center space-x-1.5 bg-[#0e0f13] border border-[#1e2029] rounded px-2.5 py-1">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase">Tasa Emisión:</span>
                    <input
                      type="number"
                      step="0.01"
                      value={invoiceFxRate}
                      onChange={(e) => setInvoiceFxRate(e.target.value)}
                      className="w-16 bg-transparent text-xs font-mono font-bold text-white focus:outline-none"
                    />
                    <span className="text-[10px] font-mono text-zinc-500">{targetCurrency}</span>
                  </div>

                  <div className="flex items-center space-x-1.5 bg-[#0e0f13] border border-[#1e2029] rounded px-2.5 py-1">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase">Tasa Liquidación:</span>
                    <input
                      type="number"
                      step="0.01"
                      value={paymentFxRate}
                      onChange={(e) => setPaymentFxRate(e.target.value)}
                      className="w-16 bg-transparent text-xs font-mono font-bold text-white focus:outline-none"
                    />
                    <span className="text-[10px] font-mono text-zinc-500">{targetCurrency}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2.5 py-1 rounded border border-emerald-800/40 flex items-center gap-1 font-semibold">
                    <Check className="w-3 h-3" /> Invariante Cuadrado en Decimal
                  </span>
                </div>
              </div>

              {/* Grid de 4 tarjetas de aislamiento analítico */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3.5">
                <div className="bg-[#121317] border border-[#1f2029] rounded-xl p-4 space-y-1">
                  <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider block">
                    1. Diferencia Nominal Bruta
                  </span>
                  <div className="text-xl font-bold font-mono text-white tabular-nums">
                    ${formatCurrency(totalNominalDiffMxn)} {targetCurrency}
                  </div>
                  <span className="text-[10px] font-mono text-zinc-400 block pt-1">
                    Facturado: ${formatCurrency(billedMxn)} | Recibido: ${formatCurrency(receivedMxn)}
                  </span>
                </div>

                <div className="bg-[#121317] border border-[#1f2029] rounded-xl p-4 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                      2. Varianza Cambiaria FX
                    </span>
                    <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                      isFxLoss ? 'text-amber-400 bg-amber-950/40 border-amber-800/40' : 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40'
                    }`}>
                      {isFxLoss ? 'PÉRDIDA FX' : 'GANANCIA FX'}
                    </span>
                  </div>
                  <div className={`text-xl font-bold font-mono tabular-nums ${isFxLoss ? 'text-amber-400' : 'text-emerald-400'}`}>
                    ${formatCurrency(Math.abs(fxVarianceMxn))} {targetCurrency}
                  </div>
                  <span className="text-[10px] font-mono text-zinc-400 block pt-1">
                    Variación macro DOF: Δ {(rateInv - ratePay).toFixed(4)} por USD
                  </span>
                </div>

                <div className="bg-[#121317] border border-[#1f2029] rounded-xl p-4 space-y-1">
                  <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider block">
                    3. Deducción Comercial Neta
                  </span>
                  <div className="text-xl font-bold font-mono text-rose-400 tabular-nums">
                    ${formatCurrency(commercialDeductionMxn)} {targetCurrency}
                  </div>
                  <span className="text-[10px] font-mono text-zinc-400 block pt-1">
                    Equivalente: ${formatCurrency(totalDeduction)} USD base disputa
                  </span>
                </div>

                <div className="bg-[#121317] border border-[#2b2512] rounded-xl p-4 space-y-1 bg-gradient-to-br from-[#121317] to-[#18160d]">
                  <span className="text-[10px] font-mono text-[#eed98d] uppercase tracking-wider block">
                    4. Saldo Exigible s/ Incoterm
                  </span>
                  <div className="text-xl font-bold font-mono text-[#eed98d] tabular-nums">
                    ${formatCurrency(curInco.verdict === 'IMPROCEDENTE_POR_INCOTERM' ? totalDeduction : claimable)} USD
                  </div>
                  <span className="text-[10px] font-mono text-zinc-400 block pt-1">
                    {curInco.verdict === 'IMPROCEDENTE_POR_INCOTERM' ? '100% Exigible (Riesgo Comprador)' : 'Sujeto a conciliación física'}
                  </span>
                </div>
              </div>

              {/* Dictamen Pericial Legal Incoterms 2020 */}
              <div className="bg-[#121317] border border-[#23242c] rounded-xl p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1b1c24] pb-3">
                  <div className="flex items-center space-x-2">
                    <Scale className="w-4 h-4 text-[#d4af37]" />
                    <h3 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                      Dictamen Jurídico de Transferencia de Riesgo (ICC Incoterms 2020)
                    </h3>
                  </div>
                  <span className={`text-[11px] font-mono font-bold px-2.5 py-1 rounded border ${curInco.verdictColor}`}>
                    {curInco.verdict}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans">
                  <div className="p-3.5 rounded-lg bg-[#0e0f13] border border-[#1b1c24] space-y-2">
                    <div className="text-[10px] font-mono text-zinc-500 uppercase">Cláusula Contractual & Punto Crítico</div>
                    <div className="text-white font-medium">{curInco.name}</div>
                    <div className="text-zinc-400 text-[11px] flex items-center gap-1.5">
                      <span className="text-[#eed98d]">Punto de entrega:</span> {curInco.point}
                    </div>
                    <div className="text-zinc-400 text-[11px] flex items-center gap-1.5">
                      <span className="text-[#eed98d]">Riesgo en transporte:</span> {curInco.riskParty}
                    </div>
                  </div>

                  <div className="p-3.5 rounded-lg bg-[#0e0f13] border border-[#1b1c24] space-y-2">
                    <div className="text-[10px] font-mono text-zinc-500 uppercase">Fundamento Normativo ICC & Recomendación</div>
                    <div className="text-zinc-300 italic text-[11px]">{curInco.basis}</div>
                    <div className="text-emerald-400 text-[11px] font-medium pt-1 border-t border-[#181a22]">
                      💡 {curInco.rec}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })()}

        {/* SUB-TAB: PERFILADOR DE FUGAS DE RETAILERS & CHECKLIST PRE-DESPACHO (Pilar 3) */}
        {activeSubTab === 'retailer_leakage' && (() => {
          const RETAILER_METRICS = {
            AMAZON: {
              name: 'Amazon Fulfillment Services (CUST-RETAIL-AMZN)',
              tier: 'ALTO',
              tierClass: 'text-amber-400 bg-amber-950/40 border-amber-800/40',
              winRate: 92.4,
              recoveryRatio: 88.5,
              volume: 248500.00,
              recovered: 219922.50,
              incoterm: 'FCA',
              leadTimeDays: 18,
              cedisAlert: 'Dallas FC (DFW) y Ontario FC reportan faltante 4x superior a media nacional en SKUs de alta tecnología (NVMe, GPUs).',
              patterns: [
                {
                  id: 'PAT-AMZ-01',
                  title: 'Penalización Automatizada ASN EDI 856',
                  freq: 88.0,
                  sev: 'CRITICA',
                  mech: 'Algoritmo interno retiene 5% del valor de la orden si el ASN EDI 856 sufre latencia > 15 min, ignorando el acuse EDI 997 válido.',
                  counter: 'Anexar bitácora de transmisión UTC del gateway EDI y exigir anulación bajo Cláusula 5.3.'
                },
                {
                  id: 'PAT-AMZ-02',
                  title: 'Mermas Sistemáticas en Muelle Dallas FC',
                  freq: 74.5,
                  sev: 'ALTA',
                  mech: 'Descarga y despaletizado automático genera declaraciones de faltantes no refrendadas en carta porte del transportista.',
                  counter: 'Aplicar precintos de seguridad C-TPAT numerados con registro fotográfico en origen.'
                }
              ],
              checklist: [
                { id: 'chk_amz_1', title: 'Emisión y Acuse 997 de ASN EDI 856 (Mínimo 4h Previas)', desc: 'Transmitir ASN a Vendor Central y resguardar confirmación 997 con 4h de antelación.', mandatory: true, risk: 'Penalización DED-ASN-PENALTY ($2,500.00 USD)' },
                { id: 'chk_amz_2', title: 'Registro Fotográfico de Precinto C-TPAT en Muelle', desc: 'Capturar 4 fotos con estampa de tiempo: tarima, flejes, precinto y remolque cerrado.', mandatory: true, risk: 'Faltante físico en muelle de Dallas FC' },
                { id: 'chk_amz_3', title: 'Verificación Grado A en Códigos GS1-128', desc: 'Escanear con lector óptico verificado cada etiqueta máster asegurando contraste > 85%.', mandatory: true, risk: 'Multas de etiquetado y reempaque' },
                { id: 'chk_amz_4', title: 'Carta Porte con Firma del Transportista y Horario', desc: 'Firma autógrafa del chofer y folio de remisión con estampa de salida.', mandatory: true, risk: 'Transferencia de riesgo legal FCA / FOB' }
              ]
            },
            WALMART: {
              name: 'Walmart Inc. & Retail Link (CUST-RETAIL-WMT)',
              tier: 'PREDATORIO',
              tierClass: 'text-rose-400 bg-rose-950/40 border-rose-800/40',
              winRate: 89.1,
              recoveryRatio: 84.7,
              volume: 342000.00,
              recovered: 289674.00,
              incoterm: 'FOB',
              leadTimeDays: 21,
              cedisAlert: '85% de las órdenes entregadas en la última semana del mes sufren deducción extemporánea de pronto pago en Retail Link.',
              patterns: [
                {
                  id: 'PAT-WMT-01',
                  title: 'Deducción Extemporánea de Pronto Pago (Fin de Mes)',
                  freq: 85.0,
                  sev: 'CRITICA',
                  mech: 'Walmart retiene 2% de pronto pago en liquidaciones a día 35 alegando fecha de corte de lote bancario interno.',
                  counter: 'Invocar caducidad formal a las 23:59 del día 10 natural según Cláusula 7.2.'
                },
                {
                  id: 'PAT-WMT-02',
                  title: 'Penalización OTIF por Congestión en Caseta',
                  freq: 68.2,
                  sev: 'ALTA',
                  mech: 'Multa de 3% por entrega tardía generada por fila de camiones en patio del CEDIS atribuible a Walmart.',
                  counter: 'Sellar Gate-In Time en carta porte al arribo a caseta para blindar ventana OTIF.'
                }
              ],
              checklist: [
                { id: 'chk_wmt_1', title: 'Sellado de Cita en Ventana OTIF Retail Link', desc: 'Grapar comprobante de cita Retail Link a carta porte con margen de 60 min.', mandatory: true, risk: 'Multa del 3% por incumplimiento OTIF' },
                { id: 'chk_wmt_2', title: 'Leyenda Anti-Extemporánea de Pronto Pago en Remisión', desc: 'Establecer expresamente que el 2% caduca el día 10 natural tras emisión.', mandatory: true, risk: 'Deducción indebida DED-EARLY-PAY ($3,500.00 USD)' },
                { id: 'chk_wmt_3', title: 'Auditoría de Tarimas Azules CHEP Grado A', desc: 'Verificar tarimas sin tablones rotos ni clavos salientes.', mandatory: true, risk: 'Rechazo en muelle de descarga' }
              ]
            },
            CISCO: {
              name: 'Cisco Systems Global Supply (CUST-RETAIL-CSCO)',
              tier: 'MEDIO',
              tierClass: 'text-amber-300 bg-amber-950/30 border-amber-700/40',
              winRate: 95.0,
              recoveryRatio: 93.2,
              volume: 185000.00,
              recovered: 172420.00,
              incoterm: 'CIP',
              leadTimeDays: 12,
              cedisAlert: 'Retenciones por prorrateo de descuentos de volumen y kits de licencias SmartNet.',
              patterns: [
                {
                  id: 'PAT-CSC-01',
                  title: 'Deducción de Margen por Desglose de Bundles',
                  freq: 45.0,
                  sev: 'MEDIA',
                  mech: 'Intento de re-facturación individual de equipos para aplicar descuentos escalonados.',
                  counter: 'Exhibir anexo de cotización cerrada con SKU único de bundle indivisible.'
                }
              ],
              checklist: [
                { id: 'chk_csc_1', title: 'Validación de SKU Bundle en PO vs Factura', desc: 'Garantizar coincidencia exacta del identificador de kit en orden y factura.', mandatory: true, risk: 'Deducciones por desglose de componentes' },
                { id: 'chk_csc_2', title: 'Anexo de Activación de Licencias SmartNet', desc: 'Vincular certificado digital de soporte al comprobante de entrega.', mandatory: false, risk: 'Retenciones de garantía técnica' }
              ]
            },
            HOMEDEPOT: {
              name: 'The Home Depot Supply Chain (CUST-RETAIL-HD)',
              tier: 'MEDIO',
              tierClass: 'text-sky-400 bg-sky-950/40 border-sky-800/40',
              winRate: 91.5,
              recoveryRatio: 87.0,
              volume: 138000.00,
              recovered: 120060.00,
              incoterm: 'FOB',
              leadTimeDays: 15,
              cedisAlert: 'Rechazos cosméticos en cajas de cartón por rozaduras menores durante el transporte.',
              patterns: [
                {
                  id: 'PAT-HD-01',
                  title: 'Rechazo por Daño Cosmético de Empaque',
                  freq: 60.0,
                  sev: 'MEDIA',
                  mech: 'Deducción íntegra de producto por deformación de caja de cartón exterior con contenido íntegro.',
                  counter: 'Protocolo de inspección conjunta: daño de caja no autoriza merma de producto apto.'
                }
              ],
              checklist: [
                { id: 'chk_hd_1', title: 'Instalación de Esquineros de Cartón Rígido', desc: 'Reforzar las 4 aristas de cada tarima antes de flejar.', mandatory: true, risk: 'Daños cosméticos por tensión de flejes' },
                { id: 'chk_hd_2', title: 'Certificación Cero Overhang (Sin Salientes)', desc: 'Verificar que ninguna caja sobresalga de la base de 48x40 pulgadas.', mandatory: true, risk: 'Rechazo en muelle cross-dock' }
              ]
            },
            MEGA_RETAILER: {
              name: 'Mega Retailer Global Corp (CUST-RETAIL-MEGA)',
              tier: 'ALTO',
              tierClass: 'text-rose-400 bg-rose-950/40 border-rose-800/40',
              winRate: 94.8,
              recoveryRatio: 91.0,
              volume: 520000.00,
              recovered: 473200.00,
              incoterm: 'FOB',
              leadTimeDays: 25,
              cedisAlert: 'Retenciones precautorias globales en facturas con más de 30 SKUs simultáneos.',
              patterns: [
                {
                  id: 'PAT-MEG-01',
                  title: 'Retención Cautelar por Auditoría Masiva Multi-SKU',
                  freq: 91.0,
                  sev: 'CRITICA',
                  mech: 'Bloqueo del 15% del valor total de órdenes multi-línea durante 45 días sin notificar discrepancias.',
                  counter: 'Generar matriz digital 3-Way Match con firma de transportista por línea de SKU.'
                }
              ],
              checklist: [
                { id: 'chk_meg_1', title: 'Packing List Digital Indexado por Tarima', desc: 'Generar archivo detallando qué SKUs específicos van en cada tarima física.', mandatory: true, risk: 'Retención cautelar de auditoría masiva' },
                { id: 'chk_meg_2', title: 'Validación Pre-Despacho SKU por SKU con RFID', desc: 'Escanear 100% de bultos para certificar conteo matemático.', mandatory: true, risk: 'Discrepancias de conteo en CEDIS' }
              ]
            }
          };

          const activeRet = RETAILER_METRICS[selectedRetailer] || RETAILER_METRICS.WALMART;

          return (
            <div className="space-y-4">
              {/* Barra de selección de Retailer */}
              <div className="flex flex-wrap items-center gap-1.5 border-b border-[#1b1c24] pb-2">
                {Object.keys(RETAILER_METRICS).map((rKey) => (
                  <button
                    key={rKey}
                    onClick={() => setSelectedRetailer(rKey)}
                    className={`btn-tactile px-3 py-1.5 rounded text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
                      selectedRetailer === rKey
                        ? 'bg-[#1b1c26] text-[#eed98d] border border-[#d4af37]/60 font-bold shadow-tactile'
                        : 'text-zinc-400 hover:text-white hover:bg-[#121319]'
                    }`}
                  >
                    <span>{rKey === 'MEGA_RETAILER' ? 'MEGA RETAILER' : rKey}</span>
                  </button>
                ))}
              </div>

              {/* Banner de KPIs del Retailer */}
              <div className="bg-[#121317] border border-[#23242c] rounded-xl p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                      <ShieldAlert className="w-4 h-4 text-[#d4af37]" />
                      {activeRet.name}
                    </h3>
                    <p className="text-xs text-zinc-400 mt-0.5 font-sans">
                      Perfil longitudinal minado sobre casos reales de auditoría B2B.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase">Clasificación de Riesgo:</span>
                    <span className={`text-xs font-mono font-bold px-2.5 py-1 rounded border ${activeRet.tierClass}`}>
                      {activeRet.tier}
                    </span>
                  </div>
                </div>

                {activeRet.cedisAlert && (
                  <div className="p-3 rounded-lg bg-[#1f1911] border border-amber-800/40 text-xs text-amber-200 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold font-mono text-[10px] uppercase block text-amber-300">Alerta de Fuga en CEDIS:</span>
                      {activeRet.cedisAlert}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                  <div className="bg-[#0e0f13] border border-[#1b1c24] rounded-lg p-3">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase block">Win Rate Histórico</span>
                    <div className="text-lg font-bold font-mono text-emerald-400 tabular-nums">{activeRet.winRate}%</div>
                  </div>
                  <div className="bg-[#0e0f13] border border-[#1b1c24] rounded-lg p-3">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase block">Tasa de Recuperación</span>
                    <div className="text-lg font-bold font-mono text-[#eed98d] tabular-nums">{activeRet.recoveryRatio}%</div>
                  </div>
                  <div className="bg-[#0e0f13] border border-[#1b1c24] rounded-lg p-3">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase block">Volumen Auditado</span>
                    <div className="text-lg font-bold font-mono text-white tabular-nums">${formatCurrency(activeRet.volume)}</div>
                  </div>
                  <div className="bg-[#0e0f13] border border-[#1b1c24] rounded-lg p-3">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase block">Incoterm Blindado</span>
                    <div className="text-lg font-bold font-mono text-sky-400">{activeRet.incoterm} 2020</div>
                  </div>
                </div>
              </div>

              {/* Patrones Sistemáticos Abusivos */}
              <div className="bg-[#121317] border border-[#23242c] rounded-xl p-5 space-y-3">
                <div className="flex items-center space-x-2 text-zinc-300">
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                  <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                    Patrones Sistemáticos & Deducciones Abusivas Detectadas
                  </h4>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-1">
                  {activeRet.patterns.map((pat) => (
                    <div key={pat.id} className="p-4 rounded-lg bg-[#0e0f13] border border-[#1e2029] space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-white font-mono">{pat.title}</span>
                        <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-rose-950/40 text-rose-300 border border-rose-800/40">
                          {pat.freq}% Frecuencia
                        </span>
                      </div>
                      <p className="text-xs text-zinc-400 leading-relaxed font-sans">{pat.mech}</p>
                      <div className="text-[11px] text-emerald-400 pt-2 border-t border-[#181a22] font-sans">
                        🛡️ <span className="font-semibold font-mono">Contra-Estrategia:</span> {pat.counter}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Checklist Preventivo Pre-Despacho Interactivo */}
              <div className="bg-[#121317] border border-[#23242c] rounded-xl p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-zinc-300">
                    <ListChecks className="w-4 h-4 text-[#d4af37]" />
                    <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                      Checklist Operacional Pre-Despacho (Escudo Preventivo de Fugas)
                    </h4>
                  </div>
                  <span className="text-[10px] font-mono text-zinc-400">
                    {Object.values(checklistCompleted).filter(Boolean).length} de {activeRet.checklist.length} verificados
                  </span>
                </div>

                <div className="space-y-2.5 pt-1">
                  {activeRet.checklist.map((item) => {
                    const isDone = checklistCompleted[item.id] || false;
                    return (
                      <div
                        key={item.id}
                        onClick={() => toggleChecklistItem(item.id)}
                        className={`p-3.5 rounded-lg border transition-all cursor-pointer flex items-start gap-3 select-none ${
                          isDone
                            ? 'bg-[#101914] border-emerald-800/50'
                            : 'bg-[#0e0f13] border-[#1e2029] hover:border-[#2b2e3e]'
                        }`}
                      >
                        <button className="mt-0.5 text-zinc-400 flex-shrink-0">
                          {isDone ? (
                            <CheckSquare className="w-4 h-4 text-emerald-400" />
                          ) : (
                            <Square className="w-4 h-4 text-zinc-600" />
                          )}
                        </button>
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center justify-between">
                            <span className={`text-xs font-semibold font-mono ${isDone ? 'text-emerald-300 line-through' : 'text-white'}`}>
                              {item.title}
                            </span>
                            <span className={`text-[9px] font-mono px-2 py-0.5 rounded border ${
                              item.mandatory
                                ? 'bg-rose-950/40 text-rose-300 border-rose-800/40'
                                : 'bg-amber-950/40 text-amber-300 border-amber-800/40'
                            }`}>
                              {item.mandatory ? 'MANDATORIO' : 'RECOMENDADO'}
                            </span>
                          </div>
                          <p className="text-xs text-zinc-400 font-sans leading-relaxed">{item.desc}</p>
                          <div className="text-[10px] font-mono text-[#eed98d] pt-1">
                            🎯 Mitiga riesgo de: <span className="text-zinc-300">{item.risk}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          );
        })()}

      </div>

    </div>
  );
}
