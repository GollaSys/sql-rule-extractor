"""Repository ingestion and file scanning."""

import os
from pathlib import Path
from typing import List, Dict, Optional
import logging

from . import Rule
from .sql_parser import SQLParser
from .app_parser import AppCodeParser


logger = logging.getLogger(__name__)


class RepositoryIngestor:
    """Scan repository and coordinate parsing."""

    def __init__(self, config: Dict):
        """
        Initialize ingestor.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.sql_parser = SQLParser(dialect=config.get("parsing", {}).get("sql_dialects", ["postgres"])[0])
        self.app_parser = AppCodeParser()

        self.file_extensions = config.get("parsing", {}).get("file_extensions", {
            "sql": [".sql", ".psql", ".pkb", ".pks", ".ddl"],
            "python": [".py"],
            "java": [".java"],
            "javascript": [".js", ".ts"]
        })

        self.ignore_patterns = config.get("parsing", {}).get("ignore_patterns", [
            "*/node_modules/*",
            "*/venv/*",
            "*/.venv/*",
            "*/dist/*",
            "*/build/*",
            "*/__pycache__/*"
        ])

        self.max_file_size = config.get("parsing", {}).get("max_file_size_mb", 10) * 1024 * 1024

    def ingest_repository(self, repo_path: str) -> List[Rule]:
        """
        Scan repository and extract all rules.

        Args:
            repo_path: Path to repository root

        Returns:
            List of all extracted rules
        """
        logger.info(f"Ingesting repository: {repo_path}")

        all_rules = []
        files_processed = 0

        # Walk the repository
        for root, dirs, files in os.walk(repo_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d))]

            for file in files:
                file_path = os.path.join(root, file)

                # Check if should process
                if self._should_ignore(file_path):
                    continue

                if not self._should_process_file(file_path):
                    continue

                # Check file size
                try:
                    if os.path.getsize(file_path) > self.max_file_size:
                        logger.warning(f"Skipping large file: {file_path}")
                        continue
                except OSError:
                    continue

                # Parse the file
                rules = self._parse_file(file_path)
                all_rules.extend(rules)
                files_processed += 1

                if files_processed % 10 == 0:
                    logger.info(f"Processed {files_processed} files, extracted {len(all_rules)} rules")

        logger.info(f"Ingestion complete. Processed {files_processed} files, extracted {len(all_rules)} rules")
        return all_rules

    def _parse_file(self, file_path: str) -> List[Rule]:
        """Parse a single file and extract rules."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Determine file type and parse accordingly
            file_type = self._get_file_type(file_path)

            if file_type == "sql":
                logger.debug(f"Parsing SQL file: {file_path}")
                return self.sql_parser.parse_file(file_path, content)
            elif file_type in ["python", "java", "javascript"]:
                logger.debug(f"Parsing {file_type} file: {file_path}")
                return self.app_parser.parse_file(file_path, content, file_type)

        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")

        return []

    def _get_file_type(self, file_path: str) -> Optional[str]:
        """Determine file type from extension."""
        ext = Path(file_path).suffix.lower()

        for file_type, extensions in self.file_extensions.items():
            if ext in extensions:
                return file_type

        return None

    def _should_process_file(self, file_path: str) -> bool:
        """Check if file should be processed."""
        file_type = self._get_file_type(file_path)
        return file_type is not None

    def _should_ignore(self, path: str) -> bool:
        """Check if path matches ignore patterns."""
        path_obj = Path(path)

        for pattern in self.ignore_patterns:
            # Simple glob-style matching
            pattern_parts = pattern.strip('*/').split('/')

            # Check if any part of the path matches the pattern
            path_parts = path_obj.parts
            for i in range(len(path_parts)):
                if path_parts[i] in pattern_parts:
                    return True

        return False

    def get_statistics(self, rules: List[Rule]) -> Dict:
        """Generate statistics about extracted rules."""
        stats = {
            "total_rules": len(rules),
            "by_type": {},
            "by_file": {},
            "unique_tables": set(),
            "unique_columns": set(),
        }

        for rule in rules:
            # Count by type
            rule_type = rule.rule_type.value
            stats["by_type"][rule_type] = stats["by_type"].get(rule_type, 0) + 1

            # Count by file
            file_path = rule.source.file_path
            stats["by_file"][file_path] = stats["by_file"].get(file_path, 0) + 1

            # Collect tables and columns
            stats["unique_tables"].update(rule.tables)
            stats["unique_columns"].update(rule.columns)

        # Convert sets to counts
        stats["unique_tables"] = len(stats["unique_tables"])
        stats["unique_columns"] = len(stats["unique_columns"])

        return stats
