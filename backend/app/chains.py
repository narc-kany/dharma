import os
import streamlit as st
from langchain_groq import ChatGroq
from langchain_neo4j import Neo4jGraph
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

# ==========================================
# 1. Initialize Cloud LLM via Groq (Streamlit Secrets)
# ==========================================
llm = ChatGroq(
    groq_api_key=st.secrets["GROQ_API_KEY"],
    model_name="llama-3.3-70b-versatile",
    temperature=0.1
)

# ==========================================
# 2. Establish Neo4j AuraDB Connection (Streamlit Secrets)
# ==========================================
graph = Neo4jGraph(
    url=st.secrets["NEO4J_URI"],
    username=st.secrets["NEO4J_USERNAME"],
    password=st.secrets["NEO4J_PASSWORD"]
)

def execute_graph_rag_retrieval(query_dict: dict) -> str:
    """
    GraphRAG Core Strategy: Finds an anchor entity via full-text search, 
    and performs a multi-hop traversal to gather context from the cloud database.
    """
    question = query_dict.get("question", "")
    
    # Simple extraction of keywords to search our entity index
    words = [w for w in question.split() if len(w) > 3]
    search_term = words[0] if words else ""
    
    if not search_term:
        return "No clear legal entities extracted from query."

    # Cypher Multi-Hop Traversal Query
    cypher_query = """
    MATCH (e)
    WHERE toLower(e.id) CONTAINS toLower($search_term)
    MATCH path = (e)-[r:DEFINES|PUNISHES_WITH|REFERENCES*1..2]-(target)
    RETURN DISTINCT 
        e.id + " --[" + type(relationships(path)[0]) + "--> " + target.id AS relationship_chain
    LIMIT 25
    """
    
    try:
        # LangChain's Neo4jGraph uses the 'params' keyword argument
        results = graph.query(cypher_query, params={"search_term": search_term})
        context_lines = [row["relationship_chain"] for row in results]
        
        if not context_lines:
            return "No matching multi-hop knowledge graph relationships found."
            
        return "\n".join(context_lines)
    except Exception as e:
        print(f"⚠️ GraphRAG Retrieval error: {e}")
        return "Knowledge Graph retrieval fallback active."

# ==========================================
# 3. Construct the Pipeline Prompt
# ==========================================
prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an expert Indian Legal Assistant powered by a Cloud GraphRAG Engine running Llama 3.1.\n"
        "Analyze the multi-hop relational path context provided below to formulate your legal response. "
        "Focus on how the sections interconnect.\n\n"
        "Knowledge Graph Context:\n{context}"
    )),
    ("human", "{question}")
])

# ==========================================
# 4. Bind into a streaming pipeline
# ==========================================
legal_graph_chain = (
    RunnablePassthrough.assign(context=RunnableLambda(execute_graph_rag_retrieval))
    | prompt
    | llm
    | StrOutputParser()
)