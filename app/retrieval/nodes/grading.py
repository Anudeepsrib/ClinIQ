from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from app.retrieval.state import GraphState
from app.core.config import settings
from app.schemas.models import RetrievalResult

# Data model for grade
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(description="Documents are relevant to the question, 'yes' or 'no'")

def grade_documents(state: GraphState) -> Dict[str, Any]:
    """
    Determines whether the retrieved documents are relevant to the question
    
    Args:
        state (dict): The current graph state
        
    Returns:
        state (dict): Updates documents key with only relevant documents
    """
    print("---CHECK RELEVANCE---")
    question = state["question"]
    documents = state["documents"]
    
    # LLM with function call (structured output)
    llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=0, api_key=settings.OPENAI_API_KEY)
    structured_llm_grader = llm.with_structured_output(GradeDocuments)
    
    system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
    If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
    
    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
        ]
    )
    
    retrieval_grader = grade_prompt | structured_llm_grader
    
    filtered_docs = []
    for doc in documents:
        score = retrieval_grader.invoke({"question": question, "document": doc.content})
        grade = score.binary_score
        
        if grade == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(doc)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            
    return {"documents": filtered_docs, "question": question}
