from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from app.schemas.models import IngestResponse, QueryRequest, QueryResponse
from app.ingestion.loader_factory import LoaderFactory
from app.retrieval.vector_store import vector_store
from app.retrieval.graph import app_graph

router = APIRouter()
loader_factory = LoaderFactory()

@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...)):
    try:
        content = await file.read()
        chunks = await loader_factory.process_file(content, file.filename, file.content_type)
        
        vector_store.add_chunks(chunks)
        
        return IngestResponse(
            file_id=file.filename, # Simple ID for MVP
            filename=file.filename,
            chunks_count=len(chunks)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error ingesting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    try:
        inputs = {"question": request.question}
        result = await app_graph.ainvoke(inputs)
        
        # If output is empty (end edge hit or no generation), handle it
        answer = result.get("generation", "No relevant documents found in the database matching your query.")
        docs = result.get("documents", [])
        
        return QueryResponse(
            answer=answer,
            sources=docs
        )
    except Exception as e:
        print(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
