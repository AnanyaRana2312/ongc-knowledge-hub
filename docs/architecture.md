# Architecture — ONGC Secure Enterprise Knowledge Hub

## 1. System Overview

The ONGC Knowledge Hub is a local-first, AI-powered document intelligence platform.
It ingests organisational documents (SOPs, manuals, reports), stores them as vector
embeddings, and answers natural language queries using a local LLM — with no data
leaving the enterprise network.

---

## 2. High-Level Component Diagram

```
                        ┌─────────────────────────────────────────┐
                        │              User Interface              │
                        │       (Browser / OpenWebUI / CLI)        │
                        └────────────────────┬────────────────────┘
                                             │ HTTP
                        ┌────────────────────▼────────────────────┐
                        │            FastAPI Backend               │
                        │  ┌──────────┐ ┌─────────┐ ┌─────────┐  │
                        │  │  /chat   │ │ /search │ │ /ingest │  │
                        │  └────┬─────┘ └────┬────┘ └────┬────┘  │
                        └───────┼────────────┼────────────┼───────┘
                                │            │            │
               ┌────────────────▼──┐  ┌──────▼──────┐  ┌─▼──────────────┐
               │   RAG Pipeline    │  │  Semantic   │  │  Ingestion     │
               │  (LangChain)      │  │   Search    │  │  Pipeline      │
               │                   │  │ (ChromaDB)  │  │ (PDF/DOCX/OCR) │
               └────────┬──────────┘  └──────┬──────┘  └───────┬────────┘
                        │                    │                  │
               ┌────────▼────────────────────▼──────────────────▼────────┐
               │                     ChromaDB                             │
               │              (Persistent Vector Store)                   │
               │                  ./data/chroma/                          │
               └─────────────────────────┬────────────────────────────────┘
                                         │ embed / retrieve
               ┌─────────────────────────▼────────────────────────────────┐
               │                      Ollama                               │
               │           (Local LLM Runtime — llama3 8B)                │
               │              http://localhost:11434                       │
               └──────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow

### 3a. Document Ingestion Flow

```
Raw Document (PDF/DOCX/Image)
        │
        ▼
  Document Loader
  (pypdf / python-docx / pytesseract)
        │
        ▼
  Text Splitter
  (LangChain RecursiveCharacterTextSplitter)
  chunk_size=1000, chunk_overlap=200
        │
        ▼
  Embedding Model
  (OllamaEmbeddings — llama3)
        │
        ▼
  ChromaDB Vector Store
  (persistent at ./data/chroma/)
```

### 3b. Query / RAG Flow

```
User Question (natural language)
        │
        ▼
  Embed Question
  (OllamaEmbeddings — llama3)
        │
        ▼
  Vector Similarity Search
  (ChromaDB — top-k=5 most relevant chunks)
        │
        ▼
  Context Assembly
  (LangChain — retrieved chunks + user question)
        │
        ▼
  LLM Generation
  (ChatOllama — llama3, grounded in retrieved context)
        │
        ▼
  Structured Response
  (answer + source document references)
```

---

## 4. Module Responsibilities

| Module | Path | Responsibility |
|---|---|---|
| Config | `backend/api/config.py` | Centralised env-based settings |
| LLM Client | `backend/models/ollama_client.py` | ChatOllama interface + health check |
| Embedding Client | `backend/models/embedding_client.py` | OllamaEmbeddings interface |
| Ingestion | `backend/ingestion/` | Load, parse, chunk, and index documents |
| RAG Pipeline | `backend/rag/` | Retrieval chain, prompt templates, reranking |
| API Routes | `backend/api/` | HTTP endpoints — chat, search, ingest |
| Frontend | `frontend/` | User-facing web interface |
| Monitoring | `monitoring/` | Prometheus metrics, Grafana dashboards |
| Security | `security/` | Cosign image signing, Sigstore verification |

---

## 5. Security Boundaries

```
┌─────────────────────────────────────────────────────────┐
│                  Enterprise Network                      │
│                                                         │
│   ┌───────────┐     ┌───────────┐     ┌─────────────┐  │
│   │  Browser  │────▶│  FastAPI  │────▶│   Ollama    │  │
│   │  (user)   │     │  (signed  │     │  (local,    │  │
│   └───────────┘     │  Docker   │     │  air-gapped)│  │
│                     │  image)   │     └─────────────┘  │
│                     └─────┬─────┘                       │
│                           │                             │
│                     ┌─────▼─────┐                       │
│                     │ ChromaDB  │                       │
│                     │ (local FS)│                       │
│                     └───────────┘                       │
│                                                         │
│   ✅ No data leaves this boundary                       │
│   ✅ All containers signed with Cosign (Week 4)         │
│   ✅ Sigstore verification enforced on deploy (Week 4)  │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Monitoring Architecture

```
FastAPI (/metrics endpoint)
        │
        ▼
  Prometheus (scrapes /metrics every 15s)
        │
        ▼
  Grafana (dashboards — query latency, doc count, error rates)
```

---

## 7. Technology Decisions

| Decision | Choice | Rationale |
|---|---|---|
| LLM runtime | Ollama | Air-gapped, free, GPU/CPU support |
| LLM model | llama3 8B | Best open-source quality/speed balance |
| Vector DB | ChromaDB | Lightweight, no separate service needed |
| API framework | FastAPI | Async, auto-docs, type-safe |
| Orchestration | LangChain | Mature RAG tooling, Ollama integration |
| Container signing | Cosign + Sigstore | Supply chain security (CNCF standard) |
| Observability | Prometheus + Grafana | Industry standard, Docker-native |
