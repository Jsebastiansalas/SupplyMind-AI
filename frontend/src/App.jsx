import React, { useState, useEffect } from 'react';
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
  MessageSquare, 
  Share2, 
  AlertCircle 
} from 'lucide-react';

export default function App() {
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
        // Cargar detalles de documentos
        const details = await apiClient.getCaseDetails(selectedCaseId);
        if (!isCancelled) setCaseDetails(details);

        // Analizar caso automáticamente con fast-path
        const rep = await apiClient.analyzeCase(selectedCaseId, fastPath, useCache);
        if (!isCancelled) setReport(rep);

        // Cargar veredicto del tribunal colegiado
        const trib = await apiClient.getTribunalEvaluation(selectedCaseId).catch(() => null);
        if (!isCancelled) setTribunalData(trib);

        // Reiniciar chat para el nuevo caso
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
      setGlobalError(`Error al ejecutar auditoría: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Manejador de Chat
  const handleSendMessage = async (text) => {
    const userMsg = { role: 'user', content: text };
    setChatMessages(prev => [...prev, userMsg]);
    setIsChatThinking(true);

    try {
      const res = await apiClient.sendChatMessage(selectedCaseId, text, chatMessages);
      const botMsg = { role: 'assistant', content: res.reply };
      setChatMessages(prev => [...prev, botMsg]);
    } catch (err) {
      const errorMsg = { role: 'assistant', content: `Error de conexión: ${err.message}` };
      setChatMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsChatThinking(false);
    }
  };

  const selectedCaseObj = cases.find(c => c.case_id === selectedCaseId);
  const activeCaseTitle = selectedCaseObj?.display_name || selectedCaseId;

  return (
    <div className="min-h-screen bg-[#020617] text-slate-100 flex flex-col font-sans">
      
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
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{globalError}</span>
            </div>
          )}

          {/* Case Title Bar & Tabs Navigation */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-xl font-bold text-white tracking-tight">
                  {activeCaseTitle}
                </h2>
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-cyan-300 font-mono font-medium">
                  {selectedCaseObj?.category || 'B2B'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                {selectedCaseObj?.description || 'Expediente bajo auditoría determinística.'}
              </p>
            </div>

            {/* 5 Navigation Tabs */}
            <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-xl bg-slate-900/90 border border-slate-800">
              <button
                onClick={() => setActiveTab('financial')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                  activeTab === 'financial'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <DollarSign className="w-3.5 h-3.5" />
                <span>Financiero</span>
              </button>

              <button
                onClick={() => setActiveTab('evidence')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                  activeTab === 'evidence'
                    ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Files className="w-3.5 h-3.5" />
                <span>Evidencias ({caseDetails?.files_count || 0})</span>
              </button>

              <button
                onClick={() => setActiveTab('tribunal')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                  activeTab === 'tribunal'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Scale className="w-3.5 h-3.5" />
                <span>Tribunal (100 Pts)</span>
              </button>

              <button
                onClick={() => setActiveTab('chat')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                  activeTab === 'chat'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5" />
                <span>Terminal Grok</span>
              </button>

              <button
                onClick={() => setActiveTab('export')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                  activeTab === 'export'
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Share2 className="w-3.5 h-3.5" />
                <span>Exportar</span>
              </button>
            </div>
          </div>

          {/* Active Tab View Rendering */}
          <div className="transition-all">
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
