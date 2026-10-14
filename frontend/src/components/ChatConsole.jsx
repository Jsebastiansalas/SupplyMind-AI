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
// 1. Renderizador Markdown Enriquecido (Tablas, Citas, Listas, Badges Neón)
// ==============================================================================
function formatInlineText(text) {
  if (!text) return text;
  
  // Dividir por bloques de código en línea `code`
  const codeParts = text.split(/(`[^`]+`)/g);
  return codeParts.map((part, pIdx) => {
    if (part.startsWith('`') && part.endsWith('`')) {
      const codeContent = part.slice(1, -1);
      // Destacar identificadores documentales con estilo badge neón
      if (/^(DEL-|INV-|PAY-|CLAUSE-|PO-|PROD-|DED-)/i.test(codeContent)) {
        return (
          <span key={pIdx} className="inline-block px-1.5 py-0.5 mx-0.5 rounded font-mono text-[11px] font-semibold bg-cyan-950/70 border border-cyan-500/40 text-cyan-300 shadow-sm shadow-cyan-900/30">
            {codeContent}
          </span>
        );
      }
      return (
        <code key={pIdx} className="px-1.5 py-0.5 rounded font-mono text-[11px] bg-slate-800 text-indigo-300 border border-slate-700">
          {codeContent}
        </code>
      );
    }

    // Procesar **negrita**
    const boldParts = part.split(/(\*\*[^*]+\*\*)/g);
    return boldParts.map((bPart, bIdx) => {
      if (bPart.startsWith('**') && bPart.endsWith('**')) {
        return <strong key={bIdx} className="font-bold text-white">{bPart.slice(2, -2)}</strong>;
      }
      
      // Procesar *cursiva*
      const italicParts = bPart.split(/(\*[^*]+\*)/g);
      return italicParts.map((iPart, iIdx) => {
        if (iPart.startsWith('*') && iPart.endsWith('*') && !iPart.startsWith('**')) {
          return <em key={iIdx} className="italic text-slate-300">{iPart.slice(1, -1)}</em>;
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
          <div key={`table-${i}`} className="my-3 overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/70 shadow-inner">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-cyan-950/40 text-cyan-300 font-mono">
                  {headers.map((h, hIdx) => (
                    <th key={hIdx} className="p-2.5 font-bold whitespace-nowrap">
                      {formatInlineText(h)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {dataRows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-slate-900/60 transition-colors odd:bg-slate-900/20">
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} className="p-2.5 text-slate-200">
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
    ? "fixed inset-4 md:inset-8 z-50 glass-card rounded-2xl flex flex-col shadow-2xl border border-cyan-500/40 bg-slate-950/95 backdrop-blur-2xl"
    : "glass-card rounded-2xl flex flex-col h-[650px] overflow-hidden";

  return (
    <div className={containerClasses}>
      
      {/* ================================================================== */}
      {/* 1. Header de la Consola con Selector de Rol & Controles           */}
      {/* ================================================================== */}
      <div className="p-3.5 border-b border-slate-800/80 bg-slate-950/80 flex flex-wrap items-center justify-between gap-3 flex-shrink-0">
        
        {/* Lado Izquierdo: Título y Selector de Rol */}
        <div className="flex items-center space-x-3">
          <div className="p-1.5 rounded-lg bg-cyan-950/60 border border-cyan-800/50 text-cyan-400">
            <Terminal className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-white">
                Terminal Grok 4.7
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-cyan-300 border border-slate-700">
                {caseId}
              </span>
            </div>
            <p className="text-[10px] text-slate-400">
              Modo activo: <strong className="text-slate-200">{currentRoleObj.label}</strong>
            </p>
          </div>
        </div>

        {/* Centro: Selector de Roles */}
        <div className="flex items-center bg-slate-900/90 p-1 rounded-xl border border-slate-800 space-x-1">
          {roles.map((r) => {
            const Icon = r.icon;
            const isSelected = selectedRole === r.id;
            return (
              <button
                key={r.id}
                onClick={() => setSelectedRole(r.id)}
                title={r.description}
                className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                  isSelected 
                    ? 'bg-slate-800 text-cyan-300 border border-cyan-500/40 shadow-sm' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <Icon className={`w-3 h-3 ${isSelected ? 'text-cyan-400' : 'text-slate-500'}`} />
                <span className="hidden sm:inline">{r.short}</span>
              </button>
            );
          })}
        </div>

        {/* Lado Derecho: Badges y Botones de Acción */}
        <div className="flex items-center space-x-1.5">
          <div className="flex items-center space-x-1 px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800/40 text-[10px] font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Grok Online</span>
          </div>

          {/* Descargar Transcripción */}
          {messages.length > 0 && (
            <button
              onClick={handleDownloadTranscript}
              className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition-colors"
              title="Descargar conversación (.md)"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          )}

          {/* Maximizar / Restaurar Pantalla Completa */}
          <button
            onClick={() => setIsFullScreen(!isFullScreen)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition-colors"
            title={isFullScreen ? "Restaurar tamaño normal" : "Pantalla completa"}
          >
            {isFullScreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>

          {/* Limpiar Conversación */}
          {onClearChat && (
            <button
              onClick={onClearChat}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
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
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
        
        {/* Mensaje de Bienvenida Contextual */}
        <div className="flex items-start space-x-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-600/30 to-indigo-600/30 border border-cyan-500/40 flex items-center justify-center text-cyan-300 flex-shrink-0 shadow-sm">
            <Bot className="w-4 h-4" />
          </div>
          <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 text-xs text-slate-200 leading-relaxed max-w-3xl shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2 mb-2">
              <span className="font-bold text-cyan-300 flex items-center space-x-1.5">
                <CurrentRoleIcon className="w-3.5 h-3.5" />
                <span>SupplyMind AI — {currentRoleObj.label}</span>
              </span>
              <span className="text-[10px] font-mono text-slate-400">Expediente {caseId}</span>
            </div>
            <p className="text-slate-300 leading-relaxed mb-2">
              He cargado el expediente completo: <strong>facturas, remisiones firmadas, comprobantes de pago, contrato comercial y dictamen del Tribunal Colegiado</strong>.
            </p>
            <p className="text-slate-400 text-[11px]">
              Tanto clientes como jurados pueden hacerme cualquier pregunta sobre <strong>desglose producto a producto</strong>, <strong>cálculo matemático exacto en Decimal</strong>, <strong>amparo de cláusulas contractuales</strong> o solicitar la <strong>redacción de cartas de objeción</strong>.
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
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm ${
                isUser 
                  ? 'bg-indigo-600/30 border border-indigo-500/40 text-indigo-300' 
                  : 'bg-gradient-to-br from-cyan-600/30 to-indigo-600/30 border border-cyan-500/40 text-cyan-300'
              }`}>
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Burbuja de Contenido */}
              <div className={`p-4 rounded-2xl border text-xs leading-relaxed max-w-3xl shadow-sm ${
                isUser 
                  ? 'bg-indigo-950/40 border-indigo-800/50 text-indigo-100 rounded-tr-none' 
                  : 'bg-slate-900/90 border-slate-800 text-slate-200 rounded-tl-none'
              }`}>
                
                {/* Header del Mensaje */}
                <div className="flex items-center justify-between border-b border-slate-800/60 pb-1.5 mb-2">
                  <span className={`font-mono text-[10px] font-bold ${isUser ? 'text-indigo-300' : 'text-cyan-400'}`}>
                    {isUser ? 'TÚ (CONSULTA)' : 'SUPPLYMIND AI'}
                  </span>
                  {!isUser && (
                    <button
                      onClick={() => handleCopyMessage(msg.content, index)}
                      className="flex items-center space-x-1 text-[10px] text-slate-400 hover:text-cyan-300 transition-colors"
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
                  <p className="whitespace-pre-wrap">{msg.content}</p>
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
            <div className="w-8 h-8 rounded-xl bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 flex-shrink-0 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 text-xs text-slate-300 flex items-center space-x-2.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce"></span>
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce [animation-delay:0.4s]"></span>
              <span className="font-mono text-cyan-300 text-[11px]">
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
      <div className="px-4 py-2.5 bg-slate-950/70 border-t border-slate-800/60 flex flex-col gap-2 flex-shrink-0">
        
        {/* Selector de Pestaña de Sugerencias */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Lightbulb className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
            <span className="text-[10px] text-slate-400 uppercase font-mono font-bold tracking-wider">
              Dudas Frecuentes:
            </span>
          </div>

          <div className="flex items-center space-x-1">
            {[
              { id: 'jurado', label: '👔 Jurados' },
              { id: 'cliente', label: '💼 Clientes' },
              { id: 'legal', label: '⚖️ Legal' },
              { id: 'borradores', label: '✉️ Borradores' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setPromptCategory(tab.id)}
                className={`text-[10px] px-2 py-0.5 rounded-md transition-colors ${
                  promptCategory === tab.id
                    ? 'bg-slate-800 text-cyan-300 font-bold border border-slate-700'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Chips de Preguntas de la Categoría Seleccionada */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-1 scrollbar-thin">
          {categorizedPrompts[promptCategory]?.map((p, i) => (
            <button
              key={i}
              onClick={() => handleQuickPrompt(p.text)}
              disabled={isThinking}
              className="group text-[11px] px-3 py-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 text-slate-300 hover:text-cyan-200 whitespace-nowrap transition-all shadow-sm flex items-center space-x-1.5 flex-shrink-0 disabled:opacity-50"
            >
              <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-800 group-hover:bg-cyan-950/80 group-hover:text-cyan-300 text-slate-400 transition-colors">
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
      <form onSubmit={handleSubmit} className="p-3 border-t border-slate-800/80 bg-slate-950/90 flex items-center space-x-2 flex-shrink-0">
        <div className="relative flex-1">
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Hazle una consulta técnica o comercial a Grok sobre ${caseId}...`}
            disabled={isThinking}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-4 pr-10 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition-colors disabled:opacity-50"
          />
          <span className="absolute right-3 top-2.5 text-[10px] font-mono text-slate-600 hidden sm:inline">
            Enter ↵
          </span>
        </div>

        <button
          type="submit"
          disabled={!inputText.trim() || isThinking}
          className="p-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 text-white hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md shadow-cyan-500/20 flex items-center justify-center flex-shrink-0"
          title="Enviar consulta"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>

    </div>
  );
}
