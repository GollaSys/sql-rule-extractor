"""Tests for SQL parser."""

import pytest
from src.extractor.sql_parser import SQLParser
from src.extractor import RuleType


class TestSQLParser:
    """Test SQL parsing functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = SQLParser(dialect="postgres")

    def test_parse_case_expression(self):
        """Test parsing CASE expressions."""
        sql = """
        SELECT
            customer_id,
            CASE
                WHEN total > 1000 THEN 'high'
                WHEN total > 500 THEN 'medium'
                ELSE 'low'
            END as tier
        FROM orders
        """

        rules = self.parser.parse_file("test.sql", sql)

        # Should extract rules from CASE
        assert len(rules) > 0

        # Check for conditional rules
        conditional_rules = [r for r in rules if r.rule_type == RuleType.CONDITIONAL]
        assert len(conditional_rules) > 0

    def test_parse_where_clause(self):
        """Test parsing WHERE clauses."""
        sql = """
        SELECT * FROM orders
        WHERE total_amount > 100
          AND status = 'active'
          AND order_date >= CURRENT_DATE - INTERVAL '30 days'
        """

        rules = self.parser.parse_file("test.sql", sql)

        # Should extract validation rules from WHERE
        assert len(rules) > 0

        # Check that variables are extracted
        rule = rules[0]
        assert len(rule.variables) > 0 or len(rule.columns) > 0

    def test_parse_check_constraint(self):
        """Test parsing CHECK constraints."""
        sql = """
        CREATE TABLE products (
            product_id SERIAL PRIMARY KEY,
            price NUMERIC(10, 2) NOT NULL,
            stock_quantity INTEGER NOT NULL,
            CONSTRAINT positive_price CHECK (price > 0),
            CONSTRAINT non_negative_stock CHECK (stock_quantity >= 0)
        )
        """

        rules = self.parser.parse_file("test.sql", sql)

        # Should extract constraint rules
        constraint_rules = [r for r in rules if r.rule_type == RuleType.CONSTRAINT]
        assert len(constraint_rules) >= 2

        # Check rule content
        rule_texts = [r.normalized_expression.lower() for r in constraint_rules]
        assert any('price' in text for text in rule_texts)
        assert any('stock_quantity' in text for text in rule_texts)

    def test_parse_stored_procedure(self):
        """Test parsing stored procedures with IF statements."""
        sql = """
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

        rules = self.parser.parse_file("test.sql", sql)

        # Should extract conditional rules from procedure
        assert len(rules) > 0

        conditional_rules = [r for r in rules if r.rule_type == RuleType.CONDITIONAL]
        # Regex captures entire IF block as one rule (which is correct)
        assert len(conditional_rules) >= 1

    def test_parse_trigger(self):
        """Test parsing triggers."""
        sql = """
        CREATE TRIGGER order_status_check
          BEFORE UPDATE ON orders
          FOR EACH ROW
          EXECUTE FUNCTION update_order_status();
        """

        rules = self.parser.parse_file("test.sql", sql)

        # Should identify trigger
        trigger_rules = [r for r in rules if r.rule_type == RuleType.TRIGGER]
        assert len(trigger_rules) > 0

    def test_rule_id_generation(self):
        """Test that rule IDs are unique and consistent."""
        sql = """
        SELECT * FROM orders WHERE total > 100
        """

        rules1 = self.parser.parse_file("test.sql", sql)
        rules2 = self.parser.parse_file("test.sql", sql)

        # Same content should generate same IDs
        assert rules1[0].id == rules2[0].id

    def test_source_location_tracking(self):
        """Test that source locations are correctly tracked."""
        sql = """
        SELECT * FROM orders
        WHERE total > 100
        """

        rules = self.parser.parse_file("test.sql", sql)

        assert len(rules) > 0
        rule = rules[0]

        # Check source location
        assert rule.source.file_path == "test.sql"
        assert rule.source.start_line >= 1
        assert rule.source.end_line >= rule.source.start_line
        assert len(rule.source.snippet) > 0

    def test_empty_sql(self):
        """Test handling of empty SQL."""
        rules = self.parser.parse_file("test.sql", "")
        assert len(rules) == 0

    def test_malformed_sql(self):
        """Test handling of malformed SQL."""
        sql = "SELECT * FROM WHERE INVALID SYNTAX"

        # Should not crash, may return empty or partial results
        rules = self.parser.parse_file("test.sql", sql)
        assert isinstance(rules, list)
