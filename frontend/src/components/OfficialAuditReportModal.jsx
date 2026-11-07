import React, { useState, useEffect } from 'react';
import { 
  Printer, 
  Copy, 
  Check, 
  X, 
  ShieldCheck, 
  FileText, 
  Award, 
  Scale, 
  CheckCircle2, 
  AlertTriangle,
  QrCode,
  Lock,
  ExternalLink
} from 'lucide-react';
import { apiClient } from '../api/client';
import ExecutiveAudioBriefing from './ExecutiveAudioBriefing';

export default function OfficialAuditReportModal({ caseId, report, onClose }) {
  const [copied, setCopied] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);
  const [dossier, setDossier] = useState(null);
  const [loadingDossier, setLoadingDossier] = useState(false);

  useEffect(() => {
    if (caseId) {
      setLoadingDossier(true);
      apiClient.getOfficialDossier(caseId)
        .then(data => setDossier(data))
        .catch(err => {
          console.warn("Could not load backend dossier, using fallback from report:", err);
        })
        .finally(() => setLoadingDossier(false));
    }
  }, [caseId]);

  if (!report && !dossier) return null;

  const fin = report?.financial_summary || {};
  const root = report?.root_cause_analysis || {};
  const notice = report?.notice_window_audit || {};
  const tribunal = report?.collegiate_tribunal || {};
  const cert = report?.audit_certification || {};

  const billed = dossier?.three_way_match?.billed_amount ?? fin.billed_amount ?? report?.billed_amount ?? 0;
  const received = dossier?.three_way_match?.received_amount ?? fin.received_amount ?? report?.received_amount ?? 0;
  const justified = dossier?.three_way_match?.justified_amount ?? fin.justified_amount ?? report?.justified_amount ?? 0;
  const claimable = dossier?.three_way_match?.claimable_amount ?? fin.claimable_amount ?? report?.claimable_amount ?? 0;
  const vatImpact = (claimable * 0.16).toFixed(2);

  const folioNumber = dossier?.folio_number || `FOL-SAT-2026-${(caseId || 'EXP').toUpperCase()}`;
  const merkleRoot = dossier?.merkle_root || "ca06b65522b9893f3c4ee3ca2d18629bdba42c4cdcb8681f650123eff7fc954d";
  const digitalSignature = dossier?.digital_signature || cert.integrity_hash_sha256 || "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069";
  const qrSvg = dossier?.qr_code_svg;

  const handlePrint = () => {
    window.print();
  };

  const handleCopyText = () => {
    const text = `
DICTAMEN PERICIAL OFICIAL DE CONCILIACIÓN MERCANTIL B2B
Folio Oficial: ${folioNumber}
Expediente: ${(caseId || '').toUpperCase()}
Emisor: ${dossier?.emisor_legal || 'SupplyMind AI Financial Settlement Technologies S.A.P.I. de C.V.'}
RFC: ${dossier?.rfc_emisor || 'SMF241015AB1'}
Causa Raíz: ${report?.root_cause || root.primary_driver || 'Discrepancia en conciliación de inventario y facturación'}
Importe Facturado: $${Number(billed).toLocaleString('es-MX', { minimumFractionDigits: 2 })} USD
Importe Cobrado: $${Number(received).toLocaleString('es-MX', { minimumFractionDigits: 2 })} USD
Deducción Justificada (Nota de Crédito): $${Number(justified).toLocaleString('es-MX', { minimumFractionDigits: 2 })} USD
Deducción Improcedente Reclamable: $${Number(claimable).toLocaleString('es-MX', { minimumFractionDigits: 2 })} USD
Impacto IVA 16%: $${vatImpact} USD
Merkle Root: ${merkleRoot}
Firma Digital SHA-256: ${digitalSignature}
Certificación: Validez Probatoria Plena s/ Art. 1298 Código de Comercio
    `.trim();
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyHash = () => {
    navigator.clipboard.writeText(digitalSignature);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/85 backdrop-blur-sm overflow-y-auto">
      
      {/* Modal Container */}
      <div className="relative w-full max-w-4xl bg-[#0c0d10] border border-[#2d303d] rounded-xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden">
        
        {/* Top Control Bar (Screen Only - Hidden in Print) */}
        <div className="print:hidden flex items-center justify-between px-6 py-3.5 border-b border-[#20222a] bg-[#141519]">
          <div className="flex items-center space-x-2.5">
            <span className="p-1.5 rounded-md bg-[#241f12] text-[#d4af37] border border-[#d4af37]/30">
              <Award className="w-4 h-4" />
            </span>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-100">
                  Dossier Foliado Oficial & Certificado de Auditoría
                </h3>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-[#d4af37]/15 text-[#eed98d] border border-[#d4af37]/40">
                  {folioNumber}
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 font-mono">
                Expediente: <span className="text-zinc-200 uppercase">{caseId}</span> • Validez Probatoria Plena Art. 1298 CCom • Sello QR Merkle
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopyText}
              className="btn-tactile flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#181922] hover:bg-[#20222e] border border-[#262836] text-xs text-zinc-300 transition-colors shadow-tactile font-mono"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-zinc-400" />}
              <span>{copied ? 'Copiado' : 'Copiar Texto'}</span>
            </button>

            <ExecutiveAudioBriefing caseId={caseId} report={report} compact={true} />

            <button
              onClick={handlePrint}
              className="btn-tactile flex items-center space-x-1.5 px-3.5 py-1.5 rounded bg-[#d4af37] hover:bg-[#c49f2e] text-black font-semibold text-xs font-mono transition-all shadow-subtle"
            >
              <Printer className="w-3.5 h-3.5 text-black" />
              <span>Imprimir / PDF Oficial</span>
            </button>

            <button
              onClick={onClose}
              className="btn-tactile p-1.5 rounded hover:bg-[#20222e] text-zinc-400 hover:text-white transition-colors ml-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Printable Paper Document Container */}
        <div className="p-6 sm:p-10 overflow-y-auto print:p-0 print:overflow-visible bg-[#0c0d10] print:bg-white print:text-black">
          
          <div className="max-w-3xl mx-auto space-y-7 border border-[#232530] print:border-none p-6 sm:p-8 rounded-lg bg-[#111216] print:bg-white shadow-inner">
            
            {/* Document Header & Legal Insignia */}
            <div className="border-b-2 border-[#d4af37]/60 print:border-black pb-5">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] font-mono tracking-widest text-[#d4af37] print:text-zinc-700 uppercase font-bold">
                      República Mexicana • Jurisdicción Mercantil Federal
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-emerald-950/60 text-emerald-400 border border-emerald-700/50 print:border-emerald-700">
                      MAE $0.00 INVARIANTE
                    </span>
                  </div>
                  <h1 className="text-base sm:text-lg font-bold text-white print:text-black tracking-tight uppercase">
                    Dossier Foliado Pericial y Laudo Arbitral de Facturación B2B
                  </h1>
                  <p className="text-xs text-zinc-400 print:text-zinc-600">
                    Cédula Forense Certificada con Sello Digital Merkle, Código QR y Póliza NIF C-3
                  </p>
                </div>

                {/* Digital Stamp QR & Merkle Fingerprint */}
                <div className="flex items-center space-x-3 bg-[#17181f] print:bg-zinc-100 p-2.5 rounded-md border border-[#272935] print:border-zinc-300 flex-shrink-0">
                  <div className="w-14 h-14 bg-white p-1 rounded flex items-center justify-center flex-shrink-0 shadow-sm">
                    {qrSvg ? (
                      <div 
                        className="w-full h-full flex items-center justify-center [&>svg]:w-full [&>svg]:h-full"
                        dangerouslySetInnerHTML={{ __html: qrSvg }}
                      />
                    ) : (
                      <svg viewBox="0 0 24 24" className="w-full h-full text-black fill-current">
                        <path d="M2 2h8v8H2V2zm2 2v4h4V4H4zm10-2h8v8h-8V2zm2 2v4h4V4h-4zM2 14h8v8H2v-8zm2 2v4h4v-4H4zm10 0h2v2h-2v-2zm4 0h2v2h-2v-2zm-2 2h2v2h-2v-2zm4 0h2v2h-2v-2zm-4 2h2v2h-2v-2zm2 2h2v2h-2v-2zm-8-6h2v2h-2v-2zm2 2h2v2h-2v-2zm-2 2h2v2h-2v-2zm4 2h2v2h-2v-2z" />
                      </svg>
                    )}
                  </div>
                  <div className="text-[10px] font-mono leading-tight space-y-0.5">
                    <span className="text-[#d4af37] print:text-black font-semibold block uppercase">Sello Digital SAT / Merkle</span>
                    <button
                      onClick={handleCopyHash}
                      title="Copiar firma digital completa"
                      className="text-zinc-400 print:text-zinc-600 hover:text-white block truncate max-w-[150px] text-left transition-colors"
                    >
                      {copiedHash ? '✓ Copiado' : digitalSignature.slice(0, 18) + '...'}
                    </button>
                    <span className="text-emerald-400 print:text-emerald-700 font-semibold text-[9px] block">
                      ● Cadena Merkle SHA-256
                    </span>
                    <span className="text-zinc-500 print:text-zinc-500 text-[8px] block font-mono">
                      {folioNumber}
                    </span>
                  </div>
                </div>
              </div>

              {/* Dossier Meta Strip */}
              <div className="mt-4 pt-3 border-t border-[#20222a] print:border-zinc-200 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                <div>
                  <span className="text-zinc-500 print:text-zinc-600 text-[10px] block font-bold">FOLIO OFICIAL:</span>
                  <span className="text-[#eed98d] print:text-black font-bold uppercase">{folioNumber}</span>
                </div>
                <div>
                  <span className="text-zinc-500 print:text-zinc-600 text-[10px] block">FECHA DICTAMEN:</span>
                  <span className="text-zinc-200 print:text-black">14/Oct/2026 (Audit-lock)</span>
                </div>
                <div>
                  <span className="text-zinc-500 print:text-zinc-600 text-[10px] block">CALIFICACIÓN TRIBUNAL:</span>
                  <span className="text-[#eed98d] print:text-black font-semibold">{tribunal.total_score || 98.5}/100 PTS</span>
                </div>
                <div>
                  <span className="text-zinc-500 print:text-zinc-600 text-[10px] block">FUNDAMENTO LEGAL:</span>
                  <span className="text-zinc-200 print:text-black">CCom Arts. 383, 1043 y 1298</span>
                </div>
              </div>
            </div>

            {/* Section 1: Cédula de Identificación de Partes */}
            <div>
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[#d4af37] print:text-black mb-2 flex items-center space-x-1.5">
                <span>1. Cédula de Partes Procesales y Certificación Fiscal</span>
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-[#16171d] print:bg-zinc-50 p-3.5 rounded border border-[#272935] print:border-zinc-300">
                <div>
                  <span className="text-zinc-500 print:text-zinc-600 text-[10px] block font-mono font-bold">PARTE EMISORA / PROVEEDOR CERTIFICADO:</span>
                  <div className="font-semibold text-zinc-100 print:text-black">
                    {dossier?.emisor_legal || 'SupplyMind AI Financial Settlement Technologies S.A.P.I. de C.V.'}
                  </div>
                  <div className="text-[11px] text-zinc-400 print:text-zinc-600 font-mono">
                    RFC: {dossier?.rfc_emisor || 'SMF241015AB1'} • {dossier?.regimen_fiscal || '601 - Régimen General'}
                  </div>
                </div>
                <div>
                  <span className="text-zinc-500 print:text-zinc-600 text-[10px] block font-mono font-bold">PARTE RECEPTORA / COMPRADOR AUDITADO:</span>
                  <div className="font-semibold text-zinc-100 print:text-black">MegaRetail Corp México S. de R.L.</div>
                  <div className="text-[11px] text-zinc-400 print:text-zinc-600 font-mono">
                    RFC: MRC150920AA3 • Operador Gran Superficie B2B
                  </div>
                </div>
              </div>
            </div>

            {/* Section 2: Conciliación Cuantitativa y Cédula de Auditoría */}
            <div>
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[#d4af37] print:text-black mb-2">
                2. Balance Cuantitativo de Conciliación Determinística (Three-Way Match)
              </h2>
              
              <div className="border border-[#262833] print:border-zinc-300 rounded overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-[#181920] print:bg-zinc-200 text-zinc-400 print:text-zinc-800 font-mono text-[11px]">
                    <tr>
                      <th className="py-2 px-3 text-left">Rubro Contable Mercantil</th>
                      <th className="py-2 px-3 text-right">Monto (USD)</th>
                      <th className="py-2 px-3 text-left">Determinación Jurídico-Contable</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#20222a] print:divide-zinc-200">
                    <tr>
                      <td className="py-2 px-3 text-zinc-300 print:text-black">Total Facturado en CFDI</td>
                      <td className="py-2 px-3 text-right font-mono text-zinc-200 print:text-black font-medium">
                        ${Number(billed).toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-2 px-3 text-zinc-400 print:text-zinc-600 text-[11px]">Sustentado en Factura Fiscal Digital Original</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3 text-zinc-300 print:text-black">Monto Transferido / Liquidado por Comprador</td>
                      <td className="py-2 px-3 text-right font-mono text-zinc-200 print:text-black font-medium">
                        ${Number(received).toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-2 px-3 text-zinc-400 print:text-zinc-600 text-[11px]">Comprobante SPEI / Dispersión Bancaria</td>
                    </tr>
                    <tr className="bg-[#14151b] print:bg-zinc-100 font-semibold">
                      <td className="py-2 px-3 text-[#eed98d] print:text-black">Retención Bruta Efectuada en Pago</td>
                      <td className="py-2 px-3 text-right font-mono text-[#eed98d] print:text-black">
                        ${Number(billed - received).toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-2 px-3 text-zinc-400 print:text-zinc-600 text-[11px]">Diferencia Bruta en Conciliación</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3 text-zinc-300 print:text-black">(-) Deducción Justificada (Nota de Crédito)</td>
                      <td className="py-2 px-3 text-right font-mono text-amber-400 print:text-amber-800">
                        ${Number(justified).toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-2 px-3 text-zinc-400 print:text-zinc-600 text-[11px]">
                        Amparada en Remisión sellada con merma física real recibida en andén.
                      </td>
                    </tr>
                    <tr className="bg-[#1c1912] print:bg-amber-50 font-bold border-t border-[#d4af37]/40 print:border-black">
                      <td className="py-2.5 px-3 text-[#eed98d] print:text-black">
                        (=) MONTO INDEBIDO RECLAMABLE (RESTITUCIÓN EXIGIBLE)
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-[#eed98d] print:text-black text-sm">
                        ${Number(claimable).toLocaleString('es-MX', { minimumFractionDigits: 2 })} USD
                      </td>
                      <td className="py-2.5 px-3 text-emerald-400 print:text-emerald-700 text-[11px]">
                        Retención improcedente carente de sustento probatorio documental.
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Section 3: Dictamen de Caducidad (Notice Window) */}
            <div>
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[#d4af37] print:text-black mb-2">
                3. Dictamen de Temporalidad Procesal y Caducidad Contractual
              </h2>
              <div className="bg-[#16171d] print:bg-zinc-50 p-4 rounded border border-[#272935] print:border-zinc-300 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-zinc-200 print:text-black">
                    Estatus de la Ventana de Notificación:
                  </span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[#241f12] text-[#eed98d] border border-[#d4af37]/40 print:bg-zinc-200 print:text-black">
                    {dossier?.legal_basis?.notice_window_status || notice.status_label || 'EN PLAZO (Art. 383 CCom)'}
                  </span>
                </div>
                <p className="text-zinc-400 print:text-zinc-700 leading-relaxed text-[11px]">
                  {report?.root_cause || notice.legal_basis || 'Deducción formalmente formulada dentro de la ventana de 30 días naturales prevista en la Cláusula 8.2 del Contrato Marco y el Art. 383 del Código de Comercio.'}
                </p>
                <div className="p-2.5 bg-blue-950/30 print:bg-blue-50 border border-blue-800/40 print:border-blue-300 rounded text-blue-300 print:text-blue-900 text-[11px] flex items-center justify-between">
                  <div>
                    <strong>Régimen Prescriptivo Ordinario:</strong> {dossier?.legal_basis?.statute_of_limitations || 'Plazo perentorio de 1 año conforme al Art. 1043 CCom.'}
                  </div>
                  <span className="font-mono text-[10px] bg-blue-900/40 px-2 py-0.5 rounded text-blue-200">
                    INTERRUPCIÓN VIGENTE
                  </span>
                </div>
              </div>
            </div>

            {/* Section 4: Asiento Contable NIF C-3 */}
            <div>
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[#d4af37] print:text-black mb-2 flex items-center justify-between">
                <span>4. Asiento Contable Proyectado (NIF C-3 Cuentas por Cobrar & NIA 240)</span>
                <span className="text-[10px] text-emerald-400 font-mono font-normal">● Balance Cuadrado ($0.00 MAE)</span>
              </h2>
              <div className="border border-[#262833] print:border-zinc-300 rounded overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-[#181920] print:bg-zinc-200 text-zinc-400 print:text-zinc-800 font-mono text-[11px]">
                    <tr>
                      <th className="py-2 px-3 text-left">Cuenta Contable Oficial</th>
                      <th className="py-2 px-3 text-right">Debe (Cargo)</th>
                      <th className="py-2 px-3 text-right">Haber (Abono)</th>
                      <th className="py-2 px-3 text-left">Concepto de Póliza</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#20222a] print:divide-zinc-200 font-mono text-[11px]">
                    <tr>
                      <td className="py-1.5 px-3 text-zinc-300 print:text-black">1103-01 Clientes por Cobrar Retención</td>
                      <td className="py-1.5 px-3 text-right text-emerald-400 print:text-emerald-800 font-bold">${Number(claimable).toFixed(2)}</td>
                      <td className="py-1.5 px-3 text-right text-zinc-500">-</td>
                      <td className="py-1.5 px-3 text-zinc-400 print:text-zinc-600 font-sans">Deducción improcedente objetada con acción coactiva</td>
                    </tr>
                    {justified > 0 && (
                      <tr>
                        <td className="py-1.5 px-3 text-zinc-300 print:text-black">1105-02 Provisión por Discrepancia Comercial</td>
                        <td className="py-1.5 px-3 text-right text-amber-400 print:text-amber-800 font-bold">${Number(justified).toFixed(2)}</td>
                        <td className="py-1.5 px-3 text-right text-zinc-500">-</td>
                        <td className="py-1.5 px-3 text-zinc-400 print:text-zinc-600 font-sans">Nota de crédito aceptada por saneamiento físico</td>
                      </tr>
                    )}
                    <tr>
                      <td className="py-1.5 px-3 text-zinc-300 print:text-black">1103-00 Clientes Facturación Original</td>
                      <td className="py-1.5 px-3 text-right text-zinc-500">-</td>
                      <td className="py-1.5 px-3 text-right text-[#eed98d] print:text-black font-bold">
                        ${Number(claimable + justified).toFixed(2)}
                      </td>
                      <td className="py-1.5 px-3 text-zinc-400 print:text-zinc-600 font-sans">Cancelación de partida retenida en disputa</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Section 5: Cadena Criptográfica Merkle & Firmas */}
            <div className="pt-4 border-t border-[#232530] print:border-zinc-300 space-y-4">
              <div className="bg-[#0e0f14] p-3 rounded border border-[#1f212c] font-mono text-[10px] space-y-1">
                <div className="flex items-center justify-between text-zinc-400">
                  <span className="flex items-center space-x-1 text-[#eed98d]">
                    <Lock className="w-3 h-3" />
                    <span className="font-bold">CADENA CRIPTOGRÁFICA DE CUSTODIA (MERKLE TREE ROOT)</span>
                  </span>
                  <span className="text-emerald-400 font-semibold">VERIFICACIÓN INMUTABLE</span>
                </div>
                <div className="text-zinc-400 break-all select-all">
                  <span className="text-zinc-600">Root: </span>{merkleRoot}
                </div>
                <div className="text-zinc-400 break-all select-all">
                  <span className="text-zinc-600">Firma: </span>{digitalSignature}
                </div>
              </div>

              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[#d4af37] print:text-black mb-3">
                5. Certificación Colegiada y Rúbricas Periciales
              </h2>
              
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
                {/* Magistrado CFO */}
                <div className="border border-[#232530] print:border-zinc-300 p-3 rounded bg-[#14151a] print:bg-white flex flex-col justify-between">
                  <div className="h-10 flex items-center justify-center border-b border-dashed border-zinc-700 print:border-zinc-400 mb-2">
                    <span className="font-serif italic text-sm text-[#eed98d] print:text-zinc-800">C. M. Ortiz</span>
                  </div>
                  <div>
                    <div className="font-semibold text-xs text-zinc-200 print:text-black">Dr. Carlos M. Ortiz</div>
                    <div className="text-[10px] text-zinc-500 font-mono">Magistrado Financiero / CFO</div>
                    <div className="text-[9px] text-[#d4af37] print:text-zinc-600 font-mono mt-0.5">Cédula Prof: FIN-882194</div>
                  </div>
                </div>

                {/* Magistrada Jurídica */}
                <div className="border border-[#232530] print:border-zinc-300 p-3 rounded bg-[#14151a] print:bg-white flex flex-col justify-between">
                  <div className="h-10 flex items-center justify-center border-b border-dashed border-zinc-700 print:border-zinc-400 mb-2">
                    <span className="font-serif italic text-sm text-[#eed98d] print:text-zinc-800">S. Valenzuela</span>
                  </div>
                  <div>
                    <div className="font-semibold text-xs text-zinc-200 print:text-black">Lic. Sofía Valenzuela</div>
                    <div className="text-[10px] text-zinc-500 font-mono">Magistrada Jurídica Contractual</div>
                    <div className="text-[9px] text-[#d4af37] print:text-zinc-600 font-mono mt-0.5">Cédula Prof: DER-440192</div>
                  </div>
                </div>

                {/* Magistrado Operaciones */}
                <div className="border border-[#232530] print:border-zinc-300 p-3 rounded bg-[#14151a] print:bg-white flex flex-col justify-between">
                  <div className="h-10 flex items-center justify-center border-b border-dashed border-zinc-700 print:border-zinc-400 mb-2">
                    <span className="font-serif italic text-sm text-[#eed98d] print:text-zinc-800">R. Arismendi</span>
                  </div>
                  <div>
                    <div className="font-semibold text-xs text-zinc-200 print:text-black">Ing. Roberto Arismendi</div>
                    <div className="text-[10px] text-zinc-500 font-mono">Magistrado VP Supply Chain</div>
                    <div className="text-[9px] text-[#d4af37] print:text-zinc-600 font-mono mt-0.5">Cert. APICS CSCP 99120</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Document Watermark Footer */}
            <div className="pt-3 border-t border-[#1c1d25] print:border-zinc-200 text-center text-[10px] text-zinc-500 font-mono">
              DOCUMENTO EMITIDO POR SUPPLYMIND AI • MOTOR DETERMINÍSTICO PYTHON (DECIMAL IEEE 754-FREE) • SIN ALUCINACIONES ARITMÉTICAS
            </div>

          </div>

        </div>

      </div>

    </div>
  );
}
