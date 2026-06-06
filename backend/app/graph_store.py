import os
from langchain_community.graphs import Neo4jGraph
from app.config import settings

def get_graph_connection() -> Neo4jGraph:
    """
    Initializes and returns a thread-safe connection to the Neo4j Graph Database
    using configuration settings loaded from the environment.
    """
    try:
        # Pass configuration parameters directly from our central config
        graph = Neo4jGraph(
            url=settings.NEO4J_URI,
            username=settings.NEO4J_USERNAME,
            password=settings.NEO4J_PASSWORD
        )
        
        # Enforce uniqueness constraints to prevent node fragmentation during extraction.
        # This ensures 'Section 378' remains a single unique node across multiple ingestions.
        graph.query(
            "CREATE CONSTRAINT unique_legal_entity IF NOT EXISTS "
            "FOR (e:__Entity__) REQUIRE e.id IS UNIQUE"
        )
        
        return graph
        
    except Exception as e:
        print(f"❌ Critical Error: Failed to establish Neo4j connection. Details: {e}")
        raise e