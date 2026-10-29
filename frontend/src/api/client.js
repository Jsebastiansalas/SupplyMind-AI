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
};

