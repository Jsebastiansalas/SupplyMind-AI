import React, { useState, useEffect, useRef } from 'react';
import { Volume2, VolumeX, Pause, Play, Square, FastForward, Sparkles, Mic } from 'lucide-react';

export default function ExecutiveAudioBriefing({ caseId, report, compact = false }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [rate, setRate] = useState(1.05);
  const [supported, setSupported] = useState(true);
  const [availableVoices, setAvailableVoices] = useState([]);
  const utteranceRef = useRef(null);

  useEffect(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setSupported(false);
      return;
    }

    const loadVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      setAvailableVoices(voices);
    };

    loadVoices();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }

    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  if (!supported || !report) return null;

  const fin = report.financial_summary || {};
  const billed = fin.billed_amount ?? report.billed_amount ?? 0;
  const received = fin.received_amount ?? report.received_amount ?? 0;
  const justified = fin.justified_amount ?? report.justified_amount ?? 0;
  const claimable = fin.claimable_amount ?? report.claimable_amount ?? 0;
  const rootCause = report.root_cause || report.root_cause_analysis?.primary_driver || 'Discrepancia en conciliación de inventario y facturación';
  const action = report.recommended_action || 'Proceder a la emisión inmediata de la carta formal de reclamación y asiento contable NIF C-3.';

  const buildExecutiveSpeech = () => {
    const caseName = (caseId || 'actual').replace(/_/g, ' ');
    const billedFmt = Number(billed).toLocaleString('es-MX', { maximumFractionDigits: 0 });
    const receivedFmt = Number(received).toLocaleString('es-MX', { maximumFractionDigits: 0 });
    const justifiedFmt = Number(justified).toLocaleString('es-MX', { maximumFractionDigits: 0 });
    const claimableFmt = Number(claimable).toLocaleString('es-MX', { maximumFractionDigits: 0 });

    let speech = `Dictamen ejecutivo de arbitraje comercial para el expediente ${caseName}. `;
    speech += `Causa raíz diagnosticada: ${rootCause}. `;
    speech += `El total facturado asciende a ${billedFmt} dólares, habiéndose recibido una liquidación parcial de ${receivedFmt} dólares. `;
    
    if (justified > 0) {
      speech += `De la retención aplicada, se valida como justificada la cantidad de ${justifiedFmt} dólares respaldada contractualmente en merma física. `;
    }

    if (claimable > 0) {
      speech += `Sin embargo, se determinan como indebidamente retenidos ${claimableFmt} dólares reclamables de forma inmediata. `;
      speech += `Conforme al artículo 383 del Código de Comercio y la cláusula perentoria de caducidad, la retención carece de validez probatoria. `;
    } else {
      speech += `El saldo auditado queda saneado en su totalidad bajo el invariante de cero error. `;
    }

    speech += `Recomendación resolutiva: ${action}`;
    return speech;
  };

  const handleTogglePlay = () => {
    if (!window.speechSynthesis) return;

    if (isPlaying && !isPaused) {
      window.speechSynthesis.pause();
      setIsPaused(true);
      return;
    }

    if (isPaused) {
      window.speechSynthesis.resume();
      setIsPaused(false);
      return;
    }

    // Nueva reproducción
    window.speechSynthesis.cancel();
    const textToSpeak = buildExecutiveSpeech();
    const utterance = new SpeechSynthesisUtterance(textToSpeak);

    // Buscar la mejor voz en español
    const esVoice = availableVoices.find(v => v.lang === 'es-MX' || v.lang === 'es_MX') ||
                    availableVoices.find(v => v.lang.startsWith('es-')) ||
                    availableVoices.find(v => v.lang.startsWith('es'));
    if (esVoice) {
      utterance.voice = esVoice;
      utterance.lang = esVoice.lang;
    } else {
      utterance.lang = 'es-MX';
    }

    utterance.rate = rate;
    utterance.pitch = 0.95; // Tono ejecutivo formal sobrio

    utterance.onstart = () => {
      setIsPlaying(true);
      setIsPaused(false);
    };

    utterance.onend = () => {
      setIsPlaying(false);
      setIsPaused(false);
    };

    utterance.onerror = (e) => {
      console.warn("SpeechSynthesis error:", e);
      setIsPlaying(false);
      setIsPaused(false);
    };

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  };

  const handleStop = () => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    setIsPlaying(false);
    setIsPaused(false);
  };

  const cycleRate = () => {
    const rates = [1.0, 1.25, 1.5];
    const nextIndex = (rates.indexOf(rate) + 1) % rates.length;
    const newRate = rates[nextIndex];
    setRate(newRate);
    if (isPlaying && !isPaused) {
      // Re-trigger with new rate seamlessly
      handleStop();
      setTimeout(() => {
        setRate(newRate);
        handleTogglePlay();
      }, 50);
    }
  };

  if (compact) {
    return (
      <div className="inline-flex items-center space-x-1.5 bg-[#161720] border border-[#2d2f3d] rounded-lg px-2.5 py-1.5 shadow-sm">
        <button
          onClick={handleTogglePlay}
          className={`flex items-center space-x-1.5 text-xs font-mono font-semibold transition-colors ${
            isPlaying
              ? 'text-[#eed98d] hover:text-white'
              : 'text-zinc-300 hover:text-[#eed98d]'
          }`}
          title={isPlaying ? (isPaused ? 'Reanudar lectura' : 'Pausar audio') : 'Escuchar dictamen ejecutivo en voz alta'}
        >
          {isPlaying && !isPaused ? (
            <>
              <Pause className="w-3.5 h-3.5 text-[#d4af37]" />
              <span className="flex space-x-0.5 items-end h-3 mr-0.5">
                <span className="w-0.5 h-2 bg-[#d4af37] animate-pulse"></span>
                <span className="w-0.5 h-3 bg-[#eed98d] animate-bounce"></span>
                <span className="w-0.5 h-1.5 bg-[#d4af37] animate-pulse"></span>
              </span>
              <span>Pausar</span>
            </>
          ) : isPaused ? (
            <>
              <Play className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
              <span>Reanudar</span>
            </>
          ) : (
            <>
              <Volume2 className="w-3.5 h-3.5 text-[#d4af37]" />
              <span>Audio Briefing</span>
            </>
          )}
        </button>

        {isPlaying && (
          <button
            onClick={handleStop}
            className="p-1 hover:bg-[#20222f] rounded text-zinc-400 hover:text-rose-400 transition-colors"
            title="Detener lectura"
          >
            <Square className="w-3 h-3 fill-current" />
          </button>
        )}

        <button
          onClick={cycleRate}
          className="text-[10px] font-mono px-1 py-0.5 rounded bg-[#1e202c] hover:bg-[#282a3a] text-zinc-400 hover:text-zinc-200"
          title="Cambiar velocidad de locución"
        >
          {rate}x
        </button>
      </div>
    );
  }

  return (
    <div className="bg-[#121319] border border-[#262836] rounded-xl p-3.5 sm:p-4 shadow-subtle flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
      <div className="flex items-center space-x-3">
        <div className={`p-2.5 rounded-lg border transition-colors ${
          isPlaying && !isPaused
            ? 'bg-[#292212] border-[#d4af37]/60 text-[#eed98d]'
            : 'bg-[#181922] border-[#2a2c3a] text-zinc-400'
        }`}>
          {isPlaying && !isPaused ? (
            <div className="flex items-end space-x-0.5 h-5 w-5 justify-center">
              <span className="w-1 h-3 bg-[#d4af37] rounded-full animate-bounce"></span>
              <span className="w-1 h-5 bg-[#eed98d] rounded-full animate-pulse"></span>
              <span className="w-1 h-2 bg-[#d4af37] rounded-full animate-bounce"></span>
              <span className="w-1 h-4 bg-[#eed98d] rounded-full animate-pulse"></span>
            </div>
          ) : (
            <Volume2 className="w-5 h-5 text-[#d4af37]" />
          )}
        </div>

        <div>
          <div className="flex items-center space-x-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-200">
              Audio Briefing C-Level
            </h4>
            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-[#eed98d]/10 text-[#eed98d] border border-[#d4af37]/30">
              Web Speech API
            </span>
          </div>
          <p className="text-[11px] text-zinc-400 mt-0.5">
            {isPlaying && !isPaused
              ? 'Sintetizando dictamen pericial en tiempo real...'
              : isPaused
              ? 'Lectura en pausa.'
              : 'Escucha el dictamen financiero y jurídico consolidado en 30 segundos.'}
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-2 self-end sm:self-auto">
        <button
          onClick={handleTogglePlay}
          className="btn-tactile flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-[#eed98d] hover:bg-[#d4af37] text-black font-semibold text-xs font-mono transition-all shadow-subtle"
        >
          {isPlaying && !isPaused ? (
            <>
              <Pause className="w-3.5 h-3.5 fill-current" />
              <span>Pausar</span>
            </>
          ) : isPaused ? (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Reanudar</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Escuchar Dictamen</span>
            </>
          )}
        </button>

        {isPlaying && (
          <button
            onClick={handleStop}
            className="btn-tactile p-2 rounded-md bg-[#1a1b24] hover:bg-rose-950/40 text-zinc-400 hover:text-rose-400 border border-[#2b2d3c] transition-colors"
            title="Detener audio"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
          </button>
        )}

        <button
          onClick={cycleRate}
          className="btn-tactile px-2.5 py-1.5 rounded-md bg-[#181922] hover:bg-[#20222f] border border-[#282a39] text-xs font-mono text-zinc-300 transition-colors"
          title="Velocidad de locución"
        >
          {rate}x
        </button>
      </div>
    </div>
  );
}
