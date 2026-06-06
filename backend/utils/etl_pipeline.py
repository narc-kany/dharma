import os
import json
import sqlite3
import glob
import lancedb
from lancedb.pydantic import LanceModel, Vector  # type: ignore
from langchain_huggingface import HuggingFaceEmbeddings # Updated Import!

# =====================================================================
# 1. DYNAMIC PATH RESOLUTION
# =====================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCUMENTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "database", "documents"))
LANCE_DB_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "vector"))

TABLE_NAME = "bare_acts"
MODEL_NAME = "yuriyvnv/legal-bge-m3"

print(f"📂 Resolved Source Directory: {DOCUMENTS_DIR}")
print(f"📂 Resolved Database Destination: {LANCE_DB_DIR}")

# =====================================================================
# 2. INITIALIZATION & SCHEMA
# =====================================================================

print(f"Initializing embedding model: {MODEL_NAME}...")
# This step takes a moment as PyTorch loads the heavy model into memory
embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
VECTOR_DIMENSION = 1024

class LegalDocumentSchema(LanceModel):
    act_name: str
    chapter: str
    section_number: str
    section_title: str
    text_content: str
    vector: Vector(VECTOR_DIMENSION)

db = lancedb.connect(LANCE_DB_DIR)
table = db.create_table(TABLE_NAME, schema=LegalDocumentSchema, mode="overwrite")

ingestion_batch = []

# =====================================================================
# 3. EXTRACT & TRANSFORM: SQLITE (Master.db)
# =====================================================================

sqlite_path = os.path.join(DOCUMENTS_DIR, "Master.db")

db_registry = {
    "IPC": "Indian Penal Code, 1860",
    "CRPC": "Code of Criminal Procedure, 1973",
    "CPC": "Civil Procedure Code, 1908",
    "HMA": "Hindu Marriage Act, 1955",
    "IDA": "Indian Divorce Act, 1869",
    "IEA": "Indian Evidence Act, 1872",
    "NIA": "Negotiable Instruments Act, 1881",
    "MVA": "The Motor Vehicles Act, 1988"
}

if os.path.exists(sqlite_path):
    print(f"\nProcessing database file: '{sqlite_path}'...")
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        for table_name, official_name in db_registry.items():
            print(f"\n -> Extracting from SQLite table: {table_name}...")
            try:
                if table_name == "IPC":
                    cursor.execute(f"SELECT chapter, Section, section_title, section_desc FROM {table_name}")
                elif table_name in ["NIA", "IEA", "CRPC", "HMA"]:
                    cursor.execute(f"SELECT chapter, section, section_title, section_desc FROM {table_name}")
                elif table_name in ["CPC", "IDA", "MVA"]:
                    cursor.execute(f"SELECT 'N/A', section, title, description FROM {table_name}")
                else:
                    continue
                
                rows = cursor.fetchall()
                total_rows = len(rows)
                print(f"    Found {total_rows} sections. Generating vectors (this may take a few minutes)...")
                
                for idx, row in enumerate(rows):
                    chapter, section, title, text = row
                    safe_title = str(title or "Untitled").strip()
                    safe_text = str(text or "").strip()
                    safe_section = str(section).strip()
                    
                    if not safe_text:
                        continue
                        
                    clean_content = f"Act: {official_name} | Section {safe_section}: {safe_title}. {safe_text}"
                    
                    ingestion_batch.append({
                        "act_name": official_name,
                        "chapter": str(chapter).strip(),
                        "section_number": safe_section,
                        "section_title": safe_title,
                        "text_content": clean_content,
                        "vector": embeddings.embed_query(clean_content)
                    })
                    
                    # Watch it work!
                    if (idx + 1) % 50 == 0:
                        print(f"    ⏳ Processed {idx + 1}/{total_rows} sections in {table_name}...")
                        
            except sqlite3.OperationalError:
                print(f"    ⚠️ Skipping table {table_name} (Not found in DB)")
        conn.close()
    except Exception as e:
        print(f"⚠️ Error connecting to SQLite database: {e}")
else:
    print(f"\nℹ️ 'Master.db' not found at {sqlite_path}. Skipping SQL.")

# =====================================================================
# 4. EXTRACT & TRANSFORM: DYNAMIC JSON DISCOVERY
# =====================================================================

print("\nScanning for JSON files...")
json_files = glob.glob(os.path.join(DOCUMENTS_DIR, "*.json"))

def infer_act_name(filename):
    lower_name = filename.lower().replace("_", " ").replace("-", " ")
    if 'ipc' in lower_name or 'penal' in lower_name or 'penel' in lower_name: return "Indian Penal Code, 1860"
    if 'crpc' in lower_name or 'criminal procedure' in lower_name: return "Code of Criminal Procedure, 1973"
    if 'cpc' in lower_name or 'civil procedure' in lower_name: return "Civil Procedure Code, 1908"
    if 'hma' in lower_name or 'hindu marriage' in lower_name: return "Hindu Marriage Act, 1955"
    if 'ida' in lower_name or 'divorce' in lower_name: return "Indian Divorce Act, 1869"
    if 'iea' in lower_name or 'evidence' in lower_name: return "Indian Evidence Act, 1872"
    if 'nia' in lower_name or 'negotiable' in lower_name: return "Negotiable Instruments Act, 1881"
    if 'mva' in lower_name or 'motor vehicle' in lower_name: return "The Motor Vehicles Act, 1988"
    return os.path.basename(filename).replace('.json', '').replace('_', ' ').title()

for json_path in json_files:
    file_name = os.path.basename(json_path)
    official_name = infer_act_name(file_name)
    print(f" -> Parsing JSON: '{file_name}' (Mapped to: {official_name})")
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            items = raw_data if isinstance(raw_data, list) else raw_data.get("sections", [])
            
            for idx, item in enumerate(items):
                section_num = str(item.get("section") or item.get("Section") or item.get("section_id") or "").strip()
                title = str(item.get("title") or item.get("section_title") or "Untitled").strip()
                body_text = str(item.get("text") or item.get("description") or item.get("section_desc") or item.get("content") or "").strip()
                chap = str(item.get("chapter") or "N/A").strip()
                
                if not body_text and not title:
                    continue
                    
                clean_content = f"Act: {official_name} | Section {section_num}: {title}. {body_text}"
                
                ingestion_batch.append({
                    "act_name": official_name,
                    "chapter": chap,
                    "section_number": section_num,
                    "section_title": title,
                    "text_content": clean_content,
                    "vector": embeddings.embed_query(clean_content)
                })
                
                if (idx + 1) % 50 == 0:
                    print(f"    ⏳ Processed {idx + 1}/{len(items)} sections in {file_name}...")
                    
    except Exception as e:
        print(f"  ⚠️ Error parsing JSON inside {file_name}: {e}")

# =====================================================================
# 5. LOAD & INDEX BUILD
# =====================================================================

total_records = len(ingestion_batch)
if total_records == 0:
    print("\n❌ Pipeline Error: No legal documents extracted. Ingestion aborted.")
else:
    print(f"\nInserting {total_records} documents into LanceDB...")
    table.add(ingestion_batch)
    
    print("Building local high-performance Inverted Index (BM25) for Hybrid Matching...")
    table.create_fts_index("text_content", replace=True)
    
    print("\n=====================================================================")
    print("🚀 ETL PIPELINE SUCCESSFUL: Hybrid Vector Store Saved!")
    print(f" Location: {LANCE_DB_DIR}")
    print("=====================================================================")