import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  ArrowRight, 
  Sparkles, 
  CheckCircle2
} from 'lucide-react';

export default function SignInView({ health }) {
  const { personas, loginAsPersona, loginWithCredentials } = useAuth();
  const [email, setEmail] = useState('jurado.evaluador@platica.mx');
  const [password, setPassword] = useState('platica2026');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setTimeout(() => {
      loginWithCredentials(email, password);
      setIsSubmitting(false);
    }, 250);
  };

  const isLive = health?.status === 'online';

  return (
    <div className="min-h-screen bg-[#0c0d10] text-zinc-200 flex flex-col justify-center items-center p-4 relative overflow-hidden font-sans">
      
      {/* Subtle Engineering Grid */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-[0.02]"
        style={{
          backgroundImage: `
            linear-gradient(to right, #ffffff 1px, transparent 1px),
            linear-gradient(to bottom, #ffffff 1px, transparent 1px)
          `,
          backgroundSize: '36px 36px'
        }}
      />

      {/* Main Login Chassis Card */}
      <div className="w-full max-w-4xl rounded-xl border border-[#252732] bg-[#121317] shadow-2xl overflow-hidden relative z-10">
        
        {/* Top Header */}
        <div className="px-6 py-4 border-b border-[#20222a] bg-[#101115] flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-[#18191f] border border-[#d4af37]/40 flex items-center justify-center text-[#d4af37] font-bold text-xs tracking-wider shadow-sm">
              SM
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-semibold tracking-tight text-white uppercase">
                  SupplyMind
                </span>
                <span className="text-zinc-600 font-light text-xs">/</span>
                <span className="text-xs text-zinc-400 font-mono">
                  Arbitraje & Conciliación B2B
                </span>
              </div>
              <p className="text-[11px] text-zinc-500 font-sans">
                Reto Platica.mx × Campuslands • Terminal Institucional
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2 px-2.5 py-1 rounded bg-[#16171d] border border-[#262832] text-zinc-400 font-mono text-[11px]">
              <span className={`w-1.5 h-1.5 rounded-full ${isLive ? 'bg-emerald-500' : 'bg-zinc-500'}`} />
              <span>Grok 4.7 Gateway</span>
            </div>
          </div>
        </div>

        {/* Chassis Body */}
        <div className="p-6 md:p-8 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          
          {/* Columna Izquierda: Formulario de Acceso Directo */}
          <div className="lg:col-span-5 space-y-4">
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">
                Terminal de Acceso
              </h2>
              <p className="text-xs text-zinc-400 mt-1 leading-relaxed">
                Ingrese con credenciales institucionales o seleccione una persona preconfigurada.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3">
              <div>
                <label className="block text-[11px] font-mono text-zinc-400 mb-1 tracking-wider uppercase">
                  Usuario o Correo Institucional
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="nombre@empresa.com"
                  className="w-full px-3 py-2 bg-[#17181f] border border-[#282a35] rounded-md text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-[#d4af37]/60 font-mono transition-colors"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-zinc-400 mb-1 tracking-wider uppercase">
                  Contraseña / Token
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••••••"
                  className="w-full px-3 py-2 bg-[#17181f] border border-[#282a35] rounded-md text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-[#d4af37]/60 font-mono transition-colors"
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2 px-4 rounded-md bg-[#1d1f27] hover:bg-[#252732] active:bg-[#1a1b22] text-[#f4f4f7] font-semibold text-xs font-mono transition-all flex items-center justify-center space-x-2 border border-[#d4af37]/50 hover:border-[#d4af37] disabled:opacity-50"
              >
                <span>{isSubmitting ? 'Validando...' : 'Acceder al Workspace'}</span>
                <ArrowRight className="w-3.5 h-3.5 text-[#d4af37]" />
              </button>
            </form>

            <div className="pt-2 border-t border-[#20222a] space-y-1 text-[10px] font-mono text-zinc-500">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-3 h-3 text-[#d4af37]" />
                <span>Protocolo Determinístico Zero-Hallucination</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-3 h-3 text-[#d4af37]" />
                <span>Cálculo Decimal Exacto (Float-Free)</span>
              </div>
            </div>
          </div>

          {/* Columna Derecha: Fast Persona Login para Jurados & Clientes */}
          <div className="lg:col-span-7 bg-[#0f1013] p-5 rounded-lg border border-[#20222a] space-y-2.5">
            <div className="flex items-center justify-between border-b border-[#20222a] pb-2">
              <div>
                <span className="text-xs font-mono font-semibold text-zinc-200 uppercase tracking-wider flex items-center space-x-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-[#d4af37]" />
                  <span>Acceso Inmediato 1-Clic</span>
                </span>
                <p className="text-[11px] text-zinc-500 mt-0.5">
                  Perfiles configurados para evaluación y demostración:
                </p>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1c1d25] text-zinc-400 border border-[#2a2c38]">
                DEMO
              </span>
            </div>

            {/* Persona 1: Jurado VIP */}
            <button
              onClick={() => loginAsPersona('judge')}
              className="w-full text-left p-3 rounded-md bg-[#14151b] hover:bg-[#191a22] border border-[#232530] hover:border-[#d4af37]/50 transition-all flex items-center justify-between group"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-md bg-[#221f14] border border-[#d4af37]/30 flex items-center justify-center text-sm flex-shrink-0">
                  {personas.judge.avatar}
                </div>
                <div>
                  <div className="text-xs font-semibold text-zinc-200 group-hover:text-white transition-colors flex items-center space-x-2">
                    <span>{personas.judge.name}</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-[#242116] text-[#eed98d] border border-[#d4af37]/30">
                      VIP
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-500 mt-0.5 leading-snug">
                    Auditoría metodológica, cero alucinación, veredicto del Tribunal Colegiado (100 pts).
                  </p>
                </div>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-[#d4af37] opacity-0 group-hover:opacity-100 transition-opacity ml-2 flex-shrink-0" />
            </button>

            {/* Persona 2: CFO */}
            <button
              onClick={() => loginAsPersona('cfo')}
              className="w-full text-left p-3 rounded-md bg-[#14151b] hover:bg-[#191a22] border border-[#232530] hover:border-[#d4af37]/50 transition-all flex items-center justify-between group"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-md bg-[#181920] border border-[#282a35] flex items-center justify-center text-sm flex-shrink-0">
                  {personas.cfo.avatar}
                </div>
                <div>
                  <div className="text-xs font-semibold text-zinc-200 group-hover:text-white transition-colors flex items-center space-x-2">
                    <span>{personas.cfo.name}</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-[#181920] text-zinc-400 border border-[#262833]">
                      CFO
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-500 mt-0.5 leading-snug">
                    Cuadratura en Decimal, conciliación de subtotales y emisión de Notas de Crédito.
                  </p>
                </div>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-[#d4af37] opacity-0 group-hover:opacity-100 transition-opacity ml-2 flex-shrink-0" />
            </button>

            {/* Persona 3: Legal Counsel */}
            <button
              onClick={() => loginAsPersona('legal')}
              className="w-full text-left p-3 rounded-md bg-[#14151b] hover:bg-[#191a22] border border-[#232530] hover:border-[#d4af37]/50 transition-all flex items-center justify-between group"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-md bg-[#181920] border border-[#282a35] flex items-center justify-center text-sm flex-shrink-0">
                  {personas.legal.avatar}
                </div>
                <div>
                  <div className="text-xs font-semibold text-zinc-200 group-hover:text-white transition-colors flex items-center space-x-2">
                    <span>{personas.legal.name}</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-[#181920] text-zinc-400 border border-[#262833]">
                      LEGAL
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-500 mt-0.5 leading-snug">
                    Jerarquía probatoria (remisión &gt; factura), cláusulas contractuales y nulidad de penalizaciones.
                  </p>
                </div>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-[#d4af37] opacity-0 group-hover:opacity-100 transition-opacity ml-2 flex-shrink-0" />
            </button>

            {/* Persona 4: COO */}
            <button
              onClick={() => loginAsPersona('coo')}
              className="w-full text-left p-3 rounded-md bg-[#14151b] hover:bg-[#191a22] border border-[#232530] hover:border-[#d4af37]/50 transition-all flex items-center justify-between group"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-md bg-[#181920] border border-[#282a35] flex items-center justify-center text-sm flex-shrink-0">
                  {personas.coo.avatar}
                </div>
                <div>
                  <div className="text-xs font-semibold text-zinc-200 group-hover:text-white transition-colors flex items-center space-x-2">
                    <span>{personas.coo.name}</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-[#181920] text-zinc-400 border border-[#262833]">
                      COO
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-500 mt-0.5 leading-snug">
                    Entregas en muelle, sellos de transportista y resolución operativa comercial.
                  </p>
                </div>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-[#d4af37] opacity-0 group-hover:opacity-100 transition-opacity ml-2 flex-shrink-0" />
            </button>

          </div>

        </div>

      </div>

      {/* Footer */}
      <div className="mt-4 text-center text-[11px] font-mono text-zinc-600 z-10">
        SupplyMind AI • Sistema de Arbitraje Comercial B2B • xAI Grok 4.7
      </div>

    </div>
  );
}
