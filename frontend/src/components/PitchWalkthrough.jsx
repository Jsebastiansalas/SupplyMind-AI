import React from 'react';
import { 
  Sparkles, 
  ChevronRight, 
  ChevronLeft, 
  X, 
  Scale, 
  Clock, 
  Layers, 
  Award, 
  FileCheck,
  Sliders,
  Printer
} from 'lucide-react';

export const PITCH_STEPS = [
  {
    step: 1,
    title: "1. La Deducción Oculta & Balance Aritmético",
    tab: "financial",
    subtab: "summary",
    icon: Layers,
    description: "Los retailers retienen fondos de manera opaca. SupplyMind AI calcula instantáneamente con precisión Decimal (cero alucinación) la ecuación: Facturado — Cobrado = Reclamable.",
    highlight: "Observa la franja contable superior con la causa raíz identificada de inmediato.",
    cta: null
  },
  {
    step: 2,
    title: "2. Auditoría de Caducidad (Notice Window - Cláusula 8.2)",
    tab: "financial",
    subtab: "summary",
    icon: Clock,
    description: "La trampa más común: el comprador deduce dinero fuera de plazo. Si el reclamo supera los 30 días naturales, la deducción queda extemporánea y nula de pleno derecho.",
    highlight: "Observa la tarjeta de Caducidad Contractual que precluye reclamos vencidos.",
    cta: null
  },
  {
    step: 3,
    title: "3. Conciliación Quirúrgica SKU por SKU & IVA 16%",
    tab: "financial",
    subtab: "sku_matching",
    icon: Scale,
    description: "Auditoría determinística renglón por renglón. Compara cantidades recibidas en remisión vs facturadas, detecta discrepancias de precio unitario y calcula la Nota de Crédito con IVA al 16%.",
    highlight: "Cambia a la pestaña 'Auditoría SKU por SKU & IVA 16%' para ver el desglose unitario.",
    cta: null
  },
  {
    step: 4,
    title: "4. Tribunal Colegiado (100 Pts) & Sandbox en Vivo",
    tab: "tribunal",
    subtab: null,
    icon: Award,
    description: "Un jurado evaluador con tres magistrados (CFO 40pts, Jurídico 30pts, Operaciones 30pts) califica la resolución. Además, puedes alterar cualquier variable en vivo con el Simulador.",
    highlight: "Prueba el Sandbox interactivo con respuesta determinística en menos de 50 ms.",
    cta: "open_sandbox"
  },
  {
    step: 5,
    title: "5. Dictamen Pericial Oficial Imprimible & ROI 16,070x",
    tab: "financial",
    subtab: "digital_cert",
    icon: FileCheck,
    description: "Un entregable formal bancario con sello SHA-256, QR criptográfico, póliza NIF C-3 y firmas del tribunal, listo para imprimir en PDF y entregar al SAT o a la Dirección General.",
    highlight: "Abre el Dictamen Pericial Oficial listo para imprimir o enviar a la junta directiva.",
    cta: "open_dossier"
  }
];

export default function PitchWalkthrough({ 
  currentStepIndex, 
  onNext, 
  onPrev, 
  onClose, 
  onOpenSandbox, 
  onOpenDossier 
}) {
  const current = PITCH_STEPS[currentStepIndex] || PITCH_STEPS[0];
  const Icon = current.icon;
  const isLast = currentStepIndex === PITCH_STEPS.length - 1;
  const isFirst = currentStepIndex === 0;

  return (
    <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-50 w-full max-w-2xl px-4 animate-in fade-in slide-in-from-bottom-4 duration-200">
      <div className="bg-[#121318]/95 backdrop-blur-md border border-[#d4af37]/40 rounded-xl shadow-2xl p-4 sm:p-5 text-white">
        
        {/* Step Progress Bar & Top Bar */}
        <div className="flex items-center justify-between pb-3 border-b border-[#242630] mb-3">
          <div className="flex items-center space-x-2">
            <span className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-[#241f12] text-[#eed98d] border border-[#d4af37]/50 text-[10px] font-mono font-bold tracking-wider uppercase">
              <Sparkles className="w-3 h-3 text-[#d4af37]" />
              <span>Modo Demostración Jurado</span>
            </span>
            <span className="text-zinc-500 font-mono text-xs">•</span>
            <span className="text-zinc-400 font-mono text-xs">
              Paso {current.step} de {PITCH_STEPS.length}
            </span>
          </div>

          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white p-1 rounded-md hover:bg-zinc-800 transition-colors"
            title="Cerrar Modo Jurado"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex items-start space-x-3.5">
          <div className="p-2 rounded-lg bg-[#181920] border border-[#2d303e] text-[#eed98d] flex-shrink-0 mt-0.5">
            <Icon className="w-5 h-5 text-[#d4af37]" />
          </div>

          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-bold text-zinc-100 tracking-tight">
              {current.title}
            </h4>
            <p className="text-xs text-zinc-300 mt-1 leading-relaxed">
              {current.description}
            </p>
            <div className="mt-2 text-[11px] font-mono text-[#eed98d] flex items-center space-x-1.5 bg-[#17181f] px-2.5 py-1.5 rounded border border-[#272935]">
              <span>💡</span>
              <span>{current.highlight}</span>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center justify-between pt-3.5 mt-3 border-t border-[#20222a]">
          
          {/* Quick Action Button for this step (if any) */}
          <div>
            {current.cta === 'open_sandbox' && (
              <button
                onClick={onOpenSandbox}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-[#1a1b24] hover:bg-[#232532] border border-[#d4af37]/40 text-xs text-[#eed98d] transition-colors"
              >
                <Sliders className="w-3.5 h-3.5 text-[#d4af37]" />
                <span>Abrir Simulador Sandbox</span>
              </button>
            )}

            {current.cta === 'open_dossier' && (
              <button
                onClick={onOpenDossier}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-[#d4af37] hover:bg-[#c49f2e] text-black font-semibold text-xs transition-colors shadow-sm"
              >
                <Printer className="w-3.5 h-3.5 text-black" />
                <span>Ver Dictamen Pericial PDF</span>
              </button>
            )}
          </div>

          {/* Stepper Buttons */}
          <div className="flex items-center space-x-2">
            <button
              onClick={onPrev}
              disabled={isFirst}
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-md border text-xs transition-colors ${
                isFirst 
                  ? 'border-transparent text-zinc-600 cursor-not-allowed' 
                  : 'border-[#2d303d] bg-[#16171d] hover:bg-[#1f2028] text-zinc-300'
              }`}
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Anterior</span>
            </button>

            {isLast ? (
              <button
                onClick={onClose}
                className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-colors"
              >
                <span>Concluir Demostración</span>
              </button>
            ) : (
              <button
                onClick={onNext}
                className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-md bg-[#d4af37] hover:bg-[#c49f2e] text-black font-semibold text-xs transition-colors shadow-sm"
              >
                <span>Siguiente Paso</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
