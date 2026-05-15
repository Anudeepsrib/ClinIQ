import logging
import re
import uuid

from app.security.vault import vault

logger = logging.getLogger(__name__)


class PIIManager:
    def __init__(self):
        self.analyzer = None
        try:
            from presidio_analyzer import AnalyzerEngine

            self.analyzer = AnalyzerEngine()
        except Exception as exc:
            logger.warning("Presidio analyzer unavailable; using regex PII fallback: %s", exc)

    def _generate_token(self, entity_type: str) -> str:
        # Generates a token like <PERSON_1234>
        # We use a UUID suffix to ensure uniqueness and mapped storage
        suffix = str(uuid.uuid4())[:8]
        return f"<{entity_type}_{suffix}>"

    def _analyze(self, text: str):
        results = []
        if self.analyzer is not None:
            results.extend(
                self.analyzer.analyze(
                    text=text,
                    entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "US_SSN"],
                    language="en",
                )
            )

        class RegexResult:
            def __init__(self, start: int, end: int, entity_type: str):
                self.start = start
                self.end = end
                self.entity_type = entity_type

        patterns = [
            ("EMAIL_ADDRESS", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
            ("US_SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
            ("PHONE_NUMBER", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
            ("PHONE_NUMBER", re.compile(r"\b\d{3}-\d{4}\b")),
            ("PERSON", re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")),
        ]
        occupied = [range(item.start, item.end) for item in results]
        for entity_type, pattern in patterns:
            for match in pattern.finditer(text):
                span = range(match.start(), match.end())
                if any(match.start() in existing or match.end() - 1 in existing for existing in occupied):
                    continue
                occupied.append(span)
                results.append(RegexResult(match.start(), match.end(), entity_type))
        return results

    def anonymize(self, text: str) -> str:
        if not text:
            return text

        results = self._analyze(text)
        sorted_results = sorted(results, key=lambda x: x.start, reverse=True)
        anonymized_text = list(text)

        for result in sorted_results:
            original_value = text[result.start : result.end]
            token = self._generate_token(result.entity_type)

            vault.store(token, original_value)
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
