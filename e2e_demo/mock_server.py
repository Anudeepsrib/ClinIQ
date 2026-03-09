from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    departments: Optional[List[str]] = None

class DocumentInfo(BaseModel):
    filename: str
    department: str
    content: str
    score: float = 0.0

class QueryResponse(BaseModel):
    answer: str
    sources: List[DocumentInfo] = []
    departments_searched: List[str] = []
    hallucination_score: str = "yes"
    confidence_score: float = 0.0
    response_type: str = "direct"
    options: List[str] = []
    masked: bool = False

@app.post("/api/v1/query", response_model=QueryResponse)
async def query_documents(req: QueryRequest):
    await asyncio.sleep(1.5) # Simulate network delay
    
    user_query = req.question.lower()
    
    # Defaults
    response = QueryResponse(
        answer="I did not understand. Could you rephrase your clinical query?"
    )

    # Scenario 1: Clarification needed
    if "lab" in user_query or "results" in user_query:
        response.answer = "I need a specific patient context to retrieve lab vitals. Which active patient are you inquiring about?"
        response.response_type = "clarification"
        response.options = ["Patterson, Emily (Bed 4)", "Rodriguez, Luis (Bed 12)", "Search Global Directory"]

    # Scenario 2: Selecting patient context after clarification
    elif "patterson" in user_query:
        # Note: In a real system the active focus gets set differently, but we mock the bot response
        response.answer = "Retrieving lab vitals for Emily Patterson... CBC shows elevated WBC count. [MASK]"
        response.confidence_score = 0.98
        response.masked = True
        response.sources = [
            DocumentInfo(filename="EMR Integration v2.1", department="general", content="Patient CBC data")
        ]

    # Scenario 3: Standard Retrieval
    elif "heparin" in user_query or "dosage" in user_query:
        response.answer = "The standard adult dosage protocol for Heparin (IV) is a bolus of 80 units/kg followed by an infusion of 18 units/kg/hr. Please re-verify against patient weight."
        response.confidence_score = 0.95
        response.sources = [
            DocumentInfo(filename="Clinical Guidelines 2025", department="general", content="Heparin IV protocol: 80 units/kg bolus, 18 units/kg/hr infusion.")
        ]
        
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mock_server:app", host="0.0.0.0", port=8001, reload=True)
