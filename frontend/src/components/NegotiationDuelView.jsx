import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { 
  Swords, 
  Scale, 
  ShieldCheck, 
  ShieldAlert, 
  Lock, 
  Unlock, 
  Play, 
  FastForward, 
  RotateCcw, 
  CheckCircle2, 
  AlertTriangle, 
  FileText, 
  Send, 
  TrendingDown, 
  ExternalLink, 
  Copy, 
  Check, 
  Bot, 
  UserCheck, 
  Building2, 
  Clock, 
  Sparkles,
  ArrowRight
} from 'lucide-react';

export default function NegotiationDuelView({ caseId = 'case_005_amazon_shortage' }) {
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState(null);
  const [error, setError] = useState(null);
  const [activeRound, setActiveRound] = useState(1);
  const [isAdvancing, setIsAdvancing] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isDispatching, setIsDispatching] = useState(false);
  const [dispatchReceipt, setDispatchReceipt] = useState(null);
  const [dossier, setDossier] = useState(null);
  const [showAgreementModal, setShowAgreementModal] = useState(false);
  const [agreementMinutes, setAgreementMinutes] = useState(null);
  const [copiedHash, setCopiedHash] = useState(false);

  // Cargar sesión de negociación activa y estado del despacho
  const loadSessionData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.getDuelSession(caseId);
      if (res && res.session) {
        setSession(res.session);
        setActiveRound(res.session.current_round || 1);
      } else {
        // Si no ha iniciado, iniciarlo con defaults
        const startRes = await apiClient.startDuel(caseId, { governance_mode: 'HUMAN_GATEKEEPER' });
        setSession(startRes.session);
        setActiveRound(startRes.session.current_round || 1);
      }

      // Intentar cargar recibo de despacho previo
      try {
        const rcptRes = await apiClient.getCasePortalReceipt(caseId);
        if (rcptRes && rcptRes.receipt) {
          setDispatchReceipt(rcptRes.receipt);
        }
      } catch {
        // No ha sido despachado aún
      }
    } catch (err) {
      setError(err.message || 'Error al conectar con la mesa de negociación');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessionData();
  }, [caseId]);

  // Avanzar una ronda
  const handleAdvanceStep = async () => {
    if (isAdvancing) return;
    setIsAdvancing(true);
    try {
      const res = await apiClient.advanceDuelStep(caseId);
      setSession(res.session);
      setActiveRound(res.session.current_round || 1);
    } catch (err) {
      alert(`Error al avanzar careo: ${err.message}`);
    } finally {
      setIsAdvancing(false);
    }
  };

  // Auto-careo completo hasta convergencia o límite
  const handleAutoPlay = async () => {
    if (isAdvancing) return;
    setIsAdvancing(true);
    try {
      let currentSession = session;
      for (let i = 0; i < 4; i++) {
        if (currentSession.status === 'AGREEMENT_REACHED' || 
            currentSession.status === 'AWAITING_HUMAN_APPROVAL' || 
            currentSession.status === 'IMPASSE_REACHED') {
          break;
        }
        const res = await apiClient.advanceDuelStep(caseId);
        currentSession = res.session;
        setSession(currentSession);
        setActiveRound(currentSession.current_round || 1);
        await new Promise(r => setTimeout(r, 600)); // Delay para visualización
      }
    } catch (err) {
      alert(`Error en simulación: ${err.message}`);
    } finally {
      setIsAdvancing(false);
    }
  };

  // Reiniciar careo
  const handleRestartDuel = async () => {
    if (!window.confirm('¿Deseas reiniciar la confrontación dialéctica desde la Ronda 1?')) return;
    setLoading(true);
    try {
      const mode = session?.governance_mode || 'HUMAN_GATEKEEPER';
      const startRes = await apiClient.startDuel(caseId, { governance_mode: mode });
      setSession(startRes.session);
      setActiveRound(1);
    } catch (err) {
      alert(`Error al reiniciar: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Conmutar modo de gobernanza
  const handleToggleGovernance = async () => {
    const currentMode = session?.governance_mode || 'HUMAN_GATEKEEPER';
    const newMode = currentMode === 'FULL_AUTONOMY' ? 'HUMAN_GATEKEEPER' : 'FULL_AUTONOMY';
    try {
      const res = await apiClient.setDuelGovernance(caseId, { governance_mode: newMode });
      setSession(res.session);
    } catch (err) {
      alert(`Salvaguarda del CFO activa: ${err.message}`);
    }
  };

  // Aprobar finiquito (Human Gatekeeper)
  const handleApproveSettlement = async () => {
    setIsApproving(true);
    try {
      const res = await apiClient.approveDuelSettlement(caseId, { operator_name: 'Director de Finanzas & Tesorería B2B' });
      setSession(res.session);
      alert('Acuerdo bilateral rubricado formalmente con sello criptográfico ZKP SHA-256.');
    } catch (err) {
      alert(`Error al aprobar: ${err.message}`);
    } finally {
      setIsApproving(false);
    }
  };

  // Despacho a portal B2B
  const handleDispatchPortal = async () => {
    setIsDispatching(true);
    try {
      const res = await apiClient.dispatchCaseToPortal(caseId, { operator_name: 'SupplyMind Robotic Dispatcher' });
      setDispatchReceipt(res.receipt);
    } catch (err) {
      alert(`Error al despachar: ${err.message}`);
    } finally {
      setIsDispatching(false);
    }
  };

  // Cargar convenio formal
  const handleOpenAgreement = async () => {
    try {
      const res = await apiClient.getDuelMinutes(caseId);
      setAgreementMinutes(res);
      setShowAgreementModal(true);
    } catch (err) {
      alert(`No se encontró convenio aún: ${err.message}`);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-20 space-y-4">
        <Swords className="w-12 h-12 text-[#d4af37] animate-pulse" />
        <p className="text-zinc-400 font-mono text-sm">Conectando con la Mesa de Negociación B2B...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 bg-rose-950/20 border border-rose-800/40 rounded-xl m-4 text-center">
        <AlertTriangle className="w-10 h-10 text-rose-400 mx-auto mb-3" />
        <h3 className="text-rose-200 font-bold mb-1">Error en la Mesa de Negociación</h3>
        <p className="text-zinc-400 text-xs font-mono">{error}</p>
        <button 
          onClick={loadSessionData}
          className="mt-4 px-4 py-2 bg-rose-900/60 hover:bg-rose-900 text-white rounded text-xs font-mono transition-colors"
        >
          Reintentar Conexión
        </button>
      </div>
    );
  }

  const rounds = session?.rounds || [];
  const currentRoundData = rounds.find(r => r.round_number === activeRound) || rounds[rounds.length - 1];
  const archetype = session?.archetype;
  const isAgreed = session?.status === 'AGREEMENT_REACHED';
  const isAwaiting = session?.status === 'AWAITING_HUMAN_APPROVAL';
  const isImpasse = session?.status === 'IMPASSE_REACHED';
  const isHighValue = (session?.total_disputed_amount || 0) >= 10000;

  return (
    <div className="space-y-5 p-4 sm:p-6 max-w-7xl mx-auto animate-in fade-in duration-200">
      
      {/* 1. Header Toolbar de Gobernanza & Dualidad */}
      <div className="bg-[#0b0c10] border border-[#1e2029] rounded-2xl p-4 sm:p-5 shadow-2xl backdrop-blur-md flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 bg-gradient-to-br from-[#d4af37]/20 to-[#997b1e]/10 border border-[#d4af37]/40 rounded-xl shadow-inner">
            <Swords className="w-6 h-6 text-[#eed98d]" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base sm:text-lg font-bold text-white tracking-tight flex items-center gap-2">
                Mesa de Negociación Bilateral & Careo IA
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#181a24] text-zinc-400 border border-[#272a39] font-mono">
                  MCTS Game Theory
                </span>
              </h2>
            </div>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">
              Expediente: <span className="text-white font-semibold">{session?.case_id}</span> | Contraparte: <span className="text-[#eed98d] font-semibold">{session?.retailer_name}</span>
            </p>
          </div>
        </div>

        {/* Controles de Dualidad de Gobernanza */}
        <div className="flex flex-wrap items-center gap-2.5 w-full lg:w-auto">
          {isHighValue && (
            <div className="px-2.5 py-1 rounded-lg bg-amber-950/40 border border-amber-600/50 text-amber-300 text-xs font-mono flex items-center space-x-1.5 shadow-sm" title="Casos ≥ $10,000 USD exigen Human Gatekeeper según la política del CFO">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
              <span>Salvaguarda CFO Activa (&ge; $10k)</span>
            </div>
          )}

          <div className="flex items-center bg-[#12131a] border border-[#222432] rounded-xl p-1 shadow-inner">
            <button
              onClick={handleToggleGovernance}
              disabled={isHighValue}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all flex items-center space-x-1.5 ${
                session?.governance_mode === 'FULL_AUTONOMY'
                  ? 'bg-gradient-to-r from-emerald-900/60 to-emerald-800/40 text-emerald-300 border border-emerald-500/50 shadow-sm'
                  : 'text-zinc-500 hover:text-zinc-300'
              } ${isHighValue ? 'opacity-50 cursor-not-allowed' : ''}`}
              title={isHighValue ? 'Bloqueado por salvaguarda financiera corporativa' : 'Permite al agente cerrar acuerdos dentro de la matriz sin confirmación'}
            >
              <Bot className="w-3.5 h-3.5" />
              <span>Piloto Automático</span>
            </button>

            <button
              onClick={handleToggleGovernance}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all flex items-center space-x-1.5 ${
                session?.governance_mode === 'HUMAN_GATEKEEPER'
                  ? 'bg-gradient-to-r from-blue-900/60 to-indigo-900/40 text-blue-300 border border-blue-500/50 shadow-sm'
                  : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>Human Gatekeeper</span>
            </button>
          </div>

          <div className="px-3 py-1.5 rounded-xl bg-[#12131a] border border-[#222432] text-xs font-mono text-zinc-300 flex items-center space-x-2">
            <span className="text-zinc-500">Tope Matriz:</span>
            <span className="text-emerald-400 font-bold">${session?.delegation_limit_amount?.toLocaleString()} USD</span>
            <span className="text-zinc-500 text-[10px]">({session?.delegation_limit_pct}%)</span>
          </div>
        </div>
      </div>

      {/* 2. Banner de Estado del Careo */}
      {isAgreed && (
        <div className="p-4 bg-emerald-950/30 border border-emerald-500/40 rounded-xl flex items-center justify-between shadow-lg">
          <div className="flex items-center space-x-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0" />
            <div>
              <h4 className="text-sm font-bold text-emerald-200">¡Acuerdo Bilateral Formalizado!</h4>
              <p className="text-xs text-zinc-300 font-mono mt-0.5">{session?.summary_verdict}</p>
            </div>
          </div>
          <button
            onClick={handleOpenAgreement}
            className="px-3 py-1.5 rounded-lg bg-emerald-900/60 hover:bg-emerald-800 text-white text-xs font-mono transition-colors flex items-center space-x-1.5 shrink-0"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Ver Convenio</span>
          </button>
        </div>
      )}

      {isAwaiting && (
        <div className="p-4 bg-amber-950/30 border border-amber-500/40 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-lg">
          <div className="flex items-center space-x-3">
            <ShieldCheck className="w-6 h-6 text-amber-400 shrink-0" />
            <div>
              <h4 className="text-sm font-bold text-amber-200">En Espera de Rúbrica de Operador (Gatekeeper)</h4>
              <p className="text-xs text-zinc-300 font-mono mt-0.5">
                Se alcanzó el punto de equilibrio en Ronda {session?.current_round}. Requiere confirmación humana antes de signar el convenio de finiquito.
              </p>
            </div>
          </div>
          <button
            onClick={handleApproveSettlement}
            disabled={isApproving}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-[#d4af37] to-[#b39023] hover:from-[#eed98d] hover:to-[#d4af37] text-black font-bold text-xs font-mono transition-all flex items-center space-x-1.5 shadow-tactile shrink-0 disabled:opacity-50"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>{isApproving ? 'Rubricando...' : 'Rubricar y Cerrar Finiquito'}</span>
          </button>
        </div>
      )}

      {/* 3. Panel Central Split-Screen: Agente Defensor vs Comprador Retailer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        
        {/* LADO IZQUIERDO: Agente Defensor SupplyMind AI (Col 5) */}
        <div className="lg:col-span-5 bg-[#0b0c10] border border-[#1e2029] rounded-2xl p-5 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#181a24]">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-blue-950/60 border border-blue-500/40 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-blue-400" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">SupplyMind AI</h3>
                  <p className="text-[10px] text-zinc-400 font-mono">Agente Defensor B2B</p>
                </div>
              </div>

              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/40 uppercase font-semibold">
                {currentRoundData?.supplier_stance || 'EVIDENCE_FIRMNESS'}
              </span>
            </div>

            {/* Cifras de Oferta SupplyMind */}
            <div className="grid grid-cols-2 gap-3 my-4">
              <div className="p-3 bg-[#111218] border border-[#1e2029] rounded-xl">
                <span className="text-[10px] text-zinc-500 font-mono block">Concesión Ofrecida (NC):</span>
                <span className="text-base font-bold text-amber-400 font-mono">
                  ${currentRoundData?.supplier_offer_credit_memo?.toLocaleString() || '0.00'} USD
                </span>
              </div>
              <div className="p-3 bg-[#111218] border border-[#1e2029] rounded-xl">
                <span className="text-[10px] text-zinc-500 font-mono block">Reclamo en Efectivo:</span>
                <span className="text-base font-bold text-emerald-400 font-mono">
                  ${currentRoundData?.supplier_claim_cash?.toLocaleString() || '0.00'} USD
                </span>
              </div>
            </div>

            {/* Burbuja de Argumentación Dialéctica */}
            <div className="p-3.5 bg-[#12141f] border border-[#222536] rounded-xl text-xs text-zinc-200 leading-relaxed font-sans shadow-inner">
              <p className="italic">"{currentRoundData?.supplier_message || 'Iniciando argumentación técnica basada en evidencias documentales...'}"</p>
            </div>

            {/* Evidencias Exhibidas */}
            <div className="mt-4 space-y-2">
              <span className="text-[11px] font-mono text-zinc-400 font-semibold block">Pruebas Exhibidas en Ronda {activeRound}:</span>
              <div className="space-y-1.5">
                {(currentRoundData?.evidence_exhibited || []).map((ev, idx) => (
                  <div key={idx} className="p-2 rounded-lg bg-[#0e0f14] border border-[#1a1c26] text-xs font-mono text-zinc-300 flex items-center space-x-2">
                    <FileText className="w-3.5 h-3.5 text-[#d4af37] shrink-0" />
                    <span className="truncate">{ev}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-[#181a24] text-[10px] font-mono text-zinc-500 flex items-center justify-between">
            <span>Algoritmo: MCTS Tree Search</span>
            <span className="text-emerald-400">Restitución Objetivo: 100% Justificado</span>
          </div>
        </div>

        {/* CENTRO: Dial de Convergencia & Navegación de Rondas (Col 2) */}
        <div className="lg:col-span-2 flex flex-col justify-between items-center bg-[#0e0f14] border border-[#1e2029] rounded-2xl p-4 shadow-xl">
          <div className="w-full text-center">
            <span className="text-[11px] font-mono text-zinc-400 block font-semibold">Careo Rondas</span>
            
            {/* Stepper de Rondas */}
            <div className="flex lg:flex-col justify-center gap-2 my-4">
              {[1, 2, 3, 4, 5].map((rNum) => {
                const roundInfo = rounds.find(r => r.round_number === rNum);
                const isCurrent = activeRound === rNum;
                const isPast = rounds.some(r => r.round_number === rNum);

                return (
                  <button
                    key={rNum}
                    onClick={() => roundInfo && setActiveRound(rNum)}
                    disabled={!roundInfo}
                    className={`w-8 h-8 rounded-full font-mono text-xs font-bold transition-all flex items-center justify-center ${
                      isCurrent
                        ? 'bg-[#d4af37] text-black shadow-tactile scale-110'
                        : isPast
                        ? 'bg-[#181a24] border border-[#272a39] text-zinc-300 hover:text-white'
                        : 'bg-[#101117] border border-[#1a1c24] text-zinc-600 opacity-40 cursor-not-allowed'
                    }`}
                  >
                    R{rNum}
                  </button>
                );
              })}
            </div>

            {/* Medidor de Spread y Convergencia */}
            <div className="my-2 p-2 rounded-xl bg-[#12131a] border border-[#1e2029] w-full">
              <span className="text-[10px] text-zinc-500 font-mono block">Brecha (Spread):</span>
              <span className="text-sm font-bold text-rose-400 font-mono block">
                ${currentRoundData?.spread?.toLocaleString() || '0.00'} USD
              </span>
              <div className="w-full bg-[#1e2029] h-1.5 rounded-full overflow-hidden mt-1.5">
                <div 
                  className="bg-gradient-to-r from-[#d4af37] to-emerald-400 h-full transition-all duration-500" 
                  style={{ width: `${currentRoundData?.convergence_pct || 0}%` }}
                />
              </div>
              <span className="text-[10px] text-zinc-400 font-mono mt-1 block">
                {currentRoundData?.convergence_pct || 0}% Convergencia
              </span>
            </div>
          </div>

          {/* Acciones de Careo */}
          <div className="w-full space-y-2 mt-4">
            <button
              onClick={handleAdvanceStep}
              disabled={isAdvancing || isAgreed || isImpasse || session?.current_round >= 5}
              className="w-full py-2 px-2.5 rounded-xl bg-gradient-to-r from-blue-900/60 to-indigo-900/40 hover:from-blue-800 hover:to-indigo-800 text-blue-200 border border-blue-500/40 font-mono text-xs font-bold transition-all flex items-center justify-center space-x-1.5 shadow-sm disabled:opacity-40"
              title="Avanzar a la siguiente ronda dialéctica"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Avanzar Ronda</span>
            </button>

            <button
              onClick={handleAutoPlay}
              disabled={isAdvancing || isAgreed || isImpasse}
              className="w-full py-1.5 px-2.5 rounded-xl bg-[#141620] hover:bg-[#1a1d2b] border border-[#272a39] text-zinc-300 font-mono text-xs transition-colors flex items-center justify-center space-x-1.5 disabled:opacity-40"
              title="Ejecutar todas las rondas hasta llegar al acuerdo"
            >
              <FastForward className="w-3.5 h-3.5" />
              <span>Auto-Careo</span>
            </button>

            <button
              onClick={handleRestartDuel}
              className="w-full py-1.5 px-2.5 rounded-xl bg-transparent hover:bg-[#161822] text-zinc-500 hover:text-zinc-300 font-mono text-[11px] transition-colors flex items-center justify-center space-x-1"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reiniciar</span>
            </button>
          </div>
        </div>

        {/* LADO DERECHO: Comprador Retailer Hostil (Col 5) */}
        <div className="lg:col-span-5 bg-[#0b0c10] border border-[#1e2029] rounded-2xl p-5 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#181a24]">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-rose-950/60 border border-rose-500/40 flex items-center justify-center">
                  <Building2 className="w-4 h-4 text-rose-400" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">{archetype?.retailer_name || session?.retailer_name}</h3>
                  <p className="text-[10px] text-zinc-400 font-mono">{archetype?.buyer_title || 'Director de Compras'}</p>
                </div>
              </div>

              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800/40 uppercase font-semibold">
                {currentRoundData?.buyer_stance || 'INTRANSIGENT'}
              </span>
            </div>

            {/* Cifras de Demanda Retailer */}
            <div className="grid grid-cols-2 gap-3 my-4">
              <div className="p-3 bg-[#111218] border border-[#1e2029] rounded-xl">
                <span className="text-[10px] text-zinc-500 font-mono block">Demanda NC Retenida:</span>
                <span className="text-base font-bold text-rose-400 font-mono">
                  ${currentRoundData?.buyer_demand_credit_memo?.toLocaleString() || '0.00'} USD
                </span>
              </div>
              <div className="p-3 bg-[#111218] border border-[#1e2029] rounded-xl">
                <span className="text-[10px] text-zinc-500 font-mono block">Oferta de Pago en Banco:</span>
                <span className="text-base font-bold text-zinc-300 font-mono">
                  ${currentRoundData?.buyer_cash_payout_offer?.toLocaleString() || '0.00'} USD
                </span>
              </div>
            </div>

            {/* Burbuja de Argumentación Retailer */}
            <div className="p-3.5 bg-[#181114] border border-[#301a20] rounded-xl text-xs text-zinc-200 leading-relaxed font-sans shadow-inner">
              <p className="italic">"{currentRoundData?.buyer_message || 'Exigiendo retención total del saldo disputado en apego a políticas comerciales.'}"</p>
            </div>

            {/* Tácticas y Puntos de Presión */}
            <div className="mt-4 space-y-2">
              <span className="text-[11px] font-mono text-zinc-400 font-semibold block">Tácticas de Desgaste Retailer:</span>
              <div className="flex flex-wrap gap-1.5">
                {(archetype?.key_pressure_points || ['Scorecard OTIF', 'Bloqueo de pagos']).map((pt, idx) => (
                  <span key={idx} className="px-2 py-1 rounded bg-[#161214] border border-rose-900/40 text-[11px] font-mono text-rose-300">
                    ⚠️ {pt}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-[#181a24] text-[10px] font-mono text-zinc-500 flex items-center justify-between">
            <span>Resistencia: {archetype?.concession_resistance_score || '8.5'}/10</span>
            <span className="text-rose-400">Tono: Hostil y Burocrático</span>
          </div>
        </div>

      </div>

      {/* 4. Terminal de Despacho Robótico a Portales B2B (Sprint 6.3) */}
      <div className="bg-[#0b0c10] border border-[#1e2029] rounded-2xl p-5 shadow-xl">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-[#181a24] gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-cyan-950/50 border border-cyan-500/40 rounded-xl">
              <Send className="w-5 h-5 text-cyan-300" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                Despachador Robótico a Portales B2B
                <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/40 font-mono">
                  Sprint 6.3 RPA
                </span>
              </h3>
              <p className="text-xs text-zinc-400 font-mono">
                Radicación pericial directa en {session?.retailer_name} (Retail Link / Vendor Central / Soriana)
              </p>
            </div>
          </div>

          <button
            onClick={handleDispatchPortal}
            disabled={isDispatching}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-xs font-mono transition-all flex items-center space-x-1.5 shadow-tactile disabled:opacity-50"
          >
            <Send className={`w-3.5 h-3.5 ${isDispatching ? 'animate-spin' : ''}`} />
            <span>{isDispatching ? 'Radicando en Portal...' : 'Despachar al Portal Retailer'}</span>
          </button>
        </div>

        {/* Bitácora y Recibo Oficial */}
        {dispatchReceipt ? (
          <div className="mt-4 space-y-3">
            <div className="p-3.5 bg-[#0e1620] border border-cyan-500/30 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <span className="text-[10px] font-mono text-cyan-400 font-semibold block">Radicación Exitosa en Portal B2B:</span>
                <span className="text-sm font-bold text-white font-mono flex items-center gap-2 mt-0.5">
                  Ticket Oficial: <span className="text-[#eed98d]">{dispatchReceipt.tracking_ticket}</span>
                </span>
                <p className="text-xs text-zinc-400 font-mono mt-1">
                  SLA de Resolución: <span className="text-white">{dispatchReceipt.estimated_sla_days} días hábiles</span> | HTTP 201 Created
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => copyToClipboard(dispatchReceipt.tracking_ticket)}
                  className="px-2.5 py-1.5 rounded-lg bg-[#14232c] hover:bg-[#1a2e3a] border border-cyan-700/40 text-cyan-300 text-xs font-mono transition-colors flex items-center space-x-1"
                >
                  {copiedHash ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>Copiar Ticket</span>
                </button>
              </div>
            </div>

            {/* Bitácora Terminal Micro-Pasos */}
            <div className="p-3 bg-[#08090d] border border-[#161822] rounded-xl font-mono text-[11px] text-zinc-300 space-y-1 max-h-40 overflow-y-auto">
              {(dispatchReceipt.log_trace || []).map((step, idx) => (
                <div key={idx} className="flex items-start space-x-2">
                  <span className="text-cyan-500 font-bold shrink-0">&gt;</span>
                  <span className="text-zinc-300">{step}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="mt-4 p-4 rounded-xl bg-[#0e0f14] border border-[#1a1c26] text-center text-xs text-zinc-500 font-mono">
            El expediente pericial consolidado está listo para radicación automática. Haz clic en "Despachar al Portal Retailer" para transmitir evidencias y obtener el folio oficial de ticket.
          </div>
        )}
      </div>

      {/* 5. Modal de Convenio Formal de Finiquito (Cosa Juzgada & ZKP) */}
      {showAgreementModal && agreementMinutes && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-150">
          <div className="bg-[#0b0c10] border border-[#d4af37]/40 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl">
            <div className="p-4 sm:p-5 border-b border-[#1e2029] flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <FileText className="w-5 h-5 text-[#eed98d]" />
                <h3 className="text-base font-bold text-white">Convenio de Transacción Mercantil & Finiquito</h3>
              </div>
              <button
                onClick={() => setShowAgreementModal(false)}
                className="text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-[#181a24] text-xs font-mono"
              >
                ✕ Cerrar
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-4 font-mono text-xs text-zinc-300 leading-relaxed">
              <div className="p-3 bg-[#111218] border border-[#222432] rounded-xl flex items-center justify-between">
                <div>
                  <span className="text-zinc-500 block text-[10px]">Sello Criptográfico ZKP SHA-256:</span>
                  <span className="text-emerald-400 font-bold break-all">{agreementMinutes.settlement_minutes_hash}</span>
                </div>
                <button
                  onClick={() => copyToClipboard(agreementMinutes.settlement_minutes_hash)}
                  className="px-2 py-1 bg-[#181a24] text-zinc-300 hover:text-white rounded text-[11px] shrink-0 ml-2"
                >
                  {copiedHash ? 'Copiado!' : 'Copiar'}
                </button>
              </div>

              <div className="p-4 bg-[#08090d] border border-[#1a1c24] rounded-xl whitespace-pre-wrap font-sans text-xs text-zinc-200">
                {agreementMinutes.markdown_content}
              </div>
            </div>

            <div className="p-4 border-t border-[#1e2029] flex justify-end space-x-3 bg-[#0e0f14] rounded-b-2xl">
              <button
                onClick={() => setShowAgreementModal(false)}
                className="px-4 py-2 rounded-xl bg-[#181a24] hover:bg-[#222432] text-white text-xs font-mono"
              >
                Cerrar Visor
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
