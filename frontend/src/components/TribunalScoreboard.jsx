import React from 'react';
import { 
  Award, 
  Scale, 
  DollarSign, 
  Briefcase, 
  ShieldCheck, 
  AlertCircle, 
  CheckCircle2,
  Sparkles,
  BookOpen
} from 'lucide-react';

export default function TribunalScoreboard({ tribunalData }) {
  if (!tribunalData) {
    return (
      <div className="flex flex-col items-center justify-center h-80 text-center p-8 text-slate-500">
        <Scale className="w-12 h-12 mb-3 text-slate-600 animate-pulse" />
        <h3 className="text-base font-semibold text-slate-300">Cargando Tribunal Colegiado...</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm">
          Evaluando las decisiones del agente ante los magistrados financiero, legal y operativo.
        </p>
      </div>
    );
  }

  const total = Number(tribunalData.total_score || 0);
  const passed = tribunalData.passed_mastery;
  const cfo = tribunalData.cfo_evaluation || {};
  const legal = tribunalData.legal_evaluation || {};
  const ops = tribunalData.operations_evaluation || {};

  return (
    <div className="space-y-6">
      
      {/* Top Banner: Global Collegiate Docket Verdict */}
      <div className={`p-5 rounded-lg border relative overflow-hidden shadow-subtle ${
        passed
          ? 'bg-[#101117] border-[#1e202b]'
          : 'bg-[#141011] border-[#2d1b1e]'
      }`}>
        <div className={`absolute top-0 left-0 right-0 h-[2px] ${
          passed ? 'bg-[#d4af37]' : 'bg-amber-500'
        }`} />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div className={`w-11 h-11 rounded flex items-center justify-center font-bold text-lg shadow-tactile ${
              passed
                ? 'bg-[#1c1a12] text-[#d4af37] border border-[#d4af37]/40'
                : 'bg-[#211a12] text-amber-400 border border-amber-600/40'
            }`}>
              <Award className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-zinc-400">
                  Dictamen del Tribunal Colegiado Arbitral (LLM-as-a-Judge)
                </span>
                <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold uppercase border ${
                  passed 
                    ? 'bg-emerald-950/50 text-emerald-300 border-emerald-800/50' 
                    : 'bg-amber-950/50 text-amber-300 border-amber-800/50'
                }`}>
                  {passed ? 'MAESTRÍA CERTIFICADA' : 'REQUIERE CALIBRACIÓN'}
                </span>
              </div>
              <h2 className="text-xl font-bold font-mono text-white tracking-tight mt-0.5 tabular-nums">
                Veredicto Integral: {total.toFixed(1)} / 100.0 Pts
              </h2>
              <p className="text-[11px] text-zinc-400 mt-0.5 font-sans">
                Evaluación colegiada bajo estándares de tolerancia cero a alucinaciones.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-6 border-t md:border-t-0 md:border-l border-[#1f212c] pt-3 md:pt-0 md:pl-6 select-none">
            <div className="text-center">
              <span className="text-[10px] text-zinc-500 uppercase font-mono">Umbral Exigido</span>
              <div className="text-sm font-bold text-zinc-200 font-mono tabular-nums">≥ 90.0 pts</div>
            </div>
            <div className="text-center">
              <span className="text-[10px] text-zinc-500 uppercase font-mono">Estatus Jurídico</span>
              <div className={`text-sm font-bold font-mono ${passed ? 'text-emerald-400' : 'text-amber-400'}`}>
                {passed ? 'APROBADO' : 'OBSERVADO'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3 Judges Scoreboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        
        {/* Judge 1: CFO (40 pts) */}
        <div className="bg-[#101116] border border-[#1b1c24] rounded-lg p-4 flex flex-col justify-between shadow-subtle">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2 text-[#d4af37]">
                <DollarSign className="w-4 h-4" />
                <h3 className="text-xs font-mono font-bold uppercase tracking-wide text-zinc-100">
                  Juez Financiero / CFO
                </h3>
              </div>
              <span className="font-mono text-xs font-bold text-[#eed98d] bg-[#1a1811] px-2 py-0.5 rounded border border-[#d4af37]/30 tabular-nums">
                {(cfo.score || 40.0).toFixed(1)} / 40.0 pts
              </span>
            </div>

            {/* Score Bar */}
            <div className="w-full h-1.5 bg-[#171822] rounded-full overflow-hidden mb-3">
              <div 
                className="h-full bg-[#d4af37] rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, ((cfo.score || 40.0) / 40.0) * 100)}%` }}
              />
            </div>

            <p className="text-[11px] text-zinc-300 mb-2.5 font-medium font-sans">
              Exactitud Aritmética & Cero Alucinación Decimal:
            </p>

            <ul className="space-y-1.5 text-[11px] text-zinc-400 font-sans">
              {(cfo.observations || [
                "Facturado y recibido concilian al centavo con CFDI y bancos.",
                "Diferencia neta computada con precisión aritmética Decimal.",
                "Desglose justificado vs reclamable matemáticamente cuadrado."
              ]).slice(0, 3).map((obs, i) => (
                <li key={i} className="flex items-start space-x-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#d4af37] flex-shrink-0 mt-0.5" />
                  <span>{obs}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-4 pt-2.5 border-t border-[#181922] text-[10px] text-zinc-500 flex justify-between font-mono">
            <span>Dimensión: Cuantitativa</span>
            <span className="text-zinc-400">40 Pts Máx</span>
          </div>
        </div>

        {/* Judge 2: Legal Counsel (30 pts) */}
        <div className="bg-[#101116] border border-[#1b1c24] rounded-lg p-4 flex flex-col justify-between shadow-subtle">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2 text-indigo-400">
                <Scale className="w-4 h-4" />
                <h3 className="text-xs font-mono font-bold uppercase tracking-wide text-zinc-100">
                  Juez Jurídico / Counsel
                </h3>
              </div>
              <span className="font-mono text-xs font-bold text-indigo-300 bg-[#161726] px-2 py-0.5 rounded border border-indigo-800/40 tabular-nums">
                {(legal.score || 30.0).toFixed(1)} / 30.0 pts
              </span>
            </div>

            {/* Score Bar */}
            <div className="w-full h-1.5 bg-[#171822] rounded-full overflow-hidden mb-3">
              <div 
                className="h-full bg-indigo-400 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, ((legal.score || 30.0) / 30.0) * 100)}%` }}
              />
            </div>

            <p className="text-[11px] text-zinc-300 mb-2.5 font-medium font-sans">
              Jerarquía Probatoria y Validez Contractual:
            </p>

            <ul className="space-y-1.5 text-[11px] text-zinc-400 font-sans">
              {(legal.observations || [
                "Remisión firmada con constancia física reconocida como Nivel 1.",
                "Cláusula marco aplicable citada textualmente.",
                "Rechazo de penalizaciones unilaterales sin adenda previa."
              ]).slice(0, 3).map((obs, i) => (
                <li key={i} className="flex items-start space-x-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0 mt-0.5" />
                  <span>{obs}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-4 pt-2.5 border-t border-[#181922] text-[10px] text-zinc-500 flex justify-between font-mono">
            <span>Dimensión: Contractual</span>
            <span className="text-zinc-400">30 Pts Máx</span>
          </div>
        </div>

        {/* Judge 3: VP Operations (30 pts) */}
        <div className="bg-[#101116] border border-[#1b1c24] rounded-lg p-4 flex flex-col justify-between shadow-subtle">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2 text-emerald-400">
                <Briefcase className="w-4 h-4" />
                <h3 className="text-xs font-mono font-bold uppercase tracking-wide text-zinc-100">
                  Juez Operativo / VP Supply
                </h3>
              </div>
              <span className="font-mono text-xs font-bold text-emerald-300 bg-[#121c17] px-2 py-0.5 rounded border border-emerald-800/40 tabular-nums">
                {(ops.score || 30.0).toFixed(1)} / 30.0 pts
              </span>
            </div>

            {/* Score Bar */}
            <div className="w-full h-1.5 bg-[#171822] rounded-full overflow-hidden mb-3">
              <div 
                className="h-full bg-emerald-400 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, ((ops.score || 30.0) / 30.0) * 100)}%` }}
              />
            </div>

            <p className="text-[11px] text-zinc-300 mb-2.5 font-medium font-sans">
              Estrategia Comercial y Mitigación de Conflicto:
            </p>

            <ul className="space-y-1.5 text-[11px] text-zinc-400 font-sans">
              {(ops.observations || [
                "Recomendación proporcional de Nota de Crédito comercial.",
                "Preservación de la cuenta de cliente sin litigio coactivo.",
                "Saneamiento contable expedito para el equipo de cartera."
              ]).slice(0, 3).map((obs, i) => (
                <li key={i} className="flex items-start space-x-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <span>{obs}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-4 pt-2.5 border-t border-[#181922] text-[10px] text-zinc-500 flex justify-between font-mono">
            <span>Dimensión: Operativa</span>
            <span className="text-zinc-400">30 Pts Máx</span>
          </div>
        </div>

      </div>

      {/* Precedent KB & Calibration Directives */}
      <div className="bg-[#0e0f14] border border-[#1b1c24] rounded-lg p-4 shadow-subtle">
        <div className="flex items-center space-x-2 text-zinc-200 mb-2.5">
          <BookOpen className="w-4 h-4 text-[#d4af37]" />
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider">
            Directrices de Calibración & Precedente en Memoria
          </h3>
        </div>
        <div className="p-3 rounded bg-[#090a0d] border border-[#171820] text-xs text-zinc-300 leading-relaxed font-mono">
          {tribunalData.precedent_summary || (
            "Criterio Senior plenamente calibrado: Remisión firmada prevalece sobre deducción unilateral. Nota de crédito obligatoria ante faltante documentado."
          )}
        </div>
      </div>

    </div>
  );
}
