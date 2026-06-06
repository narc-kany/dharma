import os
import json
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph
from langchain_groq import ChatGroq
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document

# 1. Load your Cloud Credentials from .env
load_dotenv()

# Configuration
DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../database/documents/"))

def run_cloud_migration():
    print("🚀 Connecting to Neo4j AuraDB Cloud...")
    
    # 2. Establish Cloud Graph Connection
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
    )
    
    # 3. Initialize Groq Graph Extractor (Using 70B for high-accuracy relationship extraction)
    llm = ChatGroq(
        temperature=0, 
        model_name="llama-3.3-70b-versatile",
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    
    llm_transformer = LLMGraphTransformer(
        llm=llm,
        # Restricting the model to specific legal concepts prevents hallucinated node types
        allowed_nodes=["Section", "Act", "Concept", "Punishment", "Offense"],
        allowed_relationships=["DEFINES", "PUNISHES_WITH", "REFERENCES", "MANDATES"]
    )

    # 4. Iterate over JSON Legal Acts
    if not os.path.exists(DOCS_DIR):
        print(f"❌ Error: Could not find documents folder at {DOCS_DIR}")
        return

    json_files = [f for f in os.listdir(DOCS_DIR) if f.endswith(".json")]
    print(f"📦 Found {len(json_files)} legal acts to process.")

    success_count = 0
    
    for filename in json_files:
        filepath = os.path.join(DOCS_DIR, filename)
        
        with open(filepath, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            # Use your old robust list/dict check
            items = raw_data if isinstance(raw_data, list) else raw_data.get("sections", [])
            
        print(f"📦 Parsing {len(items)} items from {filename}...")
            
        for item in items:
            # 1. Transplanted robust extraction logic
            section_num = str(item.get("section") or item.get("Section") or item.get("section_id") or "").strip()
            title = str(item.get("title") or item.get("section_title") or "Untitled").strip()
            body_text = str(item.get("text") or item.get("description") or item.get("section_desc") or item.get("content") or "").strip()
            chap = str(item.get("chapter") or "N/A").strip()
            
            # 2. Skip if it's completely empty
            if not body_text and not title:
                continue

            # 3. Format the context for the LLM to read easily
            content = f"Chapter {chap}, Section {section_num}: {title}. {body_text}"
            
            # 4. Manually construct the metadata dictionary for Neo4j
            metadata = {
                "source": filename,
                "section": section_num,
                "title": title,
                "chapter": chap
            }

            doc = Document(page_content=content, metadata=metadata)
            
            print(f"⚙️ Extracting entities for: {filename} - Section {section_num}...")
            
            try:
                # Ask Groq to extract the nodes and edges
                graph_docs = llm_transformer.convert_to_graph_documents([doc])
                
                # Push the results directly to Neo4j AuraDB
                graph.add_graph_documents(
                    graph_docs, 
                    baseEntityLabel=True, 
                    include_source=True
                )
                success_count += 1
                
            except Exception as e:
                print(f"❌ Failed to process Section {section_num}: {e}")

    print(f"\n🎉 Cloud Migration Complete! Successfully ingested {success_count} legal provisions.")

if __name__ == "__main__":
    run_cloud_migration()