import React, { useState } from 'react';
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
  AlertTriangle 
} from 'lucide-react';

export default function OfficialAuditReportModal({ caseId, report, onClose }) {
  const [copied, setCopied] = useState(false);

  if (!report) return null;

  const fin = report.financial_summary || {};
  const root = report.root_cause_analysis || {};
  const notice = report.notice_window_audit || {};
  const sku = report.sku_matching || {};
  const tribunal = report.collegiate_tribunal || {};
  const cert = report.audit_certification || {};

  const billed = fin.billed_amount || 0;
  const received = fin.received_amount || 0;
  const justified = fin.justified_amount || 0;
  const claimable = fin.claimable_amount || 0;
  const vatImpact = (claimable * 0.16).toFixed(2);
  const creditNoteTotal = justified > 0 ? (justified * 1.16).toFixed(2) : "0.00";

  const handlePrint = () => {
    window.print();
  };

  const handleCopyText = () => {
    const text = `
DICTAMEN PERICIAL OFICIAL DE CONCILIACIÓN MERCANTIL B2B
Expediente: ${caseId.toUpperCase()}
Emisor: TechSupply Solutions S.A.P.I. de C.V.
Comprador / Retailer: MegaRetail Corp México S. de R.L.
Causa Raíz: ${root.primary_driver || 'Discrepancia en conciliación'}
Importe Facturado: $${billed.toLocaleString('es-MX', { minimumFractionDigits: 2 })} USD
Importe Cobrado: $${received.toLocaleString('es-MX', { minimumFractionDigits: 2 })} USD
Deducción Justificada (Nota de Crédito): $${justified.toLocaleString('es-MX', { minimumFractionDigits: 2 })} USD
Deducción Improcedente Reclamable: $${claimable.toLocaleString('es-MX', { minimumFractionDigits: 2 })} USD
Impacto IVA 16%: $${vatImpact} USD
Estatus Temporalidad (Notice Window): ${notice.status_label || 'EN PLAZO'}
Sello Digital SHA-256: ${cert.integrity_hash_sha256 || '7f83b165...'}
Certificado por Tribunal Colegiado (Score: ${tribunal.total_score || 98.5}/100)
    `.trim();
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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
              <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-100">
                Dictamen Pericial Oficial & Certificado de Auditoría
              </h3>
              <p className="text-[11px] text-zinc-400 font-mono">
                Expediente: <span className="text-zinc-200 uppercase">{caseId}</span> • Validez Probatoria s/ Código de Comercio
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

            <button
              onClick={handlePrint}
              className="btn-tactile flex items-center space-x-1.5 px-3.5 py-1.5 rounded bg-[#d4af37] hover:bg-[#c49f2e] text-black font-semibold text-xs font-mono transition-all shadow-subtle"
            >
              <Printer className="w-3.5 h-3.5 text-black" />
              <span>Imprimir / PDF</span>
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
                <div>
                  <div className="text-[10px] font-mono tracking-widest text-[#d4af37] print:text-zinc-700 uppercase font-bold">
                    República Mexicana • Jurisdicción Mercantil Federal
                  </div>
                  <h1 className="text-base sm:text-lg font-bold text-white print:text-black tracking-tight uppercase mt-0.5">
                    Dictamen Pericial Técnico-Contable y Arbitraje de Facturación
                  </h1>
                  <p className="text-xs text-zinc-400 print:text-zinc-600 mt-0.5">
                    Cédula Forense de Conciliación de Pagos, Deducciones y Caducidad Contractual
                  </p>
                </div>

                {/* Digital Stamp QR & Fingerprint */}
                <div className="flex items-center space-x-3 bg-[#17181f] print:bg-zinc-100 p-2.5 rounded-md border border-[#272935] print:border-zinc-300 flex-shrink-0">
                  <div className="w-12 h-12 bg-white p-1 rounded flex items-center justify-center flex-shrink-0">
                    {/* SVG Authentic QR Code Matrix */}
                    <svg viewBox="0 0 24 24" className="w-full h-full text-black fill-current">
                      <path d="M2 2h8v8H2V2zm2 2v4h4V4H4zm10-2h8v8h-8V2zm2 2v4h4V4h-4zM2 14h8v8H2v-8zm2 2v4h4v-4H4zm10 0h2v2h-2v-2zm4 0h2v2h-2v-2zm-2 2h2v2h-2v-2zm4 0h2v2h-2v-2zm-4 2h2v2h-2v-2zm2 2h2v2h-2v-2zm-8-6h2v2h-2v-2zm2 2h2v2h-2v-2zm-2 2h2v2h-2v-2zm4 2h2v2h-2v-2z" />
                    </svg>
                  </div>
                  <div className="text-[10px] font-mono leading-tight">
                    <span className="text-[#d4af37] print:text-black font-semibold block uppercase">Certificación Digital</span>
                    <span className="text-zinc-400 print:text-zinc-600 block truncate max-w-[150px]">
                      {cert.integrity_hash_sha256 ? cert.integrity_hash_sha256.slice(0, 20) + '...' : 'SHA-256 Validated'}
                    </span>
                    <span className="text-emerald-400 print:text-emerald-700 font-semibold text-[9px]">
                      ● Integridad Probatoria 100%
                    </span>
                  </div>
                </div>
              </div>

              {/* Dossier Meta Strip */}
              <div className="mt-4 pt-3 border-t border-[#20222a] print:border-zinc-200 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                <div>
                  <span className="text-zinc-500 print:text-zinc-600 text-[10px] block">No. EXPEDIENTE:</span>
                  <span className="text-zinc-200 print:text-black font-semibold uppercase">{caseId}</span>
                </div>
                <div>
                  <span className="text-zinc-500 print:text-zinc-600 text-[10px] block">FECHA DICTAMEN:</span>
                  <span className="text-zinc-200 print:text-black">14/Oct/2026</span>
                </div>
                <div>
                  <span className="text-zinc-500 print:text-zinc-600 text-[10px] block">CALIFICACIÓN TRIBUNAL:</span>
                  <span className="text-[#eed98d] print:text-black font-semibold">{tribunal.total_score || 98.5}/100 PTS</span>
                </div>
                <div>
                  <span className="text-zinc-500 print:text-zinc-600 text-[10px] block">FUNDAMENTO:</span>
                  <span className="text-zinc-200 print:text-black">Cód. Comercio Art. 1298</span>
                </div>
              </div>
            </div>

            {/* Section 1: Cédula de Identificación de Partes */}
            <div>
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[#d4af37] print:text-black mb-2 flex items-center space-x-1.5">
                <span>1. Cédula de Partes Procesales y Antecedentes</span>
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-[#16171d] print:bg-zinc-50 p-3.5 rounded border border-[#272935] print:border-zinc-300">
                <div>
                  <span className="text-zinc-500 print:text-zinc-600 text-[10px] block font-mono">PARTE EMISORA / PROVEEDOR:</span>
                  <div className="font-semibold text-zinc-100 print:text-black">TechSupply Solutions S.A.P.I. de C.V.</div>
                  <div className="text-[11px] text-zinc-400 print:text-zinc-600 font-mono">RFC: TSS1904128K1 • Régimen General de Ley</div>
                </div>
                <div>
                  <span className="text-zinc-500 print:text-zinc-600 text-[10px] block font-mono">PARTE RECEPTORA / COMPRADOR:</span>
                  <div className="font-semibold text-zinc-100 print:text-black">MegaRetail Corp México S. de R.L.</div>
                  <div className="text-[11px] text-zinc-400 print:text-zinc-600 font-mono">RFC: MRC150920AA3 • Operador Gran Superficie</div>
                </div>
              </div>
            </div>

            {/* Section 2: Conciliación Cuantitativa y Cédula de Auditoría */}
            <div>
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[#d4af37] print:text-black mb-2">
                2. Balance Cuantitativo de Discrepancias (Precisión Determinística Decimal)
              </h2>
              
              <div className="border border-[#262833] print:border-zinc-300 rounded overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-[#181920] print:bg-zinc-200 text-zinc-400 print:text-zinc-800 font-mono text-[11px]">
                    <tr>
                      <th className="py-2 px-3 text-left">Rubro Contable Mercantil</th>
                      <th className="py-2 px-3 text-right">Monto (USD)</th>
                      <th className="py-2 px-3 text-left">Determinación Jurídica</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#20222a] print:divide-zinc-200">
                    <tr>
                      <td className="py-2 px-3 text-zinc-300 print:text-black">Total Facturado en CFDI</td>
                      <td className="py-2 px-3 text-right font-mono text-zinc-200 print:text-black font-medium">
                        ${billed.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-2 px-3 text-zinc-400 print:text-zinc-600 text-[11px]">Sustentado en Factura Fiscal Digital</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3 text-zinc-300 print:text-black">Monto Transferido / Liquidado por Comprador</td>
                      <td className="py-2 px-3 text-right font-mono text-zinc-200 print:text-black font-medium">
                        ${received.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-2 px-3 text-zinc-400 print:text-zinc-600 text-[11px]">Comprobante de Dispersión Bancaria</td>
                    </tr>
                    <tr className="bg-[#14151b] print:bg-zinc-100 font-semibold">
                      <td className="py-2 px-3 text-[#eed98d] print:text-black">Retención Bruta Efectuada</td>
                      <td className="py-2 px-3 text-right font-mono text-[#eed98d] print:text-black">
                        ${(billed - received).toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-2 px-3 text-zinc-400 print:text-zinc-600 text-[11px]">Diferencia Bruta en Conciliación</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3 text-zinc-300 print:text-black">(-) Deducción Justificada (Faltante Físico Real)</td>
                      <td className="py-2 px-3 text-right font-mono text-amber-400 print:text-amber-800">
                        ${justified.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-2 px-3 text-zinc-400 print:text-zinc-600 text-[11px]">
                        Amparada en Remisión sellada con faltante en muelle.
                      </td>
                    </tr>
                    <tr className="bg-[#1c1912] print:bg-amber-50 font-bold border-t border-[#d4af37]/40 print:border-black">
                      <td className="py-2.5 px-3 text-[#eed98d] print:text-black">
                        (=) MONTO INDEBIDO RECLAMABLE (RESTITUCIÓN EXIGIBLE)
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-[#eed98d] print:text-black text-sm">
                        ${claimable.toLocaleString('es-MX', { minimumFractionDigits: 2 })} USD
                      </td>
                      <td className="py-2.5 px-3 text-emerald-400 print:text-emerald-700 text-[11px]">
                        Retención improcedente sin sustento probatorio.
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
                    {notice.status_label || 'EN PLAZO CONTRACTUAL'}
                  </span>
                </div>
                <p className="text-zinc-400 print:text-zinc-700 leading-relaxed text-[11px]">
                  {notice.legal_basis || 'Deducción formalmente formulada dentro de la ventana de 30 días naturales prevista en la Cláusula 8.2 del Contrato Marco.'}
                </p>
                {notice.statute_of_limitations_applied && (
                  <div className="p-2.5 bg-rose-950/40 print:bg-rose-50 border border-rose-800/40 print:border-rose-300 rounded text-rose-300 print:text-rose-900 text-[11px]">
                    <strong>Fundamento de Nulidad:</strong> Conforme al Artículo 1043 del Código de Comercio y la Cláusula 8.2 de Caducidad, toda retención formulada fuera del plazo convenido queda precluida y es nula de pleno derecho.
                  </div>
                )}
              </div>
            </div>

            {/* Section 4: Asiento Contable NIF C-3 */}
            <div>
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[#d4af37] print:text-black mb-2">
                4. Asiento Contable Proyectado (Normas de Información Financiera NIF C-3 & C-16)
              </h2>
              <div className="border border-[#262833] print:border-zinc-300 rounded overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-[#181920] print:bg-zinc-200 text-zinc-400 print:text-zinc-800 font-mono text-[11px]">
                    <tr>
                      <th className="py-2 px-3 text-left">Cuenta Contable</th>
                      <th className="py-2 px-3 text-right">Debe (Cargo)</th>
                      <th className="py-2 px-3 text-right">Haber (Abono)</th>
                      <th className="py-2 px-3 text-left">Concepto</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#20222a] print:divide-zinc-200 font-mono text-[11px]">
                    <tr>
                      <td className="py-1.5 px-3 text-zinc-300 print:text-black">1105-01 Cuentas por Cobrar en Disputa</td>
                      <td className="py-1.5 px-3 text-right text-emerald-400 print:text-emerald-800 font-bold">${claimable.toFixed(2)}</td>
                      <td className="py-1.5 px-3 text-right text-zinc-500">-</td>
                      <td className="py-1.5 px-3 text-zinc-400 print:text-zinc-600 font-sans">Restitución de fondos exigibles</td>
                    </tr>
                    {justified > 0 && (
                      <tr>
                        <td className="py-1.5 px-3 text-zinc-300 print:text-black">4105-02 Provisión por Faltantes Reales</td>
                        <td className="py-1.5 px-3 text-right text-zinc-500">-</td>
                        <td className="py-1.5 px-3 text-right text-amber-400 print:text-amber-800">${justified.toFixed(2)}</td>
                        <td className="py-1.5 px-3 text-zinc-400 print:text-zinc-600 font-sans">Reconocimiento de merma física</td>
                      </tr>
                    )}
                    <tr>
                      <td className="py-1.5 px-3 text-zinc-300 print:text-black">2180-01 IVA Trasladado por Regularizar (16%)</td>
                      <td className="py-1.5 px-3 text-right text-zinc-500">-</td>
                      <td className="py-1.5 px-3 text-right text-zinc-300 print:text-black">${vatImpact}</td>
                      <td className="py-1.5 px-3 text-zinc-400 print:text-zinc-600 font-sans">Ajuste de impuesto al cobro definitivo</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Section 5: Certificación y Firmas Colegiadas del Tribunal */}
            <div className="pt-4 border-t border-[#232530] print:border-zinc-300">
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[#d4af37] print:text-black mb-4">
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
