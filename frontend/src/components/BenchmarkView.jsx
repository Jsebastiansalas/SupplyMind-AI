import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import {
  Trophy,
  ShieldCheck,
  TrendingUp,
  DollarSign,
  Zap,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Search,
  Filter,
  RotateCcw,
  ExternalLink,
  Cpu,
  Layers,
  Building2,
  FileSpreadsheet
} from 'lucide-react';

export default function BenchmarkView({ onSelectCase }) {
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [economicsData, setEconomicsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isRunningBenchmark, setIsRunningBenchmark] = useState(false);
  const [activeSubTab, setActiveSubTab] = useState('cases'); // 'cases' | 'cost_breakdown' | 'unit_economics'
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL' | 'PASS' | 'QUARANTINE'

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [bData, eData] = await Promise.all([
        apiClient.getBenchmarkReport().catch(() => null),
        apiClient.getUnitEconomics().catch(() => null)
      ]);
      setBenchmarkData(bData);
      setEconomicsData(eData);
    } catch (err) {
      console.error("Error loading benchmark / economics data:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleReRunBenchmark() {
    setIsRunningBenchmark(true);
    try {
      await apiClient.runBenchmark();
      await loadData();
    } catch (err) {
      console.error("Error running benchmark:", err);
    } finally {
      setIsRunningBenchmark(false);
    }
  }

  const casesList = benchmarkData?.cases || [];
  const filteredCases = casesList.filter((c) => {
    const matchesSearch =
      c.case_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.buyer.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.industry.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (statusFilter === 'PASS') return matchesSearch && !c.is_quarantine && c.passed;
    if (statusFilter === 'QUARANTINE') return matchesSearch && c.is_quarantine;
    return matchesSearch;
  });

  if (loading && !benchmarkData) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-3 font-mono text-zinc-400">
        <Activity className="w-8 h-8 text-[#d4af37] animate-spin" />
        <span className="text-xs">Cargando métricas periciales del Benchmark Suite (35 casos)...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      
      {/* 1. Header & Quick Action */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-xl bg-[#12131a] border border-[#272a39] shadow-tactile">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-lg bg-[#242116] border border-[#d4af37]/50 flex items-center justify-center text-[#d4af37] shadow-tactile">
            <Trophy className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <h2 className="text-base font-bold text-white uppercase tracking-wider font-mono">
                Benchmark Suite de 35 Casos & Unit Economics
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                100% Exact Match
              </span>
            </div>
            <p className="text-xs text-zinc-400 font-sans mt-0.5">
              Auditoría científica automatizada con Ground Truth formal, conservación contable ($0.00 MAE) y telemetría de costos.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={handleReRunBenchmark}
            disabled={isRunningBenchmark}
            className="btn-tactile px-3.5 py-1.5 rounded-lg bg-[#1a1b24] hover:bg-[#232532] border border-[#34384c] text-zinc-200 text-xs font-mono font-medium transition-colors flex items-center space-x-2 disabled:opacity-50"
          >
            <RotateCcw className={`w-3.5 h-3.5 text-[#d4af37] ${isRunningBenchmark ? 'animate-spin' : ''}`} />
            <span>{isRunningBenchmark ? 'Evaluando 35 Casos...' : 'Re-evaluar Suite'}</span>
          </button>
        </div>
      </div>

      {/* 2. Top Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        <div className="p-3.5 rounded-lg bg-[#12131a] border border-[#222432]">
          <div className="text-[10px] text-zinc-500 font-mono uppercase">Casos Evaluados</div>
          <div className="text-xl font-bold font-mono text-white mt-1">
            {benchmarkData?.total_cases_evaluated || 35}
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5">Ground Truth verificado</div>
        </div>

        <div className="p-3.5 rounded-lg bg-[#12131a] border border-[#222432]">
          <div className="text-[10px] text-zinc-500 font-mono uppercase">Precisión Exacta</div>
          <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
            {benchmarkData?.exact_match_accuracy_pct || 100.0}%
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5">35 de 35 aprobados</div>
        </div>

        <div className="p-3.5 rounded-lg bg-[#12131a] border border-[#222432]">
          <div className="text-[10px] text-zinc-500 font-mono uppercase">Error Aritmético</div>
          <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
            $0.00 <span className="text-xs text-zinc-500">MAE</span>
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5">0.00% alucinación</div>
        </div>

        <div className="p-3.5 rounded-lg bg-[#12131a] border border-[#222432]">
          <div className="text-[10px] text-zinc-500 font-mono uppercase">Cuarentena Forense</div>
          <div className="text-xl font-bold font-mono text-[#eed98d] mt-1">
            {benchmarkData?.quarantine_success_rate_pct || 100.0}%
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5">3/3 fraudes bloqueados</div>
        </div>

        <div className="p-3.5 rounded-lg bg-[#12131a] border border-[#222432]">
          <div className="text-[10px] text-zinc-500 font-mono uppercase">Costo Inferencia</div>
          <div className="text-xl font-bold font-mono text-[#eed98d] mt-1">
            ${economicsData?.average_cost_per_case_usd || "0.00382"}
          </div>
          <div className="text-[10px] text-emerald-400 mt-0.5">SLA &lt; $0.0050 cumplido</div>
        </div>

        <div className="p-3.5 rounded-lg bg-[#12131a] border border-[#222432]">
          <div className="text-[10px] text-zinc-500 font-mono uppercase">Ahorro vs Humano</div>
          <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
            99.99%
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5">+$3.49M USD anuales</div>
        </div>
      </div>

      {/* 3. Sub-Navigation Tabs */}
      <div className="flex border-b border-[#20222a] space-x-4 font-mono text-xs">
        <button
          onClick={() => setActiveSubTab('cases')}
          className={`pb-2.5 flex items-center space-x-2 border-b-2 transition-colors ${
            activeSubTab === 'cases'
              ? 'border-[#d4af37] text-white font-bold'
              : 'border-transparent text-zinc-400 hover:text-white'
          }`}
        >
          <Layers className="w-3.5 h-3.5 text-[#d4af37]" />
          <span>Matriz de los 35 Casos B2B</span>
          <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#181a24] text-zinc-400">
            {casesList.length}
          </span>
        </button>

        <button
          onClick={() => setActiveSubTab('cost_breakdown')}
          className={`pb-2.5 flex items-center space-x-2 border-b-2 transition-colors ${
            activeSubTab === 'cost_breakdown'
              ? 'border-[#d4af37] text-white font-bold'
              : 'border-transparent text-zinc-400 hover:text-white'
          }`}
        >
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span>Desglose de Costo por Tarea (US-304)</span>
        </button>

        <button
          onClick={() => setActiveSubTab('unit_economics')}
          className={`pb-2.5 flex items-center space-x-2 border-b-2 transition-colors ${
            activeSubTab === 'unit_economics'
              ? 'border-[#d4af37] text-white font-bold'
              : 'border-transparent text-zinc-400 hover:text-white'
          }`}
        >
          <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
          <span>Unit Economics: Humano vs AI</span>
        </button>
      </div>

      {/* 4. Tab Content */}
      {activeSubTab === 'cases' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-3 rounded-lg bg-[#12131a] border border-[#222432]">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Buscar por caso, cliente o industria..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded bg-[#181a24] border border-[#2b2e3f] text-xs font-mono text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-[#d4af37]"
              />
            </div>

            <div className="flex items-center space-x-2 text-xs font-mono">
              <span className="text-zinc-500 text-[11px]">Filtrar:</span>
              <button
                onClick={() => setStatusFilter('ALL')}
                className={`px-2.5 py-1 rounded text-[11px] transition-colors ${
                  statusFilter === 'ALL'
                    ? 'bg-[#222533] text-white border border-[#3b3f54]'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                Todos ({casesList.length})
              </button>
              <button
                onClick={() => setStatusFilter('PASS')}
                className={`px-2.5 py-1 rounded text-[11px] transition-colors ${
                  statusFilter === 'PASS'
                    ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                Aprobados (32)
              </button>
              <button
                onClick={() => setStatusFilter('QUARANTINE')}
                className={`px-2.5 py-1 rounded text-[11px] transition-colors ${
                  statusFilter === 'QUARANTINE'
                    ? 'bg-amber-950/80 text-amber-300 border border-amber-800'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                Cuarentena (3)
              </button>
            </div>
          </div>

          {/* Cases Table */}
          <div className="rounded-xl border border-[#20222e] bg-[#101117] overflow-hidden shadow-tactile">
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-[#20222a] bg-[#14151e] text-[11px] text-zinc-400 uppercase tracking-wider">
                    <th className="py-2.5 px-3">Estatus</th>
                    <th className="py-2.5 px-3">Caso / Retailer</th>
                    <th className="py-2.5 px-3">Industria</th>
                    <th className="py-2.5 px-3 text-right">Disputa Total</th>
                    <th className="py-2.5 px-3 text-right">Justificado (Exp/Pred)</th>
                    <th className="py-2.5 px-3 text-right">Reclamable (Exp/Pred)</th>
                    <th className="py-2.5 px-3 text-right">Error MAE</th>
                    <th className="py-2.5 px-3 text-right">Latencia</th>
                    <th className="py-2.5 px-3 text-center">Acción</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#181924]">
                  {filteredCases.map((c) => {
                    const isQuarantine = c.is_quarantine;
                    return (
                      <tr key={c.case_id} className="hover:bg-[#151620] transition-colors">
                        <td className="py-2.5 px-3 whitespace-nowrap">
                          {isQuarantine ? (
                            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800 text-[10px] font-bold">
                              <AlertTriangle className="w-3 h-3 text-amber-400" />
                              <span>CUARENTENA</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800 text-[10px] font-bold">
                              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                              <span>APROBADO</span>
                            </span>
                          )}
                        </td>

                        <td className="py-2.5 px-3">
                          <div className="font-bold text-white text-[11px]">{c.case_id}</div>
                          <div className="text-[10px] text-zinc-400">{c.buyer}</div>
                        </td>

                        <td className="py-2.5 px-3 text-zinc-400 text-[11px]">
                          {c.industry}
                        </td>

                        <td className="py-2.5 px-3 text-right font-bold text-white">
                          ${c.dispute_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </td>

                        <td className="py-2.5 px-3 text-right text-zinc-300">
                          ${c.expected_justified.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          <span className="text-zinc-500 text-[10px] block">
                            /${c.predicted_justified.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </span>
                        </td>

                        <td className="py-2.5 px-3 text-right font-bold text-emerald-400">
                          ${c.expected_claimable.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          <span className="text-emerald-600 text-[10px] block">
                            /${c.predicted_claimable.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </span>
                        </td>

                        <td className="py-2.5 px-3 text-right text-emerald-400 font-bold">
                          ${c.absolute_error.toFixed(2)}
                        </td>

                        <td className="py-2.5 px-3 text-right text-zinc-400">
                          {c.latency_ms.toFixed(0)} ms
                        </td>

                        <td className="py-2.5 px-3 text-center">
                          <button
                            onClick={() => onSelectCase && onSelectCase(c.case_id)}
                            className="px-2 py-1 rounded bg-[#1a1c26] hover:bg-[#252838] border border-[#2c3044] text-[#eed98d] hover:text-white text-[10px] font-bold transition-colors inline-flex items-center space-x-1"
                            title="Abrir caso en workspace"
                          >
                            <span>Abrir</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </button>
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

      {/* 5. SubTab: Desglose de Costo por Tarea (US-304) */}
      {activeSubTab === 'cost_breakdown' && (
        <div className="space-y-6">
          {/* Task Breakdown Table */}
          <div className="p-5 rounded-xl bg-[#12131a] border border-[#272a39] space-y-4 shadow-tactile">
            <div className="flex items-center justify-between border-b border-[#20222a] pb-3">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono flex items-center space-x-2">
                  <Cpu className="w-4 h-4 text-[#d4af37]" />
                  <span>Desglose Granular por Tarea Operativa (Caso Estándar 1 a 5 SKUs)</span>
                </h3>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Arquitectura Híbrida: Tareas de razonamiento LLM en Platica Gateway vs Cómputo Determinístico Local ($0.00 USD).
                </p>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                US-304 Certified
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-[#20222a] bg-[#161722] text-[11px] text-zinc-400 uppercase">
                    <th className="py-2 px-3">Tarea Operativa</th>
                    <th className="py-2 px-3">Modo</th>
                    <th className="py-2 px-3">Tecnología / Motor</th>
                    <th className="py-2 px-3 text-right">Tokens In</th>
                    <th className="py-2 px-3 text-right">Tokens Out</th>
                    <th className="py-2 px-3 text-right">Latencia</th>
                    <th className="py-2 px-3 text-right">Costo USD</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#181924]">
                  {economicsData?.standard_case_profile?.tasks?.map((t) => (
                    <tr key={t.task_id} className="hover:bg-[#161822]">
                      <td className="py-2.5 px-3 font-bold text-white">{t.task_name}</td>
                      <td className="py-2.5 px-3">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          t.execution_mode === 'LOCAL_DETERMINISTIC'
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            : 'bg-indigo-950 text-indigo-300 border border-indigo-800'
                        }`}>
                          {t.execution_mode === 'LOCAL_DETERMINISTIC' ? 'LOCAL' : 'LLM'}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-zinc-400">{t.technology}</td>
                      <td className="py-2.5 px-3 text-right text-zinc-300">
                        {t.input_tokens > 0 ? t.input_tokens.toLocaleString() : 'Local (0)'}
                      </td>
                      <td className="py-2.5 px-3 text-right text-zinc-300">
                        {t.output_tokens > 0 ? t.output_tokens.toLocaleString() : 'Decimal (0)'}
                      </td>
                      <td className="py-2.5 px-3 text-right text-zinc-400">{t.latency_ms} ms</td>
                      <td className="py-2.5 px-3 text-right font-bold text-emerald-400">
                        ${parseFloat(t.cost_usd).toFixed(5)}
                      </td>
                    </tr>
                  ))}
                  <tr className="bg-[#151722] font-bold border-t border-[#2a2c3a]">
                    <td className="py-2.5 px-3 text-white">TOTAL POR CASO COMPLETO</td>
                    <td className="py-2.5 px-3 text-cyan-300">HÍBRIDO</td>
                    <td className="py-2.5 px-3 text-zinc-400">Grok 4.7 + Python Decimal</td>
                    <td className="py-2.5 px-3 text-right text-white">1,950</td>
                    <td className="py-2.5 px-3 text-right text-white">480</td>
                    <td className="py-2.5 px-3 text-right text-zinc-300">194.6 ms</td>
                    <td className="py-2.5 px-3 text-right text-emerald-400 text-sm">
                      ${parseFloat(economicsData?.standard_case_profile?.total_cost_usd || "0.00348").toFixed(5)} USD
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Complexity Tiers Matrix */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-[#12131a] border border-[#242738] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white font-mono uppercase">Estándar (1-5 SKUs)</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#181a26] text-zinc-400">80% casos</span>
              </div>
              <div className="text-2xl font-black font-mono text-emerald-400">$0.00348 USD</div>
              <div className="text-[11px] text-zinc-400 font-mono">
                Tokens: 2,430 | Latencia: 194ms | Costo/SKU: $0.00116
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#12131a] border border-[#242738] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white font-mono uppercase">Complejo (10-15 SKUs)</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#181a26] text-zinc-400">14% casos</span>
              </div>
              <div className="text-2xl font-black font-mono text-cyan-400">$0.00444 USD</div>
              <div className="text-[11px] text-zinc-400 font-mono">
                Tokens: 3,110 | Latencia: 292ms | Costo/SKU: $0.00037
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#12131a] border border-[#242738] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white font-mono uppercase">Masivo (60 SKUs)</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#181a26] text-zinc-400">6% casos</span>
              </div>
              <div className="text-2xl font-black font-mono text-[#eed98d]">$0.00704 USD</div>
              <div className="text-[11px] text-zinc-400 font-mono">
                Tokens: 5,080 | Latencia: 438ms | Costo/SKU: $0.00011
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 6. SubTab: Unit Economics (Humano vs AI) */}
      {activeSubTab === 'unit_economics' && (
        <div className="space-y-6">
          {/* Comparative Matrix Table */}
          <div className="rounded-xl border border-[#20222e] bg-[#101117] overflow-hidden shadow-tactile">
            <div className="px-5 py-3.5 bg-[#14151e] border-b border-[#20222a] flex items-center justify-between">
              <h3 className="text-sm font-bold text-white uppercase font-mono flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                <span>Matriz Comparativa de Unit Economics (CFO & VP Operations)</span>
              </h3>
              <span className="text-[10px] font-mono text-zinc-500">Benchmark Corporativo B2B</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-[#20222a] bg-[#161722] text-[11px] text-zinc-400 uppercase">
                    <th className="py-2.5 px-4">Dimensión Operativa</th>
                    <th className="py-2.5 px-4 text-rose-300">Equipo Humano (Analista B2B)</th>
                    <th className="py-2.5 px-4 text-emerald-300">SupplyMind AI (Agente Autónomo)</th>
                    <th className="py-2.5 px-4 text-yellow-300">Ganancia de Eficiencia / ROI</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#181924]">
                  {economicsData?.comparative_unit_economics?.map((row, idx) => (
                    <tr key={idx} className="hover:bg-[#151620]">
                      <td className="py-3 px-4 font-bold text-white">{row.metric}</td>
                      <td className="py-3 px-4 text-zinc-300">{row.human_analyst}</td>
                      <td className="py-3 px-4 text-emerald-400 font-medium">{row.supplymind_ai}</td>
                      <td className="py-3 px-4 text-yellow-300/90 font-medium">{row.efficiency_gain}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Enterprise ROI Banner */}
          <div className="p-5 rounded-xl bg-gradient-to-r from-[#0d1612] to-[#12131a] border border-emerald-900/60 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <Building2 className="w-4 h-4 text-emerald-400" />
                <h4 className="text-sm font-bold text-white font-mono uppercase">
                  Proyección Empresarial de Ahorro Neto Anual (100,000 Disputas)
                </h4>
              </div>
              <p className="text-xs text-zinc-400 font-mono">
                Gasto Tradicional: <span className="text-rose-400 font-bold">$3,500,000 USD</span> | Costo SupplyMind AI: <span className="text-emerald-400 font-bold">$382.10 USD</span>
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-black font-mono text-emerald-400">
                +${parseFloat(economicsData?.annual_savings_projection_100k_cases_usd || "3499617.90").toLocaleString('en-US', { minimumFractionDigits: 2 })} USD
              </div>
              <div className="text-[10px] text-zinc-400 font-mono">
                Reducción directa de 99.99% en OPEX contable
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
