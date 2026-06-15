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
 * Stream a chat question to the RAG chain.
 * @param {string} question
 * @param {string|null} domain
 * @param {string|null} sessionId
 * @param {function} onChunk - Callback when a new text chunk arrives
 * @param {function} onCitations - Callback when citations arrive
 */
export async function streamChatMessage(question, domain = null, sessionId = null, onChunk, onCitations) {
  const body = { question, stream: true };
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

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    
    // Process full lines
    const lines = buffer.split("\n");
    // Keep the last incomplete line in the buffer
    buffer = lines.pop();

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const data = JSON.parse(line);
        if (data.type === "token") {
          onChunk(data.content);
        } else if (data.type === "citations") {
          onCitations(data.data);
        }
      } catch (e) {
        console.error("Failed to parse chunk", line, e);
      }
    }
  }
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

/**
 * Request a generated draft document.
 * Returns a blob which can be downloaded.
 */
export async function draftDocument(topic, domain) {
  const body = { topic };
  if (domain && domain !== "all") body.domain = domain;

  const response = await fetch(`${API_BASE}/draft/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    let detail = `Draft failed (${response.status})`;
    try {
      const err = await response.json();
      detail = err.detail || JSON.stringify(err);
    } catch { /* ignore */ }
    throw new Error(detail);
  }

  // Get filename from Content-Disposition header if possible
  let filename = "draft_report.docx";
  const disposition = response.headers.get("Content-Disposition");
  if (disposition && disposition.includes("filename=")) {
    filename = disposition.split("filename=")[1].replace(/"/g, "");
  } else if (response.headers.get("Content-Type") === "application/pdf") {
    filename = "draft_report.pdf";
  }

  const blob = await response.blob();
  return { blob, filename };
}
