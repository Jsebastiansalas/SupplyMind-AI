import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Mail, 
  Copy, 
  Check, 
  Download, 
  Code, 
  Share2, 
  ShieldAlert 
} from 'lucide-react';
import { apiClient } from '../api/client';

export default function ExportModal({ caseId, report }) {
  const [activeTab, setActiveTab] = useState('letter');
  const [claimLetter, setClaimLetter] = useState('');
  const [emailDraft, setEmailDraft] = useState({ subject: '', body: '' });
  const [copiedKey, setCopiedKey] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadExports() {
      if (!caseId) return;
      setLoading(true);
      try {
        const [letter, email] = await Promise.all([
          apiClient.getClaimLetter(caseId).catch(() => 'No procede carta de reclamación para este caso.'),
          apiClient.getEmailDraft(caseId).catch(() => ({ subject: '', body: '' })),
        ]);
        setClaimLetter(letter);
        setEmailDraft(email);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadExports();
  }, [caseId, report]);

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const downloadTextFile = (content, filename) => {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      
      {/* Sub-tabs */}
      <div className="flex border-b border-slate-800 space-x-4">
        <button
          onClick={() => setActiveTab('letter')}
          className={`pb-3 text-xs font-bold uppercase tracking-wider flex items-center space-x-2 border-b-2 transition-all ${
            activeTab === 'letter'
              ? 'border-cyan-400 text-cyan-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Carta Formal de Reclamación (.md)</span>
        </button>

        <button
          onClick={() => setActiveTab('email')}
          className={`pb-3 text-xs font-bold uppercase tracking-wider flex items-center space-x-2 border-b-2 transition-all ${
            activeTab === 'email'
              ? 'border-indigo-400 text-indigo-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Mail className="w-4 h-4" />
          <span>Borrador de Correo B2B</span>
        </button>

        <button
          onClick={() => setActiveTab('json')}
          className={`pb-3 text-xs font-bold uppercase tracking-wider flex items-center space-x-2 border-b-2 transition-all ${
            activeTab === 'json'
              ? 'border-emerald-400 text-emerald-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Code className="w-4 h-4" />
          <span>Payload JSON para ERP</span>
        </button>
      </div>

      {/* Tab 1: Carta de Reclamación */}
      {activeTab === 'letter' && (
        <div className="glass-card p-6 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Carta Formal de Objeción de Deducción y Cobro Comercial
              </h3>
              <p className="text-xs text-slate-400">
                Documento legalmente fundamentado para enviar al departamento de cuentas por pagar del cliente.
              </p>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => copyToClipboard(claimLetter, 'letter')}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 flex items-center gap-1.5 transition-colors"
              >
                {copiedKey === 'letter' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedKey === 'letter' ? 'Copiado!' : 'Copiar Texto'}</span>
              </button>

              <button
                onClick={() => downloadTextFile(claimLetter, `Carta_Reclamacion_${caseId}.md`)}
                className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-xs font-bold text-white flex items-center gap-1.5 transition-colors shadow-md shadow-cyan-600/20"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Descargar .md</span>
              </button>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/90 border border-slate-800/80 font-mono text-xs text-slate-300 max-h-[450px] overflow-auto whitespace-pre-wrap leading-relaxed">
            {loading ? 'Cargando carta...' : claimLetter}
          </div>
        </div>
      )}

      {/* Tab 2: Borrador de Correo B2B */}
      {activeTab === 'email' && (
        <div className="glass-card p-6 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Borrador Institucional de Notificación por Correo
              </h3>
              <p className="text-xs text-slate-400">
                Listo para enviar directamente a la contraparte comercial.
              </p>
            </div>

            <button
              onClick={() => copyToClipboard(`Asunto: ${emailDraft.subject}\n\n${emailDraft.body}`, 'email')}
              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white flex items-center gap-1.5 transition-colors shadow-md shadow-indigo-600/20"
            >
              {copiedKey === 'email' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedKey === 'email' ? 'Copiado!' : 'Copiar Correo'}</span>
            </button>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-[11px] font-mono text-slate-400 uppercase">Asunto:</label>
              <div className="mt-1 p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white font-mono">
                {emailDraft.subject || 'Cargando asunto...'}
              </div>
            </div>

            <div>
              <label className="text-[11px] font-mono text-slate-400 uppercase">Cuerpo del Mensaje:</label>
              <div className="mt-1 p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 font-mono whitespace-pre-wrap leading-relaxed max-h-[350px] overflow-auto">
                {emailDraft.body || 'Cargando cuerpo...'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Payload JSON */}
      {activeTab === 'json' && (
        <div className="glass-card p-6 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Payload Estructurado para ERP / Cobranza
              </h3>
              <p className="text-xs text-slate-400">
                Objeto JSON listo para integración con SAP, Oracle NetSuite o Microsoft Dynamics.
              </p>
            </div>

            <button
              onClick={() => copyToClipboard(JSON.stringify(report, null, 2), 'json')}
              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white flex items-center gap-1.5 transition-colors shadow-md shadow-emerald-600/20"
            >
              {copiedKey === 'json' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedKey === 'json' ? 'Copiado!' : 'Copiar JSON'}</span>
            </button>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/90 border border-slate-800/80 font-mono text-xs text-emerald-400 max-h-[450px] overflow-auto whitespace-pre-wrap">
            {JSON.stringify(report, null, 2)}
          </div>
        </div>
      )}

    </div>
  );
}
