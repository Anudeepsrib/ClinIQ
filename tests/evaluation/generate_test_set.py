from ragas.testset.generator import TestsetGenerator
from ragas.testset.evolutions import simple, reasoning, multi_context
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader
from app.core.config import settings
import os

# Initialize models
generator_llm = ChatOpenAI(model="gpt-3.5-turbo-16k")
critic_llm = ChatOpenAI(model="gpt-4")
embeddings = OpenAIEmbeddings()

generator = TestsetGenerator.from_langchain(
    generator_llm,
    critic_llm,
    embeddings
)

def generate_test_set():
    print("Loading documents from", settings.DOCS_DIRECTORY)
    loader = DirectoryLoader(settings.DOCS_DIRECTORY)
    documents = loader.load()
    
    print(f"Loaded {len(documents)} documents. Generating test set...")
    
    # Generate test set
    testset = generator.generate_with_langchain_docs(
        documents,
        test_size=10,
        distributions={simple: 0.5, reasoning: 0.25, multi_context: 0.25}
    )
    
    output_file = "tests/evaluation/test_set.csv"
    testset.to_pandas().to_csv(output_file, index=False)
    print(f"Test set generated and saved to {output_file}")

if __name__ == "__main__":
    generate_test_set()
