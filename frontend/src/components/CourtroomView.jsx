import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { 
  Scale, 
  Gavel, 
  ShieldAlert, 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  FileText, 
  TrendingUp, 
  Sparkles, 
  RotateCcw, 
  ChevronRight, 
  ChevronLeft,
  Download,
  Flame,
  Award,
  Layers,
  Info
} from 'lucide-react';

export default function CourtroomView({ caseId = 'case_001', onOpenDossier }) {
  const [loading, setLoading] = useState(true);
  const [courtData, setCourtData] = useState(null);
  const [error, setError] = useState(null);
  const [activeRoundIdx, setActiveRoundIdx] = useState(0);
  const [gavelStruck, setGavelStruck] = useState(false);
  const [isHardening, setIsHardening] = useState(false);
  const [hardeningResult, setHardeningResult] = useState(null);
  const [isDossierGenerating, setIsDossierGenerating] = useState(false);
  const [generatedDossierData, setGeneratedDossierData] = useState(null);

  // Cargar datos del estrado judicial adversarial
  useEffect(() => {
    let isCancelled = false;
    async function loadCourtroom() {
      setLoading(true);
      setError(null);
      setGavelStruck(false);
      try {
        const data = await apiClient.getCourtroomCareo(caseId);
        if (!isCancelled) {
          setCourtData(data);
          setActiveRoundIdx(0);
        }
      } catch (err) {
        if (!isCancelled) {
          setError(err.message || 'Error al cargar estrado dialéctico');
        }
      } finally {
        if (!isCancelled) setLoading(false);
      }
    }
    loadCourtroom();
    return () => { isCancelled = true; };
  }, [caseId]);

  const handleStrikeGavel = () => {
    setGavelStruck(true);
    // Micro-animación de impacto
    setTimeout(() => {
      // scroll to verdict smoothly if needed
    }, 400);
  };

  const handleAutoHarden = async () => {
    setIsHardening(true);
    try {
      const res = await apiClient.autoHardenCase({
        case_id: caseId,
        seller_country: 'MEXICO',
        buyer_country: 'MEXICO',
        days_to_claim: 15,
        has_edi_997: true
      });
      setHardeningResult(res);
    } catch (err) {
      alert(`Error reforzando dictamen: ${err.message}`);
    } finally {
      setIsHardening(false);
    }
  };

  const handleGenerateIccDossier = async () => {
    setIsDossierGenerating(true);
    try {
      const res = await apiClient.generateArbitrationDossier({
        case_id: caseId,
        claimant_name: courtData?.supplier_name || 'PROVEEDOR INDUSTRIAL S.A.',
        respondent_name: courtData?.retailer_name || 'NUEVA WAL MART DE MEXICO S. DE R.L.',
        institution: 'ICC',
        days_in_arrears: 90
      });
      setGeneratedDossierData(res);
      if (onOpenDossier) onOpenDossier();
    } catch (err) {
      alert(`Error generando dossier arbitral ICC: ${err.message}`);
    } finally {
      setIsDossierGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-[#0e0f14] border border-[#1e2029] rounded-xl p-12 text-center font-mono space-y-4">
        <Scale className="w-10 h-10 text-[#d4af37] animate-pulse mx-auto" />
        <div className="text-white font-bold text-sm">Constituyendo Estrado Judicial Adversarial...</div>
        <p className="text-xs text-zinc-500">
          Invocando Fiscal del Retailer, Abogado Defensor del Proveedor y Magistrado Arbitral ICC para {caseId}...
        </p>
      </div>
    );
  }

  if (error || !courtData) {
    return (
      <div className="bg-[#180f12] border border-[#3e1920] rounded-xl p-8 text-center font-mono space-y-3">
        <AlertTriangle className="w-8 h-8 text-red-400 mx-auto" />
        <div className="text-red-300 font-bold text-sm">No fue posible abrir el estrado para este caso</div>
        <p className="text-xs text-zinc-400">{error || 'Datos no disponibles'}</p>
      </div>
    );
  }

  const { prosecutor, defense, judge, rounds, mcts_strategy } = courtData;
  const currentRound = rounds[activeRoundIdx] || rounds[0];

  return (
    <div className="space-y-4 font-sans text-zinc-200 animate-in fade-in duration-200">
      
      {/* Courtroom Chamber Header */}
      <div className="bg-[#0e0f14] border border-[#1e2029] rounded-xl p-4 shadow-tactile flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-[#221f14] border border-[#3a341e] text-[#d4af37]">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-bold text-white font-mono tracking-tight">
                Estrado Dialéctico Adversarial & Simulación Judicial
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#1f1d14] text-[#eed98d] border border-[#d4af37]/40">
                {courtData.courtroom_session_id}
              </span>
            </div>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">
              Careo tripartito de alta fidelidad: Fiscal del Retailer vs Defensor Técnico del Proveedor ante Árbitro Comercial.
            </p>
          </div>
        </div>

        {/* Global Courtroom Actions */}
        <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
          <button
            onClick={handleAutoHarden}
            disabled={isHardening}
            className="px-3 py-1.5 rounded bg-[#181a24] hover:bg-[#222533] border border-[#2c3044] text-zinc-300 hover:text-white transition-all flex items-center space-x-1.5 shadow-tactile disabled:opacity-50"
            title="Someter el dictamen al Subagente Crítico Hostil y reforzarlo con escudo preventivo"
          >
            <ShieldCheck className={`w-3.5 h-3.5 text-emerald-400 ${isHardening ? 'animate-spin' : ''}`} />
            <span>{isHardening ? 'Reforzando...' : 'Auto-Reforzar Escudo'}</span>
          </button>

          <button
            onClick={handleGenerateIccDossier}
            disabled={isDossierGenerating}
            className="px-3 py-1.5 rounded bg-[#1e1929] hover:bg-[#2a2339] border border-[#4a356b] text-purple-300 hover:text-white transition-all flex items-center space-x-1.5 shadow-tactile disabled:opacity-50"
            title="Generar Dossier Foliado Institucional para Arbitraje ICC Paris / CANACO"
          >
            <FileText className={`w-3.5 h-3.5 text-purple-400 ${isDossierGenerating ? 'animate-spin' : ''}`} />
            <span>{isDossierGenerating ? 'Compilando...' : 'Dossier Arbitral ICC'}</span>
          </button>
        </div>
      </div>

      {/* Auto-Harden Notice if activated */}
      {hardeningResult && (
        <div className="bg-[#122218] border border-[#23472c] rounded-xl p-3.5 font-mono text-xs flex items-center justify-between gap-3 animate-in fade-in duration-200">
          <div className="flex items-center space-x-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span className="text-emerald-200">
              <strong>Escudo Jurídico Inyectado con Éxito:</strong> Dictamen reforzado contra 
              {hardeningResult.critique?.vulnerabilities_detected?.length || 0} objeciones potenciales del Retailer. Robustez: <strong>{hardeningResult.original_robustness_score}%</strong>.
            </span>
          </div>
          <span className="px-2 py-0.5 rounded bg-[#1c3824] text-emerald-300 border border-[#2e5d3c] font-bold">
            BLINDADO
          </span>
        </div>
      )}

      {/* THE COURTROOM BENCH (TOP CENTER: MAGISTRATE JUDGE) */}
      <div className={`border rounded-xl p-4 transition-all duration-300 shadow-modal ${
        gavelStruck 
          ? 'bg-[#15130b] border-[#d4af37]' 
          : 'bg-[#0d0e12] border-[#222432]'
      }`}>
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-3 border-b border-[#1c1e28]">
          <div className="flex items-center space-x-3">
            <div className={`p-3 rounded-xl border transition-all ${
              gavelStruck
                ? 'bg-[#d4af37] text-black border-[#d4af37] shadow-[0_0_20px_rgba(212,175,55,0.4)]'
                : 'bg-[#1e1c14] text-[#d4af37] border-[#3e371f]'
            }`}>
              <Gavel className={`w-6 h-6 ${gavelStruck ? 'animate-bounce' : ''}`} />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono uppercase tracking-wider text-[#d4af37] font-bold">
                  {judge.organization}
                </span>
                <span className="px-2 py-0.2 rounded text-[10px] font-mono font-bold bg-[#1a1c27] text-zinc-300 border border-[#272a39]">
                  Índice de Certeza: {judge.confidence_score}%
                </span>
              </div>
              <h3 className="text-base font-bold text-white font-mono">
                {judge.name}
              </h3>
            </div>
          </div>

          {/* Gavel Strike Trigger */}
          <div className="flex items-center space-x-3">
            <button
              onClick={handleStrikeGavel}
              className={`btn-tactile px-4 py-2 rounded text-xs font-mono font-bold uppercase tracking-wider transition-all flex items-center space-x-2 border shadow-tactile ${
                gavelStruck
                  ? 'bg-[#292312] text-[#eed98d] border-[#d4af37]'
                  : 'bg-[#d4af37] hover:bg-[#e4be42] text-black border-[#d4af37] hover:scale-105'
              }`}
            >
              <Gavel className="w-4 h-4 fill-current" />
              <span>{gavelStruck ? 'Sentencia Firme Ejecutable' : 'Emitir Sentencia Vinculante'}</span>
            </button>
          </div>
        </div>

        {/* Verdict & Legal Precedents Drawer */}
        <div className="mt-3 grid grid-cols-1 lg:grid-cols-12 gap-4">
          
          {/* Left Column: Ruling & Restitution Amount */}
          <div className="lg:col-span-7 space-y-2">
            <div className="flex items-center space-x-2">
              <span className={`px-2.5 py-1 rounded text-xs font-mono font-bold border ${
                judge.verdict_status === 'REEMBOLSO_TOTAL_ORDENADO'
                  ? 'bg-[#182618] text-emerald-300 border-[#2b4c2b]'
                  : 'bg-[#261818] text-red-300 border-[#4c2b2b]'
              }`}>
                {judge.verdict_status.replace(/_/g, ' ')}
              </span>
              <span className="text-xs font-mono text-zinc-400">
                Monto Restituible: <strong className="text-white">${courtData.disputed_amount.toLocaleString('es-MX', { minimumFractionDigits: 2 })} {courtData.currency}</strong>
              </span>
            </div>

            <p className="text-xs font-mono text-zinc-300 bg-[#07080a] p-3 rounded-lg border border-[#161822] leading-relaxed select-text">
              {judge.formal_ruling_text}
            </p>

            <div className="flex items-center space-x-4 text-[11px] font-mono text-zinc-400 pt-1">
              <span>Interés Legal Moratorio (Art. 362 CCom): <strong className="text-emerald-400">{judge.moratory_interest_rate_annual}% anual</strong></span>
              <span>Intereses Devengados (90d): <strong className="text-emerald-400">${judge.moratory_interest_accrued.toLocaleString('es-MX', { minimumFractionDigits: 2 })} {courtData.currency}</strong></span>
            </div>
          </div>

          {/* Right Column: Statutory Precedents */}
          <div className="lg:col-span-5 bg-[#090a0d] p-3 rounded-lg border border-[#181a24] space-y-2">
            <div className="flex items-center space-x-1.5 text-xs font-mono font-bold text-zinc-300">
              <Award className="w-3.5 h-3.5 text-[#d4af37]" />
              <span>Jurisprudencia & Precedentes Invocados</span>
            </div>

            <ul className="space-y-1.5 text-[11px] font-mono text-zinc-400">
              {judge.statutory_precedents.map((prec, pIdx) => (
                <li key={pIdx} className="flex items-start space-x-1.5">
                  <span className="text-[#d4af37] font-bold">§</span>
                  <span className="leading-snug select-text">{prec}</span>
                </li>
              ))}
            </ul>
          </div>

        </div>

      </div>

      {/* ADVERSARIAL STAGE: PROSECUTOR (LEFT) vs DEFENDER (RIGHT) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* PROSECUTOR: RETAILER AUDITOR (CRIMSON/RED ACCENT) */}
        <div className="bg-[#120d0f] border border-[#2b171c] rounded-xl p-4 space-y-3 shadow-tactile">
          <div className="flex items-center justify-between pb-2 border-b border-[#231216]">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-lg bg-[#271015] border border-[#441a21] text-red-400">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-red-400 font-bold block">
                  Parte Acusadora (Retailer)
                </span>
                <h4 className="text-xs font-bold text-white font-mono">
                  {prosecutor.organization}
                </h4>
              </div>
            </div>

            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#291116] text-red-300 border border-[#491a22]">
              {prosecutor.claim_status}
            </span>
          </div>

          <div className="space-y-1">
            <span className="text-[11px] font-mono text-zinc-500 uppercase tracking-wider block font-bold">
              Postura Procesal del Retailer:
            </span>
            <p className="text-xs font-mono text-zinc-300 leading-relaxed bg-[#0b0809] p-2.5 rounded border border-[#1e0f12] select-text">
              {prosecutor.allegation_summary}
            </p>
          </div>

          <div className="p-2 bg-[#160e11] rounded border border-[#27151a] flex items-center justify-between text-xs font-mono">
            <span className="text-zinc-400">Deducción Exigida:</span>
            <strong className="text-red-400">${courtData.disputed_amount.toLocaleString('es-MX', { minimumFractionDigits: 2 })} {courtData.currency}</strong>
          </div>
        </div>

        {/* DEFENSE COUNSEL: SUPPLYMIND ADVOCATE (EMERALD/GOLD ACCENT) */}
        <div className="bg-[#0c1310] border border-[#16291e] rounded-xl p-4 space-y-3 shadow-tactile">
          <div className="flex items-center justify-between pb-2 border-b border-[#122319]">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-lg bg-[#11271b] border border-[#1c472f] text-emerald-400">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 font-bold block">
                  Defensa Técnica (SupplyMind AI)
                </span>
                <h4 className="text-xs font-bold text-white font-mono">
                  {defense.organization}
                </h4>
              </div>
            </div>

            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#142e1f] text-emerald-300 border border-[#214f33]">
              {defense.plea_status}
            </span>
          </div>

          <div className="space-y-1">
            <span className="text-[11px] font-mono text-zinc-500 uppercase tracking-wider block font-bold">
              Estrategia Probatoria & Defensiva:
            </span>
            <p className="text-xs font-mono text-zinc-300 leading-relaxed bg-[#070d0a] p-2.5 rounded border border-[#101e16] select-text">
              {defense.defense_summary}
            </p>
          </div>

          <div className="p-2 bg-[#0e1a14] rounded border border-[#193324] flex items-center justify-between text-xs font-mono">
            <span className="text-zinc-400">Monto Acreditado / Reclamado:</span>
            <strong className="text-emerald-400">${courtData.disputed_amount.toLocaleString('es-MX', { minimumFractionDigits: 2 })} {courtData.currency}</strong>
          </div>
        </div>

      </div>

      {/* DIALECTIC DEBATE ROUNDS (CAREO PASO A PASO) */}
      <div className="bg-[#0e0f14] border border-[#1e2029] rounded-xl p-4 space-y-3 shadow-tactile">
        
        {/* Header and Round Navigation Tabs */}
        <div className="flex items-center justify-between pb-2 border-b border-[#181a24]">
          <div className="flex items-center space-x-2 font-mono text-xs font-bold text-white">
            <Layers className="w-4 h-4 text-[#d4af37]" />
            <span>Careo Dialéctico por Rondas ({rounds.length} Fases)</span>
          </div>

          <div className="flex items-center space-x-1 font-mono text-xs">
            {rounds.map((r, rIdx) => (
              <button
                key={rIdx}
                onClick={() => setActiveRoundIdx(rIdx)}
                className={`px-3 py-1 rounded transition-all flex items-center space-x-1.5 border ${
                  activeRoundIdx === rIdx
                    ? 'bg-[#221f14] text-[#eed98d] border-[#d4af37] font-bold shadow-tactile'
                    : 'bg-[#101117] text-zinc-400 hover:text-white border-[#1c1e28]'
                }`}
              >
                <span>Fase {r.round_number}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Active Round Stage */}
        <div className="bg-[#090a0d] border border-[#181a24] rounded-lg p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-white font-mono flex items-center space-x-2">
              <span className="text-[#d4af37]">Ronda {currentRound.round_number}:</span>
              <span>{currentRound.title}</span>
            </h4>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#14291c] text-emerald-300 border border-[#22482f]">
              Vencedor: {currentRound.round_winner}
            </span>
          </div>

          {/* Dialogue Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
            
            {/* Prosecutor Claim */}
            <div className="p-3 rounded-lg bg-[#160d0f] border border-[#2e151b] space-y-1.5">
              <div className="flex items-center space-x-1.5 text-red-400 font-bold text-[11px] uppercase">
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>Alegato del Retailer:</span>
              </div>
              <p className="text-zinc-200 leading-relaxed select-text">
                "{currentRound.prosecutor_claim}"
              </p>
            </div>

            {/* Defense Counter */}
            <div className="p-3 rounded-lg bg-[#0b1610] border border-[#153120] space-y-1.5">
              <div className="flex items-center space-x-1.5 text-emerald-400 font-bold text-[11px] uppercase">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Réplica de la Defensa:</span>
              </div>
              <p className="text-zinc-200 leading-relaxed select-text">
                "{currentRound.defense_counter}"
              </p>
            </div>

          </div>

          {/* Exhibited Evidence & Judicial Note */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1 font-mono text-xs">
            <div className="p-2.5 bg-[#0e1017] rounded border border-[#1b1f2e] flex items-center space-x-2">
              <FileText className="w-4 h-4 text-cyan-400 shrink-0" />
              <div>
                <span className="text-[10px] text-zinc-500 uppercase block font-bold">Prueba Desahogada:</span>
                <span className="text-zinc-300 font-bold">{currentRound.exhibited_evidence}</span>
              </div>
            </div>

            <div className="p-2.5 bg-[#17140c] rounded border border-[#322915] flex items-center space-x-2">
              <Info className="w-4 h-4 text-[#d4af37] shrink-0" />
              <div>
                <span className="text-[10px] text-zinc-500 uppercase block font-bold">Criterio del Magistrado:</span>
                <span className="text-zinc-300 font-bold">{currentRound.judicial_comment}</span>
              </div>
            </div>
          </div>

        </div>

      </div>

      {/* MCTS STRATEGY & MONTE CARLO TREE SEARCH RESULT */}
      {mcts_strategy && (
        <div className="bg-[#0e0f14] border border-[#1e2029] rounded-xl p-4 space-y-3 shadow-tactile">
          <div className="flex items-center justify-between pb-2 border-b border-[#181a24]">
            <div className="flex items-center space-x-2">
              <div className="p-1.5 rounded bg-[#181a24] text-[#d4af37]">
                <TrendingUp className="w-4 h-4" />
              </div>
              <h4 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                Estrategia Óptima Recomendada por Árbol Monte Carlo (MCTS B2B)
              </h4>
            </div>

            <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[#1f1d14] text-[#eed98d] border border-[#d4af37]/40">
              Ruta: {mcts_strategy.recommended_trajectory}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
            <div className="p-2.5 bg-[#07080a] rounded border border-[#181a24]">
              <span className="text-[10px] text-zinc-500 uppercase block">Cobro Neto Proyectado</span>
              <strong className="text-emerald-400 text-sm">
                ${mcts_strategy.expected_net_payoff.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
              </strong>
            </div>

            <div className="p-2.5 bg-[#07080a] rounded border border-[#181a24]">
              <span className="text-[10px] text-zinc-500 uppercase block">Duración Estimada</span>
              <strong className="text-white text-sm">{mcts_strategy.projected_duration_days} días</strong>
            </div>

            <div className="p-2.5 bg-[#07080a] rounded border border-[#181a24]">
              <span className="text-[10px] text-zinc-500 uppercase block">Preservación de Cuenta</span>
              <strong className="text-cyan-400 text-sm">{(mcts_strategy.relationship_retention_index * 100).toFixed(0)}%</strong>
            </div>

            <div className="p-2.5 bg-[#07080a] rounded border border-[#181a24]">
              <span className="text-[10px] text-zinc-500 uppercase block">Confianza Algorítmica</span>
              <strong className="text-[#eed98d] text-sm">{(mcts_strategy.confidence_score * 100).toFixed(1)}%</strong>
            </div>
          </div>

          <p className="text-xs font-mono text-zinc-400 bg-[#07080a] p-3 rounded border border-[#181a24] select-text">
            {mcts_strategy.executive_synthesis}
          </p>
        </div>
      )}

      {/* Generated Dossier Preview Modal Prompt if just created */}
      {generatedDossierData && (
        <div className="p-4 rounded-xl bg-[#1b1526] border border-[#3e2e5c] font-mono text-xs flex items-center justify-between gap-3 animate-in fade-in duration-150">
          <div className="space-x-2 flex items-center">
            <FileText className="w-5 h-5 text-purple-400 shrink-0" />
            <div>
              <span className="text-purple-200 font-bold block">
                Dossier Arbitral ICC Foliado Compilado ({generatedDossierData.dossier_id})
              </span>
              <span className="text-zinc-400 text-[11px]">
                {generatedDossierData.total_evidence_items} pruebas periciales foliadas con hash SHA-256 inalterable.
              </span>
            </div>
          </div>

          <button
            onClick={() => {
              const blob = new Blob([JSON.stringify(generatedDossierData, null, 2)], { type: 'application/json' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `dossier_arbitral_${caseId}.json`;
              a.click();
            }}
            className="px-3 py-1.5 rounded bg-[#2e2049] hover:bg-[#3d2c5e] text-purple-200 hover:text-white border border-purple-500/40 flex items-center space-x-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Descargar JSON Pericial</span>
          </button>
        </div>
      )}

    </div>
  );
}
