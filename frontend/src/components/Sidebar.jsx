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
    <aside className="w-80 md:w-96 flex-shrink-0 border-r border-[#20222a] bg-[#0d0e12] flex flex-col h-[calc(100vh-57px)]">
      
      {/* Search & Categories */}
      <div className="p-4 border-b border-[#20222a] bg-[#101115] space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-zinc-300">
            <FolderOpen className="w-4 h-4 text-[#d4af37]" />
            <h2 className="text-xs font-mono font-bold tracking-wider uppercase text-zinc-200">
              Expedientes en Cartera
            </h2>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded bg-[#171820] text-zinc-400 font-mono border border-[#252733]">
            {cases.length} CASOS
          </span>
        </div>

        {/* Search input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input 
            type="text"
            placeholder="Filtrar por ID o cliente..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-[#16171d] border border-[#242632] rounded-md text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-[#d4af37]/60 font-mono transition-colors"
          />
        </div>

        {/* Category Filter Pills */}
        <div className="flex flex-wrap gap-1">
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setFilterCategory(cat.id)}
              className={`text-[10px] px-2 py-0.5 rounded transition-colors font-mono font-medium ${
                filterCategory === cat.id
                  ? 'bg-[#242116] text-[#eed98d] border border-[#d4af37]/40 shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-[#16171d] border border-transparent'
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
              className={`p-3 rounded-lg border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-[#181920] border-[#d4af37]/60 shadow-sm'
                  : 'bg-[#121318]/70 border-[#1f2029] hover:bg-[#15161d] hover:border-[#2a2c38]'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-1.5 mb-1">
                    {c.has_ocr ? (
                      <Scan className="w-3.5 h-3.5 text-zinc-400 flex-shrink-0" />
                    ) : c.has_pdf ? (
                      <FileText className="w-3.5 h-3.5 text-[#d4af37] flex-shrink-0" />
                    ) : (
                      <FileSpreadsheet className="w-3.5 h-3.5 text-zinc-400 flex-shrink-0" />
                    )}
                    <h3 className={`text-xs font-semibold truncate ${isSelected ? 'text-white' : 'text-zinc-300'}`}>
                      {c.display_name}
                    </h3>
                  </div>
                  <p className="text-[11px] text-zinc-500 line-clamp-2 leading-relaxed">
                    {c.description}
                  </p>
                </div>
                <ChevronRight className={`w-3.5 h-3.5 flex-shrink-0 mt-0.5 ${isSelected ? 'text-[#d4af37]' : 'text-zinc-600'}`} />
              </div>

              {/* Tags bar */}
              <div className="mt-2.5 pt-2 border-t border-[#1f212a] flex items-center justify-between text-[10px]">
                <span className="font-mono text-zinc-400">{c.case_id}</span>
                <div className="flex items-center space-x-1.5">
                  <span className="px-1.5 py-0.2 rounded bg-[#16171e] text-zinc-400 font-mono border border-[#232530]">
                    {c.document_count} docs
                  </span>
                  {c.has_ocr && (
                    <span className="px-1.5 py-0.2 rounded bg-[#1a1b22] text-zinc-300 border border-[#262835] font-mono">
                      OCR
                    </span>
                  )}
                  {c.has_pdf && (
                    <span className="px-1.5 py-0.2 rounded bg-[#201d15] text-[#eed98d] border border-[#3b341f] font-mono">
                      PDF
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {filteredCases.length === 0 && (
          <div className="p-8 text-center text-zinc-500 text-xs font-mono">
            No se encontraron expedientes coincidentes.
          </div>
        )}
      </div>

      {/* Engine Controls & Execute Section */}
      <div className="p-4 border-t border-[#20222a] bg-[#101115] space-y-3">
        <div className="flex items-center space-x-2 text-zinc-400 text-[10px] font-mono font-semibold uppercase tracking-wider">
          <Sliders className="w-3 h-3 text-[#d4af37]" />
          <span>Configuración del Motor</span>
        </div>

        {/* Toggles */}
        <div className="space-y-1.5 text-xs">
          <label className="flex items-center justify-between cursor-pointer p-1 rounded hover:bg-[#16171d] transition-colors">
            <span className="flex items-center space-x-1.5 text-zinc-400 text-[11px]">
              <Zap className="w-3 h-3 text-zinc-500" />
              <span>Fast-Path Determinístico</span>
            </span>
            <input 
              type="checkbox" 
              checked={fastPath} 
              onChange={(e) => setFastPath(e.target.checked)}
              className="rounded bg-[#16171d] border-[#2e303d] text-[#d4af37] focus:ring-0 cursor-pointer"
            />
          </label>

          <label className="flex items-center justify-between cursor-pointer p-1 rounded hover:bg-[#16171d] transition-colors">
            <span className="flex items-center space-x-1.5 text-zinc-400 text-[11px]">
              <Database className="w-3 h-3 text-zinc-500" />
              <span>Caché en Memoria</span>
            </span>
            <input 
              type="checkbox" 
              checked={useCache} 
              onChange={(e) => setUseCache(e.target.checked)}
              className="rounded bg-[#16171d] border-[#2e303d] text-[#d4af37] focus:ring-0 cursor-pointer"
            />
          </label>
        </div>

        {/* Solid Sovereign Action Button */}
        <button
          onClick={onRunAudit}
          disabled={isAnalyzing || !selectedCaseId}
          className={`w-full py-2.5 px-4 rounded-lg font-semibold font-mono text-xs uppercase tracking-wider flex items-center justify-center space-x-2 transition-all shadow-sm ${
            isAnalyzing
              ? 'bg-[#1a1b22] text-zinc-500 cursor-not-allowed border border-[#262834]'
              : 'bg-[#1b1c23] hover:bg-[#22242c] text-[#f4f4f7] border border-[#d4af37]/60 hover:border-[#d4af37]'
          }`}
        >
          <Play className={`w-3 h-3 fill-current text-[#d4af37] ${isAnalyzing ? 'animate-spin' : ''}`} />
          <span>{isAnalyzing ? 'Auditando...' : 'Conciliar Expediente'}</span>
        </button>
      </div>

    </aside>
  );
}
