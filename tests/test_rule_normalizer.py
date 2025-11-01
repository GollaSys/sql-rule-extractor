"""Tests for rule normalizer."""

import pytest
from src.extractor.rule_normalizer import RuleNormalizer
from src.extractor import Rule, RuleType, SourceLocation


class TestRuleNormalizer:
    """Test rule normalization."""

    def setup_method(self):
        """Setup test fixtures."""
        self.normalizer = RuleNormalizer()

    def test_normalize_expression(self):
        """Test expression normalization."""
        rule = Rule(
            id="test_1",
            rule_type=RuleType.CONDITIONAL,
            description="Test rule",
            normalized_expression="total    >   100   AND   status  =  'active'",
            variables=["total", "status"],
            source=SourceLocation(
                file_path="test.sql",
                start_line=1,
                end_line=1,
                snippet="test"
            )
        )

        normalized = self.normalizer.normalize_rule(rule)

        # Should normalize whitespace
        assert "  " not in normalized.normalized_expression
        assert " > " in normalized.normalized_expression
        assert " AND " in normalized.normalized_expression

    def test_standardize_identifiers(self):
        """Test identifier standardization."""
        rule = Rule(
            id="test_1",
            rule_type=RuleType.CONDITIONAL,
            description="Test rule",
            normalized_expression="TOTAL > 100",
            variables=["TOTAL", "Total", '"total"'],
            columns=["CUSTOMER_ID", "customer_id"],
            tables=["ORDERS", "orders"],
            source=SourceLocation(
                file_path="test.sql",
                start_line=1,
                end_line=1,
                snippet="test"
            )
        )

        normalized = self.normalizer.normalize_rule(rule)

        # Should lowercase and deduplicate
        assert "total" in normalized.variables
        assert len([v for v in normalized.variables if v.lower() == "total"]) == 1

    def test_deduplicate_rules(self):
        """Test rule deduplication."""
        rules = [
            Rule(
                id="test_1",
                rule_type=RuleType.CONDITIONAL,
                description="Test",
                normalized_expression="total > 100",
                variables=[],
                source=SourceLocation(
                    file_path="test.sql",
                    start_line=1,
                    end_line=1,
                    snippet="test"
                )
            ),
            Rule(
                id="test_2",
                rule_type=RuleType.CONDITIONAL,
                description="Test",
                normalized_expression="total > 100",  # Same expression
                variables=[],
                source=SourceLocation(
                    file_path="test.sql",
                    start_line=1,
                    end_line=1,
                    snippet="test"
                )
            ),
            Rule(
                id="test_3",
                rule_type=RuleType.CONDITIONAL,
                description="Test",
                normalized_expression="total > 200",  # Different expression
                variables=[],
                source=SourceLocation(
                    file_path="test.sql",
                    start_line=2,
                    end_line=2,
                    snippet="test"
                )
            ),
        ]

        unique_rules = self.normalizer.deduplicate_rules(rules)

        # Should remove duplicate
        assert len(unique_rules) == 2

    def test_filter_low_quality_rules(self):
        """Test filtering low-quality rules."""
        rules = [
            Rule(
                id="test_1",
                rule_type=RuleType.CONDITIONAL,
                description="High quality",
                normalized_expression="total > 100",
                variables=[],
                confidence=0.9,
                source=SourceLocation(
                    file_path="test.sql",
                    start_line=1,
                    end_line=1,
                    snippet="test"
                )
            ),
            Rule(
                id="test_2",
                rule_type=RuleType.CONDITIONAL,
                description="Low quality",
                normalized_expression="x = y",
                variables=[],
                confidence=0.3,
                source=SourceLocation(
                    file_path="test.sql",
                    start_line=2,
                    end_line=2,
                    snippet="test"
                )
            ),
        ]

        filtered = self.normalizer.filter_low_quality_rules(rules, min_confidence=0.5)

        # Should keep only high confidence
        assert len(filtered) == 1
        assert filtered[0].confidence >= 0.5

    def test_normalize_comparison_operators(self):
        """Test normalization of comparison operators."""
        rule = Rule(
            id="test_1",
            rule_type=RuleType.CONDITIONAL,
            description="Test",
            normalized_expression="total==100 AND price>=50",
            variables=[],
            source=SourceLocation(
                file_path="test.sql",
                start_line=1,
                end_line=1,
                snippet="test"
            )
        )

        normalized = self.normalizer.normalize_rule(rule)

        # Should normalize == to = and add spaces
        assert " = " in normalized.normalized_expression
        assert " >= " in normalized.normalized_expression
