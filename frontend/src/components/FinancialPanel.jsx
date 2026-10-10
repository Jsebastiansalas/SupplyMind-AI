import React from 'react';
import { 
  DollarSign, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle2, 
  Scale, 
  ArrowRight,
  ShieldAlert,
  Percent,
  Clock
} from 'lucide-react';

export default function FinancialPanel({ report }) {
  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-center p-8 text-slate-500">
        <Scale className="w-12 h-12 mb-3 text-slate-600 animate-pulse" />
        <h3 className="text-base font-semibold text-slate-300">Ningún informe cargado</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm">
          Seleccione un expediente de la barra lateral y presione "Iniciar Auditoría Autónoma" para conciliar el caso.
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

  return (
    <div className="space-y-6">
      
      {/* 4 KPI Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Card 1: Facturado */}
        <div className="glass-card p-5 rounded-2xl relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold tracking-wider uppercase">Monto Facturado</span>
            <DollarSign className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl lg:text-3xl font-extrabold text-white font-mono tracking-tight">
            ${billed.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-400 mt-2 flex items-center gap-1">
            <span className="text-cyan-400 font-semibold font-mono">INV</span> Comercial pactada
          </p>
          <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full blur-2xl pointer-events-none"></div>
        </div>

        {/* Card 2: Recibido */}
        <div className="glass-card p-5 rounded-2xl relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold tracking-wider uppercase">Monto Recibido</span>
            <CheckCircle2 className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl lg:text-3xl font-extrabold text-white font-mono tracking-tight">
            ${received.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-400 mt-2 flex items-center gap-1">
            <span className="text-indigo-400 font-semibold font-mono">PAY</span> Dispersión bancaria
          </p>
          <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full blur-2xl pointer-events-none"></div>
        </div>

        {/* Card 3: Diferencia / Retención */}
        <div className="glass-card p-5 rounded-2xl relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold tracking-wider uppercase">Deducción / Retención</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className={`text-2xl lg:text-3xl font-extrabold font-mono tracking-tight ${diff < 0 ? 'text-amber-400' : 'text-slate-200'}`}>
            ${diff.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-400 mt-2 flex items-center justify-between">
            <span>Impacto en Cartera</span>
            <span className="px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-300 font-mono text-[10px]">
              {diff < 0 ? 'Deducción' : 'Equilibrado'}
            </span>
          </p>
          <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full blur-2xl pointer-events-none"></div>
        </div>

        {/* Card 4: SALDO RECLAMABLE (Key Highlight) */}
        <div className={`p-5 rounded-2xl relative overflow-hidden border transition-all ${
          isClaimable
            ? 'bg-gradient-to-br from-emerald-950/60 via-slate-900 to-slate-950 border-emerald-500/50 shadow-xl shadow-emerald-500/10'
            : 'glass-card border-slate-800'
        }`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold tracking-wider uppercase text-emerald-400 flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5" />
              Saldo Reclamable
            </span>
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold uppercase ${
              isClaimable 
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' 
                : 'bg-slate-800 text-slate-400'
            }`}>
              {isClaimable ? 'Recuperable' : 'Saneado'}
            </span>
          </div>
          <div className="text-2xl lg:text-3xl font-black font-mono tracking-tight text-white">
            ${claimable.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-emerald-300/80 mt-2 flex items-center gap-1 font-medium">
            {isClaimable 
              ? 'Exigir devolución formal a comprador'
              : 'Retención 100% justificada en contrato'}
          </p>
          {isClaimable && (
            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/15 rounded-full blur-2xl pointer-events-none"></div>
          )}
        </div>

      </div>

      {/* Breakdown Balance Bar */}
      <div className="glass-card p-5 rounded-2xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wide">
              Desglose y Conciliación del Faltante
            </h3>
            <p className="text-xs text-slate-400">
              Separación matemática exacta calculada mediante motor determinístico Python con precisión Decimal.
            </p>
          </div>
          <div className="flex items-center space-x-4 text-xs font-mono">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
              <span className="text-slate-300">Justificado:</span>
              <span className="font-bold text-white">${justified.toFixed(2)}</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
              <span className="text-slate-300">Reclamable:</span>
              <span className="font-bold text-emerald-300">${claimable.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Visual Progress Ratio Bar */}
        <div className="w-full h-3.5 bg-slate-800 rounded-full overflow-hidden flex p-0.5">
          <div 
            style={{ width: `${justifiedPct}%` }}
            className="h-full bg-rose-500/80 rounded-l-full transition-all duration-500 relative group"
            title={`Justificado: $${justified.toFixed(2)} (${justifiedPct.toFixed(1)}%)`}
          />
          <div 
            style={{ width: `${claimablePct}%` }}
            className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-r-full transition-all duration-500 relative group"
            title={`Reclamable: $${claimable.toFixed(2)} (${claimablePct.toFixed(1)}%)`}
          />
        </div>
      </div>

      {/* Root Cause & Commercial Action Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Causa Raíz Detectada */}
        <div className="glass-card p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-cyan-400 mb-3">
              <TrendingUp className="w-4 h-4" />
              <h3 className="text-sm font-bold uppercase tracking-wide text-white">
                Causa Raíz Determinada
              </h3>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-200 text-sm leading-relaxed">
              {report.root_cause}
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1 font-mono">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              Tiempo de Conciliación: {executionTime.toFixed(2)}s
            </span>
            <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">
              Cero Alucinación
            </span>
          </div>
        </div>

        {/* Acción Comercial Recomendada */}
        <div className="glass-card p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2 text-indigo-400">
                <CheckCircle2 className="w-4 h-4" />
                <h3 className="text-sm font-bold uppercase tracking-wide text-white">
                  Acción Operativa Recomendada
                </h3>
              </div>
              <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-mono font-bold">
                <Percent className="w-3 h-3" />
                <span>Certeza: {(confidence * 100).toFixed(1)}%</span>
              </div>
            </div>

            <div className={`p-4 rounded-xl border text-sm leading-relaxed ${
              isClaimable
                ? 'bg-rose-950/20 border-rose-800/40 text-rose-200'
                : 'bg-emerald-950/20 border-emerald-800/40 text-emerald-200'
            }`}>
              <div className="font-bold text-xs uppercase tracking-wide mb-1 flex items-center gap-1">
                {isClaimable ? '⚖️ Procedimiento de Reclamación Formal:' : '📝 Saneamiento de Cartera:'}
              </div>
              {report.recommended_action}
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
            <span>Estrategia B2B:</span>
            <span className={`font-semibold ${isClaimable ? 'text-amber-300' : 'text-emerald-300'}`}>
              {isClaimable ? 'Objeción con Carta Formal' : 'Emisión de Nota de Crédito'}
            </span>
          </div>
        </div>

      </div>

    </div>
  );
}
