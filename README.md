# ONGC Knowledge Hub

An enterprise-grade Retrieval-Augmented Generation (RAG) knowledge management system designed for ONGC.

---

## 📂 Project Structure

Below is the directory layout and description of the various components in this repository:

```text
ongc-knowledge-hub/
├── backend/                  # Python API and RAG engine
│   ├── api/                  # API endpoints, routing, and schemas (FastAPI)
│   ├── rag/                  # Retrieval-Augmented Generation pipelines & logic
│   ├── ingestion/            # Document parsing, chunking, and indexing
│   ├── models/               # LLM, embedding model interfaces & prompt templates
│   └── __init__.py
├── frontend/                 # Web interface (React / Next.js / Vite)
├── docs/                     # Design docs, architecture diagrams, and user manuals
├── docker/                   # Dockerfiles, configuration scripts, and profiles
├── monitoring/               # Prometheus, Grafana, and tracing setup
├── security/                 # TLS certs, authorization policies, and security configs
├── data/                     # Raw datasets, vector store files, and localized cache
├── tests/                    # Core unit, integration, and E2E test suites
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Multi-container local deployment orchestrator
└── README.md                 # Project main documentation
```

---

## 🛠️ Components Overview

### 1. [Backend](file:///d:/Repositories/ongc-knowledge-hub/backend)
Contains the Python-based RAG service orchestrator.
- **[api/](file:///d:/Repositories/ongc-knowledge-hub/backend/api)**: Houses FastAPI or standard Python API web servers, including middleware, routing, rate limiting, and dependency injection.
- **[rag/](file:///d:/Repositories/ongc-knowledge-hub/backend/rag)**: Contains context retrieval logic, vector database search, rerankers, and context-assembly pipelines.
- **[ingestion/](file:///d:/Repositories/ongc-knowledge-hub/backend/ingestion)**: Document loaders (PDFs, docs, spreadsheets), OCR modules, text splitters/chunkers, and vector ingestion runners.
- **[models/](file:///d:/Repositories/ongc-knowledge-hub/backend/models)**: Interfaces with models (OpenAI, HuggingFace, Local LLMs), handles chat templates, system instructions, and vector generation.

### 2. [Frontend](file:///d:/Repositories/ongc-knowledge-hub/frontend)
The client interface that users interact with. Features modern web UI components, response rendering, chat interface, document upload interface, and administrative dashboards.

### 3. [Docs](file:///d:/Repositories/ongc-knowledge-hub/docs)
Houses technical design documents, database schemas, integration specifications, API guides, deployment instructions, and product guides.

### 4. [Docker](file:///d:/Repositories/ongc-knowledge-hub/docker)
Environment files, service-specific Dockerfiles, entrypoint shell scripts, and multi-stage build definitions.

### 5. [Monitoring](file:///d:/Repositories/ongc-knowledge-hub/monitoring)
Configuration files for service reliability monitoring, application logs aggregation, trace setups, and dashboard visualizers.

### 6. [Security](file:///d:/Repositories/ongc-knowledge-hub/security)
Security configurations, encryption keys, IAM policy references, network configurations, and data privacy handlers.

### 7. [Data](file:///d:/Repositories/ongc-knowledge-hub/data)
Used for mounting local vector database storage, holding PDF/Excel documents for test ingestion, or storing localized cache files.

### 8. [Tests](file:///d:/Repositories/ongc-knowledge-hub/tests)
Contains unit tests, integration tests, API simulation test runners, and automated evaluation metrics for RAG accuracy.

---

## 🚀 Quick Start (Placeholder)

Detailed bootstrap and operational steps will be provided here as implementation begins.