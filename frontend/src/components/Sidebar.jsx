import React, { useState } from 'react';
import { 
  FolderOpen, 
  FileText, 
  Zap, 
  Database, 
  Play, 
  Search, 
  FileSpreadsheet, 
  Scan, 
  Swords, 
  ChevronRight,
  Sliders
} from 'lucide-react';

export default function Sidebar({
  cases = [],
  selectedCaseId,
  onSelectCase,
  onRunAudit,
  isAnalyzing,
  fastPath,
  setFastPath,
  useCache,
  setUseCache,
}) {
  const [filterCategory, setFilterCategory] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const categories = [
    { id: 'ALL', label: 'Todos' },
    { id: 'Básico', label: 'B2B Base' },
    { id: 'Empresarial PDF', label: 'PDFs' },
    { id: 'Visión OCR', label: 'OCR' },
    { id: 'Adversarial Sintético', label: 'Adversarial' },
    { id: 'Pruebas de Estrés', label: 'Resiliencia' },
  ];

  const filteredCases = cases.filter(c => {
    const matchesCat = filterCategory === 'ALL' || c.category === filterCategory;
    const matchesQuery = 
      c.case_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.display_name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesQuery;
  });

  return (
    <aside className="w-80 md:w-96 flex-shrink-0 border-r border-slate-800/80 bg-slate-950/80 backdrop-blur-xl flex flex-col h-[calc(100vh-65px)]">
      
      {/* Header Panel */}
      <div className="p-4 border-b border-slate-800/60">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2 text-slate-200">
            <FolderOpen className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold tracking-wide uppercase font-sans">
              Expedientes de Disputa
            </h2>
          </div>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
            {cases.length} casos
          </span>
        </div>

        {/* Search input */}
        <div className="relative mb-3">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input 
            type="text"
            placeholder="Buscar por ID o cliente..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition-colors"
          />
        </div>

        {/* Category Filter Pills */}
        <div className="flex flex-wrap gap-1">
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setFilterCategory(cat.id)}
              className={`text-[11px] px-2.5 py-1 rounded-md transition-all font-medium ${
                filterCategory === cat.id
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/10'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Case List Scrollable Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {filteredCases.map(c => {
          const isSelected = c.case_id === selectedCaseId;
          return (
            <div
              key={c.case_id}
              onClick={() => onSelectCase(c.case_id)}
              className={`p-3 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-slate-900/90 border-cyan-500/50 shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-500/20'
                  : 'bg-slate-900/30 border-slate-800/60 hover:bg-slate-900/60 hover:border-slate-700/80'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-1.5 mb-1">
                    {c.has_ocr ? (
                      <Scan className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                    ) : c.has_pdf ? (
                      <FileText className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                    ) : (
                      <FileSpreadsheet className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                    )}
                    <h3 className={`text-xs font-bold truncate ${isSelected ? 'text-cyan-300' : 'text-slate-200'}`}>
                      {c.display_name}
                    </h3>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                    {c.description}
                  </p>
                </div>
                <ChevronRight className={`w-4 h-4 flex-shrink-0 transition-transform ${isSelected ? 'text-cyan-400 translate-x-0.5' : 'text-slate-600'}`} />
              </div>

              {/* Tags bar */}
              <div className="mt-2.5 pt-2 border-t border-slate-800/40 flex items-center justify-between text-[10px]">
                <span className="font-mono text-slate-500">ID: {c.case_id}</span>
                <div className="flex items-center space-x-1.5">
                  <span className="px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-300 font-mono">
                    {c.document_count} docs
                  </span>
                  {c.has_ocr && (
                    <span className="px-1.5 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800/50">
                      OCR
                    </span>
                  )}
                  {c.has_pdf && (
                    <span className="px-1.5 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/50">
                      PDF
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {filteredCases.length === 0 && (
          <div className="p-8 text-center text-slate-500 text-xs">
            No se encontraron expedientes coincidentes.
          </div>
        )}
      </div>

      {/* Engine Controls & Execute Section */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/90 space-y-3">
        <div className="flex items-center space-x-2 text-slate-300 text-xs font-bold uppercase tracking-wider">
          <Sliders className="w-3.5 h-3.5 text-indigo-400" />
          <span>Configuración del Motor</span>
        </div>

        {/* Toggles */}
        <div className="space-y-2 text-xs">
          <label className="flex items-center justify-between cursor-pointer p-1.5 rounded hover:bg-slate-900/60">
            <span className="flex items-center space-x-1.5 text-slate-300">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span>Fast-Path Determinístico (&lt;1s)</span>
            </span>
            <input 
              type="checkbox" 
              checked={fastPath} 
              onChange={(e) => setFastPath(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-cyan-500 focus:ring-0 cursor-pointer"
            />
          </label>

          <label className="flex items-center justify-between cursor-pointer p-1.5 rounded hover:bg-slate-900/60">
            <span className="flex items-center space-x-1.5 text-slate-300">
              <Database className="w-3.5 h-3.5 text-cyan-400" />
              <span>Caché en Memoria Inteligente</span>
            </span>
            <input 
              type="checkbox" 
              checked={useCache} 
              onChange={(e) => setUseCache(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-cyan-500 focus:ring-0 cursor-pointer"
            />
          </label>
        </div>

        {/* Action Button */}
        <button
          onClick={onRunAudit}
          disabled={isAnalyzing || !selectedCaseId}
          className={`w-full py-2.5 px-4 rounded-xl font-bold text-xs uppercase tracking-wider flex items-center justify-center space-x-2 transition-all shadow-lg ${
            isAnalyzing
              ? 'bg-slate-800 text-slate-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-500 text-white hover:brightness-110 shadow-indigo-500/20 hover:shadow-cyan-500/30'
          }`}
        >
          <Play className={`w-3.5 h-3.5 fill-current ${isAnalyzing ? 'animate-spin' : ''}`} />
          <span>{isAnalyzing ? 'Auditando...' : 'Iniciar Auditoría Autónoma'}</span>
        </button>
      </div>

    </aside>
  );
}
