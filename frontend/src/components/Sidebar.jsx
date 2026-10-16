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
    <aside className="w-72 md:w-80 flex-shrink-0 border-r border-[#1c1d24] bg-[#0d0e12] flex flex-col h-[calc(100vh-53px)]">
      
      {/* Top Header & Search */}
      <div className="p-3.5 border-b border-[#1c1d24] space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FolderOpen className="w-4 h-4 text-[#d4af37]" />
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-300">
              Expedientes
            </span>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded bg-[#15161c] text-zinc-400 font-mono border border-[#20222a]">
            {cases.length}
          </span>
        </div>

        {/* Search input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input 
            type="text"
            placeholder="Buscar por nombre o ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-[#14151b] border border-[#20222b] rounded-md text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-[#d4af37]/60 font-mono transition-colors"
          />
        </div>

        {/* Clean 3-way Filter Switch */}
        <div className="grid grid-cols-3 gap-1 bg-[#121318] p-0.5 rounded-md border border-[#1d1f27]">
          <button
            onClick={() => setFilterType('ALL')}
            className={`py-1 text-[11px] font-mono rounded transition-colors text-center ${
              filterType === 'ALL'
                ? 'bg-[#1e2029] text-[#eed98d] font-semibold'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            Todos
          </button>
          <button
            onClick={() => setFilterType('CUSTOM')}
            className={`py-1 text-[11px] font-mono rounded transition-colors text-center ${
              filterType === 'CUSTOM'
                ? 'bg-[#1e2029] text-[#eed98d] font-semibold'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            Mis Casos
          </button>
          <button
            onClick={() => setFilterType('BASE')}
            className={`py-1 text-[11px] font-mono rounded transition-colors text-center ${
              filterType === 'BASE'
                ? 'bg-[#1e2029] text-[#eed98d] font-semibold'
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
              className={`p-2.5 rounded-lg border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-[#16171f] border-[#d4af37]/50 shadow-sm'
                  : 'bg-transparent border-transparent hover:bg-[#13141a] hover:border-[#1e2029]'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center space-x-2 truncate min-w-0">
                  <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                    isSolved ? 'bg-emerald-400' : 'bg-amber-400/80'
                  }`} />
                  <div className="truncate">
                    <h3 className={`text-xs truncate font-medium ${isSelected ? 'text-white' : 'text-zinc-300'}`}>
                      {c.display_name}
                    </h3>
                    <span className="text-[10px] text-zinc-500 font-mono">
                      {c.case_id} • {c.document_count || 0} docs
                    </span>
                  </div>
                </div>
                <ChevronRight className={`w-3.5 h-3.5 flex-shrink-0 ${isSelected ? 'text-[#d4af37]' : 'text-zinc-700'}`} />
              </div>
            </div>
          );
        })}

        {filteredCases.length === 0 && (
          <div className="p-6 text-center text-zinc-500 font-mono text-xs">
            No se encontraron casos con ese criterio.
          </div>
        )}
      </div>

      {/* Bottom Poner Caso Footer Button */}
      {onOpenCreateModal && (
        <div className="p-2.5 border-t border-[#1c1d24] bg-[#0f1014]">
          <button
            onClick={onOpenCreateModal}
            className="w-full flex items-center justify-center space-x-1.5 py-1.5 px-3 rounded-md bg-[#16171d] hover:bg-[#1d1f27] border border-[#252834] hover:border-[#d4af37]/60 text-xs font-mono text-zinc-300 hover:text-white transition-all shadow-sm"
          >
            <Plus className="w-3.5 h-3.5 text-[#d4af37]" />
            <span>Poner Nuevo Caso</span>
          </button>
        </div>
      )}

    </aside>
  );
}
