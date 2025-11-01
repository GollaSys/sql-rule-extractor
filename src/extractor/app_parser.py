"""Application code parsing to find embedded SQL and conditional logic."""

import re
from typing import List, Dict
from pathlib import Path

from . import Rule, RuleType, SourceLocation


class AppCodeParser:
    """Parse application code (Python, Java, JavaScript) for SQL and business logic."""

    def parse_file(self, file_path: str, content: str, language: str) -> List[Rule]:
        """
        Parse application code file.

        Args:
            file_path: Path to the file
            content: File content
            language: Programming language (python, java, javascript)

        Returns:
            List of extracted rules
        """
        if language == "python":
            return self._parse_python(file_path, content)
        elif language == "java":
            return self._parse_java(file_path, content)
        elif language == "javascript":
            return self._parse_javascript(file_path, content)
        return []

    def _parse_python(self, file_path: str, content: str) -> List[Rule]:
        """Parse Python code."""
        rules = []

        # Extract SQL strings
        rules.extend(self._extract_sql_strings_python(file_path, content))

        # Extract conditional logic
        rules.extend(self._extract_conditionals_python(file_path, content))

        return rules

    def _extract_sql_strings_python(self, file_path: str, content: str) -> List[Rule]:
        """Extract SQL strings from Python code."""
        rules = []

        # Match SQL in strings (single, double, or triple quotes)
        sql_patterns = [
            r'"""(.*?SELECT.*?)"""',
            r"'''(.*?SELECT.*?)'''",
            r'"(.*?SELECT.*?)"',
            r"'(.*?SELECT.*?)'"
        ]

        for pattern in sql_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.DOTALL):
                sql_content = match.group(1).strip()

                # Skip if too short
                if len(sql_content) < 10:
                    continue

                line_num = content[:match.start()].count('\n') + 1

                # Check for WHERE clause (indicates filtering logic)
                if re.search(r'WHERE', sql_content, re.IGNORECASE):
                    rule_id = f"rule_py_{hash(file_path + sql_content) % 1000000}"

                    rule = Rule(
                        id=rule_id,
                        rule_type=RuleType.VALIDATION,
                        description="SQL query with filtering condition",
                        normalized_expression=sql_content[:200],
                        variables=self._extract_placeholders_python(sql_content),
                        tables=self._extract_table_names(sql_content),
                        columns=[],
                        source=SourceLocation(
                            file_path=file_path,
                            start_line=line_num,
                            end_line=line_num + sql_content.count('\n'),
                            snippet=sql_content[:500]
                        ),
                        confidence=0.8
                    )
                    rules.append(rule)

        return rules

    def _extract_conditionals_python(self, file_path: str, content: str) -> List[Rule]:
        """Extract conditional logic from Python code."""
        rules = []

        # Match if statements with business logic indicators
        if_pattern = r'if\s+(.+?):\s*\n'

        for match in re.finditer(if_pattern, content):
            condition = match.group(1).strip()
            line_num = content[:match.start()].count('\n') + 1

            # Filter for business logic (not technical checks like 'if data' or 'if result')
            if self._is_business_logic(condition):
                rule_id = f"rule_py_cond_{hash(file_path + condition) % 1000000}"

                rule = Rule(
                    id=rule_id,
                    rule_type=RuleType.CONDITIONAL,
                    description=f"Python conditional: {condition[:50]}",
                    normalized_expression=f"IF {condition}",
                    variables=self._extract_variables_python(condition),
                    tables=[],
                    columns=[],
                    source=SourceLocation(
                        file_path=file_path,
                        start_line=line_num,
                        end_line=line_num,
                        snippet=match.group(0)
                    ),
                    confidence=0.7,
                    metadata={"language": "python"}
                )
                rules.append(rule)

        return rules

    def _parse_java(self, file_path: str, content: str) -> List[Rule]:
        """Parse Java code."""
        rules = []

        # Extract SQL strings from Java
        sql_pattern = r'"(.*?SELECT.*?)"'

        for match in re.finditer(sql_pattern, content, re.IGNORECASE | re.DOTALL):
            sql_content = match.group(1).strip()

            if len(sql_content) < 10:
                continue

            line_num = content[:match.start()].count('\n') + 1

            if re.search(r'WHERE', sql_content, re.IGNORECASE):
                rule_id = f"rule_java_{hash(file_path + sql_content) % 1000000}"

                rule = Rule(
                    id=rule_id,
                    rule_type=RuleType.VALIDATION,
                    description="SQL query from Java code",
                    normalized_expression=sql_content[:200],
                    variables=[],
                    tables=self._extract_table_names(sql_content),
                    columns=[],
                    source=SourceLocation(
                        file_path=file_path,
                        start_line=line_num,
                        end_line=line_num + sql_content.count('\n'),
                        snippet=sql_content[:500]
                    ),
                    confidence=0.75,
                    metadata={"language": "java"}
                )
                rules.append(rule)

        # Extract if statements
        if_pattern = r'if\s*\((.+?)\)\s*\{'

        for match in re.finditer(if_pattern, content):
            condition = match.group(1).strip()
            line_num = content[:match.start()].count('\n') + 1

            if self._is_business_logic(condition):
                rule_id = f"rule_java_cond_{hash(file_path + condition) % 1000000}"

                rule = Rule(
                    id=rule_id,
                    rule_type=RuleType.CONDITIONAL,
                    description=f"Java conditional: {condition[:50]}",
                    normalized_expression=f"IF {condition}",
                    variables=self._extract_variables_java(condition),
                    tables=[],
                    columns=[],
                    source=SourceLocation(
                        file_path=file_path,
                        start_line=line_num,
                        end_line=line_num,
                        snippet=match.group(0)
                    ),
                    confidence=0.7,
                    metadata={"language": "java"}
                )
                rules.append(rule)

        return rules

    def _parse_javascript(self, file_path: str, content: str) -> List[Rule]:
        """Parse JavaScript/TypeScript code."""
        rules = []

        # Extract SQL strings (often in template literals)
        sql_patterns = [
            r'`(.*?SELECT.*?)`',
            r'"(.*?SELECT.*?)"',
            r"'(.*?SELECT.*?)'"
        ]

        for pattern in sql_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.DOTALL):
                sql_content = match.group(1).strip()

                if len(sql_content) < 10:
                    continue

                line_num = content[:match.start()].count('\n') + 1

                if re.search(r'WHERE', sql_content, re.IGNORECASE):
                    rule_id = f"rule_js_{hash(file_path + sql_content) % 1000000}"

                    rule = Rule(
                        id=rule_id,
                        rule_type=RuleType.VALIDATION,
                        description="SQL query from JavaScript code",
                        normalized_expression=sql_content[:200],
                        variables=[],
                        tables=self._extract_table_names(sql_content),
                        columns=[],
                        source=SourceLocation(
                            file_path=file_path,
                            start_line=line_num,
                            end_line=line_num + sql_content.count('\n'),
                            snippet=sql_content[:500]
                        ),
                        confidence=0.75,
                        metadata={"language": "javascript"}
                    )
                    rules.append(rule)

        return rules

    def _is_business_logic(self, condition: str) -> bool:
        """Determine if condition represents business logic."""
        # Business logic indicators
        business_keywords = [
            'price', 'amount', 'total', 'discount', 'rate', 'fee',
            'age', 'date', 'status', 'eligible', 'valid', 'approved',
            'limit', 'threshold', 'minimum', 'maximum', 'balance'
        ]

        condition_lower = condition.lower()

        # Check for business keywords
        if any(keyword in condition_lower for keyword in business_keywords):
            return True

        # Check for comparisons with numbers (often business rules)
        if re.search(r'[<>=]+\s*\d+', condition):
            return True

        return False

    def _extract_placeholders_python(self, sql: str) -> List[str]:
        """Extract SQL placeholders from Python SQL string."""
        # Python SQL placeholders: %(name)s, %s, :name, ?
        placeholders = []

        # Named placeholders
        placeholders.extend(re.findall(r'%\((\w+)\)s', sql))
        placeholders.extend(re.findall(r':(\w+)', sql))

        return list(set(placeholders))

    def _extract_variables_python(self, code: str) -> List[str]:
        """Extract variable names from Python code."""
        # Match identifiers
        variables = re.findall(r'\b([a-z_][a-z0-9_]*)\b', code)

        # Filter Python keywords
        keywords = {'if', 'else', 'elif', 'for', 'while', 'in', 'is', 'not', 'and', 'or', 'true', 'false', 'none'}
        return list(set([v for v in variables if v not in keywords]))

    def _extract_variables_java(self, code: str) -> List[str]:
        """Extract variable names from Java code."""
        # Match identifiers (camelCase typical in Java)
        variables = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', code)

        # Filter Java keywords
        keywords = {'if', 'else', 'for', 'while', 'return', 'new', 'this', 'true', 'false', 'null'}
        return list(set([v for v in variables if v.lower() not in keywords]))

    def _extract_table_names(self, sql: str) -> List[str]:
        """Extract table names from SQL."""
        tables = []

        # FROM clause
        from_matches = re.finditer(r'FROM\s+(\w+)', sql, re.IGNORECASE)
        tables.extend([m.group(1) for m in from_matches])

        # JOIN clauses
        join_matches = re.finditer(r'JOIN\s+(\w+)', sql, re.IGNORECASE)
        tables.extend([m.group(1) for m in join_matches])

        return list(set(tables))
