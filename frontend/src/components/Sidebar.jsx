import React, { useState } from 'react';
import { 
  FolderOpen, 
  Search, 
  ChevronRight,
  Plus,
  FileText
} from 'lucide-react';

export default function Sidebar({
  cases = [],
  selectedCaseId,
  onSelectCase,
  onOpenCreateModal,
  solvedCaseIds = new Set(),
}) {
  const [filterType, setFilterType] = useState('ALL'); // 'ALL' | 'CUSTOM' | 'BASE'
  const [searchQuery, setSearchQuery] = useState('');

  const filteredCases = cases.filter(c => {
    const isCustom = c.category === 'Personalizado' || c.case_id.includes('custom') || c.case_id.includes('mi_');
    const matchesFilter = 
      filterType === 'ALL' ? true :
      filterType === 'CUSTOM' ? isCustom :
      !isCustom;

    const matchesQuery = 
      c.case_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.display_name.toLowerCase().includes(searchQuery.toLowerCase());

    return matchesFilter && matchesQuery;
  });

  return (
    <aside className="w-72 md:w-80 flex-shrink-0 border-r border-[#1b1c24] bg-[#090a0d] flex flex-col h-[calc(100vh-53px)] select-none">
      
      {/* Top Header & Search */}
      <div className="p-3.5 border-b border-[#1b1c24] space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FolderOpen className="w-4 h-4 text-[#d4af37]" />
            <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-zinc-300">
              Dockets / Expedientes
            </span>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded bg-[#13141b] text-zinc-400 font-mono border border-[#1e202a]">
            {cases.length} Casos
          </span>
        </div>

        {/* Search input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input 
            type="text"
            placeholder="Filtrar por nombre o folio..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-[#111218] border border-[#1e2029] focus:border-[#d4af37]/60 rounded text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none font-mono transition-colors"
          />
        </div>

        {/* Clean 3-way Filter Switch */}
        <div className="grid grid-cols-3 gap-1 bg-[#0f1015] p-0.5 rounded border border-[#1a1c24]">
          <button
            onClick={() => setFilterType('ALL')}
            className={`btn-tactile py-1 text-[10px] font-mono rounded transition-colors text-center ${
              filterType === 'ALL'
                ? 'bg-[#181a24] text-[#eed98d] font-semibold border border-[#262838]'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            Todos
          </button>
          <button
            onClick={() => setFilterType('CUSTOM')}
            className={`btn-tactile py-1 text-[10px] font-mono rounded transition-colors text-center ${
              filterType === 'CUSTOM'
                ? 'bg-[#181a24] text-[#eed98d] font-semibold border border-[#262838]'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            Mis Casos
          </button>
          <button
            onClick={() => setFilterType('BASE')}
            className={`btn-tactile py-1 text-[10px] font-mono rounded transition-colors text-center ${
              filterType === 'BASE'
                ? 'bg-[#181a24] text-[#eed98d] font-semibold border border-[#262838]'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            Base B2B
          </button>
        </div>
      </div>

      {/* Case List Scrollable Area */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {filteredCases.map(c => {
          const isSelected = c.case_id === selectedCaseId;
          const isSolved = solvedCaseIds.has(c.case_id);

          return (
            <div
              key={c.case_id}
              onClick={() => onSelectCase(c.case_id)}
              className={`p-2.5 rounded border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-[#14151e] border-[#2d3040] border-l-2 border-l-[#d4af37] shadow-subtle'
                  : 'bg-transparent border-transparent hover:bg-[#111218] hover:border-[#1a1c24]'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="truncate min-w-0 flex-1">
                  <div className="flex items-center space-x-2">
                    <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded uppercase ${
                      isSolved 
                        ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-800/40' 
                        : 'bg-amber-950/40 text-amber-400 border border-amber-800/40'
                    }`}>
                      {isSolved ? 'AUDITADO' : 'PENDIENTE'}
                    </span>
                    <span className="text-[10px] text-zinc-500 font-mono truncate">
                      {c.case_id}
                    </span>
                  </div>
                  <h3 className={`text-xs truncate font-medium mt-1 ${isSelected ? 'text-white' : 'text-zinc-300'}`}>
                    {c.display_name}
                  </h3>
                  <div className="text-[10px] text-zinc-500 font-mono mt-0.5 flex items-center space-x-2">
                    <span>{c.document_count || 0} documentos</span>
                    {c.category && (
                      <>
                        <span>•</span>
                        <span>{c.category}</span>
                      </>
                    )}
                  </div>
                </div>
                <ChevronRight className={`w-3.5 h-3.5 flex-shrink-0 ${isSelected ? 'text-[#d4af37]' : 'text-zinc-700'}`} />
              </div>
            </div>
          );
        })}

        {filteredCases.length === 0 && (
          <div className="p-6 text-center text-zinc-500 font-mono text-xs">
            No se encontraron expedientes con ese criterio.
          </div>
        )}
      </div>

      {/* Bottom Poner Caso Footer Button */}
      {onOpenCreateModal && (
        <div className="p-2.5 border-t border-[#1b1c24] bg-[#0b0c10]">
          <button
            onClick={onOpenCreateModal}
            className="btn-tactile w-full flex items-center justify-center space-x-1.5 py-1.5 px-3 rounded bg-[#13141b] hover:bg-[#181a24] border border-[#222432] hover:border-[#d4af37]/60 text-xs font-mono text-zinc-300 hover:text-white transition-all shadow-subtle"
          >
            <Plus className="w-3.5 h-3.5 text-[#d4af37]" />
            <span>Poner Nuevo Caso</span>
          </button>
        </div>
      )}

    </aside>
  );
}
