import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import {
  Clock,
  ShieldAlert,
  ShieldCheck,
  Landmark,
  FileCheck2,
  HeartHandshake,
  Wrench,
  AlertTriangle,
  CheckCircle2,
  Download,
  FileText,
  RefreshCw,
  Copy,
  Check,
  Building2,
  Truck,
  Cpu,
  BadgeDollarSign,
  Lock
} from 'lucide-react';

const URGENCY_BADGES = {
  CRITICAL_EXPIRED: {
    label: 'VENCIDO / CRÍTICO (≤ 0d)',
    bg: 'bg-rose-950/60 border-rose-500/50 text-rose-300',
    dot: 'bg-rose-500'
  },
  HIGH_IMMINENT: {
    label: 'INMINENTE (1 - 15d)',
    bg: 'bg-amber-950/60 border-amber-500/50 text-amber-300',
    dot: 'bg-amber-400'
  },
  MEDIUM_ATTENTION: {
    label: 'ATENCIÓN (16 - 30d)',
    bg: 'bg-yellow-950/50 border-yellow-600/40 text-yellow-200',
    dot: 'bg-yellow-400'
  },
  LOW_HEALTHY: {
    label: 'SALUDABLE (> 30d)',
    bg: 'bg-emerald-950/50 border-emerald-500/40 text-emerald-300',
    dot: 'bg-emerald-400'
  }
};

const MODULATION_BADGES = {
  DIPLOMATIC_PRESERVATION: {
    label: 'DIPLOMATIC PRESERVATION (RHI > 80)',
    style: 'bg-emerald-950/50 border-emerald-500/40 text-emerald-300'
  },
  FIRM_COMMERCIAL: {
    label: 'FIRM COMMERCIAL 50/50 (RHI 50-80)',
    style: 'bg-blue-950/50 border-blue-500/40 text-blue-300'
  },
  ASSERTIVE_LITIGIOUS: {
    label: 'ASSERTIVE LITIGIOUS (RHI < 50)',
    style: 'bg-rose-950/60 border-rose-500/50 text-rose-300'
  }
};

export default function ClosurePreventionView({ caseId = 'case_005_amazon_shortage' }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Sprint 7.1: SLA Watchdog
  const [slaStatus, setSlaStatus] = useState(null);
  const [interruptionNotice, setInterruptionNotice] = useState(null);
  const [fleetSla, setFleetSla] = useState(null);
  const [issuingNotice, setIssuingNotice] = useState(false);

  // Sprint 7.2: Conciliación Bancaria 3-Way EDI 820
  const [reconciliationData, setReconciliationData] = useState(null);
  const [rawEdi820, setRawEdi820] = useState('');
  const [reconciling, setReconciling] = useState(false);

  // Sprint 7.3: Salud Relacional RHI
  const [rhiReport, setRhiReport] = useState(null);

  // Sprint 7.4: RCA & CAPA
  const [rcaReport, setRcaReport] = useState(null);
  const [capaTicket, setCapaTicket] = useState(null);
  const [generatingCapa, setGeneratingCapa] = useState(false);

  const [activeModalDoc, setActiveModalDoc] = useState(null); // { title, hash, markdown, filename }
  const [copiedHash, setCopiedHash] = useState(false);

  const loadAllPhase7Data = async () => {
    setLoading(true);
    setError(null);
    try {
      const [slaRes, fleetRes, ediRes, recRes, rhiRes, rcaRes, capaRes] = await Promise.all([
        apiClient.getCaseSlaStatus(caseId),
        apiClient.getSlaFleetMonitor(12),
        apiClient.getCaseEdi820(caseId),
        apiClient.reconcileThreeWaySettlement(caseId),
        apiClient.getRelationalHealthIndex(caseId),
        apiClient.getLongitudinalRcaReport(50),
        apiClient.getCapaTicket(caseId)
      ]);

      setSlaStatus(slaRes.sla_status);
      setInterruptionNotice(slaRes.interruption_notice);
      setFleetSla(fleetRes.fleet);
      setRawEdi820(ediRes.raw_edi820 || '');
      setReconciliationData(recRes);
      setRhiReport(rhiRes.relational_health);
      setRcaReport(rcaRes.rca_report);
      setCapaTicket(capaRes.capa_ticket);
    } catch (err) {
      setError(err.message || 'Error al cargar consola de Tesorería, SLA y Prevención CAPA');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllPhase7Data();
  }, [caseId]);

  const handleIssueInterruptionNotice = async () => {
    setIssuingNotice(true);
    try {
      const res = await apiClient.interruptCasePrescription(caseId, {
        operator_name: 'Dirección Jurídica & Tesorería Corporativa B2B'
      });
      setSlaStatus(res.sla_status);
      setInterruptionNotice(res.notice);
      const fleetRes = await apiClient.getSlaFleetMonitor(12);
      setFleetSla(fleetRes.fleet);
    } catch (err) {
      alert(`Error al emitir notificación Art. 1041 CCom: ${err.message}`);
    } finally {
      setIssuingNotice(false);
    }
  };

  const handleReconcileEdi820 = async () => {
    setReconciling(true);
    try {
      const res = await apiClient.reconcileThreeWaySettlement(caseId, {
        raw_remittance_content: rawEdi820
      });
      setReconciliationData(res);
    } catch (err) {
      alert(`Error al conciliar remesa EDI 820: ${err.message}`);
    } finally {
      setReconciling(false);
    }
  };

  const handleRegenerateCapa = async (deptCode = null) => {
    setGeneratingCapa(true);
    try {
      const res = await apiClient.generateCapaTicket(caseId, {
        override_department: deptCode
      });
      setCapaTicket(res.capa_ticket);
    } catch (err) {
      alert(`Error al generar ticket CAPA: ${err.message}`);
    } finally {
      setGeneratingCapa(false);
    }
  };

  const handleDownloadMarkdown = (content, filename) => {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyText = (txt) => {
    navigator.clipboard.writeText(txt);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-20 space-y-4">
        <Landmark className="w-11 h-11 text-[#d4af37] animate-pulse" />
        <p className="text-zinc-400 font-mono text-xs uppercase tracking-widest">
          Sincronizando Reloj de Prescripción SLA, Remesas EDI 820 y Motor Preventivo CAPA...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 bg-rose-950/20 border border-rose-800/40 rounded-xl m-4 text-center">
        <AlertTriangle className="w-10 h-10 text-rose-400 mx-auto mb-3" />
        <h3 className="text-rose-200 font-bold mb-1">Error en Módulo de Tesorería & Prevención</h3>
        <p className="text-zinc-400 text-xs font-mono">{error}</p>
        <button
          onClick={loadAllPhase7Data}
          className="mt-4 px-4 py-2 bg-rose-900/60 hover:bg-rose-900 text-white rounded text-xs font-mono"
        >
          Reintentar
        </button>
      </div>
    );
  }

  const urgencyMeta = URGENCY_BADGES[slaStatus?.urgency_level] || URGENCY_BADGES.LOW_HEALTHY;
  const modMeta = MODULATION_BADGES[rhiReport?.modulation_mode] || MODULATION_BADGES.FIRM_COMMERCIAL;
  const matchInfo = reconciliationData?.three_way_match;
  const certInfo = reconciliationData?.clearance_certificate;
  const remitInfo = reconciliationData?.remittance;

  return (
    <div className="space-y-6 p-4 sm:p-6 max-w-7xl mx-auto animate-in fade-in duration-200">

      {/* ENCABEZADO EJECUTIVO FASE 7 */}
      <div className="bg-[#0b0c10] border border-[#1e2029] rounded-2xl p-5 shadow-2xl flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 bg-gradient-to-br from-[#d4af37]/20 to-[#997b1e]/10 border border-[#d4af37]/40 rounded-xl">
            <Landmark className="w-6 h-6 text-[#eed98d]" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-base sm:text-lg font-bold text-white tracking-tight">
                Tesorería Order-to-Cash (EDI 820), Prescripción SLA & Prevención CAPA
              </h2>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#181a24] text-[#eed98d] border border-[#d4af37]/30 font-mono">
                Fase 7 • Closed-Loop B2B
              </span>
            </div>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">
              Expediente Activo: <span className="text-white font-semibold">{caseId}</span> | Contraparte: <span className="text-[#eed98d]">{slaStatus?.retailer_name}</span>
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <div className={`px-3 py-1.5 rounded-xl border text-xs font-mono flex items-center gap-2 ${urgencyMeta.bg}`}>
            <span className={`w-2 h-2 rounded-full ${urgencyMeta.dot} animate-pulse`} />
            <span>SLA DTP: <strong>{slaStatus?.days_to_expiration} días</strong> ({urgencyMeta.label})</span>
          </div>

          <div className={`px-3 py-1.5 rounded-xl border text-xs font-mono flex items-center gap-2 ${modMeta.style}`}>
            <HeartHandshake className="w-3.5 h-3.5" />
            <span>RHI: <strong>{rhiReport?.rhi_score}/100</strong></span>
          </div>
        </div>
      </div>

      {/* FILA 1: US-709 WATCHDOG DE PRESCRIPCIÓN SLA (COL 7) + GUARDRAIL SALUD RELACIONAL RHI (COL 5) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">

        {/* SPRINT 7.1: WATCHDOG DE PRESCRIPCIÓN LEGAL & CADUCIDAD SLA */}
        <div className="lg:col-span-7 bg-[#0b0c10] border border-[#1e2029] rounded-2xl p-5 shadow-xl flex flex-col justify-between space-y-4">
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#181a24] gap-2">
              <div className="flex items-center space-x-2.5">
                <Clock className="w-5 h-5 text-amber-400" />
                <div>
                  <h3 className="text-sm font-bold text-white">
                    Watchdog de Prescripción Legal & Ventana SLA de Portal
                  </h3>
                  <p className="text-[11px] text-zinc-400 font-mono">
                    {slaStatus?.legal_basis}
                  </p>
                </div>
              </div>

              <button
                onClick={handleIssueInterruptionNotice}
                disabled={issuingNotice}
                className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-[#d4af37] to-[#b39023] hover:from-[#eed98d] hover:to-[#d4af37] text-black font-bold text-xs font-mono transition-all flex items-center space-x-1.5 shadow-tactile shrink-0 disabled:opacity-50"
              >
                <ShieldAlert className="w-4 h-4" />
                <span>
                  {issuingNotice
                    ? 'Sellando Art. 1041...'
                    : slaStatus?.is_prescription_interrupted
                    ? 'Re-Emitir Interrupción Art. 1041 CCom'
                    : 'Emitir Notificación de Interrupción Art. 1041 CCom'}
                </span>
              </button>
            </div>

            {/* KPIs del Reloj de Prescripción */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4">
              <div className="p-3 bg-[#111218] border border-[#1e2029] rounded-xl">
                <span className="text-[10px] text-zinc-500 font-mono block">Ventana SLA Retailer:</span>
                <span className="text-base font-bold text-white font-mono">
                  {slaStatus?.contractual_sla_days} días
                </span>
              </div>
              <div className="p-3 bg-[#111218] border border-[#1e2029] rounded-xl">
                <span className="text-[10px] text-zinc-500 font-mono block">Días Transcurridos:</span>
                <span className="text-base font-bold text-zinc-300 font-mono">
                  {slaStatus?.elapsed_days} días
                </span>
              </div>
              <div className="p-3 bg-[#111218] border border-[#1e2029] rounded-xl">
                <span className="text-[10px] text-zinc-500 font-mono block">Days-to-Prescription:</span>
                <span className={`text-base font-bold font-mono ${
                  slaStatus?.days_to_expiration <= 0 ? 'text-rose-400' :
                  slaStatus?.days_to_expiration <= 15 ? 'text-amber-400' : 'text-emerald-400'
                }`}>
                  {slaStatus?.days_to_expiration} días
                </span>
              </div>
              <div className="p-3 bg-[#111218] border border-[#1e2029] rounded-xl">
                <span className="text-[10px] text-zinc-500 font-mono block">Saldo en Riesgo:</span>
                <span className="text-base font-bold text-[#eed98d] font-mono">
                  ${slaStatus?.claimable_at_risk?.toLocaleString()} USD
                </span>
              </div>
            </div>

            {/* Estado de Interrupción Art. 1041 CCom */}
            {slaStatus?.is_prescription_interrupted && interruptionNotice ? (
              <div className="p-3.5 bg-emerald-950/30 border border-emerald-500/40 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="flex items-start space-x-2.5">
                  <Lock className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="text-xs font-bold text-emerald-300 block">
                      Reloj de Prescripción Congelado (Art. 1041 Código de Comercio)
                    </span>
                    <span className="text-[11px] text-zinc-300 font-mono block mt-0.5">
                      Folio: <strong className="text-white">{interruptionNotice.notice_id}</strong> | Hash SHA-256: {interruptionNotice.forensic_hash_sha256?.slice(0, 18)}...
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => setActiveModalDoc({
                      title: `Notificación de Interrupción Art. 1041 CCom (${interruptionNotice.notice_id})`,
                      hash: interruptionNotice.forensic_hash_sha256,
                      markdown: interruptionNotice.notice_markdown,
                      filename: `aviso_1041_${caseId}.md`
                    })}
                    className="px-2.5 py-1.5 rounded-lg bg-emerald-900/60 hover:bg-emerald-800 text-white text-xs font-mono flex items-center space-x-1"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Ver Aviso</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-3.5 bg-[#12131c] border border-[#232638] rounded-xl text-xs text-zinc-300 font-mono">
                <strong className="text-[#eed98d]">Directriz Watchdog:</strong> {slaStatus?.recommended_immediate_action}
              </div>
            )}

            {/* Semáforo de Flota SLA */}
            {fleetSla && (
              <div className="mt-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-mono text-zinc-400 font-semibold">
                    Radar de Caducidad en Flota ({fleetSla.total_cases_monitored} expedientes auditados)
                  </span>
                  <span className="text-[11px] font-mono text-amber-300">
                    Exposición Inminente: ${fleetSla.imminent_or_expired_unprotected_usd?.toLocaleString()} USD
                  </span>
                </div>
                <div className="max-h-36 overflow-y-auto space-y-1.5 pr-1">
                  {(fleetSla.cases || []).slice(0, 6).map((fc) => {
                    const b = URGENCY_BADGES[fc.urgency_level] || URGENCY_BADGES.LOW_HEALTHY;
                    return (
                      <div key={fc.case_id} className="px-3 py-1.5 rounded-lg bg-[#101118] border border-[#1b1d29] flex items-center justify-between text-xs font-mono">
                        <div className="flex items-center space-x-2 truncate">
                          <span className={`w-2 h-2 rounded-full shrink-0 ${b.dot}`} />
                          <span className="text-zinc-200 font-semibold truncate">{fc.case_id}</span>
                          <span className="text-zinc-500 text-[10px] hidden sm:inline">({fc.retailer_name})</span>
                        </div>
                        <div className="flex items-center space-x-3 shrink-0">
                          <span className="text-zinc-400">${fc.claimable_at_risk?.toLocaleString()}</span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded border ${b.bg}`}>
                            {fc.is_prescription_interrupted ? 'CONGELADO 1041' : `${fc.days_to_expiration}d`}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* SPRINT 7.3: GUARDRAIL DE SALUD RELACIONAL (LTV & CHURN INDEX RHI) */}
        <div className="lg:col-span-5 bg-[#0b0c10] border border-[#1e2029] rounded-2xl p-5 shadow-xl flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#181a24]">
              <div className="flex items-center space-x-2.5">
                <HeartHandshake className="w-5 h-5 text-emerald-400" />
                <div>
                  <h3 className="text-sm font-bold text-white">Guardrail de Salud Relacional (RHI)</h3>
                  <p className="text-[11px] text-zinc-400 font-mono">
                    LTV, Share of Wallet & Modulación Dinámica (Sprint 7.3)
                  </p>
                </div>
              </div>
              <span className="text-lg font-bold font-mono text-[#eed98d]">
                {rhiReport?.rhi_score}/100
              </span>
            </div>

            {/* Barra de RHI */}
            <div className="my-3">
              <div className="w-full h-2.5 bg-[#161822] rounded-full overflow-hidden border border-[#222536]">
                <div
                  className="h-full bg-gradient-to-r from-rose-500 via-amber-400 to-emerald-400 transition-all duration-500"
                  style={{ width: `${rhiReport?.rhi_score || 75}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] font-mono text-zinc-500 mt-1">
                <span>0 (Litigioso &lt;50)</span>
                <span>50 (Firme 50-80)</span>
                <span>80+ (Diplomático LTV)</span>
              </div>
            </div>

            {/* 4 Factores Ponderados US-705 */}
            <div className="grid grid-cols-2 gap-2.5 my-3 text-xs font-mono">
              <div className="p-2.5 bg-[#111218] border border-[#1e2029] rounded-xl">
                <span className="text-[10px] text-zinc-500 block">1. LTV Anual Cuenta:</span>
                <span className="text-sm font-bold text-white">
                  ${(rhiReport?.ltv_annual_usd || 0).toLocaleString()}
                </span>
                <span className="text-[10px] text-emerald-400 block">+{rhiReport?.ltv_score_component} / 30 pts</span>
              </div>
              <div className="p-2.5 bg-[#111218] border border-[#1e2029] rounded-xl">
                <span className="text-[10px] text-zinc-500 block">2. Share of Wallet:</span>
                <span className="text-sm font-bold text-white">
                  {rhiReport?.share_of_wallet_pct}%
                </span>
                <span className="text-[10px] text-emerald-400 block">+{rhiReport?.wallet_score_component} / 25 pts</span>
              </div>
              <div className="p-2.5 bg-[#111218] border border-[#1e2029] rounded-xl">
                <span className="text-[10px] text-zinc-500 block">3. Margen Bruto SKU:</span>
                <span className="text-sm font-bold text-white">
                  {rhiReport?.gross_margin_pct}%
                </span>
                <span className="text-[10px] text-emerald-400 block">+{rhiReport?.margin_score_component} / 25 pts</span>
              </div>
              <div className="p-2.5 bg-[#111218] border border-[#1e2029] rounded-xl">
                <span className="text-[10px] text-zinc-500 block">4. Reciprocidad:</span>
                <span className="text-sm font-bold text-white">
                  {rhiReport?.account_tier}
                </span>
                <span className="text-[10px] text-emerald-400 block">+{rhiReport?.reciprocity_score_component} / 20 pts</span>
              </div>
            </div>

            {/* Directriz de Modulación Táctica US-706 */}
            <div className="p-3 bg-[#11131d] border border-[#222638] rounded-xl space-y-1.5 text-xs">
              <div className="flex items-center justify-between font-mono">
                <span className="text-zinc-400 text-[11px]">Modo de Agresividad:</span>
                <span className="text-[#eed98d] font-bold text-[11px]">{rhiReport?.modulation_mode}</span>
              </div>
              <p className="text-zinc-300 text-xs leading-relaxed">
                {rhiReport?.tone_directive}
              </p>
              <p className="text-[11px] text-emerald-300 font-mono pt-1 border-t border-[#1c2030]">
                💡 Trade-off: {rhiReport?.commercial_tradeoff_proposal}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* FILA 2: SPRINT 7.2 CONCILIACIÓN DE REMESAS BANCARIAS EDI 820 & CIERRE 3-WAY ORDER-TO-CASH */}
      <div className="bg-[#0b0c10] border border-[#1e2029] rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#181a24] gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-emerald-950/50 border border-emerald-500/40 rounded-xl">
              <FileCheck2 className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                Conciliación de Remesas Bancarias EDI 820 & Empatador 3-Way Order-to-Cash
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700/40 font-mono">
                  MAE = ${matchInfo?.mae_precision?.toFixed(2) || '0.00'} (Decimal Exact)
                </span>
              </h3>
              <p className="text-xs text-zinc-400 font-mono">
                Verificación determinística: Factura Original − Deducción Retailer + Monto Recuperado Convenio = Depósito Neto Bancario
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleReconcileEdi820}
              disabled={reconciling}
              className="px-3.5 py-2 rounded-xl bg-emerald-800/70 hover:bg-emerald-700 text-white text-xs font-mono font-bold transition-all flex items-center space-x-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${reconciling ? 'animate-spin' : ''}`} />
              <span>{reconciling ? 'Conciliando...' : 'Ejecutar Match 3-Way'}</span>
            </button>

            {certInfo && (
              <button
                onClick={() => setActiveModalDoc({
                  title: `Certificado de Cierre y Liquidación de Cartera (${certInfo.certificate_id})`,
                  hash: certInfo.zkp_clearance_hash_sha256,
                  markdown: certInfo.certificate_markdown,
                  filename: `certificado_cierre_${caseId}.md`
                })}
                className="px-3.5 py-2 rounded-xl bg-[#181a24] hover:bg-[#222536] border border-[#d4af37]/40 text-[#eed98d] text-xs font-mono font-bold flex items-center space-x-1.5"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Certificado de Liquidación ($0.00)</span>
              </button>
            )}
          </div>
        </div>

        {/* Ecuación Visual 3-Way Settlement Matcher */}
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 items-center font-mono">
          <div className="p-3.5 bg-[#111218] border border-[#1e2029] rounded-xl">
            <span className="text-[10px] text-zinc-500 block">1. Factura Original (+)</span>
            <span className="text-base font-bold text-white">
              ${matchInfo?.original_invoice_amount?.toLocaleString()}
            </span>
            <span className="text-[10px] text-zinc-400 block mt-0.5">{matchInfo?.invoice_id}</span>
          </div>

          <div className="p-3.5 bg-[#111218] border border-rose-900/40 rounded-xl">
            <span className="text-[10px] text-zinc-500 block">2. Deducción Retailer (−)</span>
            <span className="text-base font-bold text-rose-400">
              -${matchInfo?.total_disputed_deduction?.toLocaleString()}
            </span>
            <span className="text-[10px] text-zinc-400 block mt-0.5">
              NC Aplicada: ${matchInfo?.justified_credit_memo?.toLocaleString()}
            </span>
          </div>

          <div className="p-3.5 bg-[#111218] border border-blue-900/40 rounded-xl">
            <span className="text-[10px] text-zinc-500 block">3. Recuperado Convenio (+)</span>
            <span className="text-base font-bold text-blue-400">
              +${matchInfo?.agreed_settlement_recovery?.toLocaleString()}
            </span>
            <span className="text-[10px] text-zinc-400 block mt-0.5">Restitución en Remesa</span>
          </div>

          <div className="p-3.5 bg-[#111218] border border-emerald-700/40 rounded-xl">
            <span className="text-[10px] text-zinc-500 block">4. Depósito Neto Banco (=)</span>
            <span className="text-base font-bold text-emerald-400">
              ${matchInfo?.actual_bank_remittance_cash?.toLocaleString()}
            </span>
            <span className="text-[10px] text-zinc-400 block mt-0.5">TRN: {remitInfo?.bank_reference_trn}</span>
          </div>

          <div className="p-3.5 bg-emerald-950/30 border border-emerald-500/50 rounded-xl">
            <span className="text-[10px] text-emerald-300 block">5. Saldo Insoluto Cartera</span>
            <span className="text-base font-bold text-emerald-300 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              ${certInfo?.final_open_balance?.toFixed(2) || '0.00'} USD
            </span>
            <span className="text-[10px] text-emerald-400 block mt-0.5">{matchInfo?.match_status}</span>
          </div>
        </div>

        {/* Visor Editable de Trama EDI 820 */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 pt-2">
          <div className="lg:col-span-7">
            <label className="text-[11px] font-mono text-zinc-400 font-semibold block mb-1.5">
              Trama ANSI X12 EDI 820 (Payment Order / Remittance Advice) — Editable para Auditoría:
            </label>
            <textarea
              value={rawEdi820}
              onChange={(e) => setRawEdi820(e.target.value)}
              rows={5}
              className="w-full p-3 rounded-xl bg-[#08090d] border border-[#1a1c26] font-mono text-[11px] text-emerald-300 focus:outline-none focus:border-[#d4af37]"
            />
          </div>
          <div className="lg:col-span-5 flex flex-col justify-between p-3.5 bg-[#0e1017] border border-[#1c202e] rounded-xl font-mono text-xs">
            <div className="space-y-1.5">
              <span className="text-[11px] text-[#eed98d] font-bold block">
                Resumen de Liquidación Order-to-Cash (NIF C-3)
              </span>
              <p className="text-[11px] text-zinc-300 leading-relaxed">
                {matchInfo?.formula_verification_str}
              </p>
              <div className="pt-2 border-t border-[#1b1e2b] text-[11px] text-zinc-400 space-y-1">
                <div>Folio Certificado: <span className="text-white">{certInfo?.certificate_id}</span></div>
                <div>Pagador EDI 820: <span className="text-white">{remitInfo?.payer_name}</span></div>
                <div>Hash ZKP Cierre: <span className="text-emerald-400">{certInfo?.zkp_clearance_hash_sha256?.slice(0, 24)}...</span></div>
              </div>
            </div>
            {certInfo && (
              <button
                onClick={() => handleDownloadMarkdown(certInfo.certificate_markdown, `certificado_cierre_${caseId}.md`)}
                className="mt-3 w-full py-1.5 px-3 rounded-lg bg-[#161925] hover:bg-[#1e2233] border border-[#2a2f45] text-zinc-200 text-xs flex items-center justify-center space-x-1.5"
              >
                <Download className="w-3.5 h-3.5 text-[#eed98d]" />
                <span>Descargar Certificado de Cierre (.MD)</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* FILA 3: US-710 INTELIGENCIA PREVENTIVA DE CAUSA RAÍZ (RCA) & BANCO DE ACCIONES CAPA */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">

        {/* LADO IZQUIERDO: RCA LONGITUDINAL POR DEPARTAMENTO INTERNO (COL 6) */}
        <div className="lg:col-span-6 bg-[#0b0c10] border border-[#1e2029] rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#181a24]">
            <div className="flex items-center space-x-2.5">
              <Wrench className="w-5 h-5 text-cyan-400" />
              <div>
                <h3 className="text-sm font-bold text-white">
                  Análisis Longitudinal de Causa Raíz (RCA — {rcaReport?.total_cases_analyzed || 50} Casos)
                </h3>
                <p className="text-[11px] text-zinc-400 font-mono">
                  Atribución de fugas preventivas por departamento interno del proveedor (US-707)
                </p>
              </div>
            </div>
            <span className="text-xs font-mono text-rose-400 font-bold">
              Fuga Prevenible: ${rcaReport?.total_preventable_leakage_usd?.toLocaleString()} USD
            </span>
          </div>

          <div className="space-y-3">
            {(rcaReport?.department_attributions || []).map((dept) => {
              const isSelectedCaseDept = capaTicket?.department_code === dept.department_code;
              return (
                <div
                  key={dept.department_code}
                  className={`p-3.5 rounded-xl border transition-all ${
                    isSelectedCaseDept
                      ? 'bg-[#121624] border-cyan-500/50 shadow-md'
                      : 'bg-[#101118] border-[#1d202d]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-white">{dept.department_name}</span>
                        {isSelectedCaseDept && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-700/40 font-mono">
                            Causa Raíz Caso Actual
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] text-zinc-400 font-mono block">
                        Responsable: {dept.responsible_role}
                      </span>
                    </div>
                    <div className="text-right font-mono">
                      <span className="text-sm font-bold text-[#eed98d] block">
                        ${dept.total_financial_leakage_usd?.toLocaleString()} USD
                      </span>
                      <span className="text-[10px] text-zinc-400">
                        {dept.incident_count} casos ({dept.leakage_share_pct}%)
                      </span>
                    </div>
                  </div>

                  <div className="w-full h-1.5 bg-[#1a1d29] rounded-full overflow-hidden my-2">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-500 to-[#d4af37]"
                      style={{ width: `${Math.min(100, dept.leakage_share_pct || 25)}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between pt-1 text-[11px] font-mono text-zinc-400">
                    <span className="truncate max-w-[72%]">{dept.primary_failure_modes?.[0]}</span>
                    <button
                      onClick={() => handleRegenerateCapa(dept.department_code)}
                      className="text-cyan-400 hover:text-cyan-300 underline shrink-0"
                    >
                      Emitir CAPA Depto.
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* LADO DERECHO: TICKET DE ACCIÓN CORRECTIVA Y PREVENTIVA CAPA (COL 6) */}
        <div className="lg:col-span-6 bg-[#0b0c10] border border-[#1e2029] rounded-2xl p-5 shadow-xl flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#181a24]">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-white">
                    Orden de Ingeniería Preventiva — Ticket {capaTicket?.ticket_id}
                  </h3>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-700/40 font-mono">
                    SLA {capaTicket?.sla_resolution_hours}h • {capaTicket?.severity}
                  </span>
                </div>
                <p className="text-[11px] text-zinc-400 font-mono mt-0.5">
                  Asignado a: <strong className="text-cyan-300">{capaTicket?.assigned_owner_role}</strong> ({capaTicket?.department_name})
                </p>
              </div>

              {capaTicket && (
                <button
                  onClick={() => handleDownloadMarkdown(capaTicket.markdown_content, `capa_${caseId}.md`)}
                  className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-cyan-700 to-blue-700 hover:from-cyan-600 hover:to-blue-600 text-white text-xs font-mono font-bold flex items-center space-x-1.5 shrink-0"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Descargar CAPA (.MD)</span>
                </button>
              )}
            </div>

            {/* Hallazgo y Acciones Correctivas */}
            <div className="my-3 p-3 bg-[#10121b] border border-[#1e2233] rounded-xl text-xs space-y-1.5">
              <span className="text-[10px] font-mono text-amber-400 uppercase font-bold block">
                Anomalía Operativa Detectada en {caseId}:
              </span>
              <p className="text-zinc-200 leading-relaxed">
                {capaTicket?.detected_anomaly_detail}
              </p>
            </div>

            <div className="space-y-2 my-3">
              <span className="text-[11px] font-mono text-zinc-400 font-semibold block">
                Plan de Acción Correctiva Inmediata (CAPA):
              </span>
              {(capaTicket?.corrective_actions || []).map((act, i) => (
                <div key={i} className="p-2.5 rounded-lg bg-[#111218] border border-[#1d202c] text-xs text-zinc-300 flex items-start space-x-2">
                  <span className="text-[#eed98d] font-mono font-bold shrink-0">{i + 1}.</span>
                  <span>{act}</span>
                </div>
              ))}
            </div>

            {/* Checklist Pre-Despacho */}
            <div className="space-y-1.5 mt-3">
              <span className="text-[11px] font-mono text-emerald-400 font-semibold block">
                Candado Pre-Despacho para Futuros Embarques:
              </span>
              {(capaTicket?.pre_dispatch_checklist || []).map((chk, idx) => (
                <div key={idx} className="px-3 py-1.5 rounded-lg bg-[#0d1312] border border-emerald-900/30 text-[11px] font-mono text-zinc-300">
                  {chk}
                </div>
              ))}
            </div>
          </div>

          <div className="pt-3 border-t border-[#181a24] flex items-center justify-between text-[11px] font-mono text-zinc-500">
            <span>Persistido en: reports/capa/capa_{caseId}.md</span>
            <button
              onClick={() => setActiveModalDoc({
                title: `Orden Preventiva ${capaTicket?.ticket_id}`,
                hash: capaTicket?.ticket_id,
                markdown: capaTicket?.markdown_content,
                filename: `capa_${caseId}.md`
              })}
              className="text-[#eed98d] hover:underline"
            >
              Ver Documento Completo →
            </button>
          </div>
        </div>
      </div>

      {/* MODAL UNIVERSAL DE DOCUMENTOS CERTIFICADOS FASE 7 */}
      {activeModalDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-150">
          <div className="bg-[#0b0c10] border border-[#d4af37]/40 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl">
            <div className="p-4 sm:p-5 border-b border-[#1e2029] flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <FileText className="w-5 h-5 text-[#eed98d]" />
                <h3 className="text-sm sm:text-base font-bold text-white">{activeModalDoc.title}</h3>
              </div>
              <button
                onClick={() => setActiveModalDoc(null)}
                className="text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-[#181a24] text-xs font-mono"
              >
                ✕ Cerrar
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-4 font-mono text-xs text-zinc-300">
              {activeModalDoc.hash && (
                <div className="p-3 bg-[#111218] border border-[#222432] rounded-xl flex items-center justify-between">
                  <div>
                    <span className="text-zinc-500 block text-[10px]">Identificador / Sello Forense SHA-256:</span>
                    <span className="text-emerald-400 font-bold break-all">{activeModalDoc.hash}</span>
                  </div>
                  <button
                    onClick={() => copyText(activeModalDoc.hash)}
                    className="px-2.5 py-1 bg-[#181a24] text-zinc-300 hover:text-white rounded text-[11px] shrink-0 ml-2 flex items-center gap-1"
                  >
                    {copiedHash ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedHash ? 'Copiado' : 'Copiar'}</span>
                  </button>
                </div>
              )}

              <div className="p-4 bg-[#08090d] border border-[#1a1c24] rounded-xl whitespace-pre-wrap font-sans text-xs text-zinc-200 leading-relaxed">
                {activeModalDoc.markdown}
              </div>
            </div>

            <div className="p-4 border-t border-[#1e2029] flex justify-end space-x-3 bg-[#0e0f14] rounded-b-2xl">
              <button
                onClick={() => handleDownloadMarkdown(activeModalDoc.markdown, activeModalDoc.filename)}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-[#d4af37] to-[#b39023] text-black font-bold text-xs font-mono flex items-center space-x-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Descargar {activeModalDoc.filename}</span>
              </button>
              <button
                onClick={() => setActiveModalDoc(null)}
                className="px-4 py-2 rounded-xl bg-[#181a24] hover:bg-[#222432] text-white text-xs font-mono"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
