from app.retrieval.state import GraphState
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings

def generate(state: GraphState):
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]
    
    if not documents:
        return {"generation": "I could not find any relevant information in the provided policy documents to answer your question."}
    
    # Format context with citations
    context = ""
    for i, doc in enumerate(documents):
         # doc.source is filename, metadata has sheet/page
         citation_loc = f"Page {doc.page}" if doc.page else f"Sheet {doc.metadata.get('sheet_name', 'N/A')}"
         context += f"[Ref {i+1}]: Source: {doc.source}, {citation_loc}\nContent: {doc.content}\n\n"

    template = """You are a helpful healthcare assistant representing an enterprise policy system.
    Use the following pieces of retrieved context to answer the question. 
    Do not use any outside knowledge. 
    If the answer is not in the context, say that you don't know.
    
    IMPORTANT: 
    1. You must cite your sources. Use [Ref X] notation.
    2. Do NOT provide medical advice. This is for policy/administrative information only.
    3. Ensure no real patient PHI is generated. If the context contains what looks like PHI, redaction is needed, but assuming input is clean, just focus on policy.
    
    Context:
    {context}
    
    Question: {question}
    
    Answer:"""
    
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=0, apy_key=settings.OPENAI_API_KEY)
    
    rag_chain = prompt | llm | StrOutputParser()
    
    generation = rag_chain.invoke({"context": context, "question": question})
    return {"generation": generation}
