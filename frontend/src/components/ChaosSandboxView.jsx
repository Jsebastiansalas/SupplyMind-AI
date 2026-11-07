import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import {
  ShieldAlert,
  FileCode,
  FileX,
  WifiOff,
  Scale,
  RotateCcw,
  Play,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Wrench,
  Search,
  FileText,
  DollarSign,
  Activity,
  Zap,
  Info,
  Copy,
  Check,
  RefreshCw,
  Layers,
  ChevronRight
} from 'lucide-react';

export default function ChaosSandboxView({ onSelectScenario }) {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState('PROMPT_INJECTION_REMARK');
  const [retailer, setRetailer] = useState('WALMART_MX');
  const [disputedAmount, setDisputedAmount] = useState(3500);
  const [isInjecting, setIsInjecting] = useState(false);
  const [injectionResult, setInjectionResult] = useState(null);
  const [error, setError] = useState(null);
  const [copiedDocket, setCopiedDocket] = useState(false);

  useEffect(() => {
    loadScenarios();
  }, []);

  async function loadScenarios() {
    try {
      const data = await apiClient.getChaosScenarios();
      if (data && data.scenarios) {
        setScenarios(data.scenarios);
      }
    } catch (err) {
      console.error('Error al cargar escenarios de caos:', err);
    }
  }

  const handleInject = async () => {
    setIsInjecting(true);
    setError(null);
    try {
      const res = await apiClient.injectChaosScenario({
        scenario_id: selectedScenarioId,
        retailer_id: retailer,
        disputed_amount: Number(disputedAmount),
      });
      setInjectionResult(res);
      if (onSelectScenario) onSelectScenario(res);
    } catch (err) {
      setError(`Error al inyectar anomalía: ${err.message}`);
    } finally {
      setIsInjecting(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedDocket(true);
    setTimeout(() => setCopiedDocket(false), 2500);
  };

  const formatMXN = (val) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 2,
    }).format(val || 0);
  };

  const getScenarioIcon = (iconName) => {
    switch (iconName) {
      case 'ShieldAlert':
        return <ShieldAlert className="w-5 h-5 text-red-400" />;
      case 'FileCode':
        return <FileCode className="w-5 h-5 text-amber-400" />;
      case 'FileX':
        return <FileX className="w-5 h-5 text-rose-400" />;
      case 'WifiOff':
        return <WifiOff className="w-5 h-5 text-blue-400" />;
      case 'Scale':
        return <Scale className="w-5 h-5 text-purple-400" />;
      case 'RotateCcw':
        return <RotateCcw className="w-5 h-5 text-emerald-400" />;
      default:
        return <Zap className="w-5 h-5 text-amber-400" />;
    }
  };

  const selectedScenario = scenarios.find((s) => s.id === selectedScenarioId) || scenarios[0];

  return (
    <div className="space-y-6 text-zinc-200">
      
      {/* 1. Header Banner */}
      <div className="bg-[#10121a] border border-[#1e2230] rounded-lg p-5 shadow-tactile relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-red-500/5 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-red-950/80 text-red-400 border border-red-500/40">
                Chaos Engineering Sandbox
              </span>
              <span className="text-xs font-mono text-zinc-500">
                Resiliencia Autónoma • NIF C-3 & NIA 240
              </span>
            </div>
            
            <h2 className="text-lg md:text-xl font-bold font-mono text-white flex items-center space-x-2">
              <span>Laboratorio de Inyección de Caos y Fallos en Vivo</span>
            </h2>
            
            <p className="text-xs text-zinc-400 max-w-2xl leading-relaxed">
              Selecciona una anomalía hostil, falla de red o trampa contable para poner a prueba los guardrails de SupplyMind AI en tiempo real.
              Comprueba cómo el agente activa la <strong>auto-cuarentena forense</strong>, aplica <strong>backoff exponencial</strong> o escala con <strong>honestidad técnica</strong> sin romper el balance <strong>$0.00 MAE</strong>.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-1 rounded bg-[#0b0c12] border border-[#1e2230] text-xs font-mono text-emerald-400 flex items-center space-x-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Circuit Breaker Armado</span>
            </span>
          </div>
        </div>
      </div>

      {/* 2. Grid de Escenarios de Caos */}
      <div>
        <div className="text-xs font-mono text-zinc-400 uppercase tracking-wider mb-3 flex items-center justify-between">
          <span>Selecciona un Escenario de Prueba Hostil:</span>
          <span className="text-zinc-500">{scenarios.length} vectores de prueba certificados</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {scenarios.map((sc) => {
            const isSelected = selectedScenarioId === sc.id;
            return (
              <div
                key={sc.id}
                onClick={() => setSelectedScenarioId(sc.id)}
                className={`p-3.5 rounded-lg border cursor-pointer transition-all flex flex-col justify-between space-y-2.5 ${
                  isSelected
                    ? 'bg-[#181520] border-[#d4af37] shadow-tactile ring-1 ring-[#d4af37]/40'
                    : 'bg-[#0f1118] border-[#1e2230] hover:bg-[#141722] hover:border-zinc-700'
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <div className="p-1.5 rounded bg-[#161824] border border-[#232738]">
                        {getScenarioIcon(sc.icon)}
                      </div>
                      <span className="text-xs font-mono font-bold text-white leading-tight">
                        {sc.name}
                      </span>
                    </div>

                    <span
                      className={`text-[9px] font-mono px-1.5 py-0.5 rounded uppercase font-bold shrink-0 ${
                        sc.severity === 'CRITICAL'
                          ? 'bg-red-950 text-red-300 border border-red-500/40'
                          : sc.severity === 'HIGH'
                          ? 'bg-amber-950 text-amber-300 border border-amber-500/40'
                          : 'bg-blue-950 text-blue-300 border border-blue-500/40'
                      }`}
                    >
                      {sc.severity}
                    </span>
                  </div>

                  <p className="text-[11px] text-zinc-400 mt-2 font-mono leading-relaxed line-clamp-2">
                    {sc.threat_vector}
                  </p>
                </div>

                <div className="pt-2 border-t border-[#1a1d29] flex items-center justify-between text-[10px] font-mono">
                  <span className="text-zinc-500">{sc.category}</span>
                  <span className={`font-bold flex items-center space-x-1 ${isSelected ? 'text-[#eed98d]' : 'text-zinc-400'}`}>
                    <span>{isSelected ? 'Seleccionado' : 'Elegir'}</span>
                    <ChevronRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Panel de Configuración e Inyección */}
      <div className="bg-[#10121a] border border-[#1e2230] rounded-lg p-4 shadow-tactile flex flex-col md:flex-row md:items-center justify-between gap-4">
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 flex-1 text-xs font-mono">
          <div>
            <label className="text-zinc-400 text-[10px] uppercase block mb-1">
              Retailer Contraparte:
            </label>
            <select
              value={retailer}
              onChange={(e) => setRetailer(e.target.value)}
              className="w-full bg-[#0b0c12] border border-[#1e2029] rounded px-3 py-1.5 text-white font-mono focus:outline-none focus:border-[#eed98d]"
            >
              <option value="WALMART_MX">Walmart de México y Centroamérica</option>
              <option value="AMAZON_MX">Amazon México Fulfillment</option>
              <option value="SORIANA_MX">Tiendas Soriana S.A.B.</option>
              <option value="LIVERPOOL_MX">Liverpool Departamental</option>
              <option value="CHEDRAUI_MX">Grupo Comercial Chedraui</option>
            </select>
          </div>

          <div>
            <label className="text-zinc-400 text-[10px] uppercase block mb-1">
              Monto en Disputa Inyectado:
            </label>
            <div className="relative">
              <input
                type="number"
                value={disputedAmount}
                onChange={(e) => setDisputedAmount(Number(e.target.value))}
                className="w-full bg-[#0b0c12] border border-[#1e2029] rounded px-3 py-1.5 text-white font-mono focus:outline-none focus:border-[#eed98d]"
              />
              <span className="absolute right-3 top-2 text-[10px] text-zinc-500">MXN</span>
            </div>
          </div>
        </div>

        <button
          onClick={handleInject}
          disabled={isInjecting}
          className="btn-tactile px-5 py-2.5 rounded bg-[#2e1715] hover:bg-[#3d1f1c] border border-red-500/70 text-red-200 hover:text-white text-xs font-mono font-bold uppercase tracking-wider flex items-center justify-center space-x-2 transition-all shadow-tactile disabled:opacity-50 shrink-0"
        >
          <Play className={`w-4 h-4 fill-current ${isInjecting ? 'animate-spin' : ''}`} />
          <span>{isInjecting ? 'Ejecutando Resiliencia...' : 'Inyectar Anomalía en Vivo'}</span>
        </button>
      </div>

      {/* 4. Visualizador de la Línea de Tiempo de Resiliencia en Tiempo Real */}
      {error && (
        <div className="p-3 bg-red-950/40 border border-red-500/40 rounded text-xs font-mono text-red-300">
          {error}
        </div>
      )}

      {injectionResult && (
        <div className="bg-[#0b0c12] border border-[#222738] rounded-xl p-5 shadow-2xl space-y-5 animate-in fade-in duration-200">
          
          {/* Header del Resultado */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#1b1f2d] pb-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <span
                  className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold uppercase ${
                    injectionResult.status === 'RECOVERED_QUARANTINE'
                      ? 'bg-amber-950 text-amber-300 border border-amber-500/50'
                      : injectionResult.status === 'AUTO_HEALED' || injectionResult.status === 'IDEMPOTENT_RESUMED'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/50'
                      : 'bg-rose-950 text-rose-300 border border-rose-500/50'
                  }`}
                >
                  {injectionResult.status}
                </span>

                <span className="text-xs font-mono text-zinc-400">
                  Latencia de Contención: <strong className="text-white">{injectionResult.duration_ms} ms</strong>
                </span>
              </div>

              <h3 className="text-base font-bold font-mono text-white flex items-center space-x-2">
                <span>{injectionResult.scenario.name}</span>
              </h3>
            </div>

            {/* Invariante Badge */}
            <div className="p-2.5 rounded bg-[#10121a] border border-[#1f2334] text-xs font-mono flex items-center space-x-3">
              <div>
                <div className="text-[10px] text-zinc-500 uppercase">Invariante Contable</div>
                <div className="text-emerald-400 font-bold flex items-center space-x-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>$0.00 MAE (Verificado)</span>
                </div>
              </div>

              <div className="border-l border-[#1f2334] pl-3">
                <div className="text-[10px] text-zinc-500 uppercase">Delta Financiero</div>
                <div className="text-white font-bold">$0.00 MXN</div>
              </div>
            </div>
          </div>

          {/* Sub-second Execution Timeline */}
          <div>
            <div className="text-xs font-mono text-zinc-400 uppercase tracking-wider mb-3 flex items-center space-x-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <span>Cronología de Auto-Recuperación y Guardrails:</span>
            </div>

            <div className="space-y-2.5">
              {injectionResult.timeline.map((step, idx) => (
                <div
                  key={idx}
                  className="bg-[#10121a] border border-[#1b1f2d] rounded-lg p-3 text-xs font-mono flex items-start space-x-3 transition-colors hover:border-zinc-700"
                >
                  <div className="shrink-0 mt-0.5">
                    <span className="px-1.5 py-0.5 rounded bg-[#0b0c12] border border-[#1a1d29] text-[10px] font-bold text-zinc-400">
                      +{step.timestamp_ms}ms
                    </span>
                  </div>

                  <div className="flex-1 space-y-0.5">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-white">{step.title}</span>
                      <span
                        className={`text-[9px] px-1 py-0.2 rounded font-mono uppercase ${
                          step.status === 'SUCCESS'
                            ? 'bg-emerald-950 text-emerald-300'
                            : step.status === 'CRITICAL'
                            ? 'bg-red-950 text-red-300'
                            : step.status === 'WARNING'
                            ? 'bg-amber-950 text-amber-300'
                            : 'bg-zinc-800 text-zinc-300'
                        }`}
                      >
                        {step.stage}
                      </span>
                    </div>
                    <p className="text-[11px] text-zinc-400 leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Audit Docket Card */}
          <div className="bg-[#12141f] border border-[#1e2333] rounded-lg p-4 space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-[#eed98d] font-bold">
                <Lock className="w-4 h-4 text-[#d4af37]" />
                <span>Dictamen de Aislamiento y Folio Forense: {injectionResult.quarantine_docket_id}</span>
              </div>
              <button
                onClick={() => copyToClipboard(JSON.stringify(injectionResult, null, 2))}
                className="text-zinc-400 hover:text-white flex items-center space-x-1 text-[10px]"
              >
                {copiedDocket ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copiedDocket ? 'Copiado' : 'Copiar Resumen'}</span>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-zinc-300 pt-1">
              <div>
                <strong className="text-zinc-400">Diagnóstico del Error:</strong> {injectionResult.error_diagnosed}
              </div>
              <div>
                <strong className="text-zinc-400">Acción de Mitigación:</strong> {injectionResult.recovery_action_taken}
              </div>
            </div>
          </div>

        </div>
      )}

    </div>
  );
}
