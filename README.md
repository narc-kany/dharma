# Dharma: AI-Powered Legal GraphRAG

Dharma is an advanced, end-to-end Legal RAG (Retrieval-Augmented Generation) system designed to navigate complex Indian legal frameworks. It uses a **GraphRAG** approach, combining vector similarity with structured knowledge graphs to provide accurate, context-aware legal insights.

## 🚀 Key Features
*   **Knowledge Graph Construction:** Maps legal entities (Acts, Sections, Offenses, Punishments) into a Neo4j Graph database.
*   **Hybrid Retrieval:** Combines vector-based semantic search (using BGE-M3) with keyword-based BM25 indexing for high-precision results.
*   **LLM-Powered Reasoning:** Uses Groq-hosted Llama 3.3 (70B) to extract legal nodes and relationships from raw text.
*   **Interactive UI:** A sleek, responsive dashboard built with Streamlit for intuitive querying and context inspection.

## 🏗️ Architecture
*   **Frontend:** Streamlit
*   **Vector Engine:** LanceDB
*   **Graph Engine:** Neo4j AuraDB (Cloud)
*   **LLM Inference:** Groq API (Llama-3.3-70B-Versatile)
*   **Orchestration:** LangChain

## 🛠️ Getting Started

### Prerequisites
* Python 3.11+
* A Neo4j AuraDB instance
* A Groq API Key

### Installation
1. Clone the repository:
```bash
   git clone [https://github.com/narc-kany/dharma.git](https://github.com/narc-kany/dharma.git)
   cd dharma

```

2. Setup virtual environment and dependencies:

```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r frontend/requirements.txt

```

3. Configure your secrets:
Create a `.streamlit/secrets.toml` file in the `frontend/` directory:

```toml
   GROQ_API_KEY = "gsk_..."
   NEO4J_URI = "neo4j+ssc://your-uri.databases.neo4j.io"
   NEO4J_USERNAME = "neo4j"
   NEO4J_PASSWORD = "your-password"

```

### Running the Application

```bash
streamlit run frontend/app.py

```

## 📜 Legal Acts Supported

* Indian Penal Code (IPC)
* Code of Criminal Procedure (CrPC)
* Civil Procedure Code (CPC)
* Hindu Marriage Act
* And more...

## 👨‍💻 Author

**Data Scientist & AI Engineer**

*Building production-grade ML pipelines and intelligent systems.*
