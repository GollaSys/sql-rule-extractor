"""Rule normalization and canonicalization."""

import re
from typing import List, Dict
import logging

from . import Rule


logger = logging.getLogger(__name__)


class RuleNormalizer:
    """Normalize and canonicalize extracted rules."""

    def normalize_rules(self, rules: List[Rule]) -> List[Rule]:
        """
        Normalize a list of rules.

        Args:
            rules: List of raw extracted rules

        Returns:
            List of normalized rules
        """
        normalized = []

        for rule in rules:
            try:
                normalized_rule = self.normalize_rule(rule)
                normalized.append(normalized_rule)
            except Exception as e:
                logger.error(f"Error normalizing rule {rule.id}: {e}")
                # Keep original rule if normalization fails
                normalized.append(rule)

        return normalized

    def normalize_rule(self, rule: Rule) -> Rule:
        """
        Normalize a single rule.

        Args:
            rule: Rule to normalize

        Returns:
            Normalized rule
        """
        # Normalize the expression
        normalized_expr = self._normalize_expression(rule.normalized_expression)

        # Standardize variable names
        variables = self._standardize_identifiers(rule.variables)
        columns = self._standardize_identifiers(rule.columns)
        tables = self._standardize_identifiers(rule.tables)

        # Create updated rule
        rule.normalized_expression = normalized_expr
        rule.variables = variables
        rule.columns = columns
        rule.tables = tables

        return rule

    def _normalize_expression(self, expression: str) -> str:
        """Normalize a rule expression."""
        # Use placeholders to protect multi-char operators
        normalized = expression.replace('==', '§EQ§')
        normalized = normalized.replace('>=', '§GE§')
        normalized = normalized.replace('<=', '§LE§')
        normalized = normalized.replace('!=', '§NE§')

        # Now replace single-char operators
        normalized = normalized.replace('=', ' = ')
        normalized = normalized.replace('>', ' > ')
        normalized = normalized.replace('<', ' < ')

        # Restore multi-char operators with proper spacing
        normalized = normalized.replace('§EQ§', ' = ')
        normalized = normalized.replace('§GE§', ' >= ')
        normalized = normalized.replace('§LE§', ' <= ')
        normalized = normalized.replace('§NE§', ' != ')

        # Now collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        # Standardize logical operators
        normalized = re.sub(r'\bAND\b', 'AND', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\bOR\b', 'OR', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\bNOT\b', 'NOT', normalized, flags=re.IGNORECASE)

        # Remove extra spaces around parentheses
        normalized = re.sub(r'\s*\(\s*', '(', normalized)
        normalized = re.sub(r'\s*\)\s*', ')', normalized)

        return normalized

    def _standardize_identifiers(self, identifiers: List[str]) -> List[str]:
        """Standardize identifier names."""
        standardized = []

        for identifier in identifiers:
            # Convert to lowercase for consistency
            std = identifier.lower().strip()

            # Remove quotes
            std = std.strip('"\'`')

            if std:
                standardized.append(std)

        return list(set(standardized))

    def deduplicate_rules(self, rules: List[Rule]) -> List[Rule]:
        """
        Remove duplicate rules based on normalized expression.

        Args:
            rules: List of rules

        Returns:
            Deduplicated list of rules
        """
        seen = {}
        unique_rules = []

        for rule in rules:
            # Create a fingerprint based on normalized expression and location
            fingerprint = (
                rule.normalized_expression,
                rule.source.file_path,
                rule.source.start_line
            )

            if fingerprint not in seen:
                seen[fingerprint] = True
                unique_rules.append(rule)
            else:
                logger.debug(f"Skipping duplicate rule: {rule.id}")

        logger.info(f"Deduplicated {len(rules)} rules to {len(unique_rules)} unique rules")
        return unique_rules

    def merge_similar_rules(self, rules: List[Rule], similarity_threshold: float = 0.9) -> List[Rule]:
        """
        Merge very similar rules (optional post-processing).

        Args:
            rules: List of rules
            similarity_threshold: Threshold for merging

        Returns:
            List with similar rules merged
        """
        # For now, just return rules as-is
        # Can be enhanced with semantic similarity comparison
        return rules

    def filter_low_quality_rules(self, rules: List[Rule], min_confidence: float = 0.5) -> List[Rule]:
        """
        Filter out low-quality rules.

        Args:
            rules: List of rules
            min_confidence: Minimum confidence threshold

        Returns:
            Filtered list of rules
        """
        filtered = [rule for rule in rules if rule.confidence >= min_confidence]

        logger.info(f"Filtered {len(rules)} rules to {len(filtered)} high-quality rules")
        return filtered
