from app.security.pii import pii_manager
from app.security.vault import vault


def test_vault_persistence():
    vault.store("test_token_1", "Secret Value")
    assert vault.get("test_token_1") == "Secret Value"
    assert vault.get("non_existent") is None

def test_pii_flow():
    original_text = "My name is John Doe and my email is john.doe@example.com."
    
    # 1. Anonymize
    anonymized = pii_manager.anonymize(original_text)
    
    print(f"\nOriginal: {original_text}")
    print(f"Anonymized: {anonymized}")
    
    # Assert redaction happened
    assert "John Doe" not in anonymized
    assert "john.doe@example.com" not in anonymized
    assert "<PERSON_" in anonymized
    assert "<EMAIL_ADDRESS_" in anonymized
    
    # 2. Deanonymize
    restored = pii_manager.deanonymize(anonymized)
    print(f"Restored: {restored}")
    
    # Assert restoration
    assert restored == original_text
