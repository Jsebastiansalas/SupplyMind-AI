import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  LogOut, 
  ChevronDown, 
  Check, 
  Plus
} from 'lucide-react';

export default function Header({ 
  health, 
  onOpenCreateCase
}) {
  const { currentUser, logout, loginAsPersona, personas } = useAuth();
  const [showPersonaMenu, setShowPersonaMenu] = useState(false);

  const isLive = health?.status === 'online';

  return (
    <header className="border-b border-[#1b1c24] bg-[#090a0d] px-6 py-2.5 sticky top-0 z-40">
      <div className="flex items-center justify-between">
        
        {/* Brand & Identity - Institutional Sovereign */}
        <div className="flex items-center space-x-3.5">
          <div className="w-7 h-7 rounded bg-[#14151c] border border-[#d4af37]/50 flex items-center justify-center text-[#d4af37] font-bold text-xs tracking-tight shadow-tactile select-none">
            SM
          </div>
          <div className="flex items-baseline space-x-2">
            <h1 className="text-xs font-bold tracking-wider text-zinc-100 uppercase font-mono">
              SupplyMind
            </h1>
            <span className="text-zinc-600 font-light text-xs">/</span>
            <span className="text-[11px] text-zinc-400 font-mono tracking-wide hidden sm:inline">
              Conciliación Comercial & Arbitraje B2B
            </span>
          </div>
        </div>

        {/* Right Institutional Controls */}
        <div className="flex items-center space-x-3">
          
          {/* Subtle Live Engine Status */}
          <div className="hidden sm:flex items-center space-x-2 px-2.5 py-1 rounded bg-[#111218] border border-[#1d1f29] text-[11px] text-zinc-400 font-mono select-none">
            <span className={`w-1.5 h-1.5 rounded-full ${isLive ? 'bg-emerald-400 ring-2 ring-emerald-500/20' : 'bg-zinc-600'}`} />
            <span className="text-zinc-300 font-medium">Grok 4.7</span>
            <span className="text-zinc-600">|</span>
            <span className="text-[10px] text-zinc-500">FastPath</span>
          </div>

          {/* Primary Action Button: Poner Caso */}
          {onOpenCreateCase && (
            <button
              onClick={onOpenCreateCase}
              className="btn-tactile flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#1f1d14] hover:bg-[#282518] border border-[#d4af37]/60 hover:border-[#d4af37] text-xs font-mono text-[#eed98d] font-semibold shadow-sm transition-all"
              title="Poner o subir un nuevo expediente para auditar"
            >
              <Plus className="w-3.5 h-3.5 text-[#d4af37]" />
              <span>Poner Caso</span>
            </button>
          )}

          {/* User Persona Profile */}
          {currentUser && (
            <div className="relative">
              <button
                onClick={() => setShowPersonaMenu(!showPersonaMenu)}
                className="btn-tactile flex items-center space-x-2 px-2.5 py-1.5 rounded bg-[#111218] hover:bg-[#161822] border border-[#1d1f29] hover:border-[#2a2d3b] text-xs transition-colors"
                title="Cambiar perfil"
              >
                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-[#181923] border border-[#272a39] text-[#d4af37]">
                  {currentUser.id === 'cfo' ? 'CFO' : currentUser.id === 'legal' ? 'JUR' : 'OPS'}
                </span>
                <span className="text-xs font-medium text-zinc-200 hidden md:inline">
                  {currentUser.name.split(' ')[0]}
                </span>
                <ChevronDown className="w-3 h-3 text-zinc-500" />
              </button>

              {/* Persona Dropdown */}
              {showPersonaMenu && (
                <div className="absolute right-0 mt-2 w-64 rounded-lg bg-[#111218] border border-[#222432] shadow-elevated p-1.5 z-50 animate-in fade-in duration-100">
                  <div className="px-3 py-1.5 border-b border-[#1b1d28] mb-1">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                      Perfil Activo & Perspectiva
                    </span>
                  </div>

                  <div className="space-y-0.5">
                    {Object.values(personas).map((p) => {
                      const isCurrent = currentUser?.id === p.id;
                      const roleTag = p.id === 'cfo' ? 'CFO' : p.id === 'legal' ? 'JUR' : 'OPS';
                      return (
                        <button
                          key={p.id}
                          onClick={() => {
                            loginAsPersona(p.id);
                            setShowPersonaMenu(false);
                          }}
                          className={`w-full flex items-center justify-between p-2 rounded text-left transition-colors ${
                            isCurrent
                              ? 'bg-[#181a24] text-white font-medium border border-[#252839]'
                              : 'text-zinc-400 hover:bg-[#15161f] hover:text-zinc-200'
                          }`}
                        >
                          <div className="flex items-center space-x-2.5">
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-[#12131b] border border-[#232535] text-[#d4af37]">
                              {roleTag}
                            </span>
                            <div>
                              <div className="text-xs font-medium text-zinc-200">{p.name}</div>
                              <div className="text-[10px] text-zinc-500 font-mono">{p.title}</div>
                            </div>
                          </div>
                          {isCurrent && <Check className="w-3.5 h-3.5 text-[#d4af37]" />}
                        </button>
                      );
                    })}
                  </div>

                  <div className="border-t border-[#1b1d28] mt-1 pt-1">
                    <button
                      onClick={() => {
                        setShowPersonaMenu(false);
                        logout();
                      }}
                      className="w-full flex items-center space-x-2 p-2 rounded text-xs text-rose-400 hover:bg-rose-950/20 transition-colors font-mono"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Cerrar Sesión</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

        </div>

      </div>
    </header>
  );
}
