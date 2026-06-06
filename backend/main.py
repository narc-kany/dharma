import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes

# Relative internal absolute imports mapping to your project layout
from app.schemas import IngestionRequest, IngestionResponse
from app.services.graph_extractor import LegalGraphExtractor
from app.chains import graph_rag_chain

app = FastAPI(
    title="Enterprise Local GraphRAG Engine",
    version="1.0",
    description="Unified API interface combining Llama 3.2 Ingestion and LangServe Multi-Hop Retrieval Graph Operations."
)

# Configure Cross-Origin Resource Sharing (CORS)
# Allows local frontends (Vite, Next.js, etc.) to securely talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Swap with specific origins like ["http://localhost:5173"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate the extraction service securely on boot
try:
    extractor = LegalGraphExtractor()
except Exception as e:
    print(f"⚠️ Warning: Knowledge Graph extraction engine initializing in fallback state. Error: {e}")
    extractor = None

# =====================================================================
# ENDPOINT 1: Traditional FastAPI Ingestion Route
# =====================================================================
@app.post("/api/v1/ingest", response_model=IngestionResponse)
async def ingest_legal_text(payload: IngestionRequest):
    """
    Receives text streams, splits schemas dynamically using Llama 3.2,
    and structurally populates your local Neo4j Instance.
    """
    if not extractor:
        raise HTTPException(
            status_code=503, 
            detail="The local graph transformation engine is currently unavailable."
        )
    
    try:
        metrics = extractor.extract_and_load(
            text_content=payload.text_content,
            act_name=payload.act_name,
            section_number=payload.section_number
        )
        return IngestionResponse(
            status="success",
            nodes_created=metrics["nodes"],
            edges_created=metrics["relationships"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# ENDPOINT 2: LangServe Streaming & Playground Retrieval Route
# =====================================================================
# This line auto-generates /legal-search/invoke, /legal-search/stream, and /legal-search/playground
add_routes(
    app,
    graph_rag_chain,
    path="/legal-search"
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "engine": "Ollama + Neo4j GraphRAG"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Launching Unified LangServe Backend on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)