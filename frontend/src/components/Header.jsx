import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  LogOut, 
  ChevronDown, 
  Check, 
  Activity
} from 'lucide-react';

export default function Header({ health, activeCaseName, isAnalyzing }) {
  const { currentUser, logout, loginAsPersona, personas } = useAuth();
  const [showPersonaMenu, setShowPersonaMenu] = useState(false);

  const isLive = health?.status === 'online';

  return (
    <header className="border-b border-[#20222a] bg-[#0f1013] px-6 py-3 sticky top-0 z-40">
      <div className="flex items-center justify-between">
        
        {/* Brand & Identity - Sovereign Ledger Style */}
        <div className="flex items-center space-x-3.5">
          <div className="w-8 h-8 rounded-lg bg-[#18191e] border border-[#d4af37]/40 flex items-center justify-center text-[#d4af37] font-bold text-xs tracking-wider shadow-sm flex-shrink-0">
            SM
          </div>
          <div className="flex items-baseline space-x-2">
            <h1 className="text-sm font-semibold tracking-tight text-white uppercase">
              SupplyMind
            </h1>
            <span className="text-zinc-600 font-light text-xs">/</span>
            <span className="text-xs text-zinc-400 tracking-wide font-normal hidden sm:inline">
              Arbitraje & Conciliación B2B
            </span>
          </div>
        </div>

        {/* Right Telemetry & Persona Dropdown */}
        <div className="flex items-center space-x-3">
          
          {/* Active Case Tag */}
          {activeCaseName && (
            <div className="hidden md:flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-[#16171c] border border-[#262832] text-xs">
              <span className="text-zinc-500 font-mono text-[11px]">Expediente:</span>
              <span className="font-mono text-zinc-200 font-medium text-[11px]">{activeCaseName}</span>
            </div>
          )}

          {/* Discreet Engine Status */}
          <div className="flex items-center space-x-2 px-2.5 py-1 rounded-md bg-[#16171c] border border-[#262832] text-[11px] text-zinc-400 font-mono">
            <span className={`w-1.5 h-1.5 rounded-full ${isLive ? 'bg-emerald-500' : 'bg-zinc-500'}`} />
            <span>Grok 4.7 Gateway</span>
          </div>

          {/* In-Flight Audit Indicator */}
          {isAnalyzing && (
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-[#241f12] border border-[#d4af37]/40 text-[11px] text-[#eed98d] font-mono">
              <Activity className="w-3 h-3 animate-spin text-[#d4af37]" />
              <span>Auditando...</span>
            </div>
          )}

          {/* Active User Persona Profile */}
          {currentUser && (
            <div className="relative pl-1">
              <button
                onClick={() => setShowPersonaMenu(!showPersonaMenu)}
                className="flex items-center space-x-2.5 px-3 py-1.5 rounded-md bg-[#16171c] hover:bg-[#1c1d23] border border-[#262832] hover:border-[#383a48] text-xs transition-colors"
                title="Cambiar rol o persona"
              >
                <span className="text-sm leading-none">{currentUser.avatar || '👤'}</span>
                <div className="text-left hidden sm:block">
                  <div className="text-xs font-medium text-zinc-200 leading-tight">
                    {currentUser.name}
                  </div>
                  <div className="text-[10px] text-zinc-500 truncate max-w-[140px]">
                    {currentUser.title}
                  </div>
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-zinc-400 ml-1" />
              </button>

              {/* Persona Switcher Dropdown */}
              {showPersonaMenu && (
                <div className="absolute right-0 mt-2 w-72 rounded-lg bg-[#14151a] border border-[#2a2c36] shadow-xl p-1.5 z-50 animate-in fade-in duration-100">
                  <div className="px-3 py-1.5 border-b border-[#22242c] mb-1">
                    <span className="text-[10px] font-mono font-medium text-zinc-400 uppercase tracking-wider">
                      Perfil Activo
                    </span>
                  </div>

                  <div className="space-y-0.5">
                    {Object.values(personas).map((p) => {
                      const isCurrent = currentUser?.id === p.id;
                      return (
                        <button
                          key={p.id}
                          onClick={() => {
                            loginAsPersona(p.id);
                            setShowPersonaMenu(false);
                          }}
                          className={`w-full text-left p-2 rounded-md text-xs transition-colors flex items-center justify-between ${
                            isCurrent
                              ? 'bg-[#1c1d24] text-white border border-[#d4af37]/40 font-medium'
                              : 'hover:bg-[#181920] text-zinc-400 hover:text-zinc-200'
                          }`}
                        >
                          <div className="flex items-center space-x-2.5">
                            <span className="text-sm">{p.avatar}</span>
                            <div>
                              <div className="text-xs leading-snug">{p.name}</div>
                              <div className="text-[10px] text-zinc-500">{p.title}</div>
                            </div>
                          </div>
                          {isCurrent && <Check className="w-3.5 h-3.5 text-[#d4af37]" />}
                        </button>
                      );
                    })}
                  </div>

                  <div className="pt-1.5 mt-1.5 border-t border-[#22242c] px-2 flex justify-between items-center text-[11px]">
                    <span className="text-zinc-600 font-mono text-[10px]">Sesión Activa</span>
                    <button
                      onClick={() => {
                        logout();
                        setShowPersonaMenu(false);
                      }}
                      className="text-zinc-400 hover:text-rose-400 text-[11px] flex items-center gap-1 transition-colors"
                    >
                      <LogOut className="w-3 h-3" />
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
