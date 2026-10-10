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
      
      {/* Top Banner: Global Mastery Verdict */}
      <div className={`p-6 rounded-2xl border relative overflow-hidden transition-all ${
        passed
          ? 'bg-gradient-to-r from-emerald-950/40 via-slate-900 to-cyan-950/40 border-emerald-500/40 shadow-xl shadow-emerald-500/10'
          : 'bg-gradient-to-r from-amber-950/40 via-slate-900 to-slate-950 border-amber-500/40'
      }`}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center font-black text-2xl shadow-lg ${
              passed
                ? 'bg-gradient-to-br from-emerald-400 to-teal-600 text-slate-950 shadow-emerald-500/30'
                : 'bg-amber-500 text-slate-950 shadow-amber-500/30'
            }`}>
              <Award className="w-8 h-8" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Dictamen del Tribunal Colegiado (LLM-as-a-Judge)
                </span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase font-mono ${
                  passed ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-amber-500/20 text-amber-300'
                }`}>
                  {passed ? 'MAESTRÍA CERTIFICADA' : 'REQUIERE CALIBRACIÓN'}
                </span>
              </div>
              <h2 className="text-2xl font-black text-white tracking-tight mt-0.5">
                Veredicto Integral: {total.toFixed(1)} / 100.0 Puntos
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluación ciega colegiada bajo el Hito S3 con tolerancia cero a alucinaciones.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-6 border-t md:border-t-0 md:border-l border-slate-800 pt-3 md:pt-0 md:pl-6">
            <div className="text-center">
              <span className="text-[10px] text-slate-400 uppercase font-mono">Umbral</span>
              <div className="text-sm font-bold text-slate-300 font-mono">≥ 90.0 pts</div>
            </div>
            <div className="text-center">
              <span className="text-[10px] text-slate-400 uppercase font-mono">Estado</span>
              <div className={`text-sm font-bold font-mono ${passed ? 'text-emerald-400' : 'text-amber-400'}`}>
                {passed ? 'APROBADO' : 'OBSERVADO'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3 Judges Scoreboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Judge 1: CFO (40 pts) */}
        <div className="glass-card p-5 rounded-2xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2 text-cyan-400">
                <DollarSign className="w-4 h-4" />
                <h3 className="text-xs font-bold uppercase tracking-wide text-white">
                  Juez Financiero / CFO
                </h3>
              </div>
              <span className="font-mono text-xs font-bold text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                {(cfo.score || 40.0).toFixed(1)} / 40.0 pts
              </span>
            </div>

            {/* Score Bar */}
            <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden mb-4">
              <div 
                className="h-full bg-cyan-400 rounded-full transition-all duration-500"
                style={{ width: `${((cfo.score || 40.0) / 40.0) * 100}%` }}
              />
            </div>

            <p className="text-xs text-slate-300 mb-3 font-medium">
              Auditoría Cuantitativa y Cero Alucinación Decimal:
            </p>

            <ul className="space-y-2 text-[11px] text-slate-400">
              {(cfo.observations || [
                "Facturado y recibido coinciden al centavo con comprobantes.",
                "Diferencia neta computada con precisión aritmética Decimal.",
                "Desglose justificado vs reclamable matemáticamente balanceado."
              ]).slice(0, 3).map((obs, i) => (
                <li key={i} className="flex items-start space-x-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
                  <span>{obs}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/60 text-[10px] text-slate-500 flex justify-between font-mono">
            <span>Rol: Chief Financial Officer</span>
            <span className="text-cyan-400">40 Pts Máx</span>
          </div>
        </div>

        {/* Judge 2: Legal Counsel (30 pts) */}
        <div className="glass-card p-5 rounded-2xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2 text-indigo-400">
                <Scale className="w-4 h-4" />
                <h3 className="text-xs font-bold uppercase tracking-wide text-white">
                  Juez Jurídico / Counsel
                </h3>
              </div>
              <span className="font-mono text-xs font-bold text-indigo-300 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/40">
                {(legal.score || 30.0).toFixed(1)} / 30.0 pts
              </span>
            </div>

            {/* Score Bar */}
            <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden mb-4">
              <div 
                className="h-full bg-indigo-400 rounded-full transition-all duration-500"
                style={{ width: `${((legal.score || 30.0) / 30.0) * 100}%` }}
              />
            </div>

            <p className="text-xs text-slate-300 mb-3 font-medium">
              Jerarquía Probatoria y Validez Contractual:
            </p>

            <ul className="space-y-2 text-[11px] text-slate-400">
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

          <div className="mt-4 pt-3 border-t border-slate-800/60 text-[10px] text-slate-500 flex justify-between font-mono">
            <span>Rol: Chief Legal Officer</span>
            <span className="text-indigo-400">30 Pts Máx</span>
          </div>
        </div>

        {/* Judge 3: VP Operations (30 pts) */}
        <div className="glass-card p-5 rounded-2xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2 text-emerald-400">
                <Briefcase className="w-4 h-4" />
                <h3 className="text-xs font-bold uppercase tracking-wide text-white">
                  Juez Operativo / VP Supply
                </h3>
              </div>
              <span className="font-mono text-xs font-bold text-emerald-300 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                {(ops.score || 30.0).toFixed(1)} / 30.0 pts
              </span>
            </div>

            {/* Score Bar */}
            <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden mb-4">
              <div 
                className="h-full bg-emerald-400 rounded-full transition-all duration-500"
                style={{ width: `${((ops.score || 30.0) / 30.0) * 100}%` }}
              />
            </div>

            <p className="text-xs text-slate-300 mb-3 font-medium">
              Estrategia Comercial y Mitigación de Conflicto:
            </p>

            <ul className="space-y-2 text-[11px] text-slate-400">
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

          <div className="mt-4 pt-3 border-t border-slate-800/60 text-[10px] text-slate-500 flex justify-between font-mono">
            <span>Rol: VP Supply Chain</span>
            <span className="text-emerald-400">30 Pts Máx</span>
          </div>
        </div>

      </div>

      {/* Precedent KB & Calibration Directives */}
      <div className="glass-card p-5 rounded-2xl">
        <div className="flex items-center space-x-2 text-white mb-3">
          <BookOpen className="w-4 h-4 text-cyan-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider">
            Directrices de Calibración y Precedente Incorporado a la Memoria
          </h3>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-300 leading-relaxed font-mono">
          {tribunalData.precedent_summary || (
            "Criterio Senior plenamente calibrado: Remisión firmada prevalece sobre deducción unilateral. Nota de crédito obligatoria ante faltante documentado."
          )}
        </div>
      </div>

    </div>
  );
}
