import React, { useState } from 'react';
import { 
  FileText, 
  ExternalLink, 
  Download, 
  Image as ImageIcon, 
  Eye, 
  FileSpreadsheet, 
  FileCheck, 
  Scale, 
  ShieldCheck, 
  Layers,
  Link2,
  AlertTriangle,
  CheckCircle2
} from 'lucide-react';
import { apiClient } from '../api/client';

export default function EvidenceViewer({ caseId, caseDetails, report }) {
  const [selectedFile, setSelectedFile] = useState(null);

  const files = caseDetails?.files || [];
  const evidenceList = report?.evidence || [];
  const manifest = report?.evidence_manifest || null;

  const getDocTypeIcon = (ext) => {
    if (['.png', '.jpg', '.jpeg'].includes(ext)) return <ImageIcon className="w-4 h-4 text-emerald-400" />;
    if (ext === '.pdf') return <FileText className="w-4 h-4 text-indigo-400" />;
    if (ext === '.json') return <FileSpreadsheet className="w-4 h-4 text-cyan-400" />;
    return <FileText className="w-4 h-4 text-slate-400" />;
  };

  return (
    <div className="space-y-6">
      
      {/* Pilar 3: Anclaje Fáctico Estricto & Zero Uncited Claims Banner */}
      {manifest && (
        <div className="bg-[#101116] border border-[#1b1c24] p-4 rounded-lg shadow-subtle space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1b1c24] pb-2.5">
            <div className="flex items-center space-x-2 text-[#d4af37]">
              <Link2 className="w-4 h-4" />
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-100">
                Anclaje Fáctico Estricto & Cero Alucinación (Pilar 3)
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold flex items-center gap-1 ${
                manifest.binding_verdict === 'FULL_EVIDENCE_BINDING_VERIFIED'
                  ? 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40'
                  : 'bg-amber-950/60 text-amber-300 border-amber-500/40'
              }`}>
                {manifest.binding_verdict === 'FULL_EVIDENCE_BINDING_VERIFIED' ? (
                  <>
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    <span>100% Respaldo Probatorio Verificado</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-3 h-3 text-amber-400" />
                    <span>{manifest.cautelar_items?.length || 0} Partida(s) Cautelar(es)</span>
                  </>
                )}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#161722] text-zinc-300 border border-[#222432]">
                Ratio: <strong className="text-[#d4af37]">{manifest.backing_ratio_pct}%</strong>
              </span>
            </div>
          </div>

          {/* Cautelar Items Alert */}
          {manifest.cautelar_items?.length > 0 && (
            <div className="p-3 rounded bg-amber-950/30 border border-amber-500/30 space-y-1.5">
              <div className="flex items-center space-x-2 text-amber-300 text-xs font-bold font-mono">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Observaciones de Acreditación (Requiere Comprobante Físico):</span>
              </div>
              <ul className="text-[11px] text-zinc-300 space-y-1 pl-5 list-disc font-sans">
                {manifest.cautelar_items.map((item, idx) => (
                  <li key={idx} className="leading-relaxed">{item}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Pointers Grid */}
          {manifest.evidence_pointers?.length > 0 && (
            <div className="space-y-2 pt-1">
              <div className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider">
                Punteros Probatorios Auditados ({manifest.evidence_pointers.length})
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-56 overflow-y-auto pr-1">
                {manifest.evidence_pointers.map((ptr, idx) => {
                  const isOk = ptr.status === 'ACREDITADO';
                  return (
                    <div 
                      key={idx}
                      className={`p-2.5 rounded border text-xs leading-relaxed flex items-start justify-between gap-2 ${
                        isOk
                          ? 'bg-[#0e0f14] border-[#1b1d26] text-zinc-300'
                          : 'bg-amber-950/20 border-amber-500/30 text-amber-200'
                      }`}
                    >
                      <div className="space-y-0.5 min-w-0">
                        <div className="flex items-center gap-1.5 font-mono text-[10px]">
                          <span className="text-[#d4af37] font-bold">[{ptr.doc_type}]</span>
                          <span className="text-zinc-400 truncate">{ptr.doc_id}</span>
                          {ptr.item_sku && (
                            <span className="text-indigo-300 font-bold truncate">#{ptr.item_sku}</span>
                          )}
                        </div>
                        <div className="text-[11px] font-sans text-zinc-300 leading-snug">
                          {ptr.citation_tag}
                        </div>
                      </div>
                      <div className="flex flex-col items-end flex-shrink-0">
                        <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded uppercase font-bold border ${
                          isOk 
                            ? 'bg-emerald-950/40 text-emerald-300 border-emerald-500/30' 
                            : 'bg-amber-950/40 text-amber-300 border-amber-500/30'
                        }`}>
                          {isOk ? 'Acreditado' : 'Cautelar'}
                        </span>
                        {ptr.amount > 0 && (
                          <span className="text-[10px] font-mono font-bold text-zinc-200 mt-1">
                            ${Number(ptr.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Fallback Evidence Citations Banner if no manifest */}
      {!manifest && evidenceList.length > 0 && (
        <div className="bg-[#101116] border border-[#1b1c24] p-4 rounded-lg shadow-subtle">
          <div className="flex items-center space-x-2 text-[#d4af37] mb-3">
            <ShieldCheck className="w-4 h-4" />
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-100">
              Citas Documentales y Respaldo Probatorio Cotejado
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {evidenceList.map((ev, idx) => {
              const isContract = ev.toLowerCase().includes('contract') || ev.toLowerCase().includes('cláusula') || ev.toLowerCase().includes('clausula');
              return (
                <div 
                  key={idx}
                  className={`p-2.5 rounded border text-xs leading-relaxed flex items-start space-x-2.5 ${
                    isContract
                      ? 'bg-[#141524] border-[#252842] text-indigo-200'
                      : 'bg-[#0e0f14] border-[#1b1d26] text-zinc-300'
                  }`}
                >
                  <span className="font-mono text-[#d4af37] font-bold text-[11px]">#{idx + 1}</span>
                  <span className="font-sans text-[11px]">{ev}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Grid of Documents in Case */}
      <div>
        <div className="flex items-center justify-between mb-3.5">
          <div className="flex items-center space-x-2 text-white">
            <Layers className="w-4 h-4 text-[#d4af37]" />
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider">
              Bóveda de Expedientes Integrantes ({files.length})
            </h3>
          </div>
          <span className="text-[11px] text-zinc-500 font-mono">
            Haga clic en un archivo para auditar en visor
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {files.map((f, idx) => {
            const url = apiClient.getDocumentUrl(caseId, f.filename);
            const isSelected = selectedFile?.filename === f.filename;

            return (
              <div
                key={idx}
                className={`p-3.5 rounded-lg border transition-all cursor-pointer ${
                  isSelected 
                    ? 'bg-[#151620] border-[#d4af37]/60 shadow-subtle' 
                    : 'bg-[#101116] border-[#1b1c24] hover:border-[#2b2e3e] hover:bg-[#121319]'
                }`}
                onClick={() => setSelectedFile(f)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2.5">
                    <div className="p-2 rounded bg-[#0b0c10] border border-[#1b1c24]">
                      {getDocTypeIcon(f.extension)}
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-zinc-100 font-mono truncate max-w-[170px]">
                        {f.filename}
                      </h4>
                      <p className="text-[10px] text-zinc-500 font-mono tabular-nums">
                        {(f.size_bytes / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  
                  <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded uppercase font-bold border ${
                    f.is_pdf ? 'bg-indigo-950/40 text-indigo-300 border-indigo-800/40' :
                    f.is_image ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/40' :
                    'bg-[#14151c] text-zinc-400 border-[#222430]'
                  }`}>
                    {f.extension.replace('.', '')}
                  </span>
                </div>

                {/* Actions */}
                <div className="mt-3 pt-2.5 border-t border-[#181922] flex items-center justify-between text-[11px] font-mono">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedFile(f);
                    }}
                    className="btn-tactile text-[#eed98d] hover:text-white flex items-center gap-1 font-medium"
                  >
                    <Eye className="w-3.5 h-3.5 text-[#d4af37]" />
                    Visor
                  </button>

                  <a
                    href={url}
                    download={f.filename}
                    onClick={(e) => e.stopPropagation()}
                    className="btn-tactile text-zinc-400 hover:text-white flex items-center gap-1"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Descargar
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Document Preview Panel */}
      {selectedFile && (
        <div className="p-4 rounded-lg bg-[#0e0f14] border border-[#2b2e3e] shadow-elevated space-y-3">
          <div className="flex items-center justify-between border-b border-[#1b1c24] pb-2.5">
            <div className="flex items-center space-x-2">
              <Eye className="w-4 h-4 text-[#d4af37]" />
              <h4 className="text-xs font-bold text-white font-mono uppercase tracking-wider">
                Visor Forense: {selectedFile.filename}
              </h4>
            </div>
            <button
              onClick={() => setSelectedFile(null)}
              className="btn-tactile text-xs text-zinc-400 hover:text-white px-2.5 py-1 rounded bg-[#161720] border border-[#222432] font-mono"
            >
              Cerrar Visor
            </button>
          </div>

          <div className="min-h-64 max-h-[500px] overflow-auto rounded bg-[#08090b] border border-[#181922] flex items-center justify-center p-3">
            {selectedFile.is_image ? (
              <img 
                src={apiClient.getDocumentUrl(caseId, selectedFile.filename)} 
                alt={selectedFile.filename}
                className="max-h-[460px] object-contain rounded"
              />
            ) : selectedFile.is_pdf ? (
              <iframe
                src={apiClient.getDocumentUrl(caseId, selectedFile.filename)}
                title={selectedFile.filename}
                className="w-full h-[460px] rounded border-0"
              />
            ) : (
              <div className="text-center p-6 text-zinc-400 text-xs font-mono">
                <FileText className="w-8 h-8 mx-auto mb-2 text-zinc-600" />
                <p>Archivo de datos tabulares / estructurados.</p>
                <a
                  href={apiClient.getDocumentUrl(caseId, selectedFile.filename)}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-flex items-center gap-1 text-[#eed98d] hover:underline"
                >
                  Abrir en pestaña independiente <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
