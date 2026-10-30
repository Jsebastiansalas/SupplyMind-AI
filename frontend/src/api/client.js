/**
 * frontend/src/api/client.js
 * Cliente HTTP para comunicarse con la API FastAPI de SupplyMind AI.
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const apiClient = {
  async getHealth() {
    const res = await fetch(`${BASE_URL}/health`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async getCases() {
    const res = await fetch(`${BASE_URL}/cases`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async getCaseDetails(caseId) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async analyzeCase(caseId, fastPath = true, useCache = true) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fast_path: fastPath, use_cache: useCache }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al analizar caso' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async getTribunalEvaluation(caseId) {
    const res = await fetch(`${BASE_URL}/tribunal/${caseId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async sendChatMessage(caseId, message, history = [], role = 'senior_analyst') {
    const res = await fetch(`${BASE_URL}/cases/${caseId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history, role }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async getClaimLetter(caseId) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}/claim-letter`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.text();
  },

  async getEmailDraft(caseId) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}/email-draft`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async simulateDispute(payload) {
    const res = await fetch(`${BASE_URL}/sandbox/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async getUnitEconomics() {
    const res = await fetch(`${BASE_URL}/telemetry/unit-economics`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async getBenchmarkReport() {
    const res = await fetch(`${BASE_URL}/telemetry/benchmark`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async runBenchmark() {
    const res = await fetch(`${BASE_URL}/telemetry/benchmark/run`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async runBatch(casesCount = 1000, workers = 8) {
    const res = await fetch(`${BASE_URL}/batch/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cases_count: casesCount, workers }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async getLatestBatch() {
    const res = await fetch(`${BASE_URL}/batch/latest`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async uploadCase(formData) {
    const res = await fetch(`${BASE_URL}/cases/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al subir caso' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async createGuidedCase(payload) {
    const res = await fetch(`${BASE_URL}/cases/create-guided`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al generar caso' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async deleteCase(caseId) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al eliminar caso' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  getDocumentUrl(caseId, filename) {
    return `${BASE_URL}/cases/${caseId}/documents/${filename}`;
  },

  async getPrecedentGraph() {
    const res = await fetch(`${BASE_URL}/precedents/graph`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async postSapDocument(caseId) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}/erp/sap/post-document`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async postNetSuiteJournal(caseId) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}/erp/netsuite/post-journal`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  // --- SPRINT 5.1 / 5.5: EDI B2B Nativo ---
  async getEdiSamples() {
    const res = await fetch(`${BASE_URL}/edi/samples`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async parseEdi(rawEdiContent) {
    const res = await fetch(`${BASE_URL}/edi/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_edi_content: rawEdiContent }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al decodificar paquete EDI' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async auditEdiAsn(payload) {
    const res = await fetch(`${BASE_URL}/edi/audit-asn`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al auditar ASN EDI 856' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async generateEdi824(payload) {
    const res = await fetch(`${BASE_URL}/edi/generate-824`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al generar EDI 824' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  // --- SPRINT 5.2 / 5.5: Estrado Dialéctico & Meta-Cognición ---
  async getCourtroomCareo(caseId) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}/adversarial-courtroom`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al obtener estrado dialéctico' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async getMctsSimulation(payload) {
    const res = await fetch(`${BASE_URL}/meta-cognition/mcts-simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async autoHardenCase(payload) {
    const res = await fetch(`${BASE_URL}/meta-cognition/auto-harden`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  // --- SPRINT 5.4: Radar DVI & Dossier Arbitral ICC ---
  async evaluateDvi(payload) {
    const res = await fetch(`${BASE_URL}/radar/dvi-evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async generateArbitrationDossier(payload) {
    const res = await fetch(`${BASE_URL}/radar/generate-arbitration-dossier`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al compilar dossier arbitral' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async getHighRiskDestinations() {
    const res = await fetch(`${BASE_URL}/radar/high-risk-destinations`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  // --- SPRINT 6.1 / 6.2: RPA Portales B2B & Visión Multimodal ---
  async getPortalCatalog() {
    const res = await fetch(`${BASE_URL}/portal/catalog`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async syncRetailerPortal(payload) {
    const res = await fetch(`${BASE_URL}/portal/sync-retailer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al sincronizar portal B2B' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async uploadPortalDispute(payload) {
    const res = await fetch(`${BASE_URL}/portal/upload-dispute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al cargar disputa en portal' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async inspectPalletVision(payload) {
    const res = await fetch(`${BASE_URL}/vision/inspect-pallet`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error en peritaje de visión' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async getVisionSamples() {
    const res = await fetch(`${BASE_URL}/vision/samples`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  // --- SPRINT 6.1 / 6.2 / 6.3: Careo Dialéctico B2B & Despacho a Portales ---
  async getDuelSession(caseId) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}/negotiation/duel`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async startDuel(caseId, payload = {}) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}/negotiation/duel/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al iniciar careo' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async advanceDuelStep(caseId) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}/negotiation/duel/step`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al avanzar careo' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async approveDuelSettlement(caseId, payload = {}) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}/negotiation/duel/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al aprobar finiquito' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async setDuelGovernance(caseId, payload = {}) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}/negotiation/duel/governance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al conmutar gobernanza' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async getDuelMinutes(caseId) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}/negotiation/duel/minutes`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async getDelegationMatrix() {
    const res = await fetch(`${BASE_URL}/negotiation/delegation-matrix`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async getCasePortalDossier(caseId, portalType = null) {
    const url = portalType 
      ? `${BASE_URL}/cases/${caseId}/portal/dossier?portal_type=${portalType}`
      : `${BASE_URL}/cases/${caseId}/portal/dossier`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async dispatchCaseToPortal(caseId, payload = {}) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}/portal/dispatch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Error al despachar caso a portal' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async getCasePortalReceipt(caseId) {
    const res = await fetch(`${BASE_URL}/cases/${caseId}/portal/receipt`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
};



