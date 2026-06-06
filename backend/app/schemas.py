from pydantic import BaseModel, Field

class IngestionRequest(BaseModel):
    """
    Validates incoming payloads for raw text ingestion into the Graph Engine.
    """
    text_content: str = Field(
        ..., 
        description="The raw unstructured legal text or section paragraph to extract graph triplets from."
    )
    act_name: str = Field(
        ..., 
        example="Indian Penal Code, 1860", 
        description="The overarching legal act title or framework name."
    )
    section_number: str = Field(
        ..., 
        example="Section 378", 
        description="The identifier for the specific clause or section number."
    )

class IngestionResponse(BaseModel):
    """
    Defines the response structure sent back to the data parser or client.
    """
    status: str = Field(..., example="success", description="The outcome execution state.")
    nodes_created: int = Field(..., example=5, description="Number of unique entity nodes added or merged in Neo4j.")
    edges_created: int = Field(..., example=4, description="Number of directed relationships mapped between nodes.")