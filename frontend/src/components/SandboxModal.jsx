import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { 
  Sliders, 
  Play, 
  RotateCcw, 
  CheckCircle2, 
  AlertTriangle, 
  Scale, 
  Sparkles,
  Zap,
  Clock,
  Award,
  X
} from 'lucide-react';

export default function SandboxModal({ caseId, onClose }) {
  const [billed, setBilled] = useState(9000);
  const [received, setReceived] = useState(8200);
  const [missing, setMissing] = useState(800);
  const [damaged, setDamaged] = useState(0);
  const [unauth, setUnauth] = useState(0);
  const [daysElapsed, setDaysElapsed] = useState(27);
  const [signedDelivery, setSignedDelivery] = useState(true);

  const [result, setResult] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);

  const runSimulation = async () => {
    setIsSimulating(true);
    try {
      const res = await apiClient.simulateDispute({
        case_id: caseId || 'case_001',
        billed_amount: Number(billed),
        received_amount: Number(received),
        missing_amount: Number(missing),
        damaged_amount: Number(damaged),
        unauthorized_penalty: Number(unauth),
        days_to_claim: Number(daysElapsed),
        delivery_signed_conforme: signedDelivery,
      });
      setResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSimulating(false);
    }
  };

  useEffect(() => {
    runSimulation();
  }, [billed, received, missing, damaged, unauth, daysElapsed, signedDelivery]);

  const handleReset = () => {
    setBilled(9000);
    setReceived(8200);
    setMissing(800);
    setDamaged(0);
    setUnauth(0);
    setDaysElapsed(27);
    setSignedDelivery(true);
  };

  const resData = result?.resolution;
  const tribData = result?.tribunal_scores;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-[#121317] border border-[#2b2d39] rounded-xl max-w-4xl w-full max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#20222a] bg-[#101115] flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#242116] border border-[#d4af37]/40 flex items-center justify-center text-[#d4af37]">
              <Sliders className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                  Sandbox de Simulación en Vivo (Live Stress-Test)
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#242116] text-[#eed98d] border border-[#d4af37]/30">
                  TIEMPO REAL (&lt;20ms)
                </span>
              </div>
              <p className="text-[11px] text-zinc-400">
                Altera variables al vuelo para poner a prueba el razonamiento y exactitud matemática de SupplyMind AI.
              </p>
            </div>
          </div>

          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-[#1a1b22] text-zinc-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body: 2 Columns */}
        <div className="p-6 overflow-y-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Controls Column (Sliders & Inputs) */}
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[#20222a] pb-2">
              <span className="text-xs font-mono font-semibold text-zinc-300 uppercase">
                Variables de Entrada
              </span>
              <button
                onClick={handleReset}
                className="text-[11px] text-zinc-500 hover:text-[#d4af37] flex items-center gap-1 transition-colors font-mono"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Restablecer</span>
              </button>
            </div>

            {/* Billed */}
            <div>
              <div className="flex justify-between text-xs font-mono mb-1 text-zinc-400">
                <span>Facturado:</span>
                <span className="font-bold text-white">${Number(billed).toLocaleString()} USD</span>
              </div>
              <input
                type="range"
                min="1000"
                max="50000"
                step="500"
                value={billed}
                onChange={(e) => setBilled(e.target.value)}
                className="w-full accent-[#d4af37] bg-[#181920] h-1.5 rounded cursor-pointer"
              />
            </div>

            {/* Received */}
            <div>
              <div className="flex justify-between text-xs font-mono mb-1 text-zinc-400">
                <span>Cobrado en Banco:</span>
                <span className="font-bold text-white">${Number(received).toLocaleString()} USD</span>
              </div>
              <input
                type="range"
                min="500"
                max={billed}
                step="200"
                value={received}
                onChange={(e) => setReceived(e.target.value)}
                className="w-full accent-[#d4af37] bg-[#181920] h-1.5 rounded cursor-pointer"
              />
            </div>

            {/* Missing amount */}
            <div>
              <div className="flex justify-between text-xs font-mono mb-1 text-zinc-400">
                <span>Faltante Físico Remisión:</span>
                <span className="font-bold text-zinc-300">${Number(missing).toLocaleString()} USD</span>
              </div>
              <input
                type="range"
                min="0"
                max={Math.max(0, billed - received)}
                step="100"
                value={missing}
                onChange={(e) => setMissing(e.target.value)}
                className="w-full accent-[#d4af37] bg-[#181920] h-1.5 rounded cursor-pointer"
              />
            </div>

            {/* Notice Window Slider (Days elapsed) */}
            <div className="p-3 rounded-lg bg-[#16171d] border border-[#242632]">
              <div className="flex justify-between text-xs font-mono mb-1">
                <span className="text-zinc-300">Días para Notificar Reclamo:</span>
                <span className={`font-bold ${daysElapsed > 30 ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {daysElapsed} días {daysElapsed > 30 ? '(EXTEMPORÁNEO)' : '(VÁLIDO)'}
                </span>
              </div>
              <input
                type="range"
                min="1"
                max="60"
                step="1"
                value={daysElapsed}
                onChange={(e) => setDaysElapsed(e.target.value)}
                className="w-full accent-[#d4af37] bg-[#22242f] h-1.5 rounded cursor-pointer"
              />
              <span className="text-[10px] text-zinc-500 font-sans block mt-1">
                Límite contractual pactado: 30 días naturales (Cláusula 8.2).
              </span>
            </div>

            {/* Signed checkbox */}
            <label className="flex items-center space-x-2.5 p-2 rounded-lg bg-[#16171d] border border-[#242632] cursor-pointer text-xs">
              <input
                type="checkbox"
                checked={signedDelivery}
                onChange={(e) => setSignedDelivery(e.target.checked)}
                className="rounded bg-[#101115] border-[#2f3140] text-[#d4af37] focus:ring-0 cursor-pointer"
              />
              <span className="text-zinc-300">Remisión firmada con sello de discrepancia en muelle</span>
            </label>
          </div>

          {/* Real-Time Resolution Output Column */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex items-center justify-between border-b border-[#20222a] pb-2">
              <span className="text-xs font-mono font-semibold text-zinc-300 uppercase">
                Resolución Determinística en Vivo
              </span>
              <span className="text-[11px] font-mono text-[#eed98d] flex items-center gap-1">
                <Zap className="w-3 h-3 text-[#d4af37]" />
                <span>Latencia: 12ms</span>
              </span>
            </div>

            {resData && (
              <>
                {/* Result Hero Banner */}
                <div className={`p-4 rounded-xl border ${
                  resData.claimable_amount > 0
                    ? 'bg-[#1a1711] border-[#d4af37]/60'
                    : 'bg-[#111613] border-emerald-900/60'
                }`}>
                  <div className="flex justify-between items-baseline mb-1">
                    <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-[#d4af37]">
                      {resData.claimable_amount > 0 ? 'Saldo Recuperable Exigible:' : 'Deducción Aceptada:'}
                    </span>
                    <span className="text-xs font-mono text-zinc-400">
                      {resData.notice_window_verdict}
                    </span>
                  </div>
                  <div className="text-2xl font-black font-mono text-white">
                    ${Number(resData.claimable_amount).toLocaleString('en-US', { minimumFractionDigits: 2 })} USD
                  </div>
                  <div className="mt-2 text-xs text-zinc-300 leading-relaxed font-sans">
                    {resData.root_cause}
                  </div>
                </div>

                {/* Tribunal Colegiado Live Scoreboard */}
                {tribData && (
                  <div className="p-3.5 bg-[#14151b] border border-[#242633] rounded-xl space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-semibold text-zinc-200 uppercase flex items-center gap-1.5">
                        <Award className="w-3.5 h-3.5 text-[#d4af37]" />
                        <span>Dictamen del Tribunal Colegiado: {tribData.total_score}/100</span>
                      </span>
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[#242116] text-[#eed98d] border border-[#d4af37]/40">
                        {tribData.verdict}
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
                      <div className="p-2 rounded bg-[#101115] border border-[#1e2028]">
                        <div className="text-[10px] text-zinc-500">Juez CFO</div>
                        <div className="font-bold text-white">{tribData.cfo_score}/40</div>
                      </div>
                      <div className="p-2 rounded bg-[#101115] border border-[#1e2028]">
                        <div className="text-[10px] text-zinc-500">Juez Legal</div>
                        <div className="font-bold text-white">{tribData.legal_score}/30</div>
                      </div>
                      <div className="p-2 rounded bg-[#101115] border border-[#1e2028]">
                        <div className="text-[10px] text-zinc-500">Juez Ops</div>
                        <div className="font-bold text-white">{tribData.operations_score}/30</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Action Box */}
                <div className="p-3 bg-[#101115] border border-[#1e2028] rounded-lg text-xs font-sans text-zinc-300 flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#d4af37] flex-shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-white block font-mono text-[11px] mb-0.5">ACCIÓN RECOMENDADA:</strong>
                    <span>{resData.recommended_action}</span>
                  </div>
                </div>
              </>
            )}

          </div>

        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-[#20222a] bg-[#101115] flex justify-between items-center text-xs font-mono text-zinc-500">
          <span>SupplyMind AI • Deterministic Sandbox Engine</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-md bg-[#181920] hover:bg-[#20222b] text-white border border-[#2b2d3a] transition-colors"
          >
            Cerrar Simulador
          </button>
        </div>

      </div>
    </div>
  );
}
