// src/components/ChatArea.jsx
import { useState, useRef, useEffect, useCallback } from "react";
import { sendChatMessage, streamChatMessage, checkHealth, getSessionMessages, createSession } from "../api";
import { DOMAINS, SAMPLE_QUESTIONS } from "../constants";

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

import ReactMarkdown from "react-markdown";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, AreaChart, Area, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from "recharts";

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

function CustomCodeRenderer({ node, inline, className, children, ...props }) {
  const match = /language-(\w+)/.exec(className || '');
  if (!inline && match && match[1] === 'json') {
    try {
      const data = JSON.parse(String(children).replace(/\n$/, ''));
      if (data.chart_type && data.data) {
        return (
          <div style={{ width: '100%', height: 300, background: '#1e1e1e', padding: 20, borderRadius: 8, marginTop: 10 }}>
            <ResponsiveContainer width="100%" height="100%">
              {data.chart_type === 'bar' ? (
                <BarChart data={data.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                  <XAxis dataKey="name" stroke="#ccc" />
                  <YAxis stroke="#ccc" />
                  <Tooltip contentStyle={{ background: '#333', border: 'none' }} />
                  <Legend />
                  <Bar dataKey="value" fill="#8884d8" />
                </BarChart>
              ) : data.chart_type === 'line' ? (
                <LineChart data={data.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                  <XAxis dataKey="name" stroke="#ccc" />
                  <YAxis stroke="#ccc" />
                  <Tooltip contentStyle={{ background: '#333', border: 'none' }} />
                  <Legend />
                  <Line type="monotone" dataKey="value" stroke="#82ca9d" />
                </LineChart>
              ) : data.chart_type === 'pie' ? (
                <PieChart>
                  <Pie data={data.data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                    {data.data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#333', border: 'none' }} />
                  <Legend />
                </PieChart>
              ) : (
                <pre className={className} {...props}>{children}</pre>
              )}
            </ResponsiveContainer>
          </div>
        );
      }
    } catch (e) {
      // Not a chart JSON, fallback
    }
  }
  return <code className={className} {...props}>{children}</code>;
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
            <div className="message-bubble">
              {isUser ? (
                msg.content
              ) : (
                <ReactMarkdown
                  components={{ code: CustomCodeRenderer }}
                >
                  {msg.content}
                </ReactMarkdown>
              )}
            </div>
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

export default function ChatArea({ activeSessionId, onNewSessionCreated, onNewChat }) {
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

  // Load session messages when activeSessionId changes
  useEffect(() => {
    if (!activeSessionId) {
      setMessages([]);
      return;
    }
    setLoading(true);
    getSessionMessages(activeSessionId)
      .then(data => {
        setMessages(data);
      })
      .catch(err => {
        console.error(err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [activeSessionId]);

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
      let currentSessionId = activeSessionId;
      if (!currentSessionId) {
        // Create session first
        const sess = await createSession(question.substring(0, 50));
        currentSessionId = sess.id;
        if (onNewSessionCreated) onNewSessionCreated(sess.id);
      }

      await streamChatMessage(
        question,
        domain === "all" ? null : domain,
        currentSessionId,
        (chunkText) => {
          setMessages((prev) => {
            const next = [...prev];
            const lastMsg = { ...next[next.length - 1] }; // Create a new object to avoid StrictMode double-mutation
            if (lastMsg.thinking) {
              lastMsg.thinking = false;
              lastMsg.content = chunkText;
            } else {
              lastMsg.content += chunkText;
            }
            next[next.length - 1] = lastMsg;
            return next;
          });
        },
        (citationsData) => {
          setMessages((prev) => {
            const next = [...prev];
            const lastMsg = { ...next[next.length - 1] };
            lastMsg.citations = citationsData || [];
            lastMsg.domain = domain;
            next[next.length - 1] = lastMsg;
            return next;
          });
        }
      );
      
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
          <button 
            onClick={onNewChat}
            style={{ 
              background: 'transparent', 
              border: '1px solid rgba(255,255,255,0.2)', 
              color: 'white', 
              padding: '6px 12px', 
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            + New Chat
          </button>
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
