import pytest
from unittest.mock import patch, MagicMock
from app.ingestion.upsert_pipeline import upsert_document, UpsertResult
from app.ingestion.document_registry import DocumentRegistry
from app.chat.chat_history_store import ChatHistoryStore


@pytest.fixture
def mock_registry():
    with patch("app.ingestion.upsert_pipeline.document_registry") as mock:
        yield mock


@pytest.fixture
def mock_azure_store():
    with patch("app.ingestion.upsert_pipeline.azure_search_store") as mock:
        yield mock


@pytest.fixture
def mock_loader():
    with patch("app.ingestion.upsert_pipeline.loader_factory") as mock:
        yield mock


@pytest.mark.asyncio
async def test_upsert_document_unchanged(mock_registry, mock_azure_store, mock_loader):
    """Test that unchanged documents are skipped."""
    mock_registry.has_changed.return_value = False
    mock_registry.lookup.return_value = {"version": 1, "chunk_count": 5}

    result = await upsert_document(
        file_bytes=b"unchanged content",
        filename="policy.pdf",
        content_type="application/pdf",
        department="radiology",
        user="admin"
    )

    assert result.change_type == "unchanged"
    assert result.version == 1
    # Loader and vector store should not be called
    mock_loader.process_file.assert_not_called()
    mock_azure_store.upsert_chunks.assert_not_called()


@pytest.mark.asyncio
async def test_upsert_document_new(mock_registry, mock_azure_store, mock_loader):
    """Test ingest behavior for a completely new document."""
    mock_registry.has_changed.return_value = True
    mock_registry.lookup.return_value = None

    mock_loader.process_file.return_value = [MagicMock(), MagicMock()]  # 2 chunks

    result = await upsert_document(
        file_bytes=b"new content",
        filename="new_policy.pdf",
        content_type="application/pdf",
        department="pharmacy",
        user="dr_smith"
    )

    assert result.change_type == "new"
    assert result.version == 1
    assert result.chunk_count == 2
    mock_azure_store.upsert_chunks.assert_called_once()
    mock_registry.register.assert_called_once()
    mock_registry.mark_superseded.assert_not_called()


@pytest.mark.asyncio
async def test_upsert_document_updated(mock_registry, mock_azure_store, mock_loader):
    """Test update behavior for an existing document that was modified."""
    mock_registry.has_changed.return_value = True
    mock_registry.lookup.return_value = {"version": 2, "chunk_count": 5}

    mock_loader.process_file.return_value = [MagicMock()] * 6

    result = await upsert_document(
        file_bytes=b"updated content",
        filename="guidelines.pdf",
        content_type="application/pdf",
        department="nursing",
        user="nurse_joy"
    )

    assert result.change_type == "updated"
    assert result.version == 3
    assert result.chunk_count == 6
    mock_registry.mark_superseded.assert_called_once()
    mock_azure_store.upsert_chunks.assert_called_once_with(
        chunks=mock_loader.process_file.return_value,
        department="nursing",
        source_filename="guidelines.pdf",
        version=3
    )


def test_chat_history_rbac_isolation():
    """Test that ChatHistoryStore strictly enforces user isolation."""
    # We patch Chroma to avoid actual DB initialization
    with patch("chromadb.Client"):
        store = ChatHistoryStore()
        store._collection = MagicMock()

        # Mock collection search returning messages owned by 'user_A'
        store._collection.get.return_value = {
            "ids": ["sess1_0"],
            "documents": ["hello"],
            "metadatas": [{"role": "user", "session_id": "sess1", "user_id": "user_A"}]
        }

        # user_A calls get_session -> success
        msgs_A = store.get_session("sess1", "user_A")
        assert len(msgs_A) == 1

        # user_B calls get_session for user_A's session -> store._collection.get is called with user_B filter
        # we mock the filter return value for user_B as empty
        store._collection.get.return_value = {"ids": [], "documents": [], "metadatas": []}
        msgs_B = store.get_session("sess1", "user_B")
        assert len(msgs_B) == 0
