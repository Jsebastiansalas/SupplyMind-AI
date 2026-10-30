import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import SignInView from './components/SignInView';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import FinancialPanel from './components/FinancialPanel';
import EvidenceViewer from './components/EvidenceViewer';
import TribunalScoreboard from './components/TribunalScoreboard';
import ChatConsole from './components/ChatConsole';
import ExportModal from './components/ExportModal';
import SandboxModal from './components/SandboxModal';
import UnitEconomicsModal from './components/UnitEconomicsModal';
import OfficialAuditReportModal from './components/OfficialAuditReportModal';
import PitchWalkthrough, { PITCH_STEPS } from './components/PitchWalkthrough';
import CreateCaseModal from './components/CreateCaseModal';
import CaseSummaryView from './components/CaseSummaryView';
import BenchmarkView from './components/BenchmarkView';
import EdiInspectorView from './components/EdiInspectorView';
import CourtroomView from './components/CourtroomView';
import PortalCrawlerView from './components/PortalCrawlerView';
import PalletVisionView from './components/PalletVisionView';
import NegotiationDuelView from './components/NegotiationDuelView';
import { apiClient } from './api/client';
import { 
  DollarSign, 
  Files, 
  Scale, 
  Terminal, 
  Share2, 
  AlertCircle, 
  PanelLeft, 
  PanelLeftClose, 
  Sliders, 
  TrendingUp, 
  ChevronDown, 
  Printer, 
  Sparkles, 
  Play, 
  RotateCcw, 
  Wrench, 
  Eye, 
  CheckCircle2, 
  Clock, 
  Trophy, 
  Gavel, 
  Binary, 
  Bot, 
  Camera,
  Swords
} from 'lucide-react';

function Workspace() {
  const { isAuthenticated } = useAuth();

  const [health, setHealth] = useState(null);
  const [cases, setCases] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState('case_001');
  const [caseDetails, setCaseDetails] = useState(null);
  const [report, setReport] = useState(null);
  const [tribunalData, setTribunalData] = useState(null);
  const [solvedReports, setSolvedReports] = useState({});
  const [forceShowSummary, setForceShowSummary] = useState(false);
  const [showToolsMenu, setShowToolsMenu] = useState(false);

  // Layout & UI States
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showSandboxModal, setShowSandboxModal] = useState(false);
  const [showEconomicsModal, setShowEconomicsModal] = useState(false);
  const [showDossierModal, setShowDossierModal] = useState(false);
  const [showPitchMode, setShowPitchMode] = useState(false);
  const [pitchStepIndex, setPitchStepIndex] = useState(0);
  const [financialSubTab, setFinancialSubTab] = useState('summary');
  const [showCaseSelector, setShowCaseSelector] = useState(false);

  const [activeTab, setActiveTab] = useState('financial');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [fastPath, setFastPath] = useState(true);
  const [useCache, setUseCache] = useState(true);

  const handleNextPitchStep = () => {
    const nextIdx = pitchStepIndex + 1;
    if (nextIdx < PITCH_STEPS.length) {
      setPitchStepIndex(nextIdx);
      const stepObj = PITCH_STEPS[nextIdx];
      if (stepObj.tab) setActiveTab(stepObj.tab);
      if (stepObj.subtab) setFinancialSubTab(stepObj.subtab);
    } else {
      setShowPitchMode(false);
    }
  };

  const handlePrevPitchStep = () => {
    const prevIdx = pitchStepIndex - 1;
    if (prevIdx >= 0) {
      setPitchStepIndex(prevIdx);
      const stepObj = PITCH_STEPS[prevIdx];
      if (stepObj.tab) setActiveTab(stepObj.tab);
      if (stepObj.subtab) setFinancialSubTab(stepObj.subtab);
    }
  };

  const [chatMessages, setChatMessages] = useState([]);
  const [isChatThinking, setIsChatThinking] = useState(false);
  const [globalError, setGlobalError] = useState(null);

  // 1. Cargar salud y lista de casos inicial
  useEffect(() => {
    async function initData() {
      try {
        const [hData, cList] = await Promise.all([
          apiClient.getHealth().catch(() => null),
          apiClient.getCases().catch(() => []),
        ]);
        setHealth(hData);
        setCases(cList);
        if (cList.length > 0) {
          const defaultCase = cList.find(c => c.case_id === 'case_009_mega_retailer_dispute') || cList[0];
          setSelectedCaseId(defaultCase.case_id);
        }
      } catch (err) {
        setGlobalError("No fue posible conectar con el servidor backend FastAPI.");
      }
    }
    initData();
  }, []);

  // Atajos de teclado profesionales (Linear-grade keyboard navigation)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (['INPUT', 'TEXTAREA'].includes(e.target?.tagName) || e.target?.isContentEditable) {
        return;
      }
      if (e.key === '1') {
        setActiveTab('financial');
        setForceShowSummary(false);
      } else if (e.key === '2') {
        setActiveTab('evidence');
        setForceShowSummary(false);
      } else if (e.key === '3') {
        setActiveTab('tribunal');
        setForceShowSummary(false);
      } else if (e.key === '4') {
        setActiveTab('chat');
        setForceShowSummary(false);
      } else if (e.key === '5') {
        setActiveTab('courtroom');
        setForceShowSummary(false);
      } else if (e.key === '6') {
        setActiveTab('edi');
        setForceShowSummary(false);
      } else if (e.key === '7') {
        setActiveTab('portals');
        setForceShowSummary(false);
      } else if (e.key === '8') {
        setActiveTab('vision');
        setForceShowSummary(false);
      } else if (e.key === 'b' || e.key === 'B') {
        setIsSidebarOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // 2. Al cambiar el caso seleccionado, cargar metadatos SIN conciliar en automático
  useEffect(() => {
    if (!selectedCaseId) return;

    let isCancelled = false;

    async function loadCaseData() {
      setGlobalError(null);
      try {
        const details = await apiClient.getCaseDetails(selectedCaseId);
        if (!isCancelled) setCaseDetails(details);

        if (!isCancelled) {
          const existingReport = solvedReports[selectedCaseId] || null;
          setReport(existingReport);
          setForceShowSummary(!existingReport);

          if (existingReport) {
            const trib = await apiClient.getTribunalEvaluation(selectedCaseId).catch(() => null);
            setTribunalData(trib);
          } else {
            setTribunalData(null);
          }
          setChatMessages([]);
        }
      } catch (err) {
        if (!isCancelled) setGlobalError(`Error al cargar expediente: ${err.message}`);
      }
    }

    loadCaseData();

    return () => {
      isCancelled = true;
    };
  }, [selectedCaseId]);

  // Manejador manual de auditoría (se activa SOLO al dar clic en el botón)
  const handleRunAudit = async () => {
    if (!selectedCaseId) return;
    setIsAnalyzing(true);
    setGlobalError(null);
    try {
      const rep = await apiClient.analyzeCase(selectedCaseId, fastPath, useCache);
      setReport(rep);
      setSolvedReports(prev => ({ ...prev, [selectedCaseId]: rep }));
      setForceShowSummary(false);
      const trib = await apiClient.getTribunalEvaluation(selectedCaseId).catch(() => null);
      setTribunalData(trib);
      setActiveTab('financial');
    } catch (err) {
      setGlobalError(`Error al ejecutar conciliación: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Manejador de Chat
  const handleSendMessage = async (text, role = 'senior_analyst') => {
    const userMsg = { role: 'user', content: text };
    setChatMessages(prev => [...prev, userMsg]);
    setIsChatThinking(true);

    try {
      const res = await apiClient.sendChatMessage(selectedCaseId, text, chatMessages, role);
      const botMsg = { 
        role: 'assistant', 
        content: res.reply,
        model: res.model,
        mode: res.mode,
        sources: res.sources,
      };
      setChatMessages(prev => [...prev, botMsg]);

      // Si el motor Human-in-the-Loop recalculó los saldos en vivo, actualizar toda la UI
      if (res.recalculated_report) {
        setReport(res.recalculated_report);
        setSolvedReports(prev => ({
          ...prev,
          [selectedCaseId]: res.recalculated_report
        }));
      }
    } catch (err) {
      const errorMsg = { role: 'assistant', content: `Error de conexión: ${err.message}` };
      setChatMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsChatThinking(false);
    }
  };

  // Manejador de creación de caso
  const handleCaseCreated = async (newCaseId) => {
    try {
      const updatedCases = await apiClient.getCases();
      setCases(updatedCases);
      setSelectedCaseId(newCaseId);
      setReport(null);
      setForceShowSummary(true);
    } catch (err) {
      console.error(err);
    }
  };

  if (!isAuthenticated) {
    return <SignInView health={health} />;
  }

  const selectedCaseObj = cases.find(c => c.case_id === selectedCaseId);
  const activeCaseTitle = selectedCaseObj?.display_name || selectedCaseId;

  return (
    <div className="min-h-screen bg-[#0c0d10] text-zinc-200 flex flex-col font-sans antialiased">
      
      {/* Top Header */}
      <Header 
        health={health} 
        onOpenCreateCase={() => setShowCreateModal(true)}
      />

      {/* Main Container */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* Left Navigation Sidebar (Collapsible) */}
        {isSidebarOpen && (
          <Sidebar
            cases={cases}
            selectedCaseId={selectedCaseId}
            onSelectCase={(id) => {
              setSelectedCaseId(id);
            }}
            onOpenCreateModal={() => setShowCreateModal(true)}
            solvedCaseIds={new Set(Object.keys(solvedReports))}
          />
        )}

        {/* Center / Right Content Workspace */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-4">
          
          {/* Global Error Banner */}
          {globalError && (
            <div className="p-3 rounded-lg bg-[#241315] border border-rose-900/60 text-rose-300 text-xs flex items-center space-x-2 font-mono">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{globalError}</span>
            </div>
          )}

          {/* Minimalist Executive Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#1b1c24] pb-3 select-none">
            
            {/* Left: Case Info & Status */}
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="btn-tactile p-1.5 rounded bg-[#111218] hover:bg-[#161822] border border-[#1e2029] text-zinc-400 hover:text-white transition-colors"
                title={isSidebarOpen ? "Ocultar panel lateral (B)" : "Mostrar expedientes (B)"}
              >
                {isSidebarOpen ? (
                  <PanelLeftClose className="w-4 h-4 text-[#d4af37]" />
                ) : (
                  <PanelLeft className="w-4 h-4 text-[#d4af37]" />
                )}
              </button>

              <div>
                <div className="flex items-center space-x-2">
                  <h2 className="text-sm font-bold text-white tracking-tight font-mono">
                    {activeCaseTitle}
                  </h2>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-[#14151e] text-zinc-400 font-mono border border-[#20222e]">
                    {selectedCaseObj?.category || 'B2B'}
                  </span>
                  {report ? (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/40 text-emerald-300 font-mono font-medium border border-emerald-800/40 flex items-center space-x-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      <span>Conciliado</span>
                    </span>
                  ) : (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950/40 text-amber-300 font-mono font-medium border border-amber-800/40 flex items-center space-x-1">
                      <Clock className="w-3 h-3 text-amber-400" />
                      <span>Pendiente</span>
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Actions, Tabs & Minimal Tools Menu */}
            <div className="flex items-center space-x-2">
              
              {/* If Solved: Show Tabs with Keyboard Hint Badges */}
              {report && !forceShowSummary && (
                <div className="flex items-center gap-1 p-0.5 rounded bg-[#0f1015] border border-[#1a1c24]">
                  <button
                    onClick={() => setActiveTab('financial')}
                    className={`btn-tactile px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors flex items-center space-x-1.5 ${
                      activeTab === 'financial'
                        ? 'bg-[#181a24] text-white border border-[#272a39] shadow-tactile'
                        : 'text-zinc-400 hover:text-white hover:bg-[#12131a]'
                    }`}
                  >
                    <span>Hoja Contable</span>
                    <span className="text-[9px] px-1 py-0.2 rounded bg-[#101117] text-zinc-500 font-mono hidden md:inline">1</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('evidence')}
                    className={`btn-tactile px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors flex items-center space-x-1.5 ${
                      activeTab === 'evidence'
                        ? 'bg-[#181a24] text-white border border-[#272a39] shadow-tactile'
                        : 'text-zinc-400 hover:text-white hover:bg-[#12131a]'
                    }`}
                  >
                    <span>Expediente ({caseDetails?.files_count || 0})</span>
                    <span className="text-[9px] px-1 py-0.2 rounded bg-[#101117] text-zinc-500 font-mono hidden md:inline">2</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('tribunal')}
                    className={`btn-tactile px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors flex items-center space-x-1.5 ${
                      activeTab === 'tribunal'
                        ? 'bg-[#181a24] text-white border border-[#272a39] shadow-tactile'
                        : 'text-zinc-400 hover:text-white hover:bg-[#12131a]'
                    }`}
                  >
                    <span>Tribunal</span>
                    <span className="text-[9px] px-1 py-0.2 rounded bg-[#101117] text-zinc-500 font-mono hidden md:inline">3</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('chat')}
                    className={`btn-tactile px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors flex items-center space-x-1.5 ${
                      activeTab === 'chat'
                        ? 'bg-[#181a24] text-white border border-[#272a39] shadow-tactile'
                        : 'text-zinc-400 hover:text-white hover:bg-[#12131a]'
                    }`}
                  >
                    <span>Chat Grok</span>
                    <span className="text-[9px] px-1 py-0.2 rounded bg-[#101117] text-zinc-500 font-mono hidden md:inline">4</span>
                  </button>

                  <button
                    onClick={() => {
                      setActiveTab('courtroom');
                      setForceShowSummary(false);
                    }}
                    className={`btn-tactile px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors flex items-center space-x-1.5 ${
                      activeTab === 'courtroom'
                        ? 'bg-[#221f14] text-[#eed98d] border border-[#d4af37]/60 shadow-tactile font-bold'
                        : 'text-zinc-400 hover:text-white hover:bg-[#12131a]'
                    }`}
                    title="Estrado Dialéctico Adversarial con Veredicto Arbitral ICC"
                  >
                    <Gavel className="w-3.5 h-3.5 text-[#d4af37]" />
                    <span>Estrado</span>
                    <span className="text-[9px] px-1 py-0.2 rounded bg-[#101117] text-zinc-500 font-mono hidden md:inline">5</span>
                  </button>

                  <button
                    onClick={() => {
                      setActiveTab('edi');
                      setForceShowSummary(false);
                    }}
                    className={`btn-tactile px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors flex items-center space-x-1.5 ${
                      activeTab === 'edi'
                        ? 'bg-[#14232c] text-cyan-300 border border-cyan-500/60 shadow-tactile font-bold'
                        : 'text-zinc-400 hover:text-white hover:bg-[#12131a]'
                    }`}
                    title="Inspector Forense EDI B2B ANSI X12 y Auditor ASN"
                  >
                    <Binary className="w-3.5 h-3.5 text-cyan-400" />
                    <span>EDI B2B</span>
                    <span className="text-[9px] px-1 py-0.2 rounded bg-[#101117] text-zinc-500 font-mono hidden md:inline">6</span>
                  </button>

                  <button
                    onClick={() => {
                      setActiveTab('portals');
                      setForceShowSummary(false);
                    }}
                    className={`btn-tactile px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors flex items-center space-x-1.5 ${
                      activeTab === 'portals'
                        ? 'bg-[#121c29] text-blue-300 border border-blue-500/60 shadow-tactile font-bold'
                        : 'text-zinc-400 hover:text-white hover:bg-[#12131a]'
                    }`}
                    title="RPA Autónomo y Sincronizador de Portales Retailer (Walmart, Amazon, Soriana, Liverpool)"
                  >
                    <Bot className="w-3.5 h-3.5 text-blue-400" />
                    <span>Portales</span>
                    <span className="text-[9px] px-1 py-0.2 rounded bg-[#101117] text-zinc-500 font-mono hidden md:inline">7</span>
                  </button>

                  <button
                    onClick={() => {
                      setActiveTab('duel');
                      setForceShowSummary(false);
                    }}
                    className={`btn-tactile px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors flex items-center space-x-1.5 ${
                      activeTab === 'duel'
                        ? 'bg-[#261d15] text-[#eed98d] border border-[#d4af37]/70 shadow-tactile font-bold'
                        : 'text-zinc-400 hover:text-white hover:bg-[#12131a]'
                    }`}
                    title="Mesa de Negociación Bilateral B2B (IA vs IA con MCTS y Despachador Robótico)"
                  >
                    <Swords className="w-3.5 h-3.5 text-[#d4af37]" />
                    <span>Mesa Careo</span>
                    <span className="text-[9px] px-1 py-0.2 rounded bg-[#101117] text-zinc-500 font-mono hidden md:inline">⚔️</span>
                  </button>

                  <button
                    onClick={() => {
                      setActiveTab('vision');
                      setForceShowSummary(false);
                    }}
                    className={`btn-tactile px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors flex items-center space-x-1.5 ${
                      activeTab === 'vision'
                        ? 'bg-[#12241b] text-emerald-300 border border-emerald-500/60 shadow-tactile font-bold'
                        : 'text-zinc-400 hover:text-white hover:bg-[#12131a]'
                    }`}
                    title="Laboratorio de Visión Multimodal en Muelle & Certificación C-TPAT"
                  >
                    <Camera className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Visión Muelle</span>
                    <span className="text-[9px] px-1 py-0.2 rounded bg-[#101117] text-zinc-500 font-mono hidden md:inline">8</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('benchmark')}
                    className={`btn-tactile px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors flex items-center space-x-1.5 ${
                      activeTab === 'benchmark'
                        ? 'bg-[#242116] text-[#eed98d] border border-[#d4af37]/60 shadow-tactile font-bold'
                        : 'text-zinc-400 hover:text-white hover:bg-[#12131a]'
                    }`}
                  >
                    <Trophy className="w-3.5 h-3.5 text-[#d4af37]" />
                    <span>Benchmark (35)</span>
                    <span className="text-[9px] px-1 py-0.2 rounded bg-emerald-950 text-emerald-300 font-mono hidden md:inline">100%</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('export')}
                    className={`btn-tactile px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors ${
                      activeTab === 'export'
                        ? 'bg-[#181a24] text-white border border-[#272a39] shadow-tactile'
                        : 'text-zinc-400 hover:text-white hover:bg-[#12131a]'
                    }`}
                  >
                    Exportar
                  </button>
                </div>
              )}

              {/* Dedicated Benchmark 35 Button */}
              <button
                onClick={() => setActiveTab(activeTab === 'benchmark' ? 'financial' : 'benchmark')}
                className={`btn-tactile px-2.5 py-1.5 rounded bg-[#111218] hover:bg-[#161822] border text-xs font-mono font-bold transition-all flex items-center space-x-1.5 shadow-tactile ${
                  activeTab === 'benchmark'
                    ? 'bg-[#242116] border-[#d4af37] text-[#eed98d]'
                    : 'border-[#222432] text-zinc-300 hover:text-white'
                }`}
                title="Suite de Benchmark de 35 Casos y Unit Economics"
              >
                <Trophy className="w-3.5 h-3.5 text-[#d4af37]" />
                <span className="hidden sm:inline">Benchmark 35</span>
              </button>

              {/* Toggle Summary vs Details Button */}
              {report && (
                <button
                  onClick={() => setForceShowSummary(!forceShowSummary)}
                  className="btn-tactile px-2.5 py-1 rounded bg-[#111218] hover:bg-[#161822] border border-[#1e2029] text-zinc-300 hover:text-white text-xs font-mono transition-colors flex items-center space-x-1.5"
                  title="Alternar entre resumen y reporte detallado"
                >
                  <Eye className="w-3.5 h-3.5 text-[#d4af37]" />
                  <span>{forceShowSummary ? 'Ver Hoja Contable' : 'Ver Resumen'}</span>
                </button>
              )}

              {/* Action Button: Iniciar / Re-ejecutar Conciliación */}
              <button
                onClick={handleRunAudit}
                disabled={isAnalyzing}
                className="btn-tactile px-3 py-1.5 rounded bg-[#1f1d14] hover:bg-[#282518] border border-[#d4af37]/60 hover:border-[#d4af37] text-[#eed98d] hover:text-white text-xs font-mono font-bold uppercase tracking-wider transition-all flex items-center space-x-1.5 shadow-tactile disabled:opacity-50"
              >
                {report ? (
                  <>
                    <RotateCcw className={`w-3.5 h-3.5 ${isAnalyzing ? 'animate-spin' : ''}`} />
                    <span>{isAnalyzing ? 'Auditando...' : 'Re-conciliar'}</span>
                  </>
                ) : (
                  <>
                    <Play className={`w-3.5 h-3.5 fill-current ${isAnalyzing ? 'animate-spin' : ''}`} />
                    <span>{isAnalyzing ? 'Conciliando...' : 'Conciliar Expediente'}</span>
                  </>
                )}
              </button>

              {/* Single Minimalist Herramientas Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowToolsMenu(!showToolsMenu)}
                  className="btn-tactile p-1.5 rounded bg-[#111218] hover:bg-[#161822] border border-[#1e2029] text-zinc-400 hover:text-zinc-200 transition-colors"
                  title="Herramientas adicionales"
                >
                  <Wrench className="w-3.5 h-3.5 text-[#d4af37]" />
                </button>

                {showToolsMenu && (
                  <div className="absolute right-0 mt-2 w-56 rounded-lg bg-[#0e0f14] border border-[#222432] shadow-modal p-1 z-50 animate-in fade-in duration-100 font-mono text-xs">
                    <button
                      onClick={() => {
                        setShowToolsMenu(false);
                        setShowSandboxModal(true);
                      }}
                      className="btn-tactile w-full text-left px-3 py-2 rounded hover:bg-[#181a24] text-zinc-300 hover:text-white flex items-center space-x-2"
                    >
                      <Sliders className="w-3.5 h-3.5 text-[#d4af37]" />
                      <span>Simulador Sandbox</span>
                    </button>

                    <button
                      onClick={() => {
                        setShowToolsMenu(false);
                        setShowDossierModal(true);
                      }}
                      className="btn-tactile w-full text-left px-3 py-2 rounded hover:bg-[#181a24] text-zinc-300 hover:text-white flex items-center space-x-2"
                    >
                      <Printer className="w-3.5 h-3.5 text-[#d4af37]" />
                      <span>Dictamen Oficial PDF</span>
                    </button>

                    <button
                      onClick={() => {
                        setShowToolsMenu(false);
                        setActiveTab('duel');
                      }}
                      className="btn-tactile w-full text-left px-3 py-2 rounded hover:bg-[#181a24] text-[#eed98d] hover:text-white flex items-center space-x-2"
                    >
                      <Swords className="w-3.5 h-3.5 text-[#d4af37]" />
                      <span>Mesa de Negociación B2B</span>
                    </button>

                    <button
                      onClick={() => {
                        setShowToolsMenu(false);
                        setActiveTab('courtroom');
                      }}
                      className="btn-tactile w-full text-left px-3 py-2 rounded hover:bg-[#181a24] text-zinc-300 hover:text-white flex items-center space-x-2"
                    >
                      <Gavel className="w-3.5 h-3.5 text-[#d4af37]" />
                      <span>Estrado Dialéctico (Careo)</span>
                    </button>

                    <button
                      onClick={() => {
                        setShowToolsMenu(false);
                        setActiveTab('edi');
                      }}
                      className="btn-tactile w-full text-left px-3 py-2 rounded hover:bg-[#181a24] text-zinc-300 hover:text-white flex items-center space-x-2"
                    >
                      <Binary className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Inspector EDI B2B ANSI X12</span>
                    </button>

                    <button
                      onClick={() => {
                        setShowToolsMenu(false);
                        setActiveTab('benchmark');
                      }}
                      className="btn-tactile w-full text-left px-3 py-2 rounded hover:bg-[#181a24] text-zinc-300 hover:text-white flex items-center space-x-2"
                    >
                      <Trophy className="w-3.5 h-3.5 text-[#d4af37]" />
                      <span>Benchmark Suite (35 Casos)</span>
                    </button>

                    <button
                      onClick={() => {
                        setShowToolsMenu(false);
                        setShowEconomicsModal(true);
                      }}
                      className="btn-tactile w-full text-left px-3 py-2 rounded hover:bg-[#181a24] text-zinc-300 hover:text-white flex items-center space-x-2"
                    >
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Unit Economics & ROI</span>
                    </button>

                    <button
                      onClick={() => {
                        setShowToolsMenu(false);
                        setShowPitchMode(true);
                        setPitchStepIndex(0);
                      }}
                      className="btn-tactile w-full text-left px-3 py-2 rounded hover:bg-[#181a24] text-[#eed98d] hover:text-white flex items-center space-x-2 border-t border-[#1a1c24] mt-0.5 pt-1.5"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-[#d4af37]" />
                      <span>Modo Jurado Guiado</span>
                    </button>
                  </div>
                )}
              </div>

            </div>

          </div>

          {/* Active View: Benchmark View OR EDI Inspector OR Courtroom View OR Portals OR Vision OR Summary when not resolved OR Full Financial Workspace */}
          {activeTab === 'benchmark' ? (
            <BenchmarkView 
              onSelectCase={(cId) => {
                setSelectedCaseId(cId);
                setActiveTab('financial');
              }}
            />
          ) : activeTab === 'edi' ? (
            <EdiInspectorView />
          ) : activeTab === 'courtroom' ? (
            <CourtroomView 
              caseId={selectedCaseId} 
              onOpenDossier={() => setShowDossierModal(true)} 
            />
          ) : activeTab === 'portals' ? (
            <PortalCrawlerView />
          ) : activeTab === 'duel' ? (
            <NegotiationDuelView caseId={selectedCaseId} />
          ) : activeTab === 'vision' ? (
            <PalletVisionView />
          ) : (!report || forceShowSummary) ? (
            <CaseSummaryView 
              caseDetails={caseDetails} 
              onRunAudit={handleRunAudit} 
              isAnalyzing={isAnalyzing} 
            />
          ) : (
            <div>
              {activeTab === 'financial' && (
                <FinancialPanel 
                  report={report} 
                  activeSubTab={financialSubTab}
                  onSubTabChange={setFinancialSubTab}
                  onOpenOfficialDossier={() => setShowDossierModal(true)}
                  onApplyScenario={(scenarioId) => handleSendMessage(`Aplica el escenario ${scenarioId.toLowerCase()}`, 'commercial_negotiator')}
                />
              )}

              {activeTab === 'evidence' && (
                <EvidenceViewer 
                  caseId={selectedCaseId} 
                  caseDetails={caseDetails} 
                  report={report} 
                />
              )}

              {activeTab === 'tribunal' && (
                <TribunalScoreboard 
                  caseId={selectedCaseId} 
                  tribunalData={tribunalData} 
                />
              )}

              {activeTab === 'chat' && (
                <ChatConsole 
                  caseId={selectedCaseId}
                  report={report}
                  messages={chatMessages}
                  onSendMessage={handleSendMessage}
                  isThinking={isChatThinking}
                  onClearChat={() => setChatMessages([])}
                />
              )}

              {activeTab === 'export' && (
                <ExportModal caseId={selectedCaseId} report={report} />
              )}
            </div>
          )}
        </main>
      </div>

      {/* Create Case Modal */}
      {showCreateModal && (
        <CreateCaseModal 
          onClose={() => setShowCreateModal(false)}
          onCaseCreated={handleCaseCreated}
        />
      )}

      {/* Interactive Sandbox Modal for Judges */}
      {showSandboxModal && (
        <SandboxModal 
          caseId={selectedCaseId} 
          onClose={() => setShowSandboxModal(false)} 
        />
      )}

      {/* Unit Economics & ROI Modal */}
      {showEconomicsModal && (
        <UnitEconomicsModal 
          onClose={() => setShowEconomicsModal(false)} 
        />
      )}

      {/* Official Audit Report / Printable Forensic Dossier Modal */}
      {showDossierModal && (
        <OfficialAuditReportModal 
          caseId={selectedCaseId} 
          report={report} 
          onClose={() => setShowDossierModal(false)} 
        />
      )}

      {/* Interactive Pitch Walkthrough for Judges */}
      {showPitchMode && (
        <PitchWalkthrough 
          currentStepIndex={pitchStepIndex} 
          onNext={handleNextPitchStep} 
          onPrev={handlePrevPitchStep} 
          onClose={() => setShowPitchMode(false)} 
          onOpenSandbox={() => setShowSandboxModal(true)} 
          onOpenDossier={() => setShowDossierModal(true)} 
        />
      )}

    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Workspace />
    </AuthProvider>
  );
}
