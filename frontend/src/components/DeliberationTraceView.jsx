import React, { useState } from 'react';
import { 
  Brain, 
  Scale, 
  Search, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  HelpCircle, 
  ChevronDown, 
  ChevronUp, 
  Lightbulb, 
  UserCheck, 
  Sparkles,
  Lock,
  ArrowRight
} from 'lucide-react';

export default function DeliberationTraceView({ trace, failureDiagnostics, report, onProfileSelect }) {
  const [expandedStep, setExpandedStep] = useState(null);
  const [showAllSteps, setShowAllSteps] = useState(true);

  if (!trace && !failureDiagnostics) return null;

  const steps = trace?.deliberation_steps || [];
  const autonomyTier = trace?.autonomy_tier || 'AUTONOMOUS';
  const isProviderLoss = trace?.is_provider_loss || false;
  const requiresHuman = trace?.requires_human_in_the_loop || false;
  const severity = trace?.failure_severity || failureDiagnostics?.failure_severity || 'NORMAL_RESOLUTION';

  const toggleStep = (idx) => {
    setExpandedStep(expandedStep === idx ? null : idx);
  };

  const getStepIcon = (iconName, stepNum) => {
    switch (iconName) {
      case 'Search': return <Search className="w-4 h-4 text-cyan-400" />;
      case 'Scale': return <Scale className="w-4 h-4 text-indigo-400" />;
      case 'Brain': return <Brain className="w-4 h-4 text-amber-400" />;
      case 'ShieldAlert': return <ShieldAlert className="w-4 h-4 text-rose-400" />;
      default: return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
    }
  };

  return (
    <div className="bg-[#0f1016] border border-[#232535] rounded-xl p-4 sm:p-5 shadow-tactile space-y-4">
      
      {/* 1. Header con Insignia de Metacognición y Autonomía */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#1f2130]">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-[#181926] border border-[#2b2e44] text-[#eed98d]">
            <Brain className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                Deliberación Cognitiva Profunda & Cadena de Razonamiento (Chain-of-Thought)
              </h3>
              <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-purple-950/60 text-purple-300 border border-purple-500/40">
                Metacognición Activa
              </span>
            </div>
            <p className="text-[11px] text-zinc-400">
              Auto-crítica dialéctica, detección de tensiones jurídicas y honestidad sobre límites (Rúbrica Plática).
            </p>
          </div>
        </div>

        {/* Badge de Nivel de Autonomía Realista */}
        <div className="flex items-center space-x-2">
          {requiresHuman ? (
            <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-rose-950/80 text-rose-300 border border-rose-600/50 text-[10px] font-mono font-bold">
              <UserCheck className="w-3.5 h-3.5" />
              <span>ESCALACIÓN HUMAN-IN-THE-LOOP</span>
            </span>
          ) : isProviderLoss ? (
            <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-amber-950/80 text-amber-300 border border-amber-500/50 text-[10px] font-mono font-bold">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>CAUTELA • DERROTA HONESTA DEL PROVEEDOR</span>
            </span>
          ) : (
            <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-500/50 text-[10px] font-mono font-bold">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>AUTONOMÍA AUDITADA ($0.00 MAE)</span>
            </span>
          )}

          <button
            onClick={() => setShowAllSteps(!showAllSteps)}
            className="text-[10px] font-mono px-2 py-1 rounded bg-[#161722] hover:bg-[#202232] text-zinc-400 hover:text-white border border-[#27293d] transition-colors"
          >
            {showAllSteps ? 'Plegar Pasos' : 'Desplegar 5 Pasos'}
          </button>
        </div>
      </div>

      {/* Selector de Perfil Cognitivo de Razonamiento (Mejora 4 Platica) */}
      <div className="p-2.5 rounded-lg bg-[#12141c] border border-[#202330] flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-2 text-[11px] font-mono text-zinc-400">
          <span className="text-[#eed98d] font-bold">ESTILO COGNITIVO:</span>
          <span className="text-zinc-300">{trace?.profile_name || 'Forense Equilibrado ($0.00 MAE)'}</span>
        </div>

        <div className="flex items-center space-x-1.5">
          <button
            onClick={() => onProfileSelect && onProfileSelect('BALANCED_FORENSIC')}
            className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold transition-all ${
              (!trace?.cognitive_profile || trace?.cognitive_profile === 'BALANCED_FORENSIC')
                ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/60 shadow-sm'
                : 'bg-[#181a24] text-zinc-400 hover:text-white border border-[#262838]'
            }`}
          >
            🛡️ Forense Equilibrado
          </button>

          <button
            onClick={() => onProfileSelect && onProfileSelect('CONSERVATIVE_COMMERCIAL')}
            className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold transition-all ${
              trace?.cognitive_profile === 'CONSERVATIVE_COMMERCIAL'
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/60 shadow-sm'
                : 'bg-[#181a24] text-zinc-400 hover:text-white border border-[#262838]'
            }`}
          >
            🤝 Comercial Conservador
          </button>

          <button
            onClick={() => onProfileSelect && onProfileSelect('AGGRESSIVE_LITIGIOUS')}
            className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold transition-all ${
              trace?.cognitive_profile === 'AGGRESSIVE_LITIGIOUS'
                ? 'bg-rose-950 text-rose-300 border border-rose-500/60 shadow-sm'
                : 'bg-[#181a24] text-zinc-400 hover:text-white border border-[#262838]'
            }`}
          >
            ⚖️ Cobranza Litigiosa
          </button>
        </div>
      </div>

      {/* 2. Banner de Honestidad de Errores y Límites (Si aplica Derrota o Cuarentena) */}
      {(isProviderLoss || requiresHuman) && (
        <div className={`p-3.5 rounded-lg border text-xs leading-relaxed ${
          requiresHuman 
            ? 'bg-rose-950/30 border-rose-800/40 text-rose-200' 
            : 'bg-amber-950/30 border-amber-700/40 text-amber-200'
        }`}>
          <div className="flex items-center space-x-2 font-mono font-bold text-[11px] uppercase mb-1">
            <ShieldAlert className="w-4 h-4 flex-shrink-0" />
            <span>
              {requiresHuman 
                ? 'LÍMITE OPERACIONAL ALCANZADO: NO SE ALUCINAN CERTEZAS' 
                : 'RECONOCIMIENTO HONESTO DE DERROTA COMERCIAL'}
            </span>
          </div>
          <p className="text-[11px] opacity-90">
            {isProviderLoss
              ? 'El agente comprobó que el comprador (retailer) tiene la razón 100% documentada. Formular una reclamación legal coactiva sería temerario e infundado. Se recomienda reconocer la merma mediante Nota de Crédito y cerrar la cuenta.'
              : 'El expediente presenta inconsistencias o firmas ilegibles en muelle. Para proteger la relación con el cliente y evitar reclamaciones falsas, el agente suspende la emisión automática y convoca mediación humana.'}
          </p>
        </div>
      )}

      {/* 3. Cadena de Razonamiento en 5 Pasos (Chain-of-Thought) */}
      {showAllSteps && (
        <div className="space-y-2.5 pt-1">
          {steps.map((st, idx) => {
            const isAlert = st.status === 'ALERT' || st.status === 'WARNING';
            const isStepOpen = expandedStep === idx || expandedStep === null; // Abiertos por defecto para inspección

            return (
              <div 
                key={idx}
                className={`rounded-lg border transition-all ${
                  isAlert 
                    ? 'bg-[#15131a] border-amber-600/30 hover:border-amber-500/50' 
                    : 'bg-[#12131b] border-[#222435] hover:border-[#32364c]'
                }`}
              >
                <div 
                  onClick={() => toggleStep(idx)}
                  className="p-3 flex items-center justify-between cursor-pointer select-none"
                >
                  <div className="flex items-center space-x-3">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-[#1c1e2b] border border-[#2e3146] text-[11px] font-mono font-bold text-zinc-300">
                      {st.step_number}
                    </span>
                    <div className="flex items-center space-x-2">
                      {getStepIcon(st.icon, st.step_number)}
                      <span className="text-xs font-semibold text-zinc-200">
                        {st.title}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {st.highlight && (
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                        isAlert 
                          ? 'bg-amber-950/60 text-amber-300 border border-amber-600/40' 
                          : 'bg-[#1b1d2a] text-zinc-400 border border-[#2b2e40]'
                      }`}>
                        {st.highlight}
                      </span>
                    )}
                    {isStepOpen ? <ChevronUp className="w-3.5 h-3.5 text-zinc-400" /> : <ChevronDown className="w-3.5 h-3.5 text-zinc-400" />}
                  </div>
                </div>

                {isStepOpen && (
                  <div className="px-3.5 pb-3.5 pt-1 text-xs text-zinc-300 border-t border-[#1b1c28] font-sans leading-relaxed">
                    <p className="text-[11px] text-zinc-300 bg-[#0e0f15] p-2.5 rounded border border-[#1b1d28]">
                      {st.narrative}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* 4. Pie de Honestidad Operativa y Lección Aprendida */}
      <div className="pt-2 border-t border-[#1b1d27] flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[10px] font-mono text-zinc-400">
        <div className="flex items-center space-x-1.5 text-[#eed98d]">
          <Lightbulb className="w-3.5 h-3.5 text-[#d4af37]" />
          <span>LECCIÓN APRENDIDA:</span>
          <span className="text-zinc-300 font-sans">
            {trace?.lesson_learned || 'Un agente robusto no alucina certezas donde los documentos presentan ambigüedad.'}
          </span>
        </div>
        <span className="text-zinc-500">
          Evaluado s/ Código de Comercio y NIA 240
        </span>
      </div>

    </div>
  );
}
