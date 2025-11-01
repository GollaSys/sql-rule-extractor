"""SQL parsing and rule extraction from SQL code."""

import re
import hashlib
from typing import List, Optional, Dict, Any, Tuple
import sqlglot
from sqlglot import exp, parse_one, ParseError
from sqlglot.optimizer import qualify
import sqlparse
from sqlparse.sql import Statement, Token
from sqlparse.tokens import Keyword, DML

from . import Rule, RuleType, SourceLocation


class SQLParser:
    """Parse SQL and extract business rules."""

    def __init__(self, dialect: str = "postgres"):
        """
        Initialize SQL parser.

        Args:
            dialect: SQL dialect (postgres, mysql, generic, etc.)
        """
        self.dialect = dialect

    def parse_file(self, file_path: str, content: str) -> List[Rule]:
        """
        Parse SQL file and extract all rules.

        Args:
            file_path: Path to the SQL file
            content: File content

        Returns:
            List of extracted rules
        """
        rules = []

        # Split content into logical statements
        statements = self._split_statements(content)

        for stmt_info in statements:
            stmt_text, start_line, end_line = stmt_info

            # Try different extraction methods
            rules.extend(self._extract_from_case(file_path, stmt_text, start_line))
            rules.extend(self._extract_from_where(file_path, stmt_text, start_line))
            rules.extend(self._extract_from_procedure(file_path, stmt_text, start_line))
            rules.extend(self._extract_from_trigger(file_path, stmt_text, start_line))
            rules.extend(self._extract_from_constraint(file_path, stmt_text, start_line))

        return rules

    def _split_statements(self, content: str) -> List[Tuple[str, int, int]]:
        """Split SQL content into individual statements with line numbers."""
        statements = []

        try:
            # Use sqlparse for basic statement splitting
            parsed = sqlparse.parse(content)

            current_line = 1
            for statement in parsed:
                stmt_text = str(statement).strip()
                if stmt_text:
                    # Count lines in this statement
                    line_count = stmt_text.count('\n') + 1
                    statements.append((stmt_text, current_line, current_line + line_count - 1))
                    current_line += stmt_text.count('\n') + 1
        except Exception as e:
            # Fallback: treat entire content as one statement
            statements.append((content, 1, content.count('\n') + 1))

        return statements

    def _extract_from_case(self, file_path: str, sql: str, base_line: int) -> List[Rule]:
        """Extract rules from CASE expressions."""
        rules = []

        try:
            # Parse with sqlglot
            parsed = parse_one(sql, dialect=self.dialect)

            # Find all CASE expressions
            for case_expr in parsed.find_all(exp.Case):
                case_rules = self._parse_case_expression(file_path, case_expr, sql, base_line)
                rules.extend(case_rules)
        except (ParseError, Exception) as e:
            # Fallback to regex-based extraction
            rules.extend(self._extract_case_regex(file_path, sql, base_line))

        return rules

    def _parse_case_expression(
        self, file_path: str, case_expr: exp.Case, full_sql: str, base_line: int
    ) -> List[Rule]:
        """Parse a CASE expression into rules."""
        rules = []

        case_text = case_expr.sql(dialect=self.dialect)

        # Extract WHEN conditions
        for i, if_clause in enumerate(case_expr.args.get("ifs", [])):
            condition = if_clause.args.get("this")
            result = if_clause.args.get("true")

            if condition and result:
                rule_id = self._generate_rule_id(file_path, str(condition))

                # Extract variables from condition
                variables = self._extract_variables(condition)
                tables = self._extract_tables(condition)

                rule = Rule(
                    id=rule_id,
                    rule_type=RuleType.CONDITIONAL,
                    description=f"CASE condition: {condition.sql()}",
                    normalized_expression=f"IF {condition.sql()} THEN {result.sql()}",
                    variables=variables,
                    tables=tables,
                    columns=variables,
                    source=SourceLocation(
                        file_path=file_path,
                        start_line=base_line,
                        end_line=base_line + case_text.count('\n'),
                        snippet=case_text[:500]
                    ),
                    confidence=0.9
                )
                rules.append(rule)

        # Extract ELSE clause
        else_clause = case_expr.args.get("default")
        if else_clause:
            rule_id = self._generate_rule_id(file_path, f"CASE_ELSE_{case_text}")
            rule = Rule(
                id=rule_id,
                rule_type=RuleType.CONDITIONAL,
                description="CASE default condition",
                normalized_expression=f"ELSE {else_clause.sql()}",
                variables=[],
                tables=[],
                columns=[],
                source=SourceLocation(
                    file_path=file_path,
                    start_line=base_line,
                    end_line=base_line + case_text.count('\n'),
                    snippet=case_text[:500]
                ),
                confidence=0.9
            )
            rules.append(rule)

        return rules

    def _extract_case_regex(self, file_path: str, sql: str, base_line: int) -> List[Rule]:
        """Fallback regex-based CASE extraction."""
        rules = []

        # Find CASE expressions with regex
        case_pattern = r'CASE\s+(?:WHEN\s+(.+?)\s+THEN\s+(.+?)\s*)+(?:ELSE\s+(.+?)\s+)?END'

        for match in re.finditer(case_pattern, sql, re.IGNORECASE | re.DOTALL):
            case_text = match.group(0)
            line_offset = sql[:match.start()].count('\n')

            rule_id = self._generate_rule_id(file_path, case_text)
            rule = Rule(
                id=rule_id,
                rule_type=RuleType.CONDITIONAL,
                description="CASE expression (regex extracted)",
                normalized_expression=case_text,
                variables=self._extract_variables_regex(case_text),
                tables=[],
                columns=[],
                source=SourceLocation(
                    file_path=file_path,
                    start_line=base_line + line_offset,
                    end_line=base_line + line_offset + case_text.count('\n'),
                    snippet=case_text[:500]
                ),
                confidence=0.7
            )
            rules.append(rule)

        return rules

    def _extract_from_where(self, file_path: str, sql: str, base_line: int) -> List[Rule]:
        """Extract rules from WHERE clauses."""
        rules = []

        try:
            parsed = parse_one(sql, dialect=self.dialect)

            # Find WHERE clauses
            for where_expr in parsed.find_all(exp.Where):
                condition = where_expr.this

                rule_id = self._generate_rule_id(file_path, str(condition))
                variables = self._extract_variables(condition)
                tables = self._extract_tables(condition)

                rule = Rule(
                    id=rule_id,
                    rule_type=RuleType.VALIDATION,
                    description=f"WHERE condition: {condition.sql()}",
                    normalized_expression=condition.sql(),
                    variables=variables,
                    tables=tables,
                    columns=variables,
                    source=SourceLocation(
                        file_path=file_path,
                        start_line=base_line,
                        end_line=base_line + sql.count('\n'),
                        snippet=sql[:500]
                    ),
                    confidence=0.85
                )
                rules.append(rule)
        except (ParseError, Exception):
            pass

        return rules

    def _extract_from_procedure(self, file_path: str, sql: str, base_line: int) -> List[Rule]:
        """Extract rules from stored procedures and functions."""
        rules = []

        # Look for procedural IF statements (PL/pgSQL, PL/SQL)
        if_pattern = r'IF\s+(.+?)\s+THEN\s+(.*?)(?:ELSIF\s+(.+?)\s+THEN\s+(.*?))*(?:ELSE\s+(.*?))?END\s+IF'

        for match in re.finditer(if_pattern, sql, re.IGNORECASE | re.DOTALL):
            condition = match.group(1)
            then_clause = match.group(2)
            line_offset = sql[:match.start()].count('\n')

            rule_id = self._generate_rule_id(file_path, condition)
            rule = Rule(
                id=rule_id,
                rule_type=RuleType.CONDITIONAL,
                description=f"Procedural IF: {condition}",
                normalized_expression=f"IF {condition} THEN {then_clause[:100]}...",
                variables=self._extract_variables_regex(condition),
                tables=[],
                columns=self._extract_variables_regex(condition),
                source=SourceLocation(
                    file_path=file_path,
                    start_line=base_line + line_offset,
                    end_line=base_line + line_offset + match.group(0).count('\n'),
                    snippet=match.group(0)[:500]
                ),
                confidence=0.85
            )
            rules.append(rule)

        return rules

    def _extract_from_trigger(self, file_path: str, sql: str, base_line: int) -> List[Rule]:
        """Extract rules from triggers."""
        rules = []

        # Check if this is a trigger definition
        if re.search(r'CREATE\s+(?:OR\s+REPLACE\s+)?TRIGGER', sql, re.IGNORECASE):
            rule_id = self._generate_rule_id(file_path, sql)

            # Extract trigger name
            trigger_match = re.search(r'TRIGGER\s+(\w+)', sql, re.IGNORECASE)
            trigger_name = trigger_match.group(1) if trigger_match else "unknown_trigger"

            rule = Rule(
                id=rule_id,
                rule_type=RuleType.TRIGGER,
                description=f"Trigger: {trigger_name}",
                normalized_expression=sql[:200],
                variables=[],
                tables=self._extract_table_names_regex(sql),
                columns=[],
                source=SourceLocation(
                    file_path=file_path,
                    start_line=base_line,
                    end_line=base_line + sql.count('\n'),
                    snippet=sql[:500]
                ),
                confidence=0.9
            )
            rules.append(rule)

        return rules

    def _extract_from_constraint(self, file_path: str, sql: str, base_line: int) -> List[Rule]:
        """Extract rules from CHECK constraints."""
        rules = []

        # Find CHECK constraints
        check_pattern = r'CHECK\s*\(([^)]+)\)'

        for match in re.finditer(check_pattern, sql, re.IGNORECASE):
            constraint = match.group(1)
            line_offset = sql[:match.start()].count('\n')

            rule_id = self._generate_rule_id(file_path, constraint)
            rule = Rule(
                id=rule_id,
                rule_type=RuleType.CONSTRAINT,
                description=f"CHECK constraint: {constraint}",
                normalized_expression=constraint,
                variables=self._extract_variables_regex(constraint),
                tables=[],
                columns=self._extract_variables_regex(constraint),
                source=SourceLocation(
                    file_path=file_path,
                    start_line=base_line + line_offset,
                    end_line=base_line + line_offset,
                    snippet=match.group(0)
                ),
                confidence=0.95
            )
            rules.append(rule)

        return rules

    def _extract_variables(self, expr: exp.Expression) -> List[str]:
        """Extract variable/column names from expression."""
        variables = []
        for column in expr.find_all(exp.Column):
            variables.append(column.name)
        return list(set(variables))

    def _extract_tables(self, expr: exp.Expression) -> List[str]:
        """Extract table names from expression."""
        tables = []
        for table in expr.find_all(exp.Table):
            tables.append(table.name)
        return list(set(tables))

    def _extract_variables_regex(self, text: str) -> List[str]:
        """Extract variables using regex."""
        # Match identifiers (simplistic)
        variables = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', text)
        # Filter out SQL keywords
        keywords = {'if', 'then', 'else', 'case', 'when', 'end', 'and', 'or', 'not', 'select', 'from', 'where'}
        return list(set([v for v in variables if v.lower() not in keywords]))

    def _extract_table_names_regex(self, sql: str) -> List[str]:
        """Extract table names using regex."""
        tables = []

        # FROM clause
        from_matches = re.finditer(r'FROM\s+(\w+)', sql, re.IGNORECASE)
        tables.extend([m.group(1) for m in from_matches])

        # JOIN clauses
        join_matches = re.finditer(r'JOIN\s+(\w+)', sql, re.IGNORECASE)
        tables.extend([m.group(1) for m in join_matches])

        return list(set(tables))

    def _generate_rule_id(self, file_path: str, content: str) -> str:
        """Generate unique rule ID."""
        hash_input = f"{file_path}:{content}"
        return f"rule_{hashlib.md5(hash_input.encode()).hexdigest()[:12]}"
