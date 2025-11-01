"""Example usage of SQL Rule Extractor programmatically."""

from pathlib import Path

from src.extractor.ingest import RepositoryIngestor
from src.extractor.rule_normalizer import RuleNormalizer
from src.extractor.enricher import RuleEnricher
from src.extractor.clusterer import RuleClusterer
from src.extractor.drd_generator import DRDGenerator
from src.extractor import DecisionModel, RuleDependency
from src.utils.io import load_config, save_json, save_text
from src.utils.logging import setup_logging


def main():
    """Run example analysis."""
    print("=" * 60)
    print("SQL Rule Extractor - Programmatic Example")
    print("=" * 60)
    print()

    # Setup logging
    setup_logging(level="INFO")

    # Load configuration
    config = load_config("config.yml")

    # Path to sample repository
    sample_repo = Path(__file__).parent / "sample_repos" / "sample_sql_app"

    if not sample_repo.exists():
        print(f"Error: Sample repository not found at {sample_repo}")
        return

    print(f"Analyzing repository: {sample_repo}")
    print()

    # Step 1: Ingest repository
    print("Step 1: Ingesting repository...")
    ingestor = RepositoryIngestor(config)
    rules = ingestor.ingest_repository(str(sample_repo))
    print(f"✓ Extracted {len(rules)} rules")
    print()

    # Show some statistics
    stats = ingestor.get_statistics(rules)
    print("Rule Statistics:")
    print(f"  Total rules: {stats['total_rules']}")
    print(f"  Unique tables: {stats['unique_tables']}")
    print(f"  Unique columns: {stats['unique_columns']}")
    print("  By type:")
    for rule_type, count in stats['by_type'].items():
        print(f"    {rule_type}: {count}")
    print()

    # Step 2: Normalize rules
    print("Step 2: Normalizing rules...")
    normalizer = RuleNormalizer()
    rules = normalizer.normalize_rules(rules)
    rules = normalizer.deduplicate_rules(rules)
    rules = normalizer.filter_low_quality_rules(rules, min_confidence=0.6)
    print(f"✓ Normalized to {len(rules)} unique rules")
    print()

    # Step 3: Enrich rules
    print("Step 3: Enriching rules with embeddings...")
    enricher = RuleEnricher(config)
    rules = enricher.enrich_rules(rules)
    print(f"✓ Enriched {len(rules)} rules")
    print()

    # Show some example rules
    print("Example Rules:")
    for i, rule in enumerate(rules[:3], 1):
        print(f"\n  Rule {i}:")
        print(f"    ID: {rule.id}")
        print(f"    Type: {rule.rule_type.value}")
        print(f"    Description: {rule.description[:100]}...")
        print(f"    Expression: {rule.normalized_expression[:80]}...")
        print(f"    Source: {rule.source.file_path}:{rule.source.start_line}")
        print(f"    Confidence: {rule.confidence:.2f}")
    print()

    # Step 4: Cluster rules into groups
    print("Step 4: Clustering rules into functional groups...")
    clusterer = RuleClusterer(config)
    groups = clusterer.cluster_rules(rules)
    print(f"✓ Created {len(groups)} rule groups")
    print()

    # Show groups
    print("Rule Groups:")
    for group in groups:
        print(f"\n  {group.name}:")
        print(f"    Category: {group.category}")
        print(f"    Rules: {len(group.rules)}")
        print(f"    Confidence: {group.confidence:.2f}")
        print(f"    Description: {group.description}")
    print()

    # Step 5: Infer dependencies (simple heuristic)
    print("Step 5: Inferring dependencies...")
    dependencies = []
    for i, group1 in enumerate(groups):
        tables1 = set()
        for rule in group1.rules:
            tables1.update(rule.tables)

        for j, group2 in enumerate(groups):
            if i == j:
                continue

            tables2 = set()
            for rule in group2.rules:
                tables2.update(rule.tables)

            shared = tables1 & tables2
            if shared:
                strength = min(len(shared) / 3.0, 1.0)
                dependencies.append(RuleDependency(
                    source_id=group1.id,
                    target_id=group2.id,
                    dependency_type="dataflow",
                    strength=strength
                ))

    print(f"✓ Identified {len(dependencies)} dependencies")
    print()

    # Step 6: Build decision model
    print("Step 6: Building decision model...")
    decision_model = DecisionModel(
        rules=rules,
        groups=groups,
        dependencies=dependencies,
        metadata={
            "repository": str(sample_repo),
            "total_files_processed": len(set(r.source.file_path for r in rules))
        }
    )
    print("✓ Decision model built")
    print()

    # Step 7: Generate outputs
    print("Step 7: Generating outputs...")
    generator = DRDGenerator(config)

    # Generate DMN XML
    dmn_xml = generator.generate_drd(decision_model)
    save_text(dmn_xml, "example_output/drd.xml")
    print("✓ DMN XML: example_output/drd.xml")

    # Generate Markdown report
    markdown = generator.generate_markdown_report(decision_model)
    save_text(markdown, "example_output/report.md")
    print("✓ Markdown report: example_output/report.md")

    # Generate JSON
    json_data = {
        "metadata": decision_model.metadata,
        "summary": {
            "total_rules": len(rules),
            "total_groups": len(groups),
            "total_dependencies": len(dependencies)
        },
        "rules": [r.dict() for r in rules[:10]],  # First 10 for brevity
        "groups": [g.dict() for g in groups],
        "dependencies": [d.dict() for d in dependencies]
    }
    save_json(json_data, "example_output/data.json")
    print("✓ JSON data: example_output/data.json")
    print()

    print("=" * 60)
    print("Analysis complete!")
    print("=" * 60)
    print()
    print("Generated files:")
    print("  - example_output/drd.xml      (DMN-compliant XML)")
    print("  - example_output/report.md    (Human-readable report)")
    print("  - example_output/data.json    (Structured data)")
    print()
    print("To validate traceability:")
    print("  python -m src.utils.trace_validator --drd example_output/drd.xml --repo sample_repos/sample_sql_app")
    print()


if __name__ == "__main__":
    main()
