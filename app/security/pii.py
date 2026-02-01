from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from app.security.vault import vault
import uuid

class PIIManager:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

    def _generate_token(self, entity_type: str) -> str:
        # Generates a token like <PERSON_1234>
        # We use a UUID suffix to ensure uniqueness and mapped storage
        suffix = str(uuid.uuid4())[:8]
        return f"<{entity_type}_{suffix}>"

    def anonymize(self, text: str) -> str:
        # 1. Analyze
        results = self.analyzer.analyze(text=text, entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "US_SSN"], language='en')
        
        # 2. Custom Token Logic
        # Presidio's default replacement doesn't easily return the mapping *out*.
        # So we will iterate and build our own simple replacement for now, 
        # or use a custom operator.
        
        # To keep it robust, let's use a manual replacement loop based on analysis results
        # sorted by start index to handle offsets correctly.
        
        sorted_results = sorted(results, key=lambda x: x.start, reverse=True)
        
        anonymized_text = list(text)
        
        for result in sorted_results:
            original_value = text[result.start : result.end]
            token = self._generate_token(result.entity_type)
            
            # Store in Vault
            vault.store(token, original_value)
            
            # Replace in text
            anonymized_text[result.start : result.end] = list(token)
            
        return "".join(anonymized_text)

    def deanonymize(self, text: str) -> str:
        # Provides a simple string replacement based on finding tokens.
        # This is a naive implementation but sufficient for our Vault strategy.
        # We assume tokens format <ENTITY_SUFFIX>.
        
        import re
        
        # Find all things that look like our tokens
        # Pattern: <[A-Z_]+_[a-f0-9]{8}>
        pattern = r"<[A-Z_]+_[a-f0-9]{8}>"
        
        def replace_match(match):
            token = match.group(0)
            original = vault.get(token)
            return original if original else token
            
        return re.sub(pattern, replace_match, text)

pii_manager = PIIManager()
