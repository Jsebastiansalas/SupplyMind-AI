import React, { useState, useRef, useEffect, useMemo } from 'react';
import { 
  Send, 
  Terminal, 
  Sparkles, 
  Trash2, 
  Bot, 
  User, 
  Lightbulb,
  Maximize2,
  Minimize2,
  Copy,
  Check,
  Download,
  ShieldCheck,
  Scale,
  Briefcase,
  FileText,
  ChevronRight,
  Info
} from 'lucide-react';

// ==============================================================================
// 1. Renderizador Markdown Enriquecido (Tablas, Citas, Listas, Tokens Institucionales)
// ==============================================================================
function formatInlineText(text) {
  if (!text) return text;
  
  // Dividir por bloques de código en línea `code`
  const codeParts = text.split(/(`[^`]+`)/g);
  return codeParts.map((part, pIdx) => {
    if (part.startsWith('`') && part.endsWith('`')) {
      const codeContent = part.slice(1, -1);
      // Destacar identificadores documentales con estilo institucional sobrio
      if (/^(DEL-|INV-|PAY-|CLAUSE-|PO-|PROD-|DED-)/i.test(codeContent)) {
        return (
          <span key={pIdx} className="inline-block px-1.5 py-0.5 mx-0.5 rounded font-mono text-[10px] font-semibold bg-[#171822] border border-[#282a3c] text-[#eed98d] shadow-tactile">
            {codeContent}
          </span>
        );
      }
      return (
        <code key={pIdx} className="px-1.5 py-0.5 rounded font-mono text-[11px] bg-[#14151b] text-zinc-300 border border-[#222430]">
          {codeContent}
        </code>
      );
    }

    // Procesar **negrita**
    const boldParts = part.split(/(\*\*[^*]+\*\*)/g);
    return boldParts.map((bPart, bIdx) => {
      if (bPart.startsWith('**') && bPart.endsWith('**')) {
        return <strong key={bIdx} className="font-bold text-white tracking-tight">{bPart.slice(2, -2)}</strong>;
      }
      
      // Procesar *cursiva*
      const italicParts = bPart.split(/(\*[^*]+\*)/g);
      return italicParts.map((iPart, iIdx) => {
        if (iPart.startsWith('*') && iPart.endsWith('*') && !iPart.startsWith('**')) {
          return <em key={iIdx} className="italic text-zinc-400">{iPart.slice(1, -1)}</em>;
        }
        return iPart;
      });
    });
  });
}

function RichMarkdownMessage({ content }) {
  if (!content) return null;

  const lines = content.split('\n');
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // 1. Detectar inicio de tabla Markdown
    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
        tableLines.push(lines[i].trim());
        i++;
      }

      if (tableLines.length >= 2) {
        // Primera fila: Cabeceras
        const headers = tableLines[0]
          .split('|')
          .slice(1, -1)
          .map(h => h.trim());

        // Si la segunda fila es separador | :--- | :---: |, omitirla
        let dataStartIndex = 1;
        if (tableLines[1].includes('---')) {
          dataStartIndex = 2;
        }

        const dataRows = tableLines.slice(dataStartIndex).map(rowStr => 
          rowStr.split('|').slice(1, -1).map(c => c.trim())
        );

        elements.push(
          <div key={`table-${i}`} className="my-3 overflow-x-auto rounded border border-[#1e202a] bg-[#0c0d11] shadow-subtle">
            <table className="w-full text-left text-xs border-collapse font-mono tabular-nums">
              <thead>
                <tr className="border-b border-[#1e202a] bg-[#121319] text-zinc-300">
                  {headers.map((h, hIdx) => (
                    <th key={hIdx} className="p-2.5 font-bold uppercase text-[10px] tracking-wider whitespace-nowrap">
                      {formatInlineText(h)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#181922] font-sans">
                {dataRows.map((row, rIdx) => (
                  <tr key={rIdx} className="audit-row transition-colors">
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} className="p-2.5 text-zinc-200">
                        {formatInlineText(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    }

    // 2. Encabezados
    if (line.startsWith('### ')) {
      elements.push(
        <h4 key={`h3-${i}`} className="text-sm font-bold text-cyan-300 mt-3 mb-1.5 flex items-center space-x-1.5">
          <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />
          <span>{formatInlineText(line.replace('### ', ''))}</span>
        </h4>
      );
      i++;
      continue;
    }
    if (line.startsWith('## ')) {
      elements.push(
        <h3 key={`h2-${i}`} className="text-base font-extrabold text-white mt-4 mb-2 border-b border-slate-800/80 pb-1">
          {formatInlineText(line.replace('## ', ''))}
        </h3>
      );
      i++;
      continue;
    }
    if (line.startsWith('# ')) {
      elements.push(
        <h2 key={`h1-${i}`} className="text-lg font-black text-cyan-400 mt-4 mb-2">
          {formatInlineText(line.replace('# ', ''))}
        </h2>
      );
      i++;
      continue;
    }

    // 3. Citas en bloque (Blockquotes)
    if (line.startsWith('> ')) {
      elements.push(
        <blockquote key={`bq-${i}`} className="my-2 pl-3 py-1 border-l-2 border-cyan-400 bg-cyan-950/20 text-xs italic text-cyan-100/90 rounded-r-lg">
          {formatInlineText(line.replace('> ', ''))}
        </blockquote>
      );
      i++;
      continue;
    }

    // 4. Elementos de lista con viñeta
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      elements.push(
        <div key={`li-${i}`} className="flex items-start space-x-2 my-1 pl-1 text-xs text-slate-200">
          <span className="text-cyan-400 font-bold mt-0.5">•</span>
          <span className="flex-1 leading-relaxed">{formatInlineText(line.trim().slice(2))}</span>
        </div>
      );
      i++;
      continue;
    }

    // 5. Elementos de lista numerada (ej. 1. , 2. )
    const numMatch = line.trim().match(/^(\d+)\.\s+(.*)$/);
    if (numMatch) {
      elements.push(
        <div key={`num-${i}`} className="flex items-start space-x-2 my-1 pl-1 text-xs text-slate-200">
          <span className="text-indigo-400 font-mono font-bold text-[11px] mt-0.5">{numMatch[1]}.</span>
          <span className="flex-1 leading-relaxed">{formatInlineText(numMatch[2])}</span>
        </div>
      );
      i++;
      continue;
    }

    // 6. Líneas vacías
    if (!line.trim()) {
      elements.push(<div key={`sp-${i}`} className="h-1.5" />);
      i++;
      continue;
    }

    // 7. Párrafo normal
    elements.push(
      <p key={`p-${i}`} className="text-xs leading-relaxed text-slate-200 my-1">
        {formatInlineText(line)}
      </p>
    );
    i++;
  }

  return <div className="space-y-0.5 font-sans">{elements}</div>;
}

// ==============================================================================
// 2. Componente Principal de la Terminal Interactiva
// ==============================================================================
export default function ChatConsole({ 
  caseId, 
  messages = [], 
  onSendMessage, 
  isThinking = false, 
  onClearChat 
}) {
  const [inputText, setInputText] = useState('');
  const [selectedRole, setSelectedRole] = useState('senior_analyst');
  const [promptCategory, setPromptCategory] = useState('jurado');
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Definición de Roles del Asistente
  const roles = [
    { 
      id: 'senior_analyst', 
      label: 'Analista Senior 360°', 
      short: 'Senior 360°', 
      icon: Sparkles,
      color: 'from-cyan-500 to-indigo-600',
      description: 'Visión holística equilibrando números exactos, legal y acción comercial.'
    },
    { 
      id: 'judge_auditor', 
      label: 'Jurado & Auditor', 
      short: 'Jurado/CFO', 
      icon: ShieldCheck,
      color: 'from-emerald-500 to-teal-600',
      description: 'Rigor técnico, cero alucinación Decimal, Tribunal Colegiado y métricas.'
    },
    { 
      id: 'legal_counsel', 
      label: 'Asesor Legal', 
      short: 'Legal Counsel', 
      icon: Scale,
      color: 'from-amber-500 to-orange-600',
      description: 'Cláusulas vinculantes, jerarquía probatoria e impugnación de penalizaciones.'
    },
    { 
      id: 'commercial_negotiator', 
      label: 'Negociador Comercial', 
      short: 'Negociador', 
      icon: Briefcase,
      color: 'from-purple-500 to-pink-600',
      description: 'Recuperación de cartera, diplomacia y redacción de borradores formales.'
    },
  ];

  // Sugerencias de Preguntas Segmentadas por Audiencia
  const categorizedPrompts = {
    jurado: [
      { text: "¿Cómo garantiza el agente cero alucinación matemática?", badge: "Metodología" },
      { text: "¿Cuál fue la deliberación del Tribunal Colegiado (CFO, Legal, COO)?", badge: "100 Pts" },
      { text: "¿Qué precedentes jurisprudenciales se aplicaron a este caso?", badge: "Doctrina" },
      { text: "¿Cuál es el costo de inferencia y unit economics de este análisis?", badge: "Eficiencia" },
    ],
    cliente: [
      { text: "Desglósame producto por producto qué se facturó y qué se entregó", badge: "Inventario" },
      { text: "¿Cuánto dinero podemos reclamar legalmente hoy en efectivo?", badge: "Financiero" },
      { text: "¿Por qué se rechazaron las retenciones aplicadas en el pago?", badge: "Causa Raíz" },
      { text: "¿Qué acción inmediata debe ejecutar el equipo de cartera?", badge: "Operativo" },
    ],
    legal: [
      { text: "¿Qué cláusulas del contrato amparan el rechazo de las penalizaciones?", badge: "Cláusulas" },
      { text: "¿Por qué la remisión firmada prevalece sobre reportes extemporáneos?", badge: "Pruebas" },
      { text: "¿Existe extemporaneidad en la notificación de averías del cliente?", badge: "Plazos" },
      { text: "¿Cómo fundamentamos la nulidad de deducciones unilaterales?", badge: "Objeción" },
    ],
    borradores: [
      { text: "Redáctame un correo formal para el departamento de compras objetando el pago", badge: "Correo B2B" },
      { text: "¿Qué monto debemos reconocer mediante Nota de Crédito comercial?", badge: "Nota Crédito" },
      { text: "Prepara una carta de requerimiento de pago con plazo de 15 días hábiles", badge: "Requerimiento" },
    ],
    hitl: [
      { text: "Acepta el 50% de la penalidad ASN para cuidar la relación comercial y concilia el resto", badge: "50% Concesión" },
      { text: "Condona el 100% de la penalidad operativa para cerrar el expediente de mutuo acuerdo", badge: "100% Concesión" },
      { text: "Absorbe $1,000 USD de la deducción disputada y exige el cobro del saldo restante", badge: "$1,000 Concesión" },
      { text: "Deshacer concesión y restaurar auditoría contractual original estricta", badge: "Reset Original" },
    ]
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!inputText.trim() || isThinking) return;
    onSendMessage(inputText.trim(), selectedRole);
    setInputText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleQuickPrompt = (promptText) => {
    if (isThinking) return;
    onSendMessage(promptText, selectedRole);
  };

  const handleCopyMessage = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleDownloadTranscript = () => {
    if (messages.length === 0) return;
    let markdown = `# Transcripción de Interacción — SupplyMind AI\n`;
    markdown += `**Expediente:** ${caseId}\n`;
    markdown += `**Fecha:** ${new Date().toLocaleString()}\n\n---\n\n`;
    messages.forEach(m => {
      const author = m.role === 'user' ? '👤 Usuario' : '🤖 SupplyMind AI (Grok 4.7)';
      markdown += `### ${author}\n\n${m.content}\n\n---\n\n`;
    });

    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat_transcript_${caseId}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const currentRoleObj = roles.find(r => r.id === selectedRole) || roles[0];
  const CurrentRoleIcon = currentRoleObj.icon;

  const containerClasses = isFullScreen 
    ? "fixed inset-4 md:inset-8 z-50 bg-[#0c0d11] rounded-lg flex flex-col shadow-modal border border-[#2b2e3e]"
    : "bg-[#0e0f14] border border-[#1b1c24] rounded-lg flex flex-col h-[650px] overflow-hidden shadow-elevated";

  return (
    <div className={containerClasses}>
      
      {/* ================================================================== */}
      {/* 1. Header de la Consola con Selector de Rol & Controles           */}
      {/* ================================================================== */}
      <div className="p-3 border-b border-[#1b1c24] bg-[#101116] flex flex-wrap items-center justify-between gap-3 flex-shrink-0 select-none">
        
        {/* Lado Izquierdo: Título y Selector de Rol */}
        <div className="flex items-center space-x-3">
          <div className="p-1.5 rounded bg-[#15161f] border border-[#242738] text-[#d4af37]">
            <Terminal className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-100">
                Consola Arbitral Grok 4.7
              </h3>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#15161f] text-zinc-300 border border-[#222432]">
                {caseId}
              </span>
            </div>
            <p className="text-[10px] text-zinc-400 font-mono">
              Perspectiva: <strong className="text-zinc-200">{currentRoleObj.label}</strong>
            </p>
          </div>
        </div>

        {/* Centro: Selector de Roles */}
        <div className="flex items-center bg-[#0a0b0e] p-0.5 rounded border border-[#1a1c24] space-x-0.5">
          {roles.map((r) => {
            const Icon = r.icon;
            const isSelected = selectedRole === r.id;
            return (
              <button
                key={r.id}
                onClick={() => setSelectedRole(r.id)}
                title={r.description}
                className={`btn-tactile flex items-center space-x-1.5 px-2.5 py-1 rounded text-[10px] font-mono font-medium transition-all ${
                  isSelected 
                    ? 'bg-[#181924] text-[#eed98d] border border-[#2b2e3e] shadow-tactile' 
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-[#12131a]'
                }`}
              >
                <Icon className={`w-3 h-3 ${isSelected ? 'text-[#d4af37]' : 'text-zinc-500'}`} />
                <span className="hidden sm:inline">{r.short}</span>
              </button>
            );
          })}
        </div>

        {/* Lado Derecho: Badges y Botones de Acción */}
        <div className="flex items-center space-x-1.5 font-mono">
          <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-[#101913] text-emerald-400 border border-emerald-900/50 text-[10px]">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            <span>Motor Activo</span>
          </div>

          {/* Descargar Transcripción */}
          {messages.length > 0 && (
            <button
              onClick={handleDownloadTranscript}
              className="btn-tactile p-1.5 rounded text-zinc-400 hover:text-white hover:bg-[#181922] transition-colors"
              title="Descargar conversación (.md)"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          )}

          {/* Maximizar / Restaurar Pantalla Completa */}
          <button
            onClick={() => setIsFullScreen(!isFullScreen)}
            className="btn-tactile p-1.5 rounded text-zinc-400 hover:text-white hover:bg-[#181922] transition-colors"
            title={isFullScreen ? "Restaurar tamaño normal" : "Pantalla completa"}
          >
            {isFullScreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>

          {/* Limpiar Conversación */}
          {onClearChat && (
            <button
              onClick={onClearChat}
              className="btn-tactile p-1.5 rounded text-zinc-400 hover:text-rose-400 hover:bg-[#181922] transition-colors"
              title="Limpiar conversación"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* ================================================================== */}
      {/* 2. Área de Mensajes con Scroll                                    */}
      {/* ================================================================== */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
        
        {/* Mensaje de Bienvenida Contextual */}
        <div className="flex items-start space-x-3">
          <div className="w-7 h-7 rounded bg-[#161720] border border-[#252838] flex items-center justify-center text-[#d4af37] flex-shrink-0 shadow-tactile text-xs font-mono font-bold select-none">
            SM
          </div>
          <div className="p-3.5 rounded-lg bg-[#111218] border border-[#1b1c24] text-xs text-zinc-200 leading-relaxed max-w-3xl shadow-subtle">
            <div className="flex items-center justify-between border-b border-[#1b1c24] pb-2 mb-2 font-mono">
              <span className="font-bold text-[#eed98d] flex items-center space-x-1.5">
                <CurrentRoleIcon className="w-3.5 h-3.5 text-[#d4af37]" />
                <span>SupplyMind — {currentRoleObj.label}</span>
              </span>
              <span className="text-[10px] text-zinc-500">Expediente {caseId}</span>
            </div>
            <p className="text-zinc-300 leading-relaxed mb-1.5 font-sans">
              Expediente integrado en memoria: <strong>facturas CFDI, remisiones firmadas, comprobantes de pago SPEI, contrato comercial y dictamen pericial colegiado</strong>.
            </p>
            <p className="text-zinc-400 text-[11px] font-sans">
              Disponible para consultas de <strong>desglose producto a producto</strong>, <strong>cálculo determinístico en Python Decimal</strong>, <strong>amparo de cláusulas contractuales</strong> o <strong>redacción de cartas de objeción</strong>.
            </p>
          </div>
        </div>

        {/* Mensajes Dinámicos */}
        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          return (
            <div 
              key={index}
              className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
            >
              {/* Avatar */}
              <div className={`w-7 h-7 rounded flex items-center justify-center flex-shrink-0 shadow-tactile text-xs font-mono font-bold select-none ${
                isUser 
                  ? 'bg-[#181926] border border-[#282a3e] text-indigo-300' 
                  : 'bg-[#161720] border border-[#252838] text-[#d4af37]'
              }`}>
                {isUser ? <User className="w-3.5 h-3.5" /> : 'SM'}
              </div>

              {/* Burbuja de Contenido */}
              <div className={`p-3.5 rounded-lg border text-xs leading-relaxed max-w-3xl shadow-subtle ${
                isUser 
                  ? 'bg-[#151624] border-[#25283e] text-zinc-100' 
                  : 'bg-[#111218] border-[#1b1c24] text-zinc-200'
              }`}>
                
                {/* Header del Mensaje */}
                <div className="flex items-center justify-between border-b border-[#1b1c24] pb-1.5 mb-2 font-mono">
                  <span className={`text-[10px] font-bold ${isUser ? 'text-indigo-300' : 'text-[#eed98d]'}`}>
                    {isUser ? 'CONSULTA USUARIO' : 'SUPPLYMIND AI'}
                  </span>
                  {!isUser && (
                    <button
                      onClick={() => handleCopyMessage(msg.content, index)}
                      className="btn-tactile flex items-center space-x-1 text-[10px] text-zinc-400 hover:text-white transition-colors"
                      title="Copiar texto de la respuesta"
                    >
                      {copiedIndex === index ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-400" />
                          <span className="text-emerald-400">Copiado</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copiar</span>
                        </>
                      )}
                    </button>
                  )}
                </div>

                {/* Contenido Renderizado */}
                {isUser ? (
                  <p className="whitespace-pre-wrap font-sans">{msg.content}</p>
                ) : (
                  <RichMarkdownMessage content={msg.content} />
                )}
              </div>
            </div>
          );
        })}

        {/* Indicador de Pensamiento */}
        {isThinking && (
          <div className="flex items-start space-x-3">
            <div className="w-7 h-7 rounded bg-[#161720] border border-[#252838] flex items-center justify-center text-[#d4af37] flex-shrink-0 text-xs font-mono font-bold">
              SM
            </div>
            <div className="p-3 rounded-lg bg-[#111218] border border-[#1b1c24] text-xs text-zinc-300 flex items-center space-x-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#d4af37] animate-pulse"></span>
              <span className="font-mono text-[#eed98d] text-[11px]">
                Grok 4.7 analizando expediente con precisión Decimal...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* ================================================================== */}
      {/* 3. Barra de Sugerencias Segmentadas por Audiencia                  */}
      {/* ================================================================== */}
      <div className="px-3.5 py-2 bg-[#0a0b0e] border-t border-[#1b1c24] flex flex-col gap-1.5 flex-shrink-0 select-none">
        
        {/* Selector de Pestaña de Sugerencias */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Lightbulb className="w-3.5 h-3.5 text-[#d4af37] flex-shrink-0" />
            <span className="text-[10px] text-zinc-400 uppercase font-mono font-bold tracking-wider">
              Consultas Rápidas:
            </span>
          </div>

          <div className="flex items-center space-x-1 font-mono">
            {[
              { id: 'jurado', label: 'Jurados' },
              { id: 'hitl', label: '⚡ Concesión Human' },
              { id: 'cliente', label: 'Clientes' },
              { id: 'legal', label: 'Legal' },
              { id: 'borradores', label: 'Borradores' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setPromptCategory(tab.id)}
                className={`btn-tactile text-[10px] px-2 py-0.5 rounded transition-colors ${
                  promptCategory === tab.id
                    ? 'bg-[#181a24] text-[#eed98d] font-bold border border-[#272a39]'
                    : 'text-zinc-500 hover:text-zinc-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Chips de Preguntas de la Categoría Seleccionada */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-0.5">
          {categorizedPrompts[promptCategory]?.map((p, i) => (
            <button
              key={i}
              onClick={() => handleQuickPrompt(p.text)}
              disabled={isThinking}
              className="btn-tactile text-[11px] px-2.5 py-1 rounded bg-[#111218] hover:bg-[#161822] border border-[#1e202a] hover:border-[#2f3244] text-zinc-300 hover:text-white whitespace-nowrap transition-all shadow-subtle flex items-center space-x-1.5 flex-shrink-0 disabled:opacity-50"
            >
              <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-[#171822] text-[#eed98d]">
                {p.badge}
              </span>
              <span>{p.text}</span>
            </button>
          ))}
        </div>
      </div>

      {/* ================================================================== */}
      {/* 4. Formulario de Entrada con Atajos de Teclado                    */}
      {/* ================================================================== */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-[#1b1c24] bg-[#0c0d11] flex items-center space-x-2 flex-shrink-0">
        <div className="relative flex-1">
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Hazle una consulta técnica o pericial a Grok sobre ${caseId}...`}
            disabled={isThinking}
            className="w-full bg-[#111218] border border-[#1e2029] focus:border-[#d4af37]/60 rounded pl-3.5 pr-10 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none transition-colors disabled:opacity-50 font-mono"
          />
          <span className="absolute right-3 top-2 text-[10px] font-mono text-zinc-600 hidden sm:inline select-none">
            Enter ↵
          </span>
        </div>

        <button
          type="submit"
          disabled={!inputText.trim() || isThinking}
          className="btn-tactile px-3 py-2 rounded bg-[#1f1d14] hover:bg-[#282518] border border-[#d4af37]/60 text-[#eed98d] hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-subtle flex items-center justify-center flex-shrink-0"
          title="Enviar consulta"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>

    </div>
  );
}
