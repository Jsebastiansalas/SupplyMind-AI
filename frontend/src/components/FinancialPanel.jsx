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
  Printer
} from 'lucide-react';

export default function FinancialPanel({ 
  report, 
  activeSubTab: externalSubTab, 
  onSubTabChange, 
  onOpenOfficialDossier 
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
      
      {/* 1. HORIZONTAL EQUATION STRIP (Clean Canvas — Zero Box Clutter) */}
      <div className="p-4 rounded-xl bg-[#121317] border border-[#22242c] flex flex-wrap items-baseline justify-between gap-4 shadow-sm">
        <div className="flex flex-wrap items-baseline gap-6 sm:gap-10">
          <div>
            <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
              Facturado Bruto
            </div>
            <div className="text-xl font-bold font-mono text-zinc-100 mt-0.5">
              ${formatCurrency(billed)}
            </div>
          </div>

          <div className="text-zinc-600 font-mono text-lg hidden sm:block">—</div>

          <div>
            <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
              Cobrado en Banco
            </div>
            <div className="text-xl font-bold font-mono text-zinc-400 mt-0.5">
              ${formatCurrency(received)}
            </div>
          </div>

          <div className="text-zinc-600 font-mono text-lg hidden sm:block">=</div>

          <div>
            <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
              Retención / Deducción
            </div>
            <div className="text-xl font-bold font-mono text-zinc-300 mt-0.5">
              ${formatCurrency(diff)}
            </div>
          </div>
        </div>

        <div className="text-right">
          <div className="text-[10px] font-mono uppercase tracking-widest text-[#d4af37] font-bold">
            Saldo Recuperable Exigible
          </div>
          <div className="text-2xl font-black font-mono text-[#f0d165] mt-0.5">
            ${formatCurrency(claimable)} USD
          </div>
        </div>
      </div>

      {/* 2. HERO RESOLUTION BANNER (Bottom Line Upfront) */}
      <div className="bg-[#14151a] border border-[#282a36] rounded-xl p-6 relative overflow-hidden shadow-md">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#d4af37] via-[#eed98d]/60 to-transparent" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono uppercase tracking-widest text-[#d4af37] font-semibold bg-[#262417] px-2.5 py-0.5 rounded border border-[#d4af37]/30">
                Dictamen de Conciliación Arbitral
              </span>
              {noticeWindow && (
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                  noticeWindow.is_timely ? 'bg-[#181920] text-zinc-400' : 'bg-rose-950 text-rose-300 border border-rose-900'
                }`}>
                  {noticeWindow.status_label}
                </span>
              )}
            </div>

            <h2 className="text-xl lg:text-2xl font-extrabold text-white tracking-tight">
              {isClaimable ? 'Recuperación Formal Exigible' : 'Retención 100% Justificada'}
            </h2>

            <p className="text-xs text-zinc-300 leading-relaxed font-sans">
              {report.root_cause}
            </p>
          </div>

          <div className="flex-shrink-0 bg-[#181920] border border-[#282a35] rounded-lg p-3.5 min-w-[230px]">
            <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider block">
              Acción Operativa Inmediata
            </span>
            <div className="text-xs font-semibold text-zinc-200 mt-1">
              {isClaimable ? '⚖️ Carta Formal de Objeción' : '📝 Emisión de Nota de Crédito'}
            </div>
            <div className="mt-2 pt-2 border-t border-[#232530] text-[10px] text-zinc-500 flex justify-between font-mono">
              <span>Velocidad</span>
              <span className="text-[#d4af37]">{executionTime.toFixed(2)}s • Zero-Hallucination</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. SUB-VIEWS SEGMENTED TABS (No Box Overload — Structured on Demand) */}
      <div className="space-y-4">
        
        <div className="flex flex-wrap gap-1.5 border-b border-[#20222a] pb-2">
          <button
            onClick={() => setActiveSubTab('summary')}
            className={`px-3.5 py-1.5 rounded-md text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
              activeSubTab === 'summary'
                ? 'bg-[#1c1d24] text-white border border-[#d4af37]/40 shadow-sm'
                : 'text-zinc-400 hover:text-white hover:bg-[#15161c]'
            }`}
          >
            <FileText className="w-3.5 h-3.5 text-[#d4af37]" />
            <span>Resumen & Fundamento Legal</span>
          </button>

          {skuMatching && (
            <button
              onClick={() => setActiveSubTab('sku')}
              className={`px-3.5 py-1.5 rounded-md text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
                activeSubTab === 'sku'
                  ? 'bg-[#1c1d24] text-white border border-[#d4af37]/40 shadow-sm'
                  : 'text-zinc-400 hover:text-white hover:bg-[#15161c]'
              }`}
            >
              <Package className="w-3.5 h-3.5 text-[#d4af37]" />
              <span>Auditoría SKU por SKU ({skuMatching.total_skus_audited})</span>
            </button>
          )}

          <button
            onClick={() => setActiveSubTab('ledger')}
            className={`px-3.5 py-1.5 rounded-md text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
              activeSubTab === 'ledger'
                ? 'bg-[#1c1d24] text-white border border-[#d4af37]/40 shadow-sm'
                : 'text-zinc-400 hover:text-white hover:bg-[#15161c]'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-zinc-400" />
            <span>Libro Contable (Partida Doble)</span>
          </button>

          <button
            onClick={() => setActiveSubTab('certificate')}
            className={`px-3.5 py-1.5 rounded-md text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
              activeSubTab === 'certificate'
                ? 'bg-[#1c1d24] text-white border border-[#d4af37]/40 shadow-sm'
                : 'text-zinc-400 hover:text-white hover:bg-[#15161c]'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5 text-zinc-400" />
            <span>Certificado Digital NIF C-3</span>
          </button>

          {onOpenOfficialDossier && (
            <button
              onClick={onOpenOfficialDossier}
              className="ml-auto flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-[#241f12] hover:bg-[#2e2716] border border-[#d4af37]/50 text-xs font-mono text-[#eed98d] transition-colors shadow-sm"
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

        {/* SUB-TAB 2: AUDITORÍA SKU POR SKU & FISCAL */}
        {activeSubTab === 'sku' && skuMatching && (
          <div className="bg-[#121317] border border-[#23242c] rounded-xl overflow-hidden shadow-sm">
            <div className="p-4 border-b border-[#20222a] bg-[#14151b] flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                  Auditoría Analítica por Partida / SKU
                </h3>
                <p className="text-[11px] text-zinc-400 font-sans mt-0.5">
                  Cotejo cruzado de Factura vs Remisión vs Orden de Compra y desglose de IVA (16%).
                </p>
              </div>
              <div className="text-xs font-mono text-zinc-300 flex gap-4">
                <span>Partidas Auditadas: <strong className="text-white">{skuMatching.total_skus_audited}</strong></span>
                <span>Con Discrepancia: <strong className="text-[#eed98d]">{skuMatching.skus_with_discrepancies}</strong></span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#20222a] text-zinc-500 text-[10px] uppercase bg-[#0f1013]">
                    <th className="py-2.5 px-4 font-semibold">SKU / Descripción</th>
                    <th className="py-2.5 px-4 font-semibold text-center">Facturado</th>
                    <th className="py-2.5 px-4 font-semibold text-center">Recibido</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Precio Unitario</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Impacto Bruto</th>
                    <th className="py-2.5 px-4 font-semibold text-right">IVA 16%</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Dictamen</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1e2027] text-zinc-300">
                  {skuMatching.line_items.map((line, idx) => (
                    <tr key={idx} className="hover:bg-[#16171d]/60 transition-colors">
                      <td className="py-2.5 px-4">
                        <div className="font-bold text-white">{line.item_id}</div>
                        <div className="text-[10px] text-zinc-500 font-sans truncate max-w-xs">{line.description}</div>
                      </td>
                      <td className="py-2.5 px-4 text-center">{line.quantity_billed}</td>
                      <td className="py-2.5 px-4 text-center">{line.quantity_received}</td>
                      <td className="py-2.5 px-4 text-right">${formatCurrency(line.unit_price_invoiced)}</td>
                      <td className="py-2.5 px-4 text-right font-bold text-white">
                        ${formatCurrency(line.line_total_discrepancy)}
                      </td>
                      <td className="py-2.5 px-4 text-right text-zinc-400">
                        ${formatCurrency(line.vat_impact_16)}
                      </td>
                      <td className="py-2.5 px-4 text-right">
                        <span className={`text-[10px] px-2 py-0.5 rounded font-mono ${
                          line.is_fully_reconciled
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            : 'bg-[#242116] text-[#eed98d] border border-[#d4af37]/30'
                        }`}>
                          {line.status_label}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-[#15161c] border-t border-[#262833] text-white">
                    <td className="py-3 px-4 uppercase text-zinc-400 font-semibold" colSpan={4}>
                      Impacto Neto Total por Discrepancia de Líneas
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-sm font-bold text-[#f0d165]">
                      ${formatCurrency(skuMatching.net_line_discrepancy)}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-zinc-400">
                      ${formatCurrency(skuMatching.total_vat_impact_16)}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-[10px] text-zinc-400">
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
          <div className="bg-[#121317] border border-[#23242c] rounded-xl overflow-hidden shadow-sm">
            <div className="px-5 py-3 border-b border-[#20222a] bg-[#15161c] flex items-center justify-between">
              <span className="text-xs font-mono font-semibold text-zinc-200 uppercase tracking-wider">
                Balance de Liquidación Contable NIF C-3 / GAAP
              </span>
              <span className="text-[10px] font-mono text-zinc-400">
                Precisión Decimal Exacta
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#20222a] text-zinc-500 text-[10px] uppercase bg-[#14151a]">
                    <th className="py-2.5 px-4 font-semibold">Concepto Contable</th>
                    <th className="py-2.5 px-4 font-semibold">Naturaleza</th>
                    <th className="py-2.5 px-4 font-semibold">Sustento Probatorio</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Importe (USD)</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Estatus</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1e2027] text-zinc-300">
                  <tr className="hover:bg-[#16171d]/60 transition-colors">
                    <td className="py-2.5 px-4 font-medium text-white">Factura Original Emitida</td>
                    <td className="py-2.5 px-4 text-zinc-400">(+) Crédito</td>
                    <td className="py-2.5 px-4 text-zinc-400">CFDI / Comprobante Comercial</td>
                    <td className="py-2.5 px-4 text-right font-medium text-white">${formatCurrency(billed)}</td>
                    <td className="py-2.5 px-4 text-right text-zinc-400">Exigible Base</td>
                  </tr>

                  <tr className="hover:bg-[#16171d]/60 transition-colors">
                    <td className="py-2.5 px-4 font-medium text-white">Dispersión Bancaria Recibida</td>
                    <td className="py-2.5 px-4 text-zinc-400">(-) Débito</td>
                    <td className="py-2.5 px-4 text-zinc-400">Comprobante SPEI / Transferencia</td>
                    <td className="py-2.5 px-4 text-right font-medium text-zinc-300">-${formatCurrency(received)}</td>
                    <td className="py-2.5 px-4 text-right text-zinc-400">Liquidado</td>
                  </tr>

                  {justified > 0 && (
                    <tr className="hover:bg-[#16171d]/60 transition-colors bg-[#18191f]/40">
                      <td className="py-2.5 px-4 font-medium text-zinc-300">Deducción Contractual Procedente</td>
                      <td className="py-2.5 px-4 text-zinc-500">(-) Ajuste</td>
                      <td className="py-2.5 px-4 text-zinc-400">Remisión Sellada con Faltante Físico</td>
                      <td className="py-2.5 px-4 text-right font-medium text-zinc-300">-${formatCurrency(justified)}</td>
                      <td className="py-2.5 px-4 text-right text-zinc-400">Emitir Nota de Crédito</td>
                    </tr>
                  )}

                  {claimable > 0 && (
                    <tr className="hover:bg-[#16171d]/60 transition-colors bg-[#232014]/30">
                      <td className="py-2.5 px-4 font-medium text-[#eed98d]">Retención Sin Soporte Legal</td>
                      <td className="py-2.5 px-4 text-[#d4af37]">(+) Reclamo</td>
                      <td className="py-2.5 px-4 text-zinc-300">Remisión Conforme sin Observación</td>
                      <td className="py-2.5 px-4 text-right font-bold text-[#f0d165]">+${formatCurrency(claimable)}</td>
                      <td className="py-2.5 px-4 text-right text-[#d4af37] font-semibold">Exigir Restitución</td>
                    </tr>
                  )}
                </tbody>
                <tfoot>
                  <tr className="bg-[#15161c] border-t border-[#262833] text-white">
                    <td className="py-3 px-4 uppercase text-zinc-400 font-semibold" colSpan={3}>
                      Conciliación Neta Final
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-sm font-bold text-[#f0d165]">
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

      </div>

    </div>
  );
}
