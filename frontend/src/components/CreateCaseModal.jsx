import React, { useState, useRef } from 'react';
import { apiClient } from '../api/client';
import { 
  X, 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Sparkles, 
  Layers, 
  FileCheck, 
  Plus, 
  Trash2,
  Sliders,
  DollarSign
} from 'lucide-react';

export default function CreateCaseModal({ onClose, onCaseCreated }) {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'guided'

  // --- Upload Mode States ---
  const [caseId, setCaseId] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [description, setDescription] = useState('');
  const [files, setFiles] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef(null);

  // --- Guided Mode States ---
  const [guidedId, setGuidedId] = useState('');
  const [guidedName, setGuidedName] = useState('');
  const [vendorId, setVendorId] = useState('VEN-PROVEEDOR-01');
  const [customerId, setCustomerId] = useState('CUST-RETAIL-01');
  const [poReference, setPoReference] = useState('PO-2026-8801');
  const [itemName, setItemName] = useState('Lote Suministros Industriales');
  const [orderedQty, setOrderedQty] = useState(100);
  const [deliveredQty, setDeliveredQty] = useState(85);
  const [missingQty, setMissingQty] = useState(15);
  const [unitPrice, setUnitPrice] = useState(60.0);
  const [unauthPenalty, setUnauthPenalty] = useState(300.0);
  const [penaltyReason, setPenaltyReason] = useState('Deducción por retraso no convenido en contrato');
  const [deliverySigned, setDeliverySigned] = useState(true);

  // File handling
  const handleFileChange = (e) => {
    if (e.target.files) {
      const added = Array.from(e.target.files);
      setFiles((prev) => [...prev, ...added]);
    }
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      const added = Array.from(e.dataTransfer.files);
      setFiles((prev) => [...prev, ...added]);
    }
  };

  // Submit Upload
  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!caseId.trim()) {
      setErrorMessage('Por favor ingresa un identificador para el caso (ej. case_mi_empresa).');
      return;
    }
    if (files.length === 0) {
      setErrorMessage('Por favor adjunta al menos un archivo (PDF, JSON o imagen).');
      return;
    }

    setErrorMessage('');
    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('case_id', caseId.trim());
      formData.append('display_name', displayName.trim() || caseId.trim());
      formData.append('category', 'Personalizado');
      formData.append('description', description.trim() || 'Expediente subido por el usuario.');

      files.forEach((f) => {
        formData.append('files', f);
      });

      const res = await apiClient.uploadCase(formData);
      onCaseCreated(res.case_id);
      onClose();
    } catch (err) {
      setErrorMessage(err.message || 'Error al subir el expediente.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Submit Guided
  const handleGuidedSubmit = async (e) => {
    e.preventDefault();
    if (!guidedId.trim()) {
      setErrorMessage('Por favor ingresa un identificador para el caso.');
      return;
    }

    setErrorMessage('');
    setIsSubmitting(true);

    try {
      const payload = {
        case_id: guidedId.trim(),
        display_name: guidedName.trim() || guidedId.trim(),
        category: 'Personalizado',
        description: `Disputa ${vendorId} vs ${customerId} con faltante físico y penalizaciones.`,
        vendor_id: vendorId,
        customer_id: customerId,
        po_reference: poReference,
        currency: 'USD',
        items: [
          {
            item_id: 'SKU-PROD-01',
            description: itemName,
            ordered_quantity: Number(orderedQty),
            delivered_quantity: Number(deliveredQty),
            missing_quantity: Number(missingQty),
            damaged_quantity: 0,
            agreed_unit_price: Number(unitPrice),
            invoiced_unit_price: Number(unitPrice),
          },
        ],
        unauthorized_penalty: Number(unauthPenalty),
        unauthorized_penalty_reason: penaltyReason,
        delivery_signed: deliverySigned,
        days_to_claim: 18,
        contract_tolerance: 0.0,
      };

      const res = await apiClient.createGuidedCase(payload);
      onCaseCreated(res.case_id);
      onClose();
    } catch (err) {
      setErrorMessage(err.message || 'Error al generar el caso.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Detect file signatures from names
  const detectedDocTypes = files.map((f) => {
    const n = f.name.toLowerCase();
    if (n.includes('inv') || n.includes('fact')) return 'Factura';
    if (n.includes('po') || n.includes('orden') || n.includes('purchase')) return 'Orden de Compra';
    if (n.includes('del') || n.includes('remis') || n.includes('pod') || n.includes('guia')) return 'Remisión';
    if (n.includes('pay') || n.includes('pago') || n.includes('remittance')) return 'Comprobante Pago';
    if (n.includes('cont') || n.includes('acuerdo') || n.includes('contract')) return 'Contrato';
    return 'Documento General';
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-[#101115] border border-[#2b2d39] rounded-xl max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#20222a] bg-[#14151b] flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#242116] border border-[#d4af37]/40 flex items-center justify-center text-[#d4af37]">
              <UploadCloud className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                Poner Caso para Conciliación
              </h3>
              <p className="text-[11px] text-zinc-400">
                Sube tus documentos o genera un caso guiado para que el agente lo audite
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded-md text-zinc-400 hover:text-white hover:bg-[#1f2029] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="px-6 pt-3 border-b border-[#20222a] bg-[#121318] flex space-x-2">
          <button
            onClick={() => { setActiveTab('upload'); setErrorMessage(''); }}
            className={`flex items-center space-x-2 px-3 py-2 text-xs font-mono font-medium rounded-t-md transition-colors border-b-2 ${
              activeTab === 'upload'
                ? 'border-[#d4af37] text-[#eed98d] bg-[#171820]'
                : 'border-transparent text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Subir Archivos (PDF, JSON, Imágenes)</span>
          </button>

          <button
            onClick={() => { setActiveTab('guided'); setErrorMessage(''); }}
            className={`flex items-center space-x-2 px-3 py-2 text-xs font-mono font-medium rounded-t-md transition-colors border-b-2 ${
              activeTab === 'guided'
                ? 'border-[#d4af37] text-[#eed98d] bg-[#171820]'
                : 'border-transparent text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Generador Rápido Guiado</span>
          </button>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="mx-6 mt-4 p-3 bg-red-950/40 border border-red-500/30 rounded-lg flex items-center space-x-2.5 text-xs text-red-300 font-mono">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-400" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'upload' ? (
            <form onSubmit={handleUploadSubmit} className="space-y-4">
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-mono text-zinc-400 mb-1">
                    ID DEL CASO <span className="text-[#d4af37]">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="ej. case_mi_empresa"
                    value={caseId}
                    onChange={(e) => setCaseId(e.target.value)}
                    className="w-full px-3 py-2 bg-[#16171d] border border-[#242632] rounded-md text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-[#d4af37]/60 font-mono"
                  />
                  <span className="text-[10px] text-zinc-500">Se guardará en data/cases/{caseId || 'tu_caso'}</span>
                </div>

                <div>
                  <label className="block text-[11px] font-mono text-zinc-400 mb-1">
                    NOMBRE VISIBLE
                  </label>
                  <input
                    type="text"
                    placeholder="ej. Disputa Logística Alfa 2026"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    className="w-full px-3 py-2 bg-[#16171d] border border-[#242632] rounded-md text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-[#d4af37]/60 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-zinc-400 mb-1">
                  DESCRIPCIÓN COMERCIAL
                </label>
                <input
                  type="text"
                  placeholder="ej. Discrepancia por faltante en muelle y deducción indebida..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 bg-[#16171d] border border-[#242632] rounded-md text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-[#d4af37]/60 font-mono"
                />
              </div>

              {/* Drag & Drop Area */}
              <div>
                <label className="block text-[11px] font-mono text-zinc-400 mb-1">
                  ARCHIVOS DEL EXPEDIENTE <span className="text-[#d4af37]">*</span>
                </label>
                <div 
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-[#2b2d39] hover:border-[#d4af37]/50 bg-[#14151b] hover:bg-[#181920] rounded-xl p-5 text-center cursor-pointer transition-colors"
                >
                  <UploadCloud className="w-8 h-8 text-[#d4af37] mx-auto mb-2 opacity-80" />
                  <p className="text-xs text-zinc-200 font-mono font-medium">
                    Haz clic para seleccionar o arrastra aquí tus documentos
                  </p>
                  <p className="text-[11px] text-zinc-500 mt-1">
                    Formatos soportados: PDF, JSON, PNG, JPG, JPEG, Markdown
                  </p>
                  <input 
                    type="file"
                    multiple
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    className="hidden"
                    accept=".pdf,.json,.png,.jpg,.jpeg,.webp,.md,.txt"
                  />
                </div>
              </div>

              {/* Uploaded Files List */}
              {files.length > 0 && (
                <div className="space-y-1.5 bg-[#13141a] p-3 rounded-lg border border-[#242632]">
                  <div className="flex items-center justify-between text-[11px] font-mono text-zinc-400 mb-1">
                    <span>Documentos agregados ({files.length}):</span>
                    <button 
                      type="button"
                      onClick={() => setFiles([])}
                      className="text-zinc-500 hover:text-red-400 transition-colors"
                    >
                      Limpiar todo
                    </button>
                  </div>
                  <div className="max-h-36 overflow-y-auto space-y-1">
                    {files.map((file, idx) => (
                      <div 
                        key={idx}
                        className="flex items-center justify-between px-2.5 py-1.5 rounded bg-[#181922] border border-[#252733] text-xs font-mono"
                      >
                        <div className="flex items-center space-x-2 truncate">
                          <FileText className="w-3.5 h-3.5 text-[#d4af37]" />
                          <span className="text-zinc-200 truncate">{file.name}</span>
                          <span className="text-[10px] text-zinc-500">
                            ({(file.size / 1024).toFixed(1)} KB)
                          </span>
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#20222e] text-[#eed98d]">
                            {detectedDocTypes[idx]}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeFile(idx)}
                          className="text-zinc-500 hover:text-red-400 p-1"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-2.5 px-4 bg-[#242116] hover:bg-[#2d2615] border border-[#d4af37]/60 hover:border-[#d4af37] text-[#eed98d] font-mono font-bold text-xs uppercase tracking-wider rounded-lg transition-all flex items-center justify-center space-x-2 shadow-lg disabled:opacity-50"
                >
                  <Sparkles className="w-4 h-4 text-[#d4af37]" />
                  <span>{isSubmitting ? 'Cargando y Preparando...' : 'Cargar y Analizar con Agente'}</span>
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleGuidedSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-mono text-zinc-400 mb-1">
                    ID DEL CASO <span className="text-[#d4af37]">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="ej. case_mi_retailer"
                    value={guidedId}
                    onChange={(e) => setGuidedId(e.target.value)}
                    className="w-full px-3 py-2 bg-[#16171d] border border-[#242632] rounded-md text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-[#d4af37]/60 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-mono text-zinc-400 mb-1">
                    NOMBRE VISIBLE
                  </label>
                  <input
                    type="text"
                    placeholder="ej. Disputa Retail Sur"
                    value={guidedName}
                    onChange={(e) => setGuidedName(e.target.value)}
                    className="w-full px-3 py-2 bg-[#16171d] border border-[#242632] rounded-md text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-[#d4af37]/60 font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-[11px] font-mono text-zinc-400 mb-1">PROVEEDOR</label>
                  <input
                    type="text"
                    value={vendorId}
                    onChange={(e) => setVendorId(e.target.value)}
                    className="w-full px-3 py-1.5 bg-[#16171d] border border-[#242632] rounded-md text-xs text-zinc-200 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-mono text-zinc-400 mb-1">COMPRADOR / CLIENTE</label>
                  <input
                    type="text"
                    value={customerId}
                    onChange={(e) => setCustomerId(e.target.value)}
                    className="w-full px-3 py-1.5 bg-[#16171d] border border-[#242632] rounded-md text-xs text-zinc-200 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-mono text-zinc-400 mb-1">REF. ORDEN COMPRA</label>
                  <input
                    type="text"
                    value={poReference}
                    onChange={(e) => setPoReference(e.target.value)}
                    className="w-full px-3 py-1.5 bg-[#16171d] border border-[#242632] rounded-md text-xs text-zinc-200 font-mono"
                  />
                </div>
              </div>

              {/* Items Section */}
              <div className="bg-[#13141a] p-3 rounded-lg border border-[#242632] space-y-3">
                <span className="text-[11px] font-mono text-[#eed98d] font-semibold block">
                  Mercancía y Conciliación Física
                </span>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] font-mono text-zinc-400 mb-1">DESCRIPCIÓN DE PRODUCTO</label>
                    <input
                      type="text"
                      value={itemName}
                      onChange={(e) => setItemName(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-[#181922] border border-[#262836] rounded text-xs text-zinc-200 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono text-zinc-400 mb-1">PRECIO UNITARIO ($)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={unitPrice}
                      onChange={(e) => setUnitPrice(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-[#181922] border border-[#262836] rounded text-xs text-zinc-200 font-mono"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[10px] font-mono text-zinc-400 mb-1">CANT. PEDIDA</label>
                    <input
                      type="number"
                      value={orderedQty}
                      onChange={(e) => setOrderedQty(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-[#181922] border border-[#262836] rounded text-xs text-zinc-200 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono text-zinc-400 mb-1">CANT. RECIBIDA</label>
                    <input
                      type="number"
                      value={deliveredQty}
                      onChange={(e) => setDeliveredQty(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-[#181922] border border-[#262836] rounded text-xs text-zinc-200 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono text-zinc-400 mb-1">FALTANTE FÍSICO</label>
                    <input
                      type="number"
                      value={missingQty}
                      onChange={(e) => setMissingQty(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-[#181922] border border-[#262836] rounded text-xs text-zinc-200 font-mono text-amber-400"
                    />
                  </div>
                </div>
              </div>

              {/* Deductions Section */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-mono text-zinc-400 mb-1">
                    PENALIZACIÓN NO AUTORIZADA ($ USD)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={unauthPenalty}
                    onChange={(e) => setUnauthPenalty(e.target.value)}
                    className="w-full px-3 py-1.5 bg-[#16171d] border border-[#242632] rounded-md text-xs text-zinc-200 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-mono text-zinc-400 mb-1">
                    REMISIÓN FIRMADA CON SELLO
                  </label>
                  <select
                    value={deliverySigned ? 'true' : 'false'}
                    onChange={(e) => setDeliverySigned(e.target.value === 'true')}
                    className="w-full px-3 py-1.5 bg-[#16171d] border border-[#242632] rounded-md text-xs text-zinc-200 font-mono"
                  >
                    <option value="true">Sí (Con sello y firma de discrepancia)</option>
                    <option value="false">No (Sin firma / Deducción unilateral)</option>
                  </select>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-2.5 px-4 bg-[#242116] hover:bg-[#2d2615] border border-[#d4af37]/60 hover:border-[#d4af37] text-[#eed98d] font-mono font-bold text-xs uppercase tracking-wider rounded-lg transition-all flex items-center justify-center space-x-2 shadow-lg disabled:opacity-50"
                >
                  <Sparkles className="w-4 h-4 text-[#d4af37]" />
                  <span>{isSubmitting ? 'Generando y Auditando...' : 'Generar Expediente y Analizar'}</span>
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
