// src/components/Sidebar.jsx
import { useState, useEffect, useCallback } from "react";
import { ingestDocument, fetchDocuments, deleteDocument, getSessions, deleteSession, renameSession } from "../api";
import { INGEST_DOMAINS } from "../constants";

export default function Sidebar({ onUploadSuccess, activeSessionId, onSelectSession, refreshTrigger }) {
  const [domain, setDomain] = useState(INGEST_DOMAINS[0].value);
  const [uploadStatus, setUploadStatus] = useState(null); // null | {type, message}
  const [dragActive, setDragActive] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [sessions, setSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(true);

  const loadSessions = useCallback(async () => {
    try {
      const data = await getSessions();
      setSessions(data || []);
    } catch {
      setSessions([]);
    } finally {
      setLoadingSessions(false);
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    try {
      const data = await fetchDocuments();
      // fetchDocuments now returns a flat array directly
      setDocuments(Array.isArray(data) ? data : []);
    } catch {
      setDocuments([]);
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions, refreshTrigger]);

  const handleFile = async (file) => {
    if (!file) return;

    const allowed = [".pdf", ".docx", ".png", ".jpg", ".jpeg", ".tiff"];
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!allowed.includes(ext)) {
      setUploadStatus({ type: "error", message: `Unsupported file type: ${ext}` });
      return;
    }

    setUploadStatus({ type: "loading", message: `Uploading "${file.name}"…` });
    try {
      await ingestDocument(file, domain);
      setUploadStatus({ type: "success", message: `"${file.name}" is being processed in the background. It will appear here once finished.` });
      if (onUploadSuccess) onUploadSuccess();
      setTimeout(() => setUploadStatus(null), 6000);
    } catch (err) {
      setUploadStatus({ type: "error", message: err.message });
    }
  };

  const handleDelete = async (filename) => {
    const displayname = filename.split(/[/\\]/).pop();
    if (!window.confirm(`Are you sure you want to delete "${displayname}"? This will remove all its data from the knowledge base.`)) {
      return;
    }
    
    setUploadStatus({ type: "loading", message: `Deleting "${displayname}"…` });
    try {
      await deleteDocument(filename);
      setUploadStatus({ type: "success", message: `"${displayname}" deleted successfully!` });
      await loadDocuments();
      setTimeout(() => setUploadStatus(null), 4000);
    } catch (err) {
      setUploadStatus({ type: "error", message: err.message });
    }
  };

  const handleDeleteSession = async (e, sessionId) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this chat session? All its messages will be lost.")) {
      return;
    }
    try {
      await deleteSession(sessionId);
      if (activeSessionId === sessionId) {
        onSelectSession(null);
      }
      loadSessions();
    } catch (err) {
      alert(`Failed to delete session: ${err.message}`);
    }
  };

  const handleRenameSession = async (e, sessionId, currentTitle) => {
    e.stopPropagation();
    const newTitle = window.prompt("Enter new chat title:", currentTitle);
    if (!newTitle || !newTitle.trim()) return;
    try {
      await renameSession(sessionId, newTitle.trim());
      loadSessions();
    } catch (err) {
      alert(`Failed to rename session: ${err.message}`);
    }
  };

  const handleChange = (e) => handleFile(e.target.files?.[0]);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    handleFile(e.dataTransfer.files?.[0]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => setDragActive(false);

  const getFileIcon = (filename) => {
    const ext = filename.split(".").pop().toLowerCase();
    if (ext === "pdf") return "📄";
    if (["docx", "doc"].includes(ext)) return "📝";
    if (["png", "jpg", "jpeg", "tiff"].includes(ext)) return "🖼️";
    return "📎";
  };

  return (
    <aside className="sidebar">
      {/* Header */}
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">O</div>
          <div className="sidebar-logo-text">
            <span className="sidebar-logo-title">ONGC Knowledge Hub</span>
            <span className="sidebar-logo-sub">AI-Powered Intelligence</span>
          </div>
        </div>
        <p className="sidebar-tagline">Secure • Local • Enterprise-Grade</p>
      </div>

      {/* Upload Section */}
      <div className="sidebar-section">
        <p className="sidebar-section-label">📁 Ingest Document</p>

        <select
          id="domain-select"
          className="domain-select"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          aria-label="Select domain"
        >
          {INGEST_DOMAINS.map((d) => (
            <option key={d.value} value={d.value}>
              {d.label}
            </option>
          ))}
        </select>

        <div
          className={`drop-zone ${dragActive ? "drag-active" : ""}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          role="button"
          aria-label="Upload document"
          tabIndex={0}
        >
          <span className="drop-zone-icon">☁️</span>
          <p className="drop-zone-title">Drop file here or click to browse</p>
          <p className="drop-zone-sub">PDF, DOCX, PNG, JPG, TIFF</p>
          <input
            type="file"
            accept=".pdf,.docx,.doc,.png,.jpg,.jpeg,.tiff"
            onChange={handleChange}
            aria-hidden="true"
            tabIndex={-1}
          />
        </div>

        {uploadStatus && (
          <div className={`upload-status ${uploadStatus.type}`}>
            {uploadStatus.type === "loading" && <div className="spinner" />}
            {uploadStatus.type === "success" && "✅"}
            {uploadStatus.type === "error" && "❌"}
            <span>{uploadStatus.message}</span>
          </div>
        )}
      </div>

      {/* Draft Report Section */}
      <div className="sidebar-section">
        <p className="sidebar-section-label">📝 Draft Report</p>
        <button 
          className="welcome-chip" 
          style={{ width: "100%", justifyContent: "center", background: "rgba(255,255,255,0.05)" }}
          onClick={() => {
            const topic = window.prompt("Enter report topic (e.g., 'Draft a safety manual as a PDF'):");
            if (!topic) return;
            const draftDomain = window.prompt("Enter domain (e.g., 'all', 'annual_reports'):", "all");
            
            setUploadStatus({ type: "loading", message: "Drafting document..." });
            import('../api').then(({ draftDocument }) => {
              draftDocument(topic, draftDomain)
                .then(({ blob, filename }) => {
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = filename;
                  document.body.appendChild(a);
                  a.click();
                  window.URL.revokeObjectURL(url);
                  a.remove();
                  setUploadStatus({ type: "success", message: "Draft downloaded!" });
                  setTimeout(() => setUploadStatus(null), 4000);
                })
                .catch(err => {
                  setUploadStatus({ type: "error", message: err.message });
                });
            });
          }}
        >
          ✨ Generate Document
        </button>
      </div>

      {/* Chat History Section */}
      <div className="sidebar-section" style={{ borderBottom: "none", paddingBottom: 0 }}>
        <p className="sidebar-section-label">💬 Chat History</p>
      </div>

      <div className="docs-list" style={{ maxHeight: '200px' }}>
        {loadingSessions ? (
          <div className="docs-list-empty">Loading…</div>
        ) : sessions.length === 0 ? (
          <div className="docs-list-empty">No previous chats.</div>
        ) : (
          sessions.map((sess) => (
            <div 
              className={`doc-item ${activeSessionId === sess.id ? 'active' : ''}`} 
              key={sess.id}
              onClick={() => onSelectSession(sess.id)}
              style={{ cursor: 'pointer', background: activeSessionId === sess.id ? 'rgba(255,255,255,0.1)' : 'transparent' }}
            >
              <span className="doc-item-icon">💭</span>
              <div className="doc-item-info">
                <div className="doc-item-name" title={sess.title}>
                  {sess.title}
                </div>
                <div className="doc-item-domain" style={{ fontSize: '10px' }}>
                  {new Date(sess.created_at).toLocaleString()}
                </div>
              </div>
              <div className="session-actions" style={{ display: 'flex', gap: '4px' }}>
                <button 
                  onClick={(e) => handleRenameSession(e, sess.id, sess.title)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '12px',
                    padding: '4px',
                    lineHeight: 1
                  }}
                  title="Rename chat"
                >
                  ✏️
                </button>
                <button 
                  onClick={(e) => handleDeleteSession(e, sess.id)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '12px',
                    padding: '4px',
                    lineHeight: 1
                  }}
                  title="Delete chat"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Ingested Documents */}
      <div className="sidebar-section" style={{ borderBottom: "none", paddingBottom: 0 }}>
        <p className="sidebar-section-label">📚 Ingested Documents</p>
      </div>

      <div className="docs-list">
        {loadingDocs ? (
          <div className="docs-list-empty">Loading…</div>
        ) : documents.length === 0 ? (
          <div className="docs-list-empty">No documents ingested yet.</div>
        ) : (
          documents.map((doc, i) => (
            <div className="doc-item" key={i}>
              <span className="doc-item-icon">{getFileIcon(doc.source)}</span>
              <div className="doc-item-info">
                <div className="doc-item-name" title={doc.source}>
                  {doc.source.split(/[/\\]/).pop()}
                </div>
                <div className="doc-item-domain">{doc.domain.replace(/_/g, " ")}</div>
              </div>
              <button 
                onClick={() => handleDelete(doc.source)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '14px',
                  opacity: 0.5,
                  padding: '4px',
                  transition: 'opacity 0.2s',
                  lineHeight: 1
                }}
                onMouseOver={(e) => e.currentTarget.style.opacity = '1'}
                onMouseOut={(e) => e.currentTarget.style.opacity = '0.5'}
                title="Delete document"
              >
                🗑️
              </button>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
