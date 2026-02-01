from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request, Header
from typing import List
from app.schemas.models import IngestResponse, QueryRequest, QueryResponse
from app.ingestion.loader_factory import LoaderFactory
from app.retrieval.vector_store import vector_store
from app.retrieval.graph import app_graph
from app.core.limiter import limiter

router = APIRouter()
loader_factory = LoaderFactory()

@router.post("/ingest", response_model=IngestResponse)
@limiter.limit("5/minute")
async def ingest_document(request: Request, file: UploadFile = File(...)):
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
@limiter.limit("5/minute")
async def query_documents(request: Request, request_body: QueryRequest, x_role: str = Header("public", alias="X-Role")):
    try:
        # Verify role (though we just read it for MVP behavior toggling)
        # In a real app, we'd check JWT permissions here.
        role = x_role.lower()
        
        inputs = {"question": request_body.question}
        result = await app_graph.ainvoke(inputs)
        
        # If output is empty (end edge hit or no generation), handle it
        answer = result.get("generation", "No relevant documents found in the database matching your query.")
        docs = result.get("documents", [])
        
        # RBAC & De-anonymization Logic
        if role == "doctor":
            from app.security.pii import pii_manager # Local import to avoid circular dependency if any
            answer = pii_manager.deanonymize(answer)
            # Optionally unmask source docs too
            for doc in docs:
                doc.page_content = pii_manager.deanonymize(doc.page_content)
        
        return QueryResponse(
            answer=answer,
            sources=docs
        )
    except Exception as e:
        print(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
