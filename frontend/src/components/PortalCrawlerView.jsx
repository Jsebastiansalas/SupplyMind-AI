import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { 
  Globe, 
  Bot, 
  Play, 
  RotateCcw, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  ExternalLink, 
  Send, 
  ShieldCheck, 
  FileText, 
  ChevronRight,
  TrendingDown,
  Sparkles,
  Terminal,
  Layers
} from 'lucide-react';

export default function PortalCrawlerView() {
  const [portals, setPortals] = useState([]);
  const [selectedPortal, setSelectedPortal] = useState('WALMART_RETAIL_LINK');
  const [syncResult, setSyncResult] = useState(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [submittingDeductionId, setSubmittingDeductionId] = useState(null);
  const [submissionSuccessMap, setSubmissionSuccessMap] = useState({});

  // Cargar catálogo de portales al montar
  useEffect(() => {
    async function loadCatalog() {
      try {
        const res = await apiClient.getPortalCatalog();
        if (res && res.supported_portals) {
          setPortals(res.supported_portals);
        }
      } catch (err) {
        console.error('Error cargando portales:', err);
      }
    }
    loadCatalog();
    handleRunSync('WALMART_RETAIL_LINK');
  }, []);

  const handleRunSync = async (portalId = selectedPortal) => {
    setIsSyncing(true);
    try {
      const res = await apiClient.syncRetailerPortal({
        portal_type: portalId,
        max_items: 4
      });
      setSyncResult(res);
    } catch (err) {
      alert(`Error en sincronización: ${err.message}`);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleDisputeInPortal = async (deduction) => {
    setSubmittingDeductionId(deduction.deduction_id);
    try {
      const res = await apiClient.uploadPortalDispute({
        portal_type: deduction.portal_type,
        deduction_id: deduction.deduction_id,
        case_id: 'case_001',
        claimable_amount: parseFloat(deduction.amount)
      });
      setSubmissionSuccessMap(prev => ({
        ...prev,
        [deduction.deduction_id]: res
      }));
    } catch (err) {
      alert(`Error al cargar objeción en portal: ${err.message}`);
    } finally {
      setSubmittingDeductionId(null);
    }
  };

  return (
    <div className="space-y-4 font-sans text-zinc-200 animate-in fade-in duration-200">
      
      {/* Top Header Card */}
      <div className="bg-[#0e0f14] border border-[#1e2029] rounded-xl p-4 shadow-tactile flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-[#141b24] border border-[#1f3045] text-cyan-400">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-bold text-white font-mono tracking-tight">
                RPA Autónomo & Conector de Portales Retailer
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#14261d] text-emerald-300 border border-[#234b32]">
                Agente Desatendido 24/7
              </span>
            </div>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">
              Extracción nocturna automática de notas de débito y carga desatendida de apelaciones en Walmart, Amazon, Soriana y Liverpool.
            </p>
          </div>
        </div>

        {/* Action Button */}
        <button
          onClick={() => handleRunSync(selectedPortal)}
          disabled={isSyncing}
          className="btn-tactile px-4 py-2 rounded bg-[#10222b] hover:bg-[#16303d] border border-cyan-500/60 text-cyan-300 hover:text-white font-mono text-xs font-bold transition-all flex items-center space-x-2 shadow-tactile disabled:opacity-50"
        >
          <Play className={`w-3.5 h-3.5 fill-current ${isSyncing ? 'animate-spin' : ''}`} />
          <span>{isSyncing ? 'Sincronizando Portal...' : 'Ejecutar Bot de Cosecha'}</span>
        </button>
      </div>

      {/* Retailer Portals Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { id: 'WALMART_RETAIL_LINK', name: 'Walmart Retail Link / Luminate', country: 'México / USA', auth: 'SSO SAML2', color: 'border-blue-500/40 text-blue-400' },
          { id: 'AMAZON_VENDOR_CENTRAL', name: 'Amazon Vendor Central', country: 'USA / Global', auth: 'OAuth2 Cognito', color: 'border-amber-500/40 text-amber-400' },
          { id: 'SORIANA_B2B', name: 'Soriana Portal Proveedores', country: 'México', auth: 'Certificado FIEL', color: 'border-emerald-500/40 text-emerald-400' },
          { id: 'LIVERPOOL_B2B', name: 'Liverpool Cuentas por Pagar', country: 'México', auth: 'Mutual TLS Bearer', color: 'border-purple-500/40 text-purple-400' }
        ].map((p) => {
          const isSelected = selectedPortal === p.id;
          return (
            <button
              key={p.id}
              onClick={() => {
                setSelectedPortal(p.id);
                handleRunSync(p.id);
              }}
              className={`p-3.5 rounded-xl text-left font-mono transition-all border ${
                isSelected
                  ? 'bg-[#141622] border-cyan-500 shadow-tactile'
                  : 'bg-[#0a0b0e] border-[#1a1c25] hover:border-zinc-700'
              }`}
            >
              <div className="flex items-center justify-between pb-1.5">
                <span className={`text-[10px] font-bold uppercase tracking-wider ${p.color}`}>
                  {p.country}
                </span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" title="Bot Activo en Línea" />
              </div>
              <h4 className="text-xs font-bold text-white leading-snug">{p.name}</h4>
              <span className="text-[10px] text-zinc-500 block mt-1">Auth: {p.auth}</span>
            </button>
          );
        })}
      </div>

      {/* Live Terminal Log Stream & Sync Results */}
      {syncResult && (
        <div className="space-y-4">
          
          {/* Terminal Log Banner */}
          <div className="bg-[#07080a] border border-[#161822] rounded-xl p-3.5 space-y-2 font-mono text-xs shadow-tactile">
            <div className="flex items-center justify-between pb-1.5 border-b border-[#141620]">
              <div className="flex items-center space-x-2 text-zinc-400">
                <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                <span className="font-bold text-white">Traza de Ejecución Desatendida ({syncResult.sync_id})</span>
              </div>
              <span className="text-[11px] text-zinc-500">{syncResult.execution_mode}</span>
            </div>

            <div className="space-y-1 text-zinc-300 max-h-28 overflow-y-auto font-mono text-[11px] select-text">
              {syncResult.log_trace.map((logLine, idx) => (
                <div key={idx} className="flex items-start space-x-2">
                  <span className="text-cyan-500">&gt;</span>
                  <span className="leading-relaxed">{logLine}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Harvested Deductions Table */}
          <div className="bg-[#0e0f14] border border-[#1e2029] rounded-xl p-4 space-y-3 shadow-tactile">
            <div className="flex items-center justify-between pb-2 border-b border-[#181a24]">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono font-bold text-white">
                  Deducciones Extraídas del Portal ({syncResult.total_deductions_found} partidas)
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#1f1d14] text-[#eed98d] border border-[#d4af37]/40">
                  Volumen en Riesgo: ${parseFloat(syncResult.total_disputed_amount).toLocaleString('es-MX', { minimumFractionDigits: 2 })} {syncResult.currency}
                </span>
              </div>

              <span className="text-xs font-mono text-zinc-500">
                {syncResult.retailer_name}
              </span>
            </div>

            <div className="overflow-x-auto rounded-lg border border-[#161822]">
              <table className="w-full text-left font-mono text-xs">
                <thead className="bg-[#10121a] text-zinc-400 uppercase text-[10px] tracking-wider border-b border-[#1c1e2c]">
                  <tr>
                    <th className="p-2.5">ID Retención</th>
                    <th className="p-2.5">Factura / PO</th>
                    <th className="p-2.5">Código & Concepto</th>
                    <th className="p-2.5">Monto Retenido</th>
                    <th className="p-2.5">Plazo Límite</th>
                    <th className="p-2.5 text-right">Acción Desatendida</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#141622] text-zinc-300">
                  {syncResult.deductions.map((ded) => {
                    const isSubmitting = submittingDeductionId === ded.deduction_id;
                    const submissionResult = submissionSuccessMap[ded.deduction_id];

                    return (
                      <tr key={ded.deduction_id} className="hover:bg-[#12141e] transition-colors">
                        <td className="p-2.5 text-[#eed98d] font-bold select-text">{ded.deduction_id}</td>
                        <td className="p-2.5">
                          <span className="text-white font-bold block">{ded.invoice_reference}</span>
                          <span className="text-zinc-500 text-[10px]">{ded.po_reference}</span>
                        </td>
                        <td className="p-2.5">
                          <span className="px-1.5 py-0.2 rounded bg-[#181a24] text-cyan-300 font-bold text-[10px] border border-[#232737] mr-1.5">
                            DE {ded.deduction_code}
                          </span>
                          <span className="text-zinc-300 select-text">{ded.deduction_reason}</span>
                        </td>
                        <td className="p-2.5 text-red-400 font-bold select-text">
                          ${parseFloat(ded.amount).toLocaleString('es-MX', { minimumFractionDigits: 2 })} {ded.currency}
                        </td>
                        <td className="p-2.5 text-zinc-400 text-[11px] select-text">
                          {ded.dispute_deadline}
                        </td>
                        <td className="p-2.5 text-right">
                          {submissionResult ? (
                            <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded bg-[#122419] border border-[#1e452c] text-emerald-300 text-[11px] font-bold">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                              <span title={`Sello: ${submissionResult.confirmation_seal}`}>{submissionResult.tracking_ticket}</span>
                            </div>
                          ) : (
                            <button
                              onClick={() => handleDisputeInPortal(ded)}
                              disabled={isSubmitting}
                              className="btn-tactile px-3 py-1 rounded bg-[#181f2b] hover:bg-[#202c3e] border border-cyan-500/50 text-cyan-300 hover:text-white text-xs font-bold transition-all inline-flex items-center space-x-1.5 shadow-tactile disabled:opacity-50"
                              title="Subir expediente pericial y carta de objeción directamente al portal"
                            >
                              <Send className={`w-3 h-3 ${isSubmitting ? 'animate-spin' : ''}`} />
                              <span>{isSubmitting ? 'Cargando...' : 'Auto-Disputar'}</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

          </div>

        </div>
      )}

    </div>
  );
}
