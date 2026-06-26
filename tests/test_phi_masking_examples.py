import json
from pathlib import Path

from app.security.pii import pii_manager

EXAMPLES_PATH = Path(__file__).parent / "evaluation" / "phi_masking_examples.json"


def test_phi_masking_examples_anonymize_and_restore():
    examples = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))["examples"]
    assert examples

    for example in examples:
        anonymized = pii_manager.anonymize(example["input"])

        for raw_value in example["must_mask"]:
            assert raw_value not in anonymized, example["id"]
        for token_prefix in example["expected_token_prefixes"]:
            assert token_prefix in anonymized, example["id"]
        for preserved_text in example["must_preserve"]:
            assert preserved_text in anonymized, example["id"]

        assert pii_manager.deanonymize(anonymized) == example["input"]
