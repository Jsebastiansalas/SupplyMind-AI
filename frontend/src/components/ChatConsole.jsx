import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Terminal, 
  Sparkles, 
  Trash2, 
  Bot, 
  User, 
  CornerDownLeft,
  Lightbulb
} from 'lucide-react';

export default function ChatConsole({ 
  caseId, 
  messages = [], 
  onSendMessage, 
  isThinking = false, 
  onClearChat 
}) {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef(null);

  const quickPrompts = [
    "¿Cuánto dinero podemos reclamar legalmente?",
    "¿Por qué se rechazó o aceptó la deducción?",
    "¿Qué cláusula del contrato ampara el veredicto?",
    "¿Qué acción operativa debe ejecutar cartera?"
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim() || isThinking) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handleQuickPrompt = (prompt) => {
    if (isThinking) return;
    onSendMessage(prompt);
  };

  return (
    <div className="glass-card rounded-2xl flex flex-col h-[600px] overflow-hidden">
      
      {/* Console Header */}
      <div className="p-4 border-b border-slate-800/80 bg-slate-950/70 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-white">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider">
            Terminal de Interacción con Grok 4.7 (Expediente: {caseId})
          </h3>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800/40">
            Conectado a Grok
          </span>
          {onClearChat && (
            <button
              onClick={onClearChat}
              className="p-1 rounded text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-colors"
              title="Limpiar conversación"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        
        {/* Welcome message */}
        <div className="flex items-start space-x-3">
          <div className="w-7 h-7 rounded-lg bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 flex-shrink-0">
            <Bot className="w-4 h-4" />
          </div>
          <div className="p-3 rounded-2xl bg-slate-900/90 border border-slate-800 text-xs text-slate-200 leading-relaxed max-w-2xl">
            <p className="font-semibold text-cyan-400 mb-1">SupplyMind AI Digital Analyst</p>
            He completado la auditoría matemática y contractual del expediente <strong>{caseId}</strong>.
            Puedes preguntarme sobre montos exactos, cláusulas vinculantes o solicitar que redacte argumentos para la contraparte.
          </div>
        </div>

        {/* Dynamic Messages */}
        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          return (
            <div 
              key={index}
              className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
            >
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                isUser 
                  ? 'bg-indigo-600/20 border border-indigo-500/30 text-indigo-400' 
                  : 'bg-cyan-600/20 border border-cyan-500/30 text-cyan-400'
              }`}>
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className={`p-3.5 rounded-2xl border text-xs leading-relaxed max-w-2xl ${
                isUser 
                  ? 'bg-indigo-950/40 border-indigo-800/40 text-indigo-100 rounded-tr-none' 
                  : 'bg-slate-900/90 border-slate-800 text-slate-200 rounded-tl-none'
              }`}>
                <div className="whitespace-pre-wrap">{msg.content}</div>
              </div>
            </div>
          );
        })}

        {/* Loading Spinner Indicator */}
        {isThinking && (
          <div className="flex items-start space-x-3">
            <div className="w-7 h-7 rounded-lg bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 flex-shrink-0 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 text-xs text-slate-400 flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce"></span>
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce [animation-delay:0.4s]"></span>
              <span className="font-mono text-cyan-400">Consultando a Grok...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts Bar */}
      <div className="px-4 py-2 bg-slate-950/60 border-t border-slate-800/50 flex items-center space-x-2 overflow-x-auto">
        <Lightbulb className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
        <span className="text-[10px] text-slate-400 uppercase font-mono flex-shrink-0">Sugerencias:</span>
        {quickPrompts.map((p, i) => (
          <button
            key={i}
            onClick={() => handleQuickPrompt(p)}
            className="text-[11px] px-2.5 py-1 rounded-full bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-cyan-300 whitespace-nowrap transition-colors"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-slate-800/80 bg-slate-950/90 flex items-center space-x-2">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={`Hazle una pregunta a Grok sobre ${caseId}...`}
          disabled={isThinking}
          className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition-colors disabled:opacity-50"
        />

        <button
          type="submit"
          disabled={!inputText.trim() || isThinking}
          className="p-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 text-white hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md shadow-cyan-500/20"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>

    </div>
  );
}
