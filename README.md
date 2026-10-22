# ResearchGraph AI — Evidence-Grounded Research Intelligence

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Django: 4.2 LTS](https://img.shields.io/badge/django-4.2%20LTS-green.svg)](https://www.djangoproject.com/)
[![React: 18](https://img.shields.io/badge/react-18-cyan.svg)](https://react.dev/)
[![LangGraph](https://img.shields.io/badge/orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Vector Search: pgvector](https://img.shields.io/badge/vector-pgvector-purple.svg)](https://github.com/pgvector/pgvector)
[![CI Status](https://img.shields.io/badge/CI-Passing-brightgreen.svg)](.github/workflows/ci.yml)

**ResearchGraph AI** is an open-source, evidence-grounded research intelligence platform that turns collections of scientific research papers and technical documents into a verifiable, interconnected knowledge-and-claim system.

Unlike standard PDF chatbots that return conversational answers with unverified hallucinations, ResearchGraph AI structures literature into **traceable claims, verbatim supporting passages, character-level source offsets, and stance-aware inter-paper relationships (Supports, Contradicts, Qualifies, Depends On).**

---

## 🌟 Key Features

1. **Precision Ingestion & Provenance Preservation (`backend/ingestion/`)**:
   - PyMuPDF (`fitz`) layout parsing for PDFs, text, and Markdown files.
   - Preserves page numbers, section headings, token counts, and `start_char` / `end_char` offsets.
   - SHA-256 cryptographic deduplication prevents duplicate ingestion.
   - Full cascading deletion for GDPR/privacy compliance (deleting a paper removes all derived embeddings, claims, citations, and graph edges).

2. **Hybrid Semantic & Lexical Retrieval (`backend/retrieval/`)**:
   - Dense vector embeddings ($D=384$) powered by local Ollama or deterministic semantic feature projection.
   - Sparse lexical BM25 matching with title/heading boosting.
   - Reciprocal Rank Fusion (RRF) with calibrated underlying similarity scoring.
   - Strict **Citation Validation Engine**: mathematically audits synthesized reports to verify every citation references an actual retrieved passage, penalizing fabricated sources.

3. **Structured Claim & Stance Extraction (`backend/claims/`)**:
   - Extracts structured factual claims with exact verbatim supporting passages.
   - Scientific entity recognition (Methods, Datasets, Architectures, Metrics).
   - Deep Stance & Contradiction Detection: distinguishes genuine empirical disagreement from superficial semantic similarity, flagging tensions for human review.

4. **Multi-Agent Research Workflow via LangGraph (`backend/agents/`)**:
   - Bounded 7-agent pipeline:
     1. **Research Planner**: Decomposes complex questions into targeted subquestions.
     2. **Evidence Retriever**: Queries hybrid index and verifies corpus sufficiency.
     3. **Claim Extractor**: Identifies factual findings and source passages.
     4. **Evidence Comparator**: Cross-references claims across papers to detect consensus and contradictions.
     5. **Synthesis Agent**: Generates comprehensive grounded analysis with numbered citations.
     6. **Citation Validator**: Audits every citation in the text against retrieved sources; triggers feedback loop if hallucinated references are found.
     7. **Report Generator**: Compiles executive summary, claim breakdown, and explicit evidence gap notices.
   - **Grounded Refusal**: If the indexed collection lacks sufficient evidence on a subject, the system issues a clear evidence gap notice rather than fabricating an answer.

5. **Full Research Dashboard (`frontend/`)**:
   - **Document Library**: Upload dropzone, real-time ingestion status indicators, document metadata, and cascade deletion.
   - **Research Workspace**: Natural-language query interface with live 7-stage animated agent stepper.
   - **Search Results Playground**: Term highlighting, score sliders, and 1-click citation lookup.
   - **Claim Explorer**: Filterable claims by document, review status, entity, and confidence.
   - **Interactive Knowledge Graph**: Canvas-based visual property graph with force physics, zoom/pan navigation, and provenance drawer.
   - **Cross-Paper Comparison Matrix**: Side-by-side tabular comparison across documents on key research variables.
   - **Contradiction Review Queue**: Dedicated queue for reviewing tensions between papers with Accept/Reject/Modify controls.
   - **Research Reports**: Export to Markdown, HTML, or JSON.
   - **Scientific Evaluation Dashboard**: Live Chart.js visualization of Recall@K, MRR, Citation Precision, Extraction F1, Contradiction F1, and Latency.

6. **Evaluation Framework (`backend/evaluation/`)**:
   - Standardized labeled ground-truth dataset (`sample_evaluation/ground_truth.json`).
   - Human-reviewed labels for claims, empirical contradictions, and unanswerable refusal cases.
   - Zero contamination of inference data.

---

## 🛠️ Technology Stack

- **Frontend**: React 18, React Router v6, Plain Vanilla CSS (modern dark mode, glassmorphism, responsive grid), Chart.js. *No Tailwind or Bootstrap.*
- **Backend**: Python 3.9+, Django 4.2 LTS, Django REST Framework.
- **Database & Vectors**: PostgreSQL with `pgvector` (production & Docker) / SQLite vector fallback (zero-setup local dev/test).
- **Document Extraction**: PyMuPDF (`fitz`).
- **LLM Orchestration**: LangGraph.
- **Local Inference**: Ollama (`llama3`, `nomic-embed-text`) with deterministic offline fallback engine.
- **Testing**: pytest & pytest-django.
- **Deployment**: Docker Compose & Podman compatible.

---

## 🚀 Quickstart Guide

### Option A: Local Development (Fastest, zero-setup)

#### 1. Clone & Set Up Backend Virtual Environment
```bash
git clone https://github.com/your-org/researchgraph-ai.git
cd researchgraph-ai

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run migrations and seed sample research documents
python backend/manage.py migrate
python backend/seed_data.py
```

#### 2. Start Django API Server
```bash
python backend/manage.py runserver 127.0.0.1:8000
```

#### 3. Start React Frontend
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

### Option B: Docker Compose (PostgreSQL + pgvector)

```bash
# Build and run containers
docker-compose up --build
```
- Frontend: `http://localhost:5173`
- Django API: `http://localhost:8000/api/`
- PostgreSQL pgvector: `localhost:5432`

---

## 🧪 Running the Test Suite

Run all 16 automated tests covering ingestion, chunk offsets, hybrid retrieval, citation validation, multi-agent workflows, and evaluation metrics:

```bash
source .venv/bin/activate
pytest -v
```

---

## 📊 Scientific Benchmark Evaluation

Execute the evaluation benchmark suite against human-labeled ground truth:

```bash
# Via CLI:
source .venv/bin/activate
python3 -c "
import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'researchgraph.settings')
import sys; sys.path.insert(0, 'backend'); django.setup()
from evaluation.runner import EvaluationRunner
res = EvaluationRunner().run_benchmark()
print('Summary Metrics:', res['summary'])
"
```
Or open the **Evaluation** tab in the dashboard at `http://localhost:5173/evaluation` and click **"▶ Execute Benchmark Suite"**.

---

## 📁 Repository Structure

```
researchgraph-ai/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── seed_data.py
│   ├── researchgraph/      # Settings, URLs, WSGI, ASGI
│   ├── core/               # Unified database models & serializers
│   ├── ingestion/          # PDF/Text layout parsers, offset chunker, pipeline
│   ├── retrieval/          # Hybrid vector/lexical search, reranker, citation validator
│   ├── claims/             # Structured claim extraction, evidence comparator
│   ├── graph/              # Relational knowledge graph service & traversal
│   ├── agents/             # 7-Agent LangGraph research synthesis workflow
│   └── evaluation/         # Recall@K, MRR, Citation & Contradiction metrics runner
├── frontend/
│   ├── src/
│   │   ├── pages/          # 9 complete functional dashboard views
│   │   ├── components/     # Navbar, EvidenceDrawer, ReviewModal
│   │   ├── api.js          # Unified API client
│   │   └── index.css       # Complete dark-mode design system
├── sample_documents/       # Open-access research papers on GraphRAG, DPR, Hallucination
├── sample_evaluation/      # Standardized ground-truth benchmark dataset
├── docs/
│   ├── architecture.md     # In-depth architectural & dataflow specification
│   └── evaluation_methodology.md # Scientific metric definitions & ground truth formulas
├── tests/                  # Pytest test suite (16 tests)
├── Dockerfile
├── docker-compose.yml
├── .github/workflows/ci.yml
├── SECURITY.md
└── LICENSE
```

---

## 📜 Documentation

- [System Architecture](docs/architecture.md)
- [Evaluation Methodology](docs/evaluation_methodology.md)
- [Security Policy](SECURITY.md)

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
