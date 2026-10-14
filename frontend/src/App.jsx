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
import { apiClient } from './api/client';
import { 
  DollarSign, 
  Files, 
  Scale, 
  Terminal, 
  Share2, 
  AlertCircle 
} from 'lucide-react';

function Workspace() {
  const { isAuthenticated } = useAuth();

  const [health, setHealth] = useState(null);
  const [cases, setCases] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState('case_001');
  const [caseDetails, setCaseDetails] = useState(null);
  const [report, setReport] = useState(null);
  const [tribunalData, setTribunalData] = useState(null);

  const [activeTab, setActiveTab] = useState('financial');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [fastPath, setFastPath] = useState(true);
  const [useCache, setUseCache] = useState(true);

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
          const defaultCase = cList.find(c => c.case_id === 'case_001') || cList[0];
          setSelectedCaseId(defaultCase.case_id);
        }
      } catch (err) {
        setGlobalError("No fue posible conectar con el servidor backend FastAPI.");
      }
    }
    initData();
  }, []);

  // 2. Al cambiar el caso seleccionado, cargar detalles y ejecutar análisis
  useEffect(() => {
    if (!selectedCaseId) return;

    let isCancelled = false;

    async function loadCaseData() {
      setIsAnalyzing(true);
      setGlobalError(null);
      try {
        const details = await apiClient.getCaseDetails(selectedCaseId);
        if (!isCancelled) setCaseDetails(details);

        const rep = await apiClient.analyzeCase(selectedCaseId, fastPath, useCache);
        if (!isCancelled) setReport(rep);

        const trib = await apiClient.getTribunalEvaluation(selectedCaseId).catch(() => null);
        if (!isCancelled) setTribunalData(trib);

        if (!isCancelled) setChatMessages([]);
      } catch (err) {
        if (!isCancelled) setGlobalError(`Error en análisis: ${err.message}`);
      } finally {
        if (!isCancelled) setIsAnalyzing(false);
      }
    }

    loadCaseData();

    return () => {
      isCancelled = true;
    };
  }, [selectedCaseId]);

  // Manejador manual de auditoría
  const handleRunAudit = async () => {
    if (!selectedCaseId) return;
    setIsAnalyzing(true);
    setGlobalError(null);
    try {
      const rep = await apiClient.analyzeCase(selectedCaseId, fastPath, useCache);
      setReport(rep);
      const trib = await apiClient.getTribunalEvaluation(selectedCaseId).catch(() => null);
      setTribunalData(trib);
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
    } catch (err) {
      const errorMsg = { role: 'assistant', content: `Error de conexión: ${err.message}` };
      setChatMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsChatThinking(false);
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
        activeCaseName={selectedCaseId} 
        isAnalyzing={isAnalyzing} 
      />

      {/* Main Container */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Left Navigation Sidebar */}
        <Sidebar
          cases={cases}
          selectedCaseId={selectedCaseId}
          onSelectCase={setSelectedCaseId}
          onRunAudit={handleRunAudit}
          isAnalyzing={isAnalyzing}
          fastPath={fastPath}
          setFastPath={setFastPath}
          useCache={useCache}
          setUseCache={setUseCache}
        />

        {/* Center / Right Content Workspace */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-8 space-y-6">
          
          {/* Global Error Banner */}
          {globalError && (
            <div className="p-3.5 rounded-lg bg-[#241315] border border-rose-900/60 text-rose-300 text-xs flex items-center space-x-2 font-mono">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{globalError}</span>
            </div>
          )}

          {/* Case Title Bar & Tabs Navigation */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-[#20222a] pb-4">
            <div>
              <div className="flex items-center space-x-2.5">
                <h2 className="text-xl font-bold text-white tracking-tight">
                  {activeCaseTitle}
                </h2>
                <span className="text-[10px] px-2 py-0.5 rounded bg-[#242116] text-[#eed98d] font-mono font-semibold border border-[#d4af37]/30">
                  {selectedCaseObj?.category || 'B2B'}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-[#16171d] text-zinc-400 font-mono border border-[#242632]">
                  {selectedCaseId}
                </span>
              </div>
              <p className="text-xs text-zinc-400 mt-1 max-w-2xl">
                {selectedCaseObj?.description || 'Expediente comercial bajo auditoría determinística.'}
              </p>
            </div>

            {/* 5 Navigation Tabs - Sovereign Ledger Design */}
            <div className="flex flex-wrap items-center gap-1 p-1 rounded-lg bg-[#121317] border border-[#22242c]">
              <button
                onClick={() => setActiveTab('financial')}
                className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
                  activeTab === 'financial'
                    ? 'bg-[#1c1d24] text-white border border-[#d4af37]/50 shadow-sm'
                    : 'text-zinc-400 hover:text-white hover:bg-[#16171d]'
                }`}
              >
                <DollarSign className="w-3.5 h-3.5 text-[#d4af37]" />
                <span>Hoja Contable</span>
              </button>

              <button
                onClick={() => setActiveTab('evidence')}
                className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
                  activeTab === 'evidence'
                    ? 'bg-[#1c1d24] text-white border border-[#d4af37]/50 shadow-sm'
                    : 'text-zinc-400 hover:text-white hover:bg-[#16171d]'
                }`}
              >
                <Files className="w-3.5 h-3.5 text-zinc-400" />
                <span>Expediente ({caseDetails?.files_count || 0})</span>
              </button>

              <button
                onClick={() => setActiveTab('tribunal')}
                className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
                  activeTab === 'tribunal'
                    ? 'bg-[#1c1d24] text-white border border-[#d4af37]/50 shadow-sm'
                    : 'text-zinc-400 hover:text-white hover:bg-[#16171d]'
                }`}
              >
                <Scale className="w-3.5 h-3.5 text-zinc-400" />
                <span>Tribunal Colegiado (100 Pts)</span>
              </button>

              <button
                onClick={() => setActiveTab('chat')}
                className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
                  activeTab === 'chat'
                    ? 'bg-[#1c1d24] text-white border border-[#d4af37]/50 shadow-sm'
                    : 'text-zinc-400 hover:text-white hover:bg-[#16171d]'
                }`}
              >
                <Terminal className="w-3.5 h-3.5 text-zinc-400" />
                <span>Terminal Grok</span>
              </button>

              <button
                onClick={() => setActiveTab('export')}
                className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-colors flex items-center gap-1.5 ${
                  activeTab === 'export'
                    ? 'bg-[#1c1d24] text-white border border-[#d4af37]/50 shadow-sm'
                    : 'text-zinc-400 hover:text-white hover:bg-[#16171d]'
                }`}
              >
                <Share2 className="w-3.5 h-3.5 text-zinc-400" />
                <span>Exportar Dictamen</span>
              </button>
            </div>
          </div>

          {/* Active Tab View */}
          <div>
            {activeTab === 'financial' && (
              <FinancialPanel report={report} />
            )}

            {activeTab === 'evidence' && (
              <EvidenceViewer 
                caseId={selectedCaseId} 
                caseDetails={caseDetails} 
                report={report} 
              />
            )}

            {activeTab === 'tribunal' && (
              <TribunalScoreboard tribunalData={tribunalData} />
            )}

            {activeTab === 'chat' && (
              <ChatConsole
                caseId={selectedCaseId}
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

        </main>
      </div>

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
