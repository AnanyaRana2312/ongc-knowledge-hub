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

## 🚀 Quick Start & Deployment Guide

Follow these steps to clone, configure, run, and access the ONGC Knowledge Hub application locally.

### 📋 Prerequisites

Before starting, ensure you have the following installed on your machine:
* **Git**
* **Docker & Docker Compose**
* **Ollama** (for local LLM execution — download from [ollama.com](https://ollama.com))

---

### 📥 1. Clone the Repository

Clone the project repository to your local machine and navigate into the root directory:
```bash
git clone https://github.com/AnanyaRana2312/ongc-knowledge-hub.git
cd ongc-knowledge-hub
```

---

### ⚙️ 2. Environment Configuration

Copy the example configuration file to create your local `.env` file:
```bash
cp .env.example .env
```
Inside the `.env` file, the defaults are optimized for local hardware (e.g. 4GB GPUs):
* `OLLAMA_MODEL=llama3.2` (Modern 3B parameter model, optimized for VRAM)
* `OLLAMA_EMBEDDING_MODEL=nomic-embed-text` (Vector embeddings model)
* `OLLAMA_BASE_URL=http://localhost:11434` (Ollama host URL)

---

### 🦙 3. Setup Ollama & Pull Models

1. **Start the Ollama application** on your host machine.
2. **Download the models**: Open your terminal or PowerShell and pull the LLM and embedding models specified in the `.env` file:
   ```bash
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```

> [!TIP]
> **Disk Space / VRAM Optimization on Windows:**
> If your `C:` drive is running low on space, you can redirect Ollama to save all models to another drive (e.g. `D:`) by setting the `OLLAMA_MODELS` environment variable in PowerShell:
> ```powershell
> [Environment]::SetEnvironmentVariable("OLLAMA_MODELS", "D:\OllamaModels", "User")
> ```
> *Make sure to restart the Ollama application after running this command to apply the changes.*

---

### 🐳 4. Launch the Application

Build and launch all application containers (Backend, Frontend, and Monitoring services) in the background:
```bash
docker compose up --build -d
```
This command builds the images and spins up the multi-container environment.

---

### 🌐 5. Accessing the Services

Once the containers are running, you can access the different components of the system at the following URLs:

| Service | URL | Description |
| :--- | :--- | :--- |
| **Frontend UI** | [http://localhost](http://localhost) | Main React/Vite interface for chat & document drafting. |
| **Backend API** | [http://localhost:8000](http://localhost:8000) | FastAPI server endpoints and interactive Swagger docs at `/docs`. |
| **Grafana** | [http://localhost:3000](http://localhost:3000) | System dashboard and performance metrics. |
| **Prometheus** | [http://localhost:9090](http://localhost:9090) | Time-series database containing metrics scrape data. |

---

### 🧪 6. Running Tests

To verify that the backend services, retriever, and RAG pipelines are working correctly inside the Docker container, run the test suite:
```bash
docker compose exec backend pytest
```

---

### 🛑 Stopping the Application

To shut down all running services and containers, run:
```bash
docker compose down
```