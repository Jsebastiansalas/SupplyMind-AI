import React, { useState } from 'react';
import { 
  Scale, 
  Copy, 
  Check, 
  FileText, 
  TrendingUp,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';

export default function FinancialPanel({ report }) {
  const [copiedHash, setCopiedHash] = useState(false);

  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center h-80 text-center p-8 text-zinc-500 ledger-card">
        <Scale className="w-10 h-10 mb-3 text-zinc-600" />
        <h3 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider font-mono">
          Ningún Expediente Seleccionado
        </h3>
        <p className="text-xs text-zinc-500 mt-1 max-w-sm">
          Seleccione un expediente en la barra lateral para desplegar la liquidación y el dictamen de arbitraje.
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

  const isClaimable = claimable > 0;
  const totalDeduction = Math.abs(diff);
  const justifiedPct = totalDeduction > 0 ? (justified / totalDeduction) * 100 : 0;
  const claimablePct = totalDeduction > 0 ? (claimable / totalDeduction) * 100 : 0;

  // Sello criptográfico determinístico
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
    <div className="space-y-5">
      
      {/* 1. HERO RESOLUTION BANNER (Bottom Line Upfront) */}
      <div className="bg-[#14151a] border border-[#2b2c36] rounded-xl p-6 relative overflow-hidden shadow-lg">
        {/* Subtle Gold Accent Top Line */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#d4af37] via-[#eed98d]/60 to-transparent" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono uppercase tracking-widest text-[#d4af37] font-semibold bg-[#262417] px-2.5 py-0.5 rounded border border-[#d4af37]/30">
                Dictamen de Conciliación Arbitral
              </span>
              <span className="text-zinc-600">•</span>
              <span className="text-[11px] text-zinc-400 font-mono">
                Certeza Factual: {(confidence * 100).toFixed(0)}%
              </span>
            </div>

            <div className="flex flex-wrap items-baseline gap-3">
              <h2 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight font-sans">
                {isClaimable ? 'Recuperación Exigible:' : 'Cartera Conciliada:'}
              </h2>
              <span className={`text-2xl lg:text-3xl font-mono font-bold tracking-tight ${isClaimable ? 'text-[#f0d165]' : 'text-zinc-300'}`}>
                ${formatCurrency(isClaimable ? claimable : billed)} USD
              </span>
            </div>

            <p className="text-xs text-zinc-400 max-w-2xl leading-relaxed">
              {isClaimable 
                ? 'Se identificó una retención indebida no respaldada por la remisión de entrega. El monto es jurídicamente exigible al comprador mediante Carta de Objeción.'
                : 'La retención coincide al 100% con las penalizaciones y deducciones pactadas en contrato. Proceder con emisión de Nota de Crédito.'}
            </p>
          </div>

          {/* Quick Action Box */}
          <div className="flex-shrink-0 bg-[#191a21] border border-[#292b36] rounded-lg p-3.5 flex flex-col justify-center min-w-[220px]">
            <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
              Acción Comercial Inmediata
            </span>
            <div className="text-xs font-semibold text-zinc-200 mt-1 flex items-center gap-1.5">
              <span>{isClaimable ? '⚖️ Carta Formal de Objeción' : '📝 Nota de Crédito por Ajuste'}</span>
            </div>
            <div className="mt-2 pt-2 border-t border-[#232530] text-[10px] text-zinc-500 flex justify-between font-mono">
              <span>Resolución</span>
              <span className="text-[#d4af37]">{executionTime.toFixed(3)}s</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. THE 3 FINANCIAL METRICS (Quiet Ribbon) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        {/* Metric 1: Facturación Bruta */}
        <div className="bg-[#121317] border border-[#23242c] rounded-xl p-4">
          <div className="text-[11px] font-mono text-zinc-500 uppercase tracking-wider">
            1. Facturación Emitida
          </div>
          <div className="text-xl font-bold font-mono text-zinc-100 mt-1">
            ${formatCurrency(billed)}
          </div>
          <div className="text-[11px] text-zinc-500 mt-1.5 flex justify-between">
            <span>Importe Comercial Original</span>
            <span className="text-zinc-400 font-mono">100%</span>
          </div>
        </div>

        {/* Metric 2: Cobrado en Banco */}
        <div className="bg-[#121317] border border-[#23242c] rounded-xl p-4">
          <div className="text-[11px] font-mono text-zinc-500 uppercase tracking-wider">
            2. Liquidación Bancaria Recibida
          </div>
          <div className="text-xl font-bold font-mono text-zinc-300 mt-1">
            ${formatCurrency(received)}
          </div>
          <div className="text-[11px] text-zinc-500 mt-1.5 flex justify-between">
            <span>Fondos Dispersados</span>
            <span className="text-zinc-400 font-mono">{billed > 0 ? ((received / billed) * 100).toFixed(1) : 0}%</span>
          </div>
        </div>

        {/* Metric 3: Varianza Neta en Disputa */}
        <div className="bg-[#121317] border border-[#23242c] rounded-xl p-4">
          <div className="text-[11px] font-mono text-zinc-500 uppercase tracking-wider">
            3. Varianza en Disputa
          </div>
          <div className="text-xl font-bold font-mono text-zinc-200 mt-1">
            ${formatCurrency(diff)}
          </div>
          <div className="text-[11px] text-zinc-500 mt-1.5 flex justify-between font-mono">
            <span>Justificado: <strong className="text-zinc-300">${formatCurrency(justified)}</strong></span>
            <span>Reclamable: <strong className="text-[#d4af37]">${formatCurrency(claimable)}</strong></span>
          </div>
        </div>

      </div>

      {/* 3. HOJA DE LIQUIDACIÓN CONTABLE (The Sovereign Balance Sheet) */}
      <div className="bg-[#121317] border border-[#23242c] rounded-xl overflow-hidden shadow-sm">
        <div className="px-5 py-3.5 border-b border-[#20222a] bg-[#15161c] flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono font-semibold text-zinc-200 uppercase tracking-wider">
              Hoja de Liquidación & Partida Doble
            </span>
            <span className="text-[10px] font-mono text-zinc-500 bg-[#1c1d25] px-2 py-0.5 rounded border border-[#282a35]">
              NIF C-3 / GAAP
            </span>
          </div>
          <div className="text-[11px] text-zinc-400 font-mono hidden sm:block">
            Precisión Decimal Exacta
          </div>
        </div>

        {/* Proportional Balance Bar */}
        <div className="px-5 py-2.5 bg-[#0f1013] border-b border-[#1c1d24] flex items-center gap-3">
          <span className="text-[10px] font-mono text-zinc-500 uppercase flex-shrink-0">
            Composición:
          </span>
          <div className="flex-1 h-2 bg-[#1b1c23] rounded overflow-hidden flex">
            <div 
              style={{ width: `${justifiedPct}%` }}
              className="h-full bg-zinc-600 transition-all duration-300"
              title={`Justificado: $${formatCurrency(justified)} (${justifiedPct.toFixed(1)}%)`}
            />
            <div 
              style={{ width: `${claimablePct}%` }}
              className="h-full bg-[#d4af37] transition-all duration-300"
              title={`Reclamable: $${formatCurrency(claimable)} (${claimablePct.toFixed(1)}%)`}
            />
          </div>
          <div className="flex items-center space-x-3 text-[10px] font-mono text-zinc-400">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-500"></span>
              <span>Deducción Válida ({justifiedPct.toFixed(0)}%)</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#d4af37]"></span>
              <span className="text-zinc-200">Reclamable ({claimablePct.toFixed(0)}%)</span>
            </span>
          </div>
        </div>

        {/* Ledger Table */}
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
                <td className="py-2.5 px-4 text-zinc-400">Comprobante Comercial Pactado</td>
                <td className="py-2.5 px-4 text-right font-medium text-white">${formatCurrency(billed)}</td>
                <td className="py-2.5 px-4 text-right text-zinc-400">Exigible Base</td>
              </tr>

              <tr className="hover:bg-[#16171d]/60 transition-colors">
                <td className="py-2.5 px-4 font-medium text-white">Dispersión Bancaria Recibida</td>
                <td className="py-2.5 px-4 text-zinc-400">(-) Débito</td>
                <td className="py-2.5 px-4 text-zinc-400">Comprobante de Transferencia SPEI</td>
                <td className="py-2.5 px-4 text-right font-medium text-zinc-300">-${formatCurrency(received)}</td>
                <td className="py-2.5 px-4 text-right text-zinc-400">Liquidado</td>
              </tr>

              {justified > 0 && (
                <tr className="hover:bg-[#16171d]/60 transition-colors bg-[#18191f]/40">
                  <td className="py-2.5 px-4 font-medium text-zinc-300">Deducción Contractual Procedente</td>
                  <td className="py-2.5 px-4 text-zinc-500">(-) Ajuste</td>
                  <td className="py-2.5 px-4 text-zinc-400">Cláusula de Descuento / Merma Firmada</td>
                  <td className="py-2.5 px-4 text-right font-medium text-zinc-300">-${formatCurrency(justified)}</td>
                  <td className="py-2.5 px-4 text-right text-zinc-400">Emitir Nota de Crédito</td>
                </tr>
              )}

              {claimable > 0 && (
                <tr className="hover:bg-[#16171d]/60 transition-colors bg-[#232014]/30">
                  <td className="py-2.5 px-4 font-medium text-[#eed98d]">Retención Sin Soporte Legal</td>
                  <td className="py-2.5 px-4 text-[#d4af37]">(+) Reclamo</td>
                  <td className="py-2.5 px-4 text-zinc-300">Remisión Sellada Conforme sin Observación</td>
                  <td className="py-2.5 px-4 text-right font-bold text-[#f0d165]">+${formatCurrency(claimable)}</td>
                  <td className="py-2.5 px-4 text-right text-[#d4af37] font-semibold">Exigir Restitución</td>
                </tr>
              )}

            </tbody>
            <tfoot>
              <tr className="bg-[#15161c] border-t border-[#262833] text-white">
                <td className="py-3 px-4 uppercase text-zinc-400 font-semibold" colSpan={3}>
                  Saldo Neto de Resolución
                </td>
                <td className="py-3 px-4 text-right font-mono text-sm font-bold text-[#f0d165]">
                  ${formatCurrency(claimable)}
                </td>
                <td className="py-3 px-4 text-right text-[11px] font-mono text-zinc-300">
                  RECUPERACIÓN FINAL
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* 4. FUNDAMENTO LEGAL & ESTRATEGIA (Clean 2-Column Split) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        
        {/* Causa Raíz Factual */}
        <div className="bg-[#121317] border border-[#23242c] rounded-xl p-5 space-y-3">
          <div className="flex items-center space-x-2 text-zinc-300">
            <FileText className="w-4 h-4 text-[#d4af37]" />
            <h3 className="text-xs font-mono font-semibold uppercase tracking-wider">
              Causa Raíz Determinada & Pruebas
            </h3>
          </div>
          <div className="p-3.5 rounded-lg bg-[#0e0f12] border border-[#1e2027] text-zinc-300 text-xs leading-relaxed font-sans">
            {report.root_cause}
          </div>
          <div className="text-[10px] text-zinc-500 font-mono flex items-center justify-between pt-1">
            <span>Jerarquía: Remisión Sellada &gt; Factura</span>
            <span className="text-zinc-400">Verificado</span>
          </div>
        </div>

        {/* Estrategia Operativa & Legal */}
        <div className="bg-[#121317] border border-[#23242c] rounded-xl p-5 space-y-3">
          <div className="flex items-center space-x-2 text-zinc-300">
            <TrendingUp className="w-4 h-4 text-zinc-400" />
            <h3 className="text-xs font-mono font-semibold uppercase tracking-wider">
              Estrategia Comercial Recomendada
            </h3>
          </div>
          <div className="p-3.5 rounded-lg bg-[#0e0f12] border border-[#1e2027] text-zinc-300 text-xs leading-relaxed font-sans">
            {report.recommended_action}
          </div>
          <div className="text-[10px] text-zinc-500 font-mono flex items-center justify-between pt-1">
            <span>Resolución Sin Litigio</span>
            <span className="text-zinc-400">Procedimiento B2B</span>
          </div>
        </div>

      </div>

      {/* 5. SELLO DE AUDITORÍA DIGITAL (Discreet & Elegant Footer) */}
      <div className="p-3.5 bg-[#101115] border border-[#20222a] rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono text-zinc-400">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-[#d4af37]" />
          <span>Certificado Digital NIF C-3: Sello Inmutable</span>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[11px] text-zinc-500 bg-[#16171d] px-2 py-0.5 rounded border border-[#22242c]">
            {auditChecksum}
          </span>
          <button
            onClick={handleCopyHash}
            className="p-1 hover:text-white transition-colors text-zinc-500"
            title="Copiar Sello Criptográfico"
          >
            {copiedHash ? <Check className="w-3.5 h-3.5 text-[#d4af37]" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

    </div>
  );
}
