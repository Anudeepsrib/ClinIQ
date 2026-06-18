from langchain_community.document_loaders import DirectoryLoader

from app.chat.llm_provider import get_chat_model
from app.core.config import settings
from app.retrieval.gemini_embeddings import gemini_embeddings

try:
    from ragas.testset.evolutions import multi_context, reasoning, simple
    from ragas.testset.generator import TestsetGenerator
except ImportError as exc:
    raise SystemExit(
        "Optional RAGAS evaluation dependencies are not installed. "
        "Install a patched RAGAS release before running this script."
    ) from exc

# Use the same configured provider family as the app.
generator_llm = get_chat_model(temperature=0.4)
critic_llm = get_chat_model(temperature=0)
embeddings = gemini_embeddings

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
