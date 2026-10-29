import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { 
  Eye, 
  Camera, 
  ShieldCheck, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  Download, 
  FileText, 
  Layers, 
  Sparkles, 
  Info,
  RotateCcw,
  Box,
  MapPin,
  Lock,
  Unlock
} from 'lucide-react';

export default function PalletVisionView() {
  const [samples, setSamples] = useState([]);
  const [selectedSampleIdx, setSelectedSampleIdx] = useState(0);
  const [activeCert, setActiveCert] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedBoxIdx, setSelectedBoxIdx] = useState(0);

  // Cargar muestras periciales al montar
  useEffect(() => {
    async function loadSamples() {
      setLoading(true);
      try {
        const res = await apiClient.getVisionSamples();
        if (res && res.samples && res.samples.length > 0) {
          setSamples(res.samples);
          setActiveCert(res.samples[0].certificate);
        }
      } catch (err) {
        console.error('Error cargando muestras de visión:', err);
      } finally {
        setLoading(false);
      }
    }
    loadSamples();
  }, []);

  const handleSelectSample = (idx) => {
    setSelectedSampleIdx(idx);
    if (samples[idx]) {
      setActiveCert(samples[idx].certificate);
      setSelectedBoxIdx(0);
    }
  };

  const handleDownloadCertificateJson = () => {
    if (!activeCert) return;
    const blob = new Blob([JSON.stringify(activeCert, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `certificado_carga_${activeCert.certificate_id}.json`;
    a.click();
  };

  const currentSample = samples[selectedSampleIdx];
  const selectedBox = activeCert?.bounding_boxes?.[selectedBoxIdx];

  return (
    <div className="space-y-4 font-sans text-zinc-200 animate-in fade-in duration-200">
      
      {/* Top Header Card */}
      <div className="bg-[#0e0f14] border border-[#1e2029] rounded-xl p-4 shadow-tactile flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-[#14231b] border border-[#214732] text-emerald-400">
            <Camera className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-bold text-white font-mono tracking-tight">
                Laboratorio de Visión Multimodal en Muelle & Certificación C-TPAT
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#14261d] text-emerald-300 border border-[#234b32]">
                ISO 17712 Compliant
              </span>
            </div>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">
              Auditoría fotográfica pericial: OCR de precintos de alta seguridad, detección de emplaye, conteo volumétrico y Bounding Boxes.
            </p>
          </div>
        </div>

        {/* Certificate Export Button */}
        {activeCert && (
          <button
            onClick={handleDownloadCertificateJson}
            className="btn-tactile px-3.5 py-2 rounded bg-[#16271c] hover:bg-[#203a29] border border-emerald-500/60 text-emerald-300 hover:text-white font-mono text-xs font-bold transition-all flex items-center space-x-2 shadow-tactile"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Descargar Certificado Forense</span>
          </button>
        )}
      </div>

      {/* Preset Inspection Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-2 bg-[#090a0d] p-2.5 rounded-lg border border-[#1a1c24] font-mono text-xs">
        <div className="flex items-center space-x-2">
          <span className="text-zinc-500 font-bold uppercase text-[11px]">Inspección Forense Activa:</span>
          <div className="flex flex-wrap gap-1.5">
            {samples.map((s, idx) => (
              <button
                key={s.sample_id}
                onClick={() => handleSelectSample(idx)}
                className={`px-3 py-1 rounded text-xs transition-colors flex items-center space-x-1.5 border ${
                  selectedSampleIdx === idx
                    ? 'bg-[#182a1d] text-emerald-300 border-emerald-500/70 font-bold shadow-tactile'
                    : 'bg-[#111218] text-zinc-400 hover:text-white border-[#1e2029]'
                }`}
              >
                <Eye className="w-3 h-3" />
                <span>{s.title}</span>
              </button>
            ))}
          </div>
        </div>

        {activeCert && (
          <div className="flex items-center space-x-2 text-zinc-400">
            <MapPin className="w-3.5 h-3.5 text-[#d4af37]" />
            <span className="text-zinc-300">{activeCert.dock_location}</span>
          </div>
        )}
      </div>

      {/* Main Inspection Stage: Pallet Visual Canvas (Left) + Evidence Breakdown (Right) */}
      {activeCert && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          
          {/* Left Canvas (Simulated Multi-Angle Pallet Inspector with Overlay Bounding Boxes) */}
          <div className="lg:col-span-7 bg-[#07080a] border border-[#1e2029] rounded-xl p-4 flex flex-col space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#141622]">
              <span className="text-xs font-mono font-bold text-white flex items-center space-x-1.5">
                <Box className="w-3.5 h-3.5 text-cyan-400" />
                <span>Fotograma de Recepción en Bahía (Resolución 4K Forense)</span>
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#10151f] text-cyan-300 border border-[#1b2a42]">
                {activeCert.bounding_boxes.length} Objetos Delimitados
              </span>
            </div>

            {/* Visual Canvas Simulator */}
            <div className="relative w-full h-80 rounded-lg bg-[#0b0d13] border border-[#1a1e2d] overflow-hidden flex items-center justify-center select-none shadow-inner">
              
              {/* Graphical Pallet Representation */}
              <div className="w-64 h-64 border-2 border-dashed border-[#23293d] rounded-lg relative flex flex-col justify-end p-2 items-center bg-[#0e111a]/80">
                
                {/* Security Seal Icon at top */}
                <div className="absolute top-2 w-14 h-12 rounded border border-emerald-500/80 bg-emerald-950/60 flex flex-col items-center justify-center text-[9px] font-mono text-emerald-300">
                  <Lock className="w-3.5 h-3.5" />
                  <span>C-TPAT</span>
                </div>

                {/* Stiff tiers */}
                <div className="w-full grid grid-cols-4 gap-1 mb-2">
                  {[...Array(16)].map((_, i) => (
                    <div 
                      key={i} 
                      className={`h-8 rounded border text-[8px] font-mono flex items-center justify-center font-bold ${
                        activeCert.overall_verdict === 'IRREGULARITY_FLAGGED' && (i === 5 || i === 9)
                          ? 'bg-red-950/80 border-red-500/80 text-red-300'
                          : 'bg-[#151c28] border-[#2b354e] text-zinc-400'
                      }`}
                    >
                      BOX
                    </div>
                  ))}
                </div>

                {/* Wooden Pallet Base */}
                <div className="w-full h-6 rounded bg-[#2a2215] border border-[#524125] flex items-center justify-between px-3 text-[9px] font-mono text-[#eed98d]">
                  <span>CHEP GMA 48x40</span>
                  <span>SOLID BLOCK</span>
                </div>

              </div>

              {/* Interactive Bounding Boxes Overlaid */}
              <div className="absolute inset-0 p-4 pointer-events-none">
                {activeCert.bounding_boxes.map((bbox, bIdx) => {
                  const isSelected = selectedBoxIdx === bIdx;
                  // Map normalized 0-1000 to percentages
                  const top = `${bbox.box_2d[0] / 10}%`;
                  const left = `${bbox.box_2d[1] / 10}%`;
                  const height = `${(bbox.box_2d[2] - bbox.box_2d[0]) / 10}%`;
                  const width = `${(bbox.box_2d[3] - bbox.box_2d[1]) / 10}%`;

                  return (
                    <div
                      key={bIdx}
                      style={{ top, left, width, height, borderColor: bbox.color_hex }}
                      className={`absolute border-2 rounded transition-all pointer-events-auto cursor-pointer flex flex-col justify-between p-1 ${
                        isSelected
                          ? 'shadow-[0_0_15px_rgba(16,185,129,0.5)] bg-emerald-500/10'
                          : 'opacity-70 hover:opacity-100'
                      }`}
                      onClick={() => setSelectedBoxIdx(bIdx)}
                    >
                      <span 
                        style={{ backgroundColor: bbox.color_hex }} 
                        className="text-[9px] font-mono font-bold text-black px-1 rounded w-max"
                      >
                        {bbox.label} ({(bbox.confidence * 100).toFixed(0)}%)
                      </span>
                    </div>
                  );
                })}
              </div>

            </div>

            {/* Selected Bounding Box Details Bar */}
            {selectedBox && (
              <div className="p-3 bg-[#0d0f17] border border-[#1c2236] rounded-lg font-mono text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-white font-bold flex items-center space-x-1.5">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: selectedBox.color_hex }} />
                    <span>{selectedBox.label}</span>
                  </span>
                  <span className="text-zinc-400 text-[11px]">
                    Certeza: <strong className="text-white">{(selectedBox.confidence * 100).toFixed(1)}%</strong>
                  </span>
                </div>
                <p className="text-zinc-300 text-[11px] leading-relaxed select-text">
                  {selectedBox.details}
                </p>
              </div>
            )}

          </div>

          {/* Right Column: Forensic Certificate & Statutory Findings */}
          <div className="lg:col-span-5 bg-[#0e0f14] border border-[#1e2029] rounded-xl p-4 flex flex-col space-y-3">
            
            {/* Verdict Badge */}
            <div className="flex items-center justify-between pb-2 border-b border-[#181a24]">
              <span className="text-xs font-mono font-bold text-white">
                Certificado Criptográfico C-TPAT
              </span>
              {activeCert.overall_verdict === 'CARGO_PRISTINE_ACCEPTED' ? (
                <span className="px-2.5 py-1 rounded bg-[#142b1c] border border-[#235334] text-emerald-300 text-xs font-mono font-bold flex items-center space-x-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>CARGA PRÍSTINA (CONFORME)</span>
                </span>
              ) : (
                <span className="px-2.5 py-1 rounded bg-[#2d1414] border border-[#5a2222] text-red-300 text-xs font-mono font-bold flex items-center space-x-1">
                  <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
                  <span>ALERTA DE MERMA</span>
                </span>
              )}
            </div>

            {/* Seal & Pallet Audits Grid */}
            <div className="grid grid-cols-2 gap-2.5 font-mono text-xs">
              <div className="p-2.5 rounded bg-[#090a0e] border border-[#181a24] space-y-1">
                <span className="text-[10px] text-zinc-500 uppercase block font-bold">Precinto de Seguridad</span>
                <strong className="text-emerald-400 block text-xs select-text">
                  #{activeCert.seal_audit.seal_number_detected}
                </strong>
                <span className="text-[10px] text-zinc-400 block">
                  Estado: {activeCert.seal_audit.seal_status}
                </span>
              </div>

              <div className="p-2.5 rounded bg-[#090a0e] border border-[#181a24] space-y-1">
                <span className="text-[10px] text-zinc-500 uppercase block font-bold">Conteo de Bultos</span>
                <strong className="text-white block text-xs">
                  {activeCert.pallet_audit.total_boxes_detected} Cajas Estibadas
                </strong>
                <span className="text-[10px] text-zinc-400 block">
                  Dañadas: {activeCert.pallet_audit.damaged_boxes_count} bultos
                </span>
              </div>
            </div>

            {/* Cryptographic Hash Seed */}
            <div className="p-2.5 bg-[#07080a] rounded border border-[#161822] font-mono text-[11px] space-y-1">
              <span className="text-[10px] text-zinc-500 uppercase block font-bold">Hash Forense SHA-256 (Inalterable)</span>
              <span className="text-cyan-400 break-all select-text font-mono block">
                {activeCert.forensic_sha256_hash}
              </span>
            </div>

            {/* Legal Statement */}
            <div className="p-3 bg-[#0d1219] rounded-lg border border-[#1c2a38] space-y-1.5 font-mono text-xs">
              <span className="text-[10px] text-cyan-400 uppercase tracking-wider block font-bold">
                Conclusión Probatoria Pericial (Art. 88 CCom):
              </span>
              <p className="text-zinc-200 leading-relaxed text-[11px] select-text">
                {activeCert.evidentiary_legal_statement}
              </p>
            </div>

            <div className="pt-1 flex items-center justify-between text-[10px] font-mono text-zinc-500">
              <span>Folio: {activeCert.certificate_id}</span>
              <span>Timestamp UTC: {activeCert.inspected_at_utc.slice(0, 19)}Z</span>
            </div>

          </div>

        </div>
      )}

    </div>
  );
}
