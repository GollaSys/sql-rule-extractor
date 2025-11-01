"""Traceability validation - verify DRD links back to source code."""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from lxml import etree as ET

logger = logging.getLogger(__name__)


class TraceabilityValidator:
    """Validate traceability links in DMN/DRD."""

    def __init__(self, drd_path: str, repo_path: str):
        """
        Initialize validator.

        Args:
            drd_path: Path to DMN XML file
            repo_path: Path to source repository
        """
        self.drd_path = drd_path
        self.repo_path = Path(repo_path)

        # Parse DMN
        self.tree = ET.parse(drd_path)
        self.root = self.tree.getroot()

        # Extract namespace
        self.ns = self._extract_namespaces()

    def _extract_namespaces(self) -> Dict[str, str]:
        """Extract namespaces from DMN."""
        return {
            "dmn": "https://www.omg.org/spec/DMN/20191111/MODEL/",
            "ext": "http://sql-rule-extractor/dmn"
        }

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate all traceability links.

        Returns:
            Tuple of (success, list of errors)
        """
        logger.info("Validating traceability links")

        errors = []
        validated_count = 0

        # Find all traceability source elements
        sources = self.root.findall(".//ext:source", self.ns)

        if not sources:
            errors.append("No traceability sources found in DMN")
            return False, errors

        for source in sources:
            rule_id = source.get("ruleId")
            file_path = source.get("file")
            start_line = int(source.get("startLine"))
            end_line = int(source.get("endLine"))

            snippet_elem = source.find("ext:snippet", self.ns)
            expected_snippet = snippet_elem.text if snippet_elem is not None else None

            # Validate this link
            is_valid, error = self._validate_link(
                rule_id, file_path, start_line, end_line, expected_snippet
            )

            if not is_valid:
                errors.append(error)
            else:
                validated_count += 1

        success = len(errors) == 0

        if success:
            logger.info(f"Successfully validated {validated_count} traceability links")
        else:
            logger.error(f"Validation failed with {len(errors)} errors")

        return success, errors

    def _validate_link(
        self,
        rule_id: str,
        file_path: str,
        start_line: int,
        end_line: int,
        expected_snippet: str
    ) -> Tuple[bool, str]:
        """Validate a single traceability link."""
        # Check if file exists
        full_path = self.repo_path / file_path

        if not full_path.exists():
            return False, f"Rule {rule_id}: File not found: {file_path}"

        # Read file and extract lines
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            # Check line numbers are valid
            if start_line < 1 or start_line > len(lines):
                return False, f"Rule {rule_id}: Invalid start line {start_line} in {file_path}"

            if end_line < start_line or end_line > len(lines):
                return False, f"Rule {rule_id}: Invalid end line {end_line} in {file_path}"

            # Extract actual snippet (with some tolerance)
            actual_snippet = "".join(lines[start_line-1:end_line]).strip()

            # Compare snippets (allow for truncation)
            if expected_snippet:
                expected_clean = expected_snippet.strip()[:200]
                actual_clean = actual_snippet[:200]

                # Allow fuzzy match
                if expected_clean not in actual_clean and actual_clean not in expected_clean:
                    return False, (
                        f"Rule {rule_id}: Snippet mismatch in {file_path}:{start_line}\n"
                        f"Expected: {expected_clean[:50]}...\n"
                        f"Actual: {actual_clean[:50]}..."
                    )

        except Exception as e:
            return False, f"Rule {rule_id}: Error reading {file_path}: {e}"

        return True, ""

    def generate_report(self) -> str:
        """Generate validation report."""
        success, errors = self.validate()

        report_lines = ["# Traceability Validation Report\n"]

        if success:
            report_lines.append("✅ **All traceability links validated successfully**\n")
        else:
            report_lines.append(f"❌ **Validation failed with {len(errors)} errors**\n")
            report_lines.append("\n## Errors\n")

            for error in errors:
                report_lines.append(f"- {error}")

        return "\n".join(report_lines)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate traceability links in DMN/DRD"
    )
    parser.add_argument(
        "--drd",
        required=True,
        help="Path to DMN XML file"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Path to source repository"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Setup logging
    from .logging import setup_logging
    setup_logging(level="DEBUG" if args.verbose else "INFO")

    # Validate
    validator = TraceabilityValidator(args.drd, args.repo)
    success, errors = validator.validate()

    # Print report
    print(validator.generate_report())

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
