"""Command-line interface for SQL Rule Extractor."""

import sys
import logging
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from extractor.ingest import RepositoryIngestor
from extractor.rule_normalizer import RuleNormalizer
from extractor.enricher import RuleEnricher
from extractor.clusterer import RuleClusterer
from extractor.drd_generator import DRDGenerator
from extractor import DecisionModel, RuleDependency
from utils.io import load_config, save_json, save_text, ensure_dir
from utils.logging import setup_logging


logger = logging.getLogger(__name__)
console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """SQL Rule Extractor - Extract business rules from SQL codebases."""
    pass


@cli.command()
@click.option(
    "--repo",
    required=True,
    type=click.Path(exists=True),
    help="Path to repository to analyze"
)
@click.option(
    "--out",
    default="drd.xml",
    type=click.Path(),
    help="Output file path"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["dmn", "markdown", "json", "all"]),
    default="dmn",
    help="Output format"
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    default="config.yml",
    help="Configuration file path"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Dry run - only show statistics, don't write output"
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Verbose output"
)
def analyze(
    repo: str,
    out: str,
    output_format: str,
    config: str,
    dry_run: bool,
    verbose: bool
):
    """Analyze repository and extract business rules."""
    # Load configuration
    try:
        if Path(config).exists():
            cfg = load_config(config)
        else:
            console.print(f"[yellow]Config file not found: {config}, using defaults[/yellow]")
            cfg = _get_default_config()
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        sys.exit(1)

    # Setup logging
    log_level = "DEBUG" if verbose else cfg.get("logging", {}).get("level", "INFO")
    setup_logging(level=log_level)

    console.print(f"[bold blue]SQL Rule Extractor[/bold blue]")
    console.print(f"Analyzing repository: {repo}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 1: Ingest repository
        task = progress.add_task("Ingesting repository...", total=None)
        ingestor = RepositoryIngestor(cfg)
        rules = ingestor.ingest_repository(repo)
        progress.update(task, completed=True)
        console.print(f"✓ Extracted {len(rules)} rules")

        if len(rules) == 0:
            console.print("[yellow]No rules found. Check repository path and file types.[/yellow]")
            sys.exit(0)

        # Step 2: Normalize rules
        task = progress.add_task("Normalizing rules...", total=None)
        normalizer = RuleNormalizer()
        rules = normalizer.normalize_rules(rules)
        rules = normalizer.deduplicate_rules(rules)
        rules = normalizer.filter_low_quality_rules(rules)
        progress.update(task, completed=True)
        console.print(f"✓ Normalized to {len(rules)} unique rules")

        # Step 3: Enrich rules
        task = progress.add_task("Enriching rules...", total=None)
        enricher = RuleEnricher(cfg)
        rules = enricher.enrich_rules(rules)
        progress.update(task, completed=True)
        console.print(f"✓ Enriched {len(rules)} rules")

        # Step 4: Cluster rules
        task = progress.add_task("Clustering rules...", total=None)
        clusterer = RuleClusterer(cfg)
        groups = clusterer.cluster_rules(rules)
        progress.update(task, completed=True)
        console.print(f"✓ Created {len(groups)} rule groups")

        # Step 5: Build decision model
        task = progress.add_task("Building decision model...", total=None)
        dependencies = _infer_dependencies(groups)
        decision_model = DecisionModel(
            rules=rules,
            groups=groups,
            dependencies=dependencies
        )
        progress.update(task, completed=True)
        console.print(f"✓ Built decision model with {len(dependencies)} dependencies")

    # Show statistics
    _show_statistics(rules, groups, ingestor.get_statistics(rules))

    # Dry run - exit here
    if dry_run:
        console.print("\n[yellow]Dry run complete. No files written.[/yellow]")
        return

    # Generate outputs
    console.print(f"\n[bold]Generating outputs...[/bold]")

    try:
        generator = DRDGenerator(cfg)

        if output_format == "dmn" or output_format == "all":
            dmn_xml = generator.generate_drd(decision_model)
            dmn_path = out if out.endswith('.xml') else f"{out}.xml"
            save_text(dmn_xml, dmn_path)
            console.print(f"✓ DMN XML: {dmn_path}")

        if output_format == "markdown" or output_format == "all":
            markdown = generator.generate_markdown_report(decision_model)
            md_path = out.replace('.xml', '.md') if out.endswith('.xml') else f"{out}.md"
            save_text(markdown, md_path)
            console.print(f"✓ Markdown report: {md_path}")

        if output_format == "json" or output_format == "all":
            # Convert to JSON-serializable format
            json_data = {
                "rules": [r.dict() for r in rules],
                "groups": [g.dict() for g in groups],
                "dependencies": [d.dict() for d in dependencies]
            }
            json_path = out.replace('.xml', '.json') if out.endswith('.xml') else f"{out}.json"
            save_json(json_data, json_path)
            console.print(f"✓ JSON data: {json_path}")

        console.print(f"\n[bold green]Analysis complete![/bold green]")

    except Exception as e:
        console.print(f"[red]Error generating output: {e}[/red]")
        logger.exception(e)
        sys.exit(1)


def _show_statistics(rules, groups, stats):
    """Display statistics table."""
    console.print("\n[bold]Statistics:[/bold]")

    # Rules by type
    table = Table(title="Rules by Type")
    table.add_column("Type", style="cyan")
    table.add_column("Count", justify="right", style="green")

    for rule_type, count in stats["by_type"].items():
        table.add_row(rule_type, str(count))

    console.print(table)

    # Groups
    if groups:
        table = Table(title="Rule Groups")
        table.add_column("Group", style="cyan")
        table.add_column("Category", style="yellow")
        table.add_column("Rules", justify="right", style="green")
        table.add_column("Confidence", justify="right", style="magenta")

        for group in groups[:10]:  # Show first 10
            table.add_row(
                group.name,
                group.category,
                str(len(group.rules)),
                f"{group.confidence:.2f}"
            )

        console.print(table)


def _infer_dependencies(groups):
    """Infer dependencies between rule groups."""
    dependencies = []

    # Simple heuristic: groups sharing tables/columns are related
    for i, group1 in enumerate(groups):
        tables1 = set()
        columns1 = set()
        for rule in group1.rules:
            tables1.update(rule.tables)
            columns1.update(rule.columns)

        for j, group2 in enumerate(groups):
            if i == j:
                continue

            tables2 = set()
            columns2 = set()
            for rule in group2.rules:
                tables2.update(rule.tables)
                columns2.update(rule.columns)

            # Check for shared elements
            shared_tables = tables1 & tables2
            shared_columns = columns1 & columns2

            if shared_tables or shared_columns:
                strength = (len(shared_tables) + len(shared_columns)) / 10.0
                strength = min(strength, 1.0)

                dependencies.append(RuleDependency(
                    source_id=group1.id,
                    target_id=group2.id,
                    dependency_type="dataflow",
                    strength=strength
                ))

    return dependencies


def _get_default_config():
    """Get default configuration."""
    return {
        "llm": {
            "provider": "stub"
        },
        "clustering": {
            "method": "kmeans",
            "n_clusters": 5
        },
        "parsing": {
            "sql_dialects": ["postgres"],
            "max_file_size_mb": 10
        },
        "output": {
            "include_snippets": True,
            "pretty_print_xml": True
        },
        "logging": {
            "level": "INFO"
        }
    }


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
