import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { 
  Binary, 
  FileCode, 
  Play, 
  RotateCcw, 
  Copy, 
  Check, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  ShieldCheck, 
  Send, 
  ChevronRight, 
  Layers, 
  FileText,
  Sparkles
} from 'lucide-react';

export default function EdiInspectorView() {
  const [samples, setSamples] = useState({});
  const [selectedSampleKey, setSelectedSampleKey] = useState('850');
  const [rawEdi, setRawEdi] = useState('');
  const [activeSubMode, setActiveSubMode] = useState('parser'); // 'parser' | 'asn_auditor' | 'generator_824'
  
  // Parse state
  const [parseResult, setParseResult] = useState(null);
  const [selectedSegmentIdx, setSelectedSegmentIdx] = useState(0);
  const [isParsing, setIsParsing] = useState(false);
  const [parseError, setParseError] = useState(null);
  const [copiedRaw, setCopiedRaw] = useState(false);

  // ASN Auditor state
  const [asnRawInput, setAsnRawInput] = useState('');
  const [ack997RawInput, setAck997RawInput] = useState('');
  const [scheduledDockTime, setScheduledDockTime] = useState('2026-10-18T14:00:00Z');
  const [requiredLeadHours, setRequiredLeadHours] = useState(4.0);
  const [auditResult, setAuditResult] = useState(null);
  const [isAuditing, setIsAuditing] = useState(false);

  // 824 Generator state
  const [genDisputeId, setGenDisputeId] = useState('DISP-WM-8841');
  const [genRetailerId, setGenRetailerId] = useState('WALMART_EDI');
  const [genSupplierId, setGenSupplierId] = useState('PROVEEDOR_CORP');
  const [genInvoiceNum, setGenInvoiceNum] = useState('FAC-2026-8841');
  const [genDeductionCode, setGenDeductionCode] = useState('86');
  const [genClaimableAmount, setGenClaimableAmount] = useState('18500.00');
  const [genRejectionBasis, setGenRejectionBasis] = useState('Remisión sellada en muelle sin salvedad + Art. 88 Código de Comercio');
  const [generated824Result, setGenerated824Result] = useState(null);
  const [isGenerating824, setIsGenerating824] = useState(false);

  // Cargar muestras EDI al montar
  useEffect(() => {
    async function loadSamples() {
      try {
        const data = await apiClient.getEdiSamples();
        if (data && data.samples) {
          setSamples(data.samples);
          if (data.samples['850']) {
            setRawEdi(data.samples['850']);
          }
          if (data.samples['856']) {
            setAsnRawInput(data.samples['856']);
          }
          if (data.samples['997']) {
            setAck997RawInput(data.samples['997']);
          }
        }
      } catch (err) {
        console.error('Error cargando muestras EDI:', err);
      }
    }
    loadSamples();
  }, []);

  // Parsear texto inicial automáticamente
  useEffect(() => {
    if (rawEdi) {
      handleParseEdi(rawEdi);
    }
  }, [selectedSampleKey]);

  const handleSelectSample = (key) => {
    setSelectedSampleKey(key);
    if (samples[key]) {
      setRawEdi(samples[key]);
      handleParseEdi(samples[key]);
    }
  };

  const handleParseEdi = async (contentToParse = rawEdi) => {
    if (!contentToParse || !contentToParse.trim()) return;
    setIsParsing(true);
    setParseError(null);
    try {
      const res = await apiClient.parseEdi(contentToParse);
      setParseResult(res);
      setSelectedSegmentIdx(0);
    } catch (err) {
      setParseError(err.message || 'Error al decodificar paquete EDI');
    } finally {
      setIsParsing(false);
    }
  };

  const handleCopyRaw = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedRaw(true);
    setTimeout(() => setCopiedRaw(false), 2000);
  };

  const handleRunAsnAudit = async () => {
    setIsAuditing(true);
    try {
      const res = await apiClient.auditEdiAsn({
        asn_raw: asnRawInput || samples['856'] || '',
        ack_997_raw: ack997RawInput || samples['997'] || '',
        scheduled_dock_time_iso: scheduledDockTime,
        required_lead_hours: parseFloat(requiredLeadHours) || 4.0,
      });
      setAuditResult(res);
    } catch (err) {
      alert(`Error en auditoría ASN: ${err.message}`);
    } finally {
      setIsAuditing(false);
    }
  };

  const handleRunGenerate824 = async () => {
    setIsGenerating824(true);
    try {
      const res = await apiClient.generateEdi824({
        dispute_id: genDisputeId,
        retailer_sender_id: genRetailerId,
        supplier_receiver_id: genSupplierId,
        invoice_number: genInvoiceNum,
        deduction_code: genDeductionCode,
        claimable_amount: parseFloat(genClaimableAmount) || 0.0,
        rejection_basis: genRejectionBasis,
      });
      setGenerated824Result(res);
    } catch (err) {
      alert(`Error generando EDI 824: ${err.message}`);
    } finally {
      setIsGenerating824(false);
    }
  };

  // Segmentos parseados de la transacción activa
  const activeTx = parseResult?.transactions?.[0];
  const allSegments = activeTx?.segments || [];
  const selectedSegment = allSegments[selectedSegmentIdx] || allSegments[0];

  return (
    <div className="space-y-4 font-sans text-zinc-200 animate-in fade-in duration-200">
      
      {/* Top Banner & Mode Switcher */}
      <div className="bg-[#0e0f14] border border-[#1e2029] rounded-xl p-4 shadow-tactile flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-[#181a24] border border-[#272a39] text-[#d4af37]">
            <Binary className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-bold text-white font-mono tracking-tight">
                Inspector Forense EDI B2B ANSI X12
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#1d2719] text-[#7ee787] border border-[#23421e]">
                Nativo sin Middleware
              </span>
            </div>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">
              Decodificador sintáctico en vivo de transacciones 850, 810, 856, 861, 820, 997 y Generador 824.
            </p>
          </div>
        </div>

        {/* Sub-Tabs */}
        <div className="flex items-center space-x-1.5 p-1 bg-[#090a0d] border border-[#1a1c24] rounded-lg font-mono text-xs">
          <button
            onClick={() => setActiveSubMode('parser')}
            className={`px-3 py-1.5 rounded transition-all flex items-center space-x-1.5 ${
              activeSubMode === 'parser'
                ? 'bg-[#1e202d] text-white border border-[#2c3044] shadow-tactile font-bold'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <FileCode className="w-3.5 h-3.5 text-[#d4af37]" />
            <span>Decodificador de Segmentos</span>
          </button>

          <button
            onClick={() => setActiveSubMode('asn_auditor')}
            className={`px-3 py-1.5 rounded transition-all flex items-center space-x-1.5 ${
              activeSubMode === 'asn_auditor'
                ? 'bg-[#1e202d] text-white border border-[#2c3044] shadow-tactile font-bold'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span>Auditor ASN vs 997 UTC</span>
          </button>

          <button
            onClick={() => setActiveSubMode('generator_824')}
            className={`px-3 py-1.5 rounded transition-all flex items-center space-x-1.5 ${
              activeSubMode === 'generator_824'
                ? 'bg-[#1e202d] text-white border border-[#2c3044] shadow-tactile font-bold'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Send className="w-3.5 h-3.5 text-emerald-400" />
            <span>Generador EDI 824</span>
          </button>
        </div>
      </div>

      {/* MODE 1: PARSER & SEGMENT EXPLORER */}
      {activeSubMode === 'parser' && (
        <div className="space-y-4">
          
          {/* Preset Buttons Bar */}
          <div className="flex flex-wrap items-center justify-between gap-2 bg-[#090a0d] p-2.5 rounded-lg border border-[#1a1c24] font-mono text-xs">
            <div className="flex items-center space-x-2">
              <span className="text-zinc-500 font-bold uppercase tracking-wider text-[11px]">Transacciones Preconfiguradas:</span>
              <div className="flex flex-wrap gap-1">
                {[
                  { key: '850', label: '850 (PO)', desc: 'Orden de Compra' },
                  { key: '810', label: '810 (IN)', desc: 'Factura Comercial' },
                  { key: '856', label: '856 (SH)', desc: 'Advance Ship Notice' },
                  { key: '861', label: '861 (RC)', desc: 'Receiving Advice' },
                  { key: '820', label: '820 (RA)', desc: 'Remittance / Deductions' },
                  { key: '997', label: '997 (FA)', desc: 'Acuse Funcional' },
                ].map((item) => (
                  <button
                    key={item.key}
                    onClick={() => handleSelectSample(item.key)}
                    className={`px-2.5 py-1 rounded text-xs transition-colors flex items-center space-x-1 border ${
                      selectedSampleKey === item.key
                        ? 'bg-[#252217] text-[#eed98d] border-[#d4af37]/60 font-bold'
                        : 'bg-[#111218] text-zinc-400 hover:text-white border-[#1e2029]'
                    }`}
                    title={item.desc}
                  >
                    <span>{item.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleCopyRaw(rawEdi)}
                className="px-2.5 py-1 rounded bg-[#111218] hover:bg-[#181a24] border border-[#1e2029] text-zinc-400 hover:text-white transition-colors flex items-center space-x-1"
                title="Copiar texto EDI crudo al portapapeles"
              >
                {copiedRaw ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copiedRaw ? 'Copiado' : 'Copiar EDI'}</span>
              </button>

              <button
                onClick={() => handleParseEdi(rawEdi)}
                disabled={isParsing}
                className="px-3 py-1 rounded bg-[#1f1d14] hover:bg-[#282518] border border-[#d4af37]/70 text-[#eed98d] hover:text-white font-bold transition-all flex items-center space-x-1.5 shadow-tactile disabled:opacity-50"
              >
                <Play className={`w-3 h-3 fill-current ${isParsing ? 'animate-spin' : ''}`} />
                <span>{isParsing ? 'Decodificando...' : 'Re-analizar'}</span>
              </button>
            </div>
          </div>

          {/* Grid: Raw Editor on Left, Parsed Structure on Right */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            
            {/* Left: Raw EDI Textarea */}
            <div className="lg:col-span-5 bg-[#0e0f14] border border-[#1e2029] rounded-xl p-3 flex flex-col space-y-2">
              <div className="flex items-center justify-between pb-2 border-b border-[#181a24]">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold text-zinc-300">Contenido EDI Crudo (ANSI X12)</span>
                  {parseResult && (
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#161822] text-zinc-400 border border-[#222533]">
                      Sep: '{parseResult.element_separator}' | Term: '{parseResult.segment_terminator}'
                    </span>
                  )}
                </div>
                <span className="text-[11px] font-mono text-zinc-500">
                  {rawEdi.split('\n').length} líneas
                </span>
              </div>

              <textarea
                value={rawEdi}
                onChange={(e) => setRawEdi(e.target.value)}
                placeholder="Pega aquí el paquete crudo ANSI X12 (ISA*...~)..."
                rows={16}
                className="w-full bg-[#07080a] border border-[#181a22] rounded-lg p-3 text-xs font-mono text-zinc-300 focus:outline-none focus:border-[#d4af37] resize-none leading-relaxed select-text"
                spellCheck={false}
              />

              {parseError && (
                <div className="p-2.5 rounded bg-[#241315] border border-[#441a1e] text-red-300 text-xs font-mono flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                  <span>{parseError}</span>
                </div>
              )}
            </div>

            {/* Right: Parsed Segment Inspector */}
            <div className="lg:col-span-7 bg-[#0e0f14] border border-[#1e2029] rounded-xl p-3 flex flex-col space-y-3">
              
              {/* Header with summary badges */}
              <div className="flex items-center justify-between pb-2 border-b border-[#181a24]">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold text-white">Desglose Sintáctico de Segmentos</span>
                  {activeTx && (
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#1f1d14] text-[#eed98d] border border-[#d4af37]/40 font-bold">
                      EDI {activeTx.transaction_set_id} ({activeTx.transaction_type})
                    </span>
                  )}
                </div>
                {parseResult && (
                  <span className="text-xs font-mono text-zinc-400">
                    Total: <strong className="text-white">{parseResult.total_segments}</strong> segmentos
                  </span>
                )}
              </div>

              {/* Segments Pill Selector / Visual Chain */}
              <div className="bg-[#07080a] p-2 rounded-lg border border-[#181a22] flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
                {allSegments.map((seg, idx) => {
                  const isSelected = selectedSegmentIdx === idx;
                  const isSpecial = ['ST', 'SE', 'ISA', 'IEA', 'GS', 'GE'].includes(seg.tag);
                  const isPayload = ['PO1', 'IT1', 'BIG', 'BEG', 'SN1', 'RCD', 'BPR'].includes(seg.tag);
                  
                  return (
                    <button
                      key={idx}
                      onClick={() => setSelectedSegmentIdx(idx)}
                      className={`px-2 py-1 rounded text-xs font-mono transition-all flex items-center space-x-1 border ${
                        isSelected
                          ? 'bg-[#d4af37] text-black font-bold border-[#d4af37] shadow-tactile'
                          : isSpecial
                          ? 'bg-[#151722] text-zinc-300 border-[#222536] hover:border-zinc-500'
                          : isPayload
                          ? 'bg-[#1c2419] text-emerald-300 border-[#2d4725] hover:border-emerald-500'
                          : 'bg-[#0f1016] text-zinc-400 border-[#1c1e2a] hover:border-zinc-600'
                      }`}
                      title={`Línea ${idx + 1}: ${seg.raw}`}
                    >
                      <span className="text-[10px] opacity-70">#{idx + 1}</span>
                      <span>{seg.tag}</span>
                    </button>
                  );
                })}
              </div>

              {/* Detail Table of Selected Segment */}
              {selectedSegment ? (
                <div className="bg-[#090a0d] border border-[#181a22] rounded-lg p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 rounded bg-[#181a24] text-[#eed98d] font-mono font-bold text-xs border border-[#272a39]">
                        Segmento {selectedSegment.tag}
                      </span>
                      <span className="text-xs text-zinc-400 font-mono">
                        ({selectedSegment.elements?.length || 0} elementos posicionales)
                      </span>
                    </div>
                    <span className="text-[11px] font-mono text-zinc-500">
                      Terminador: {selectedSegment.raw.slice(-1)}
                    </span>
                  </div>

                  {/* Raw string preview */}
                  <div className="p-2 bg-[#050608] rounded border border-[#14151b] font-mono text-xs text-zinc-300 break-all select-text">
                    <span className="text-zinc-500">Raw: </span>
                    <strong className="text-white">{selectedSegment.raw}</strong>
                  </div>

                  {/* Element Breakdown Table */}
                  <div className="max-h-60 overflow-y-auto rounded border border-[#161822]">
                    <table className="w-full text-left font-mono text-xs">
                      <thead className="bg-[#10121a] text-zinc-400 uppercase text-[10px] tracking-wider border-b border-[#1c1e2c]">
                        <tr>
                          <th className="p-2 w-16">Posición</th>
                          <th className="p-2 w-28">Elemento</th>
                          <th className="p-2">Valor Crudo</th>
                          <th className="p-2">Significado Semántico B2B</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#141622] text-zinc-300">
                        {selectedSegment.elements?.map((el, elIdx) => {
                          const elemCode = `${selectedSegment.tag}${String(elIdx + 1).padStart(2, '0')}`;
                          let semanticNote = 'Elemento de datos';
                          
                          if (selectedSegment.tag === 'BEG') {
                            if (elIdx === 0) semanticNote = 'Código de Transacción (00=Original)';
                            if (elIdx === 1) semanticNote = 'Tipo de Orden (SA=Stand-Alone PO)';
                            if (elIdx === 2) semanticNote = 'Número de Orden de Compra';
                            if (elIdx === 4) semanticNote = 'Fecha de Emisión (YYYYMMDD)';
                          } else if (selectedSegment.tag === 'PO1' || selectedSegment.tag === 'IT1') {
                            if (elIdx === 0) semanticNote = 'Número de Partida (Line Item)';
                            if (elIdx === 1) semanticNote = 'Cantidad Pedida/Facturada';
                            if (elIdx === 2) semanticNote = 'Unidad de Medida (CA=Caja, EA=Pieza)';
                            if (elIdx === 3) semanticNote = 'Precio Unitario Acordado ($)';
                            if (elIdx === 6) semanticNote = 'Código SKU del Producto';
                          } else if (selectedSegment.tag === 'ISA') {
                            if (elIdx === 5) semanticNote = 'Interchange Sender ID';
                            if (elIdx === 7) semanticNote = 'Interchange Receiver ID';
                            if (elIdx === 8) semanticNote = 'Fecha Interchange (YYMMDD)';
                            if (elIdx === 12) semanticNote = 'Número de Control de Intercambio';
                          }

                          return (
                            <tr key={elIdx} className="hover:bg-[#12141e] transition-colors">
                              <td className="p-2 text-zinc-500 font-bold">#{elIdx + 1}</td>
                              <td className="p-2 text-[#eed98d] font-bold">{elemCode}</td>
                              <td className="p-2 text-white font-bold select-text">{el || <span className="text-zinc-600">NULL</span>}</td>
                              <td className="p-2 text-zinc-400 text-[11px]">{semanticNote}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                </div>
              ) : (
                <div className="p-6 text-center text-zinc-500 font-mono text-xs">
                  Selecciona un segmento de la lista superior para inspeccionar sus elementos.
                </div>
              )}

            </div>

          </div>

        </div>
      )}

      {/* MODE 2: ASN TIMELINESS AUDITOR */}
      {activeSubMode === 'asn_auditor' && (
        <div className="bg-[#0e0f14] border border-[#1e2029] rounded-xl p-5 space-y-4">
          
          <div className="flex items-center justify-between pb-3 border-b border-[#181a24]">
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded bg-[#101b24] border border-[#1d354a] text-cyan-400">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white font-mono">
                  Auditor Forense de Lead-Time: EDI 856 (ASN) vs Acuse 997 UTC
                </h3>
                <p className="text-xs text-zinc-400 font-mono">
                  Calcula la ventana exacta de transmisión contra la cita de muelle. Desvirtúa multas extemporáneas de Retailers.
                </p>
              </div>
            </div>

            <button
              onClick={handleRunAsnAudit}
              disabled={isAuditing}
              className="btn-tactile px-4 py-2 rounded bg-[#14232c] hover:bg-[#1c3240] border border-cyan-500/50 text-cyan-300 hover:text-white text-xs font-mono font-bold transition-all flex items-center space-x-2 shadow-tactile disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 fill-current ${isAuditing ? 'animate-spin' : ''}`} />
              <span>{isAuditing ? 'Auditando Lead-Time...' : 'Ejecutar Auditoría Forense'}</span>
            </button>
          </div>

          {/* Form Parameters */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono font-bold text-zinc-300 mb-1">
                Cita Programada de Descarga en Muelle (Scheduled Dock Time UTC)
              </label>
              <input
                type="text"
                value={scheduledDockTime}
                onChange={(e) => setScheduledDockTime(e.target.value)}
                className="w-full bg-[#07080a] border border-[#181a22] rounded p-2 text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
              />
              <span className="text-[10px] font-mono text-zinc-500">Formato ISO: YYYY-MM-DDTHH:MM:SSZ</span>
            </div>

            <div>
              <label className="block text-xs font-mono font-bold text-zinc-300 mb-1">
                Horas de Antelación Mínima Contractual (Lead Time Required)
              </label>
              <input
                type="number"
                step="0.5"
                value={requiredLeadHours}
                onChange={(e) => setRequiredLeadHours(e.target.value)}
                className="w-full bg-[#07080a] border border-[#181a22] rounded p-2 text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
              />
              <span className="text-[10px] font-mono text-zinc-500">Estándar Walmart/Amazon: 4.0 horas previas al arribo</span>
            </div>
          </div>

          {/* Inputs for ASN 856 and 997 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <span className="text-xs font-mono font-bold text-zinc-300">Contenido EDI 856 (ASN)</span>
              <textarea
                value={asnRawInput}
                onChange={(e) => setAsnRawInput(e.target.value)}
                rows={6}
                className="w-full bg-[#07080a] border border-[#181a22] rounded p-2 text-xs font-mono text-zinc-300 focus:outline-none focus:border-cyan-500 select-text"
              />
            </div>

            <div className="space-y-1">
              <span className="text-xs font-mono font-bold text-zinc-300">Contenido EDI 997 (Functional Acknowledgment)</span>
              <textarea
                value={ack997RawInput}
                onChange={(e) => setAck997RawInput(e.target.value)}
                rows={6}
                className="w-full bg-[#07080a] border border-[#181a22] rounded p-2 text-xs font-mono text-zinc-300 focus:outline-none focus:border-cyan-500 select-text"
              />
            </div>
          </div>

          {/* Result Card */}
          {auditResult && (
            <div className="bg-[#090a0d] border border-[#1f2937] rounded-xl p-4 space-y-3 animate-in fade-in duration-150">
              <div className="flex items-center justify-between pb-2 border-b border-[#181a24]">
                <div className="flex items-center space-x-2">
                  {auditResult.is_compliant ? (
                    <span className="px-2.5 py-1 rounded bg-[#16271c] border border-[#2b4c33] text-emerald-300 text-xs font-mono font-bold flex items-center space-x-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span>TRANSMISIÓN CONFORME A CONTRATO ({auditResult.timeliness_status})</span>
                    </span>
                  ) : (
                    <span className="px-2.5 py-1 rounded bg-[#2b1717] border border-[#522525] text-red-300 text-xs font-mono font-bold flex items-center space-x-1.5">
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                      <span>INCUMPLIMIENTO / RETARDO ({auditResult.timeliness_status})</span>
                    </span>
                  )}
                  <span className="text-xs font-mono text-zinc-400">
                    Lead-Time Efectivo: <strong className="text-white">{auditResult.effective_lead_hours} horas</strong>
                  </span>
                </div>

                <span className="text-xs font-mono text-zinc-500">
                  Transmisión ASN: {auditResult.asn_transmitted_at_utc}
                </span>
              </div>

              {/* Argumento de Defensa */}
              <div className="p-3 bg-[#0d1117] rounded-lg border border-[#1e293b] space-y-1.5">
                <span className="text-[11px] font-mono font-bold text-cyan-400 uppercase tracking-wider">
                  Escudo Pericial & Fundamento Jurídico de Defensa:
                </span>
                <p className="text-xs font-mono text-zinc-200 leading-relaxed select-text">
                  {auditResult.defense_argument}
                </p>
              </div>
            </div>
          )}

        </div>
      )}

      {/* MODE 3: EDI 824 APPLICATION ADVICE GENERATOR */}
      {activeSubMode === 'generator_824' && (
        <div className="bg-[#0e0f14] border border-[#1e2029] rounded-xl p-5 space-y-4">
          
          <div className="flex items-center justify-between pb-3 border-b border-[#181a24]">
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded bg-[#102419] border border-[#1d4a2d] text-emerald-400">
                <Send className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white font-mono">
                  Generador Oficial de Notificación de Rechazo EDI 824 (Application Advice)
                </h3>
                <p className="text-xs text-zinc-400 font-mono">
                  Genera la transacción formal ANSI X12 824 de rechazo inmediato de nota de débito conforme al estándar B2B.
                </p>
              </div>
            </div>

            <button
              onClick={handleRunGenerate824}
              disabled={isGenerating824}
              className="btn-tactile px-4 py-2 rounded bg-[#142c1e] hover:bg-[#1a3c28] border border-emerald-500/50 text-emerald-300 hover:text-white text-xs font-mono font-bold transition-all flex items-center space-x-2 shadow-tactile disabled:opacity-50"
            >
              <Sparkles className={`w-3.5 h-3.5 fill-current ${isGenerating824 ? 'animate-spin' : ''}`} />
              <span>{isGenerating824 ? 'Generando 824...' : 'Generar Paquete EDI 824'}</span>
            </button>
          </div>

          {/* Form Fields */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-mono font-bold text-zinc-300 mb-1">ID Disputa</label>
              <input
                type="text"
                value={genDisputeId}
                onChange={(e) => setGenDisputeId(e.target.value)}
                className="w-full bg-[#07080a] border border-[#181a22] rounded p-2 text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-mono font-bold text-zinc-300 mb-1">ID EDI Retailer (Sender)</label>
              <input
                type="text"
                value={genRetailerId}
                onChange={(e) => setGenRetailerId(e.target.value)}
                className="w-full bg-[#07080a] border border-[#181a22] rounded p-2 text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-mono font-bold text-zinc-300 mb-1">ID EDI Proveedor (Receiver)</label>
              <input
                type="text"
                value={genSupplierId}
                onChange={(e) => setGenSupplierId(e.target.value)}
                className="w-full bg-[#07080a] border border-[#181a22] rounded p-2 text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-mono font-bold text-zinc-300 mb-1">Factura Disputada</label>
              <input
                type="text"
                value={genInvoiceNum}
                onChange={(e) => setGenInvoiceNum(e.target.value)}
                className="w-full bg-[#07080a] border border-[#181a22] rounded p-2 text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-mono font-bold text-zinc-300 mb-1">Código Deducción ANSI (DE 426)</label>
              <input
                type="text"
                value={genDeductionCode}
                onChange={(e) => setGenDeductionCode(e.target.value)}
                className="w-full bg-[#07080a] border border-[#181a22] rounded p-2 text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-mono font-bold text-zinc-300 mb-1">Monto Reclamado ($)</label>
              <input
                type="text"
                value={genClaimableAmount}
                onChange={(e) => setGenClaimableAmount(e.target.value)}
                className="w-full bg-[#07080a] border border-[#181a22] rounded p-2 text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono font-bold text-zinc-300 mb-1">Fundamento Contractual / Pericial de Rechazo</label>
            <input
              type="text"
              value={genRejectionBasis}
              onChange={(e) => setGenRejectionBasis(e.target.value)}
              className="w-full bg-[#07080a] border border-[#181a22] rounded p-2 text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          {/* Generated Result Output */}
          {generated824Result && (
            <div className="bg-[#090a0d] border border-[#1b3323] rounded-xl p-4 space-y-3 animate-in fade-in duration-150">
              <div className="flex items-center justify-between pb-2 border-b border-[#181a24]">
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 rounded bg-[#16271c] text-emerald-400 font-mono font-bold text-xs border border-[#2b4c33]">
                    EDI 824 GENERADO EXITOSAMENTE
                  </span>
                  <span className="text-xs font-mono text-zinc-400">
                    {generated824Result.segments_count} segmentos estándar X12
                  </span>
                </div>

                <button
                  onClick={() => handleCopyRaw(generated824Result.raw_edi_824)}
                  className="px-2.5 py-1 rounded bg-[#111218] hover:bg-[#181a24] border border-[#1e2029] text-zinc-300 hover:text-white text-xs font-mono transition-colors flex items-center space-x-1"
                >
                  {copiedRaw ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedRaw ? 'Copiado' : 'Copiar EDI 824'}</span>
                </button>
              </div>

              <pre className="p-3 bg-[#050608] border border-[#131d17] rounded-lg text-xs font-mono text-emerald-300 overflow-x-auto select-text leading-relaxed">
                {generated824Result.raw_edi_824}
              </pre>
            </div>
          )}

        </div>
      )}

    </div>
  );
}
