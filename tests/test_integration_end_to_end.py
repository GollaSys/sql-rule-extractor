"""End-to-end integration tests."""

import pytest
import os
from pathlib import Path
import tempfile
from lxml import etree as ET

from src.extractor.ingest import RepositoryIngestor
from src.extractor.rule_normalizer import RuleNormalizer
from src.extractor.enricher import RuleEnricher
from src.extractor.clusterer import RuleClusterer
from src.extractor.drd_generator import DRDGenerator
from src.extractor import DecisionModel, RuleDependency


class TestEndToEnd:
    """End-to-end integration tests."""

    def setup_method(self):
        """Setup test configuration."""
        self.config = {
            "llm": {
                "provider": "stub"
            },
            "clustering": {
                "method": "kmeans",
                "n_clusters": 3
            },
            "parsing": {
                "sql_dialects": ["postgres"],
                "max_file_size_mb": 10,
                "file_extensions": {
                    "sql": [".sql"],
                    "python": [".py"]
                },
                "ignore_patterns": []
            },
            "output": {
                "include_snippets": True,
                "pretty_print_xml": True
            },
            "dmn": {
                "namespace": "http://test/dmn",
                "exporter": "Test",
                "exporter_version": "1.0",
                "include_extensions": True,
                "decision_prefix": "Decision_",
                "input_data_prefix": "InputData_"
            },
            "enrichment": {
                "enable_domain_mapping": True,
                "enable_semantic_analysis": False
            },
            "logging": {
                "level": "INFO"
            }
        }

    def test_full_pipeline_sample_repo(self):
        """Test full pipeline on sample repository."""
        # Get sample repo path
        sample_repo = Path(__file__).parent.parent / "sample_repos" / "sample_sql_app"

        if not sample_repo.exists():
            pytest.skip("Sample repository not found")

        # Step 1: Ingest
        ingestor = RepositoryIngestor(self.config)
        rules = ingestor.ingest_repository(str(sample_repo))

        # Should extract rules from sample repo
        assert len(rules) > 0, "No rules extracted from sample repository"

        # Should have different rule types
        rule_types = set(r.rule_type for r in rules)
        assert len(rule_types) > 0

        # Step 2: Normalize
        normalizer = RuleNormalizer()
        rules = normalizer.normalize_rules(rules)
        rules = normalizer.deduplicate_rules(rules)

        assert len(rules) > 0

        # Step 3: Enrich
        enricher = RuleEnricher(self.config)
        rules = enricher.enrich_rules(rules)

        # All rules should have embeddings
        assert all(r.embedding is not None for r in rules)

        # Step 4: Cluster
        clusterer = RuleClusterer(self.config)
        groups = clusterer.cluster_rules(rules)

        assert len(groups) > 0
        # All rules should be in groups
        total_rules = sum(len(g.rules) for g in groups)
        assert total_rules == len(rules)

        # Step 5: Build decision model
        dependencies = []
        decision_model = DecisionModel(
            rules=rules,
            groups=groups,
            dependencies=dependencies
        )

        # Step 6: Generate DRD
        generator = DRDGenerator(self.config)
        dmn_xml = generator.generate_drd(decision_model)

        # Should generate valid XML
        assert dmn_xml is not None
        assert len(dmn_xml) > 0
        assert '<?xml' in dmn_xml
        assert 'definitions' in dmn_xml

        # Validate XML structure
        root = ET.fromstring(dmn_xml.encode('utf-8'))
        assert root is not None

        # Check for decision elements
        ns = {"dmn": "https://www.omg.org/spec/DMN/20191111/MODEL/"}
        decisions = root.findall(".//dmn:decision", ns)
        assert len(decisions) > 0, "No decision elements found in DMN"

        # Step 7: Generate markdown report
        markdown = generator.generate_markdown_report(decision_model)
        assert markdown is not None
        assert "Business Rules Report" in markdown
        assert str(len(rules)) in markdown

    def test_specific_rule_extraction(self):
        """Test that specific known rules are extracted correctly."""
        # Create temp file with known SQL
        with tempfile.TemporaryDirectory() as tmpdir:
            sql_file = Path(tmpdir) / "test.sql"
            sql_content = """
            CREATE FUNCTION calc_discount(total NUMERIC) RETURNS NUMERIC AS $$
            BEGIN
              IF total > 1000 THEN
                RETURN total * 0.1;
              ELSIF total > 500 THEN
                RETURN total * 0.05;
              ELSE
                RETURN 0;
              END IF;
            END;
            $$ LANGUAGE plpgsql;
            """
            sql_file.write_text(sql_content)

            # Ingest
            ingestor = RepositoryIngestor(self.config)
            rules = ingestor.ingest_repository(tmpdir)

            # Should extract at least 1 rule
            assert len(rules) >= 1

            # Check for discount calculation rules - should find the 1000 threshold
            rule_texts = [r.normalized_expression.lower() for r in rules]
            assert any('1000' in text for text in rule_texts)

    def test_traceability_in_dmn(self):
        """Test that DMN includes traceability information."""
        sample_repo = Path(__file__).parent.parent / "sample_repos" / "sample_sql_app"

        if not sample_repo.exists():
            pytest.skip("Sample repository not found")

        # Run pipeline
        ingestor = RepositoryIngestor(self.config)
        rules = ingestor.ingest_repository(str(sample_repo))

        normalizer = RuleNormalizer()
        rules = normalizer.normalize_rules(rules)
        rules = normalizer.deduplicate_rules(rules)[:10]  # Limit for speed

        enricher = RuleEnricher(self.config)
        rules = enricher.enrich_rules(rules)

        clusterer = RuleClusterer(self.config)
        groups = clusterer.cluster_rules(rules)

        decision_model = DecisionModel(
            rules=rules,
            groups=groups,
            dependencies=[]
        )

        generator = DRDGenerator(self.config)
        dmn_xml = generator.generate_drd(decision_model)

        # Parse XML and check for traceability
        root = ET.fromstring(dmn_xml.encode('utf-8'))
        ns = {
            "dmn": "https://www.omg.org/spec/DMN/20191111/MODEL/",
            "ext": "http://test/dmn"
        }

        # Find extension elements with traceability
        traceability = root.findall(".//ext:traceability", ns)
        assert len(traceability) > 0, "No traceability information found"

        # Check for source elements
        sources = root.findall(".//ext:source", ns)
        assert len(sources) > 0, "No source elements found"

        # Verify source attributes
        source = sources[0]
        assert source.get("ruleId") is not None
        assert source.get("file") is not None
        assert source.get("startLine") is not None
        assert source.get("endLine") is not None

    def test_statistics_generation(self):
        """Test that statistics are correctly generated."""
        sample_repo = Path(__file__).parent.parent / "sample_repos" / "sample_sql_app"

        if not sample_repo.exists():
            pytest.skip("Sample repository not found")

        ingestor = RepositoryIngestor(self.config)
        rules = ingestor.ingest_repository(str(sample_repo))

        stats = ingestor.get_statistics(rules)

        # Check statistics structure
        assert "total_rules" in stats
        assert "by_type" in stats
        assert "by_file" in stats
        assert "unique_tables" in stats
        assert "unique_columns" in stats

        # Verify counts
        assert stats["total_rules"] == len(rules)
        assert stats["unique_tables"] >= 0
        assert stats["unique_columns"] >= 0

    def test_dmn_validation(self):
        """Test that generated DMN is well-formed XML."""
        # Create minimal decision model
        from src.extractor import Rule, RuleGroup, RuleType, SourceLocation

        rule = Rule(
            id="test_rule",
            rule_type=RuleType.CONDITIONAL,
            description="Test rule",
            normalized_expression="x > 10",
            variables=["x"],
            tables=[],
            columns=[],
            source=SourceLocation(
                file_path="test.sql",
                start_line=1,
                end_line=1,
                snippet="x > 10"
            ),
            embedding=[0.1] * 384
        )

        group = RuleGroup(
            id="test_group",
            name="Test Group",
            description="Test group",
            rules=[rule],
            category="Test",
            confidence=0.9
        )

        model = DecisionModel(
            rules=[rule],
            groups=[group],
            dependencies=[]
        )

        generator = DRDGenerator(self.config)
        dmn_xml = generator.generate_drd(model)

        # Should parse as valid XML
        try:
            root = ET.fromstring(dmn_xml.encode('utf-8'))
            assert root is not None
        except ET.XMLSyntaxError as e:
            pytest.fail(f"Generated DMN is not valid XML: {e}")
