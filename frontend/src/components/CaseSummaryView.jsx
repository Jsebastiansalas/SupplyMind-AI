import React from 'react';
import { 
  Play, 
  FileText, 
  ShieldCheck, 
  Scale, 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  FileCheck2,
  FolderOpen,
  ArrowRight,
  Sparkles,
  Activity
} from 'lucide-react';

export default function CaseSummaryView({ 
  caseDetails, 
  onRunAudit, 
  isAnalyzing 
}) {
  if (!caseDetails) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-zinc-500 font-mono text-xs">
        <FolderOpen className="w-8 h-8 mb-2 opacity-40" />
        <span>Cargando expediente...</span>
      </div>
    );
  }

  const mapped = caseDetails.mapped_documents || {};
  const docChecklist = [
    { role: 'invoice', label: 'Factura Comercial', req: 'invoice.json / .pdf' },
    { role: 'purchase_order', label: 'Orden de Compra', req: 'purchase_order.json / .pdf' },
    { role: 'delivery', label: 'Remisión de Entrega', req: 'delivery.json / .pdf / .png' },
    { role: 'payment', label: 'Comprobante de Pago', req: 'payment.json / .pdf' },
    { role: 'contract', label: 'Contrato Comercial', req: 'contract.json / .pdf / .md' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-4 animate-in fade-in duration-200">
      
      {/* Top Banner: Resumen y Estado */}
      <div className="p-6 rounded-xl bg-[#111216] border border-[#232530] shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2.5">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-950/60 text-amber-300 border border-amber-500/30">
                PENDIENTE DE CONCILIACIÓN
              </span>
              <span className="text-zinc-500 text-xs font-mono">
                {caseDetails.case_id}
              </span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              {caseDetails.display_name}
            </h2>
            <p className="text-xs text-zinc-400 max-w-2xl leading-relaxed">
              {caseDetails.description || 'Expediente comercial cargado en cartera listo para arbitraje.'}
            </p>
          </div>

          {/* Action Call to Action Button */}
          <div className="flex-shrink-0">
            <button
              onClick={onRunAudit}
              disabled={isAnalyzing}
              className="w-full md:w-auto px-6 py-3 rounded-lg bg-[#242116] hover:bg-[#2e2a1a] border border-[#d4af37] text-[#eed98d] hover:text-white font-mono font-bold text-xs uppercase tracking-wider transition-all flex items-center justify-center space-x-2.5 shadow-lg hover:shadow-[#d4af37]/10 disabled:opacity-50"
            >
              {isAnalyzing ? (
                <>
                  <Activity className="w-4 h-4 animate-spin text-[#d4af37]" />
                  <span>Conciliando Expediente...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 text-[#d4af37] fill-[#d4af37]" />
                  <span>Iniciar Conciliación</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Grid: 2 Columnas de Preparación */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        
        {/* Columna 1: Documentos del Expediente */}
        <div className="p-5 rounded-xl bg-[#111216] border border-[#20222a] space-y-3">
          <div className="flex items-center justify-between border-b border-[#1d1f27] pb-3">
            <div className="flex items-center space-x-2 text-zinc-300">
              <FileText className="w-4 h-4 text-[#d4af37]" />
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider">
                Documentos Encontrados ({caseDetails.files_count || 0})
              </h3>
            </div>
            <span className="text-[10px] font-mono text-zinc-500">
              Clasificación Automática
            </span>
          </div>

          <div className="space-y-2 pt-1">
            {docChecklist.map((item) => {
              const detected = mapped[item.role];
              return (
                <div 
                  key={item.role}
                  className="flex items-center justify-between px-3 py-2 rounded-lg bg-[#14151c] border border-[#1e2029] text-xs font-mono"
                >
                  <div className="flex items-center space-x-2 truncate">
                    {detected ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    ) : (
                      <Clock className="w-4 h-4 text-zinc-600 flex-shrink-0" />
                    )}
                    <span className="text-zinc-300 font-medium">{item.label}</span>
                  </div>
                  <span className="text-[11px] text-zinc-400 truncate max-w-[140px]">
                    {detected || item.req}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Columna 2: Reglas que evaluará el Agente */}
        <div className="p-5 rounded-xl bg-[#111216] border border-[#20222a] space-y-3">
          <div className="flex items-center justify-between border-b border-[#1d1f27] pb-3">
            <div className="flex items-center space-x-2 text-zinc-300">
              <ShieldCheck className="w-4 h-4 text-[#d4af37]" />
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider">
                Criterios de Conciliación
              </h3>
            </div>
            <span className="text-[10px] font-mono text-zinc-500">
              Cero Alucinación
            </span>
          </div>

          <div className="space-y-2.5 pt-1 text-xs font-mono text-zinc-400">
            <div className="p-3 rounded-lg bg-[#14151c] border border-[#1e2029] space-y-1">
              <div className="text-zinc-200 font-medium flex items-center space-x-1.5">
                <span className="text-[#d4af37]">1.</span>
                <span>Cruce Matemático Exacto (Decimal)</span>
              </div>
              <p className="text-[11px] text-zinc-500">
                Conciliación línea por línea de cantidades facturadas vs recibidas y precios unitarios pactados en orden de compra.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-[#14151c] border border-[#1e2029] space-y-1">
              <div className="text-zinc-200 font-medium flex items-center space-x-1.5">
                <span className="text-[#d4af37]">2.</span>
                <span>Auditoría de Remisión Física</span>
              </div>
              <p className="text-[11px] text-zinc-500">
                Inspección de firmas, sellos de discrepancia en muelle de recepción y reportes de avería.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-[#14151c] border border-[#1e2029] space-y-1">
              <div className="text-zinc-200 font-medium flex items-center space-x-1.5">
                <span className="text-[#d4af37]">3.</span>
                <span>Contraste Contractual</span>
              </div>
              <p className="text-[11px] text-zinc-500">
                Evaluación jurídica de cláusulas de tolerancia, ventanas de notificación y legalidad de penalizaciones retenidas.
              </p>
            </div>
          </div>
        </div>

      </div>

      {/* Footer Hint */}
      <div className="text-center py-2">
        <p className="text-xs text-zinc-500 font-mono">
          Haz clic en <span className="text-[#eed98d] font-semibold">"Iniciar Conciliación"</span> para que el agente ejecute el análisis y emita el dictamen financiero.
        </p>
      </div>

    </div>
  );
}
