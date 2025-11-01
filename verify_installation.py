#!/usr/bin/env python3
"""Verification script to test SQL Rule Extractor installation."""

import sys
from pathlib import Path


def check_python_version():
    """Check Python version >= 3.10."""
    print("Checking Python version...", end=" ")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro}")
        print(f"  Error: Python 3.10+ required")
        return False


def check_dependencies():
    """Check required dependencies are installed."""
    print("\nChecking dependencies...")

    required_packages = [
        "langchain",
        "sqlglot",
        "sqlparse",
        "networkx",
        "sklearn",
        "pydantic",
        "lxml",
        "click",
        "rich",
        "yaml",
        "numpy",
        "pytest"
    ]

    missing = []

    for package in required_packages:
        try:
            # Special cases for package names
            if package == "sklearn":
                __import__("sklearn")
            elif package == "yaml":
                __import__("yaml")
            else:
                __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package}")
            missing.append(package)

    if missing:
        print(f"\n  Error: Missing packages: {', '.join(missing)}")
        print("  Run: pip install -r requirements.txt")
        return False

    return True


def check_project_structure():
    """Check project structure is complete."""
    print("\nChecking project structure...")

    required_paths = [
        "src/__init__.py",
        "src/cli.py",
        "src/extractor/__init__.py",
        "src/extractor/sql_parser.py",
        "src/extractor/app_parser.py",
        "src/extractor/ingest.py",
        "src/extractor/rule_normalizer.py",
        "src/extractor/enricher.py",
        "src/extractor/clusterer.py",
        "src/extractor/drd_generator.py",
        "src/utils/__init__.py",
        "src/utils/io.py",
        "src/utils/logging.py",
        "src/utils/trace_validator.py",
        "tests/__init__.py",
        "tests/test_sql_parser.py",
        "tests/test_rule_normalizer.py",
        "tests/test_clusterer.py",
        "tests/test_integration_end_to_end.py",
        "sample_repos/sample_sql_app/schema.sql",
        "sample_repos/sample_sql_app/procedures.sql",
        "sample_repos/sample_sql_app/app.py",
        "config.yml",
        "requirements.txt",
        "README.md",
    ]

    missing = []
    project_root = Path(__file__).parent

    for path in required_paths:
        full_path = project_root / path
        if full_path.exists():
            print(f"  ✓ {path}")
        else:
            print(f"  ✗ {path}")
            missing.append(path)

    if missing:
        print(f"\n  Error: Missing files/directories:")
        for path in missing:
            print(f"    - {path}")
        return False

    return True


def check_imports():
    """Check that project modules can be imported."""
    print("\nChecking project imports...")

    try:
        print("  Importing src.extractor...", end=" ")
        from src.extractor import Rule, RuleType, SourceLocation
        print("✓")

        print("  Importing src.extractor.sql_parser...", end=" ")
        from src.extractor.sql_parser import SQLParser
        print("✓")

        print("  Importing src.extractor.ingest...", end=" ")
        from src.extractor.ingest import RepositoryIngestor
        print("✓")

        print("  Importing src.extractor.rule_normalizer...", end=" ")
        from src.extractor.rule_normalizer import RuleNormalizer
        print("✓")

        print("  Importing src.extractor.enricher...", end=" ")
        from src.extractor.enricher import RuleEnricher
        print("✓")

        print("  Importing src.extractor.clusterer...", end=" ")
        from src.extractor.clusterer import RuleClusterer
        print("✓")

        print("  Importing src.extractor.drd_generator...", end=" ")
        from src.extractor.drd_generator import DRDGenerator
        print("✓")

        return True

    except ImportError as e:
        print(f"✗\n  Error: {e}")
        return False


def run_basic_test():
    """Run a basic functional test."""
    print("\nRunning basic functional test...")

    try:
        from src.extractor.sql_parser import SQLParser
        from src.extractor import RuleType

        parser = SQLParser()
        sql = "SELECT * FROM orders WHERE total > 100"

        print("  Parsing test SQL...", end=" ")
        rules = parser.parse_file("test.sql", sql)
        print(f"✓ (extracted {len(rules)} rules)")

        if len(rules) > 0:
            print(f"  Rule type: {rules[0].rule_type.value}")
            print(f"  Rule ID: {rules[0].id}")
            return True
        else:
            print("  Warning: No rules extracted (may be normal for simple SQL)")
            return True

    except Exception as e:
        print(f"✗\n  Error: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("SQL Rule Extractor - Installation Verification")
    print("=" * 60)
    print()

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Project Structure", check_project_structure),
        ("Module Imports", check_imports),
        ("Basic Functionality", run_basic_test),
    ]

    results = {}

    for name, check_func in checks:
        results[name] = check_func()

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("✓ All checks passed!")
        print()
        print("Next steps:")
        print("  1. Run tests: pytest -v")
        print("  2. Try the example: python example_usage.py")
        print("  3. Analyze sample repo:")
        print("     python -m src.cli analyze --repo sample_repos/sample_sql_app --out drd.xml --format all")
        print()
        return 0
    else:
        print("✗ Some checks failed. Please fix the errors above.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
