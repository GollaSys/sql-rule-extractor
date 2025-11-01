"""Tests for rule clusterer."""

import pytest
import numpy as np
from src.extractor.clusterer import RuleClusterer
from src.extractor import Rule, RuleType, SourceLocation


class TestRuleClusterer:
    """Test rule clustering."""

    def setup_method(self):
        """Setup test fixtures."""
        self.config = {
            "clustering": {
                "method": "kmeans",
                "n_clusters": 2
            }
        }
        self.clusterer = RuleClusterer(self.config)

    def create_rule(self, rule_id, description, embedding=None):
        """Helper to create test rule."""
        if embedding is None:
            # Generate random embedding
            np.random.seed(hash(rule_id) % 2**32)
            embedding = np.random.randn(384).tolist()

        return Rule(
            id=rule_id,
            rule_type=RuleType.CONDITIONAL,
            description=description,
            normalized_expression=f"test_{rule_id}",
            variables=[],
            embedding=embedding,
            source=SourceLocation(
                file_path="test.sql",
                start_line=1,
                end_line=1,
                snippet="test"
            ),
            metadata={"domain_concepts": ["pricing"]}
        )

    def test_cluster_with_kmeans(self):
        """Test K-means clustering."""
        # Create rules with embeddings
        rules = [
            self.create_rule("r1", "pricing rule 1"),
            self.create_rule("r2", "pricing rule 2"),
            self.create_rule("r3", "eligibility rule 1"),
            self.create_rule("r4", "eligibility rule 2"),
        ]

        groups = self.clusterer.cluster_rules(rules)

        # Should create groups
        assert len(groups) > 0
        assert len(groups) <= self.config["clustering"]["n_clusters"]

        # All rules should be assigned
        total_rules = sum(len(g.rules) for g in groups)
        assert total_rules == len(rules)

    def test_cluster_without_embeddings(self):
        """Test clustering fallback without embeddings."""
        rules = [
            Rule(
                id="r1",
                rule_type=RuleType.CONDITIONAL,
                description="Test",
                normalized_expression="test",
                variables=[],
                embedding=None,  # No embedding
                source=SourceLocation(
                    file_path="test1.sql",
                    start_line=1,
                    end_line=1,
                    snippet="test"
                )
            ),
            Rule(
                id="r2",
                rule_type=RuleType.VALIDATION,
                description="Test",
                normalized_expression="test",
                variables=[],
                embedding=None,
                source=SourceLocation(
                    file_path="test1.sql",
                    start_line=2,
                    end_line=2,
                    snippet="test"
                )
            ),
        ]

        groups = self.clusterer.cluster_rules(rules)

        # Should use metadata-based grouping
        assert len(groups) > 0

    def test_empty_rules(self):
        """Test clustering with empty rule list."""
        groups = self.clusterer.cluster_rules([])
        assert len(groups) == 0

    def test_single_rule(self):
        """Test clustering with single rule."""
        rules = [self.create_rule("r1", "test rule")]

        groups = self.clusterer.cluster_rules(rules)

        assert len(groups) == 1
        assert len(groups[0].rules) == 1

    def test_group_attributes(self):
        """Test that groups have required attributes."""
        rules = [
            self.create_rule("r1", "pricing rule"),
            self.create_rule("r2", "pricing rule"),
        ]

        groups = self.clusterer.cluster_rules(rules)

        assert len(groups) > 0
        group = groups[0]

        # Check required attributes
        assert group.id is not None
        assert group.name is not None
        assert group.description is not None
        assert group.category is not None
        assert 0 <= group.confidence <= 1
        assert len(group.rules) > 0

    def test_infer_category(self):
        """Test category inference from domain concepts."""
        rules = [
            self.create_rule("r1", "pricing rule 1"),
            self.create_rule("r2", "pricing rule 2"),
        ]

        # Set domain concepts
        for rule in rules:
            rule.metadata["domain_concepts"] = ["pricing", "discount"]

        groups = self.clusterer.cluster_rules(rules)

        assert len(groups) > 0
        # Category should be inferred from domain concepts
        assert groups[0].category is not None
