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
    <header className="border-b border-[#1c1d24] bg-[#0d0e12] px-6 py-2.5 sticky top-0 z-40">
      <div className="flex items-center justify-between">
        
        {/* Brand & Identity - Minimalist */}
        <div className="flex items-center space-x-3">
          <div className="w-7 h-7 rounded-md bg-[#16171d] border border-[#d4af37]/40 flex items-center justify-center text-[#d4af37] font-bold text-xs shadow-sm">
            SM
          </div>
          <div className="flex items-baseline space-x-2">
            <h1 className="text-sm font-semibold tracking-tight text-white uppercase font-mono">
              SupplyMind AI
            </h1>
            <span className="text-zinc-600 font-light text-xs">/</span>
            <span className="text-xs text-zinc-400 font-mono hidden sm:inline">
              Conciliación Comercial
            </span>
          </div>
        </div>

        {/* Right Minimal Controls */}
        <div className="flex items-center space-x-3">
          
          {/* Subtle Live Status */}
          <div className="hidden sm:flex items-center space-x-2 px-2.5 py-1 rounded bg-[#13141a] border border-[#1e2029] text-[11px] text-zinc-400 font-mono">
            <span className={`w-1.5 h-1.5 rounded-full ${isLive ? 'bg-emerald-500' : 'bg-zinc-500'}`} />
            <span>Grok 4.7</span>
          </div>

          {/* Primary Action Button: Poner Caso */}
          {onOpenCreateCase && (
            <button
              onClick={onOpenCreateCase}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-[#242116] hover:bg-[#2e2a1b] border border-[#d4af37]/60 hover:border-[#d4af37] text-xs font-mono text-[#eed98d] font-semibold transition-all shadow-sm"
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
                className="flex items-center space-x-2 px-2.5 py-1.5 rounded-md bg-[#13141a] hover:bg-[#181922] border border-[#1e2029] hover:border-[#2f3140] text-xs transition-colors"
                title="Cambiar perfil"
              >
                <span className="text-sm leading-none">{currentUser.avatar || '👤'}</span>
                <span className="text-xs font-medium text-zinc-300 hidden md:inline">
                  {currentUser.name.split(' ')[0]}
                </span>
                <ChevronDown className="w-3 h-3 text-zinc-500" />
              </button>

              {/* Persona Dropdown */}
              {showPersonaMenu && (
                <div className="absolute right-0 mt-2 w-64 rounded-lg bg-[#14151a] border border-[#242633] shadow-2xl p-1.5 z-50 animate-in fade-in duration-100">
                  <div className="px-3 py-1.5 border-b border-[#1f202b] mb-1">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
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
                          className={`w-full flex items-center justify-between p-2 rounded text-left transition-colors ${
                            isCurrent
                              ? 'bg-[#1e202b] text-white font-medium'
                              : 'text-zinc-400 hover:bg-[#181922] hover:text-zinc-200'
                          }`}
                        >
                          <div className="flex items-center space-x-2">
                            <span>{p.avatar}</span>
                            <div>
                              <div className="text-xs">{p.name}</div>
                              <div className="text-[10px] text-zinc-500">{p.title}</div>
                            </div>
                          </div>
                          {isCurrent && <Check className="w-3.5 h-3.5 text-[#d4af37]" />}
                        </button>
                      );
                    })}
                  </div>

                  <div className="border-t border-[#1f202b] mt-1 pt-1">
                    <button
                      onClick={() => {
                        setShowPersonaMenu(false);
                        logout();
                      }}
                      className="w-full flex items-center space-x-2 p-2 rounded text-xs text-rose-400 hover:bg-rose-950/30 transition-colors font-mono"
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
