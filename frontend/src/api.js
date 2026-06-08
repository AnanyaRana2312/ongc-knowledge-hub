// src/api.js
// Centralised API communication layer for the ONGC Knowledge Hub backend.

const API_BASE = "http://localhost:8000";

/**
 * Upload a document to a specific domain.
 * Domain is sent as a query parameter matching the backend DomainEnum values.
 * @param {File} file
 * @param {string} domain
 * @returns {Promise<object>}
 */
export async function ingestDocument(file, domain) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}/ingest/?domain=${encodeURIComponent(domain)}`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    let detail = `Upload failed (${response.status})`;
    try {
      const err = await response.json();
      detail = err.detail || JSON.stringify(err);
    } catch {/* ignore parse error */}
    throw new Error(detail);
  }
  return response.json();
}

/**
 * Send a chat question to the RAG chain.
 * @param {string} question
 * @param {string|null} domain  Pass null to trigger cross-domain search
 * @returns {Promise<{answer: string, citations: string[]}>}
 */
export async function sendChatMessage(question, domain = null, sessionId = null) {
  const body = { question };
  if (domain && domain !== "all") body.domain = domain;
  if (sessionId) body.session_id = sessionId;

  const response = await fetch(`${API_BASE}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `Chat request failed (${response.status})`);
  }
  return response.json();
}

/**
 * Fetch the list of all ingested documents.
 * The API returns a flat array of {source, domain} objects.
 * @returns {Promise<Array<{source: string, domain: string}>>}
 */
export async function fetchDocuments() {
  const response = await fetch(`${API_BASE}/documents/`);
  if (!response.ok) throw new Error("Could not fetch documents");
  const data = await response.json();
  // API returns a flat array, not {documents: [...]}
  return Array.isArray(data) ? data : (data.documents || []);
}

/**
 * Check API + Ollama health.
 * @returns {Promise<{status: string, ollama: string}>}
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error("API unreachable");
  return response.json();
}

/**
 * Delete a document from the vector store by its filename.
 * @param {string} filename
 * @returns {Promise<void>}
 */
export async function deleteDocument(filename) {
  const response = await fetch(`${API_BASE}/documents/${encodeURIComponent(filename)}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    let detail = `Delete failed (${response.status})`;
    try {
      const err = await response.json();
      detail = err.detail || JSON.stringify(err);
    } catch {/* ignore parse error */}
    throw new Error(detail);
  }
}

/**
 * Fetch all chat sessions.
 */
export async function getSessions() {
  const response = await fetch(`${API_BASE}/sessions/`);
  if (!response.ok) throw new Error("Could not fetch sessions");
  return response.json();
}

/**
 * Fetch messages for a specific session.
 */
export async function getSessionMessages(sessionId) {
  const response = await fetch(`${API_BASE}/sessions/${encodeURIComponent(sessionId)}`);
  if (!response.ok) throw new Error("Could not fetch session messages");
  return response.json();
}

/**
 * Create a new chat session.
 */
export async function createSession(title) {
  const response = await fetch(`${API_BASE}/sessions/?title=${encodeURIComponent(title)}`, {
    method: "POST"
  });
  if (!response.ok) throw new Error("Could not create session");
  return response.json();
}
