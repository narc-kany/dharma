import os
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_ollama import ChatOllama
from langchain_core.documents import Document
from app.config import settings

class LegalGraphExtractor:
    def __init__(self):
        # Establish connection to Neo4j using variables from config
        self.graph = Neo4jGraph(
            url=settings.NEO4J_URI,
            username=settings.NEO4J_USERNAME,
            password=settings.NEO4J_PASSWORD
        )
        
        # Initialize local Ollama instance
        # Note: Ensure the model (e.g., llama3.1) is already pulled via `ollama pull llama3.1`
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.0  # Set to 0 for maximum determinism in extraction
        )
        
        # Configure Graph Transformer optimized for local schema matching
        self.transformer = LLMGraphTransformer(
            llm=self.llm,
            allowed_nodes=["LegalSection", "Crime", "Penalty", "Authority", "LegalConcept"],
            allowed_relationships=["DEFINES", "PUNISHES_WITH", "APPLIES_TO", "REFERENCES", "OVERRIDES"],
            strict_mode=True # Forces the local LLM to stick tightly to our defined ontology
        )

    def extract_and_load(self, text_content: str, act_name: str, section_number: str) -> dict:
        """
        Extracts semantic graph entities and relationships using a local Ollama model
        and commits them to the Neo4j instance.
        """
        if not text_content.strip():
            return {"nodes": 0, "relationships": 0}

        # Wrap text block into a Document item
        doc = Document(
            page_content=text_content,
            metadata={"act_name": act_name, "section": section_number}
        )
        
        try:
            # Run extraction through local Ollama model
            graph_docs = self.transformer.convert_to_graph_documents([doc])
            
            if graph_docs:
                # Insert extracted entities and edges into Neo4j
                self.graph.add_graph_documents(graph_docs)
                
                return {
                    "nodes": len(graph_docs[0].nodes),
                    "relationships": len(graph_docs[0].relationships)
                }
        except Exception as e:
            # Local models can sometimes output invalid formatting that breaks parsing
            print(f"⚠️ Extraction failed for Act: {act_name}, Sec: {section_number}. Error: {e}")
            
        return {"nodes": 0, "relationships": 0}