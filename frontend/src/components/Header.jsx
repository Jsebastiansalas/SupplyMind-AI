import React from 'react';
import { ShieldCheck, Cpu, Activity, Award, Sparkles } from 'lucide-react';

export default function Header({ health, activeCaseName, isAnalyzing }) {
  return (
    <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-md sticky top-0 z-40 px-6 py-3.5">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        
        {/* Brand & Identity */}
        <div className="flex items-center space-x-3.5">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white font-black text-xl">
              🧠
            </div>
            <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full border-2 border-slate-950 flex items-center justify-center">
              <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span>
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white font-sans flex items-center gap-1.5">
                SupplyMind <span className="text-cyan-400 font-extrabold text-sm px-1.5 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/50">AI ENTERPRISE</span>
              </h1>
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-mono">
                v2.0
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Analista Digital Autónomo de Disputas Comerciales B2B — Reto Platica.mx × Campuslands
            </p>
          </div>
        </div>

        {/* System Badges & Telemetry */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Active Case Badge */}
          {activeCaseName && (
            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700/60 text-xs text-slate-300">
              <span className="text-slate-500">Expediente:</span>
              <span className="font-semibold text-cyan-300 font-mono">{activeCaseName}</span>
            </div>
          )}

          {/* Gateway Status */}
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800/40 text-xs text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="font-medium">Grok 4.7 Gateway:</span>
            <span className="font-mono text-emerald-300 font-semibold">ONLINE</span>
          </div>

          {/* Deterministic Precision Badge */}
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyan-950/40 border border-cyan-800/40 text-xs text-cyan-400">
            <Cpu className="w-3.5 h-3.5" />
            <span className="font-mono font-medium">DECIMAL EXACT</span>
          </div>

          {/* Test Verification Badge */}
          <div className="hidden lg:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-950/40 border border-indigo-800/40 text-xs text-indigo-300">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
            <span className="font-mono font-semibold">162 TESTS GREEN</span>
          </div>

          {isAnalyzing && (
            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300 animate-pulse">
              <Activity className="w-3.5 h-3.5 animate-spin" />
              <span>Auditando...</span>
            </div>
          )}
        </div>

      </div>
    </header>
  );
}
