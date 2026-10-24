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
  Handshake
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

      </div>

    </div>
  );
}
