import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

from app.security.pii import pii_manager

class TestPhase1(unittest.TestCase):

    def test_pii_redaction(self):
        print("\nTesting PII Redaction...")
        sample_text = "Patient John Doe (phone: 555-0123) has an appointment."
        anonymized = pii_manager.anonymize(sample_text)
        print(f"Original: {sample_text}")
        print(f"Anonymized: {anonymized}")
        
        self.assertNotEqual(sample_text, anonymized)
        self.assertIn("<PERSON_", anonymized)
        self.assertIn("<PHONE_NUMBER_", anonymized)
        self.assertNotIn("John Doe", anonymized)
        self.assertNotIn("555-0123", anonymized)
        print("PII Redaction Test Passed!")

    @patch('app.retrieval.vector_store.Chroma')
    @patch('app.retrieval.vector_store.OpenAIEmbeddings')
    def test_hybrid_search_structure(self, mock_embeddings, mock_chroma):
        print("\nTesting Hybrid Search Structure...")
        # Mock Chroma get to return some docs for BM25 init
        mock_db_instance = MagicMock()
        mock_chroma.return_value = mock_db_instance
        mock_db_instance.get.return_value = {
            'documents': ["doc1 content", "doc2 content"],
            'metadatas': [{"source": "s1"}, {"source": "s2"}]
        }
        mock_db_instance.as_retriever.return_value.invoke.return_value = [] # mock semantic search result
        
        from app.retrieval.vector_store import VectorStore
        
        # Initialize VectorStore (should trigger BM25 init)
        vs = VectorStore()
        
        # Verify BM25 is initialized
        self.assertIsNotNone(vs.bm25_retriever)
        print("BM25 Initialized successfully.")
        
        # Test hybrid search call
        results = vs.hybrid_search("query")
        # Since we mocked semantic search to return empty, and BM25 likewise (mocks don't inherently search),
        # we just want to ensure it runs without error.
        print("Hybrid Search called successfully.")

if __name__ == '__main__':
    unittest.main()
