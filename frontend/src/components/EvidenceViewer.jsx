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
  Layers
} from 'lucide-react';
import { apiClient } from '../api/client';

export default function EvidenceViewer({ caseId, caseDetails, report }) {
  const [selectedFile, setSelectedFile] = useState(null);

  const files = caseDetails?.files || [];
  const evidenceList = report?.evidence || [];

  const getDocTypeIcon = (ext) => {
    if (['.png', '.jpg', '.jpeg'].includes(ext)) return <ImageIcon className="w-4 h-4 text-emerald-400" />;
    if (ext === '.pdf') return <FileText className="w-4 h-4 text-indigo-400" />;
    if (ext === '.json') return <FileSpreadsheet className="w-4 h-4 text-cyan-400" />;
    return <FileText className="w-4 h-4 text-slate-400" />;
  };

  return (
    <div className="space-y-6">
      
      {/* Evidence Citations Banner */}
      {evidenceList.length > 0 && (
        <div className="glass-card p-5 rounded-2xl">
          <div className="flex items-center space-x-2 text-cyan-400 mb-3">
            <ShieldCheck className="w-4 h-4" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-white">
              Citas Documentales y Respaldo Probatorio Verificado
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {evidenceList.map((ev, idx) => {
              const isContract = ev.toLowerCase().includes('contract') || ev.toLowerCase().includes('cláusula') || ev.toLowerCase().includes('clausula');
              return (
                <div 
                  key={idx}
                  className={`p-3 rounded-xl border text-xs leading-relaxed flex items-start space-x-2.5 ${
                    isContract
                      ? 'bg-indigo-950/20 border-indigo-800/40 text-indigo-200'
                      : 'bg-slate-900/60 border-slate-800 text-slate-300'
                  }`}
                >
                  <span className="font-mono text-cyan-400 font-bold">#{idx + 1}</span>
                  <span>{ev}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Grid of Documents in Case */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2 text-white">
            <Layers className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider">
              Documentos Integrantes del Expediente ({files.length})
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Haga clic en un archivo para previsualizar o descargar
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {files.map((f, idx) => {
            const url = apiClient.getDocumentUrl(caseId, f.filename);
            const isSelected = selectedFile?.filename === f.filename;

            return (
              <div
                key={idx}
                className={`glass-card p-4 rounded-xl border transition-all cursor-pointer ${
                  isSelected ? 'border-cyan-500 ring-1 ring-cyan-500/30' : 'hover:border-slate-700'
                }`}
                onClick={() => setSelectedFile(f)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2.5">
                    <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                      {getDocTypeIcon(f.extension)}
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-white font-mono truncate max-w-[180px]">
                        {f.filename}
                      </h4>
                      <p className="text-[11px] text-slate-400 font-mono">
                        {(f.size_bytes / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  
                  <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded uppercase font-semibold ${
                    f.is_pdf ? 'bg-indigo-950/60 text-indigo-300' :
                    f.is_image ? 'bg-emerald-950/60 text-emerald-300' :
                    'bg-slate-800 text-slate-400'
                  }`}>
                    {f.extension.replace('.', '')}
                  </span>
                </div>

                {/* Actions */}
                <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center justify-between">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedFile(f);
                    }}
                    className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    Previsualizar
                  </button>

                  <a
                    href={url}
                    download={f.filename}
                    onClick={(e) => e.stopPropagation()}
                    className="text-[11px] text-slate-400 hover:text-white flex items-center gap-1"
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
        <div className="glass-panel p-5 rounded-2xl border border-cyan-500/30 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Eye className="w-4 h-4 text-cyan-400" />
              <h4 className="text-xs font-bold text-white font-mono uppercase">
                Visor en Vivo: {selectedFile.filename}
              </h4>
            </div>
            <button
              onClick={() => setSelectedFile(null)}
              className="text-xs text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-800"
            >
              Cerrar
            </button>
          </div>

          <div className="min-h-64 max-h-[500px] overflow-auto rounded-xl bg-slate-950/90 border border-slate-800 flex items-center justify-center p-4">
            {selectedFile.is_image ? (
              <img 
                src={apiClient.getDocumentUrl(caseId, selectedFile.filename)} 
                alt={selectedFile.filename}
                className="max-h-[460px] object-contain rounded shadow-lg"
              />
            ) : selectedFile.is_pdf ? (
              <iframe
                src={apiClient.getDocumentUrl(caseId, selectedFile.filename)}
                title={selectedFile.filename}
                className="w-full h-[460px] rounded border-0"
              />
            ) : (
              <div className="text-center p-6 text-slate-400 text-xs">
                <FileText className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                <p>Archivo de texto o datos estructurados.</p>
                <a
                  href={apiClient.getDocumentUrl(caseId, selectedFile.filename)}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-flex items-center gap-1 text-cyan-400 hover:underline"
                >
                  Abrir en nueva pestaña <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
