// src/components/ChatArea.jsx
import { useState, useRef, useEffect, useCallback } from "react";
import { sendChatMessage, checkHealth } from "../api";
import { DOMAINS, SAMPLE_QUESTIONS } from "../constants";

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

function Message({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`message ${msg.role}`}>
      <div className="message-avatar">
        {isUser ? "👤" : "🤖"}
      </div>
      <div className="message-content">
        {msg.thinking ? (
          <div className="thinking-bubble">
            <div className="thinking-dot" />
            <div className="thinking-dot" />
            <div className="thinking-dot" />
          </div>
        ) : (
          <>
            <div className="message-bubble">{msg.content}</div>
            {!isUser && msg.domain && msg.domain !== "all" && (
              <span className="domain-badge">🗂️ {msg.domain.replace(/_/g, " ")}</span>
            )}
            {!isUser && msg.citations && msg.citations.length > 0 && (
              <div className="citations">
                <span className="citations-label">Sources</span>
                {msg.citations.map((c, i) => {
                  // Citations are objects: {source, page, domain, chunk_index}
                  const filename = typeof c === "string"
                    ? c.split(/[/\\]/).pop()
                    : (c.source || "").split(/[/\\]/).pop();
                  const domain = typeof c === "object" ? c.domain : null;
                  return (
                    <div className="citation-item" key={i}>
                      📎 {filename}
                      {domain && domain !== "default" && (
                        <span style={{ opacity: 0.6, marginLeft: 4 }}>· {domain.replace(/_/g, " ")}</span>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function ChatArea() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [domain, setDomain] = useState("all");
  const [loading, setLoading] = useState(false);
  const [apiOnline, setApiOnline] = useState(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Check health on mount
  useEffect(() => {
    checkHealth()
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false));
  }, []);

  // Auto-resize textarea
  const handleInputChange = (e) => {
    setInput(e.target.value);
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = Math.min(ta.scrollHeight, 150) + "px";
    }
  };

  const handleSend = async (text) => {
    const question = (text || input).trim();
    if (!question || loading) return;

    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    const userMsg = { role: "user", content: question };
    const thinkingMsg = { role: "assistant", thinking: true, content: "" };

    setMessages((prev) => [...prev, userMsg, thinkingMsg]);
    setLoading(true);

    try {
      const data = await sendChatMessage(question, domain === "all" ? null : domain);
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: "assistant",
          content: data.answer,
          citations: data.citations || [],
          domain: domain,
        };
        return next;
      });
    } catch (err) {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: "assistant",
          content: `⚠️ Error: ${err.message}`,
          citations: [],
        };
        return next;
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <main className="main-area">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-left">
          <h1 className="chat-header-title">AI Knowledge Assistant</h1>
          <p className="chat-header-sub">
            Powered by Llama 3 · ChromaDB · LangChain
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <select
            id="chat-domain-select"
            className="domain-select"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            style={{ width: "auto", marginBottom: 0, fontSize: "12px", padding: "6px 32px 6px 12px" }}
            aria-label="Select search domain"
          >
            {DOMAINS.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
          <div className={`status-pill ${apiOnline === false ? "error" : ""}`}
            style={apiOnline === false ? {
              background: "rgba(239,68,68,0.1)",
              border: "1px solid rgba(239,68,68,0.2)",
              color: "#f87171"
            } : {}}
          >
            <div className="status-dot"
              style={apiOnline === false ? { background: "#ef4444", animation: "none" } : {}}
            />
            {apiOnline === null ? "Connecting…" : apiOnline ? "Online" : "Offline"}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="welcome-screen">
            <span className="welcome-icon">🔬</span>
            <h2 className="welcome-title">
              Ask anything about <span>ONGC</span>
            </h2>
            <p className="welcome-sub">
              Upload your organizational documents using the sidebar, then ask
              questions in natural language. The AI will search across all
              ingested knowledge and give you a grounded, cited answer.
            </p>
            <div className="welcome-chips">
              {SAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  className="welcome-chip"
                  onClick={() => handleSend(q)}
                  type="button"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => <Message key={i} msg={msg} />)
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <textarea
            id="chat-input"
            ref={textareaRef}
            className="chat-input"
            placeholder="Ask a question about your documents…"
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            rows={1}
            aria-label="Chat input"
            disabled={loading}
          />
          <button
            id="send-button"
            className="send-button"
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            aria-label="Send message"
            type="button"
          >
            <SendIcon />
          </button>
        </div>
        <p className="input-hint">Press Enter to send · Shift+Enter for new line</p>
      </div>
    </main>
  );
}
