"""Semantic enrichment of rules using LLM."""

import logging
from typing import List, Dict, Optional
import numpy as np

from . import Rule


logger = logging.getLogger(__name__)


class LLMAdapter:
    """Base class for LLM adapters."""

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        raise NotImplementedError

    def generate_description(self, rule: Rule) -> str:
        """Generate human-readable description for rule."""
        raise NotImplementedError


class StubLLMAdapter(LLMAdapter):
    """Stub LLM for testing - generates deterministic embeddings."""

    def __init__(self):
        """Initialize stub LLM."""
        self.embedding_dim = 384  # Standard sentence transformer dimension

    def generate_embedding(self, text: str) -> List[float]:
        """Generate deterministic embedding based on text hash."""
        # Use text hash to generate deterministic but varied embeddings
        hash_val = hash(text)
        np.random.seed(hash_val % (2**32))

        # Generate random unit vector
        embedding = np.random.randn(self.embedding_dim)
        embedding = embedding / np.linalg.norm(embedding)

        return embedding.tolist()

    def generate_description(self, rule: Rule) -> str:
        """Generate simple description."""
        return rule.description


class AnthropicLLMAdapter(LLMAdapter):
    """Anthropic Claude adapter."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize Anthropic adapter."""
        try:
            from langchain_anthropic import ChatAnthropic

            self.client = ChatAnthropic(
                api_key=api_key,
                model=model,
                temperature=0.1
            )
            self.embedding_model = self._init_embedding_model()
        except Exception as e:
            logger.error(f"Error initializing Anthropic client: {e}")
            raise

    def _init_embedding_model(self):
        """Initialize embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f"Could not load sentence transformer: {e}")
            return None

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if self.embedding_model:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        else:
            # Fallback to stub
            return StubLLMAdapter().generate_embedding(text)

    def generate_description(self, rule: Rule) -> str:
        """Generate description using Claude."""
        try:
            prompt = f"""Analyze this business rule and provide a concise, clear description:

Rule Type: {rule.rule_type}
Expression: {rule.normalized_expression}
Source File: {rule.source.file_path}
Tables: {', '.join(rule.tables)}
Columns: {', '.join(rule.columns)}

Provide a 1-2 sentence business-friendly description of what this rule does."""

            response = self.client.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error generating description: {e}")
            return rule.description


class RuleEnricher:
    """Enrich rules with semantic information."""

    def __init__(self, config: Dict):
        """
        Initialize enricher.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.llm_adapter = self._create_llm_adapter()

    def _create_llm_adapter(self) -> LLMAdapter:
        """Create appropriate LLM adapter based on config."""
        llm_config = self.config.get("llm", {})
        provider = llm_config.get("provider", "stub")

        if provider == "stub":
            logger.info("Using stub LLM adapter")
            return StubLLMAdapter()
        elif provider == "anthropic":
            import os
            api_key = os.getenv(llm_config.get("api_key_env", "ANTHROPIC_API_KEY"))
            if not api_key:
                logger.warning("Anthropic API key not found, falling back to stub")
                return StubLLMAdapter()

            model = llm_config.get("model", "claude-3-5-sonnet-20241022")
            logger.info(f"Using Anthropic adapter with model {model}")
            return AnthropicLLMAdapter(api_key, model)
        else:
            logger.warning(f"Unknown LLM provider {provider}, using stub")
            return StubLLMAdapter()

    def enrich_rules(self, rules: List[Rule]) -> List[Rule]:
        """
        Enrich rules with embeddings and enhanced descriptions.

        Args:
            rules: List of rules to enrich

        Returns:
            List of enriched rules
        """
        logger.info(f"Enriching {len(rules)} rules")

        enriched = []
        for i, rule in enumerate(rules):
            try:
                enriched_rule = self.enrich_rule(rule)
                enriched.append(enriched_rule)

                if (i + 1) % 50 == 0:
                    logger.info(f"Enriched {i + 1}/{len(rules)} rules")
            except Exception as e:
                logger.error(f"Error enriching rule {rule.id}: {e}")
                enriched.append(rule)

        return enriched

    def enrich_rule(self, rule: Rule) -> Rule:
        """
        Enrich a single rule.

        Args:
            rule: Rule to enrich

        Returns:
            Enriched rule
        """
        # Generate embedding
        if rule.embedding is None:
            text_for_embedding = self._create_embedding_text(rule)
            rule.embedding = self.llm_adapter.generate_embedding(text_for_embedding)

        # Enhance description if enabled
        if self.config.get("enrichment", {}).get("enable_semantic_analysis", True):
            if isinstance(self.llm_adapter, AnthropicLLMAdapter):
                rule.description = self.llm_adapter.generate_description(rule)

        # Map to domain concepts
        if self.config.get("enrichment", {}).get("enable_domain_mapping", True):
            rule.metadata["domain_concepts"] = self._map_domain_concepts(rule)

        return rule

    def _create_embedding_text(self, rule: Rule) -> str:
        """Create text representation for embedding."""
        parts = [
            rule.description,
            rule.normalized_expression,
            " ".join(rule.tables),
            " ".join(rule.columns)
        ]
        return " | ".join([p for p in parts if p])

    def _map_domain_concepts(self, rule: Rule) -> List[str]:
        """Map rule to domain concepts."""
        concepts = []

        # Simple heuristic mapping based on keywords
        text = (rule.description + " " + rule.normalized_expression).lower()

        domain_keywords = {
            "pricing": ["price", "cost", "amount", "discount", "rate", "fee", "charge"],
            "eligibility": ["eligible", "qualify", "valid", "approved", "authorized"],
            "customer": ["customer", "client", "user", "account"],
            "order": ["order", "purchase", "transaction", "sale"],
            "inventory": ["inventory", "stock", "quantity", "available"],
            "payment": ["payment", "paid", "balance", "due", "invoice"],
            "date": ["date", "time", "period", "expiry", "deadline"],
            "validation": ["check", "validate", "verify", "ensure", "must"],
        }

        for concept, keywords in domain_keywords.items():
            if any(keyword in text for keyword in keywords):
                concepts.append(concept)

        return concepts
