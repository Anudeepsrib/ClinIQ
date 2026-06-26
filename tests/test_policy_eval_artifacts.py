import json
from pathlib import Path

EVAL_DIR = Path(__file__).parent / "evaluation"
CORPUS_DIR = EVAL_DIR / "policy_corpus"


def _load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_policy_corpus_manifest_documents_exist_and_include_expected_terms():
    manifest = json.loads((CORPUS_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["synthetic"] is True
    assert "No real patient data" in manifest["disclaimer"]

    for doc in manifest["documents"]:
        path = CORPUS_DIR / doc["filename"]
        assert path.exists(), f"Missing corpus document: {path}"

        text = path.read_text(encoding="utf-8").lower()
        assert doc["doc_id"].lower() in text
        assert "synthetic" in text
        for term in doc["expected_terms"]:
            assert term.lower() in text


def test_retrieval_dataset_targets_known_policy_documents():
    manifest = json.loads((CORPUS_DIR / "manifest.json").read_text(encoding="utf-8"))
    docs_by_id = {doc["doc_id"]: doc for doc in manifest["documents"]}
    rows = _load_jsonl(EVAL_DIR / "retrieval_eval_dataset.jsonl")

    assert rows
    for row in rows:
        assert row["expected_doc_ids"], f"{row['id']} has no expected documents"
        context = []
        for doc_id in row["expected_doc_ids"]:
            assert doc_id in docs_by_id
            context.append(
                (CORPUS_DIR / docs_by_id[doc_id]["filename"]).read_text(encoding="utf-8")
            )

        joined_context = "\n".join(context).lower()
        for term in row["expected_answer_terms"]:
            assert term.lower() in joined_context
        for unsupported in row["must_not_answer"]:
            assert unsupported


def test_retrieval_dataset_covers_required_demo_personas():
    rows = _load_jsonl(EVAL_DIR / "retrieval_eval_dataset.jsonl")
    personas = {row["persona"] for row in rows}
    assert {"nurse", "admin", "compliance_reviewer"}.issubset(personas)
