# SQL Rule Extractor & DRD Generator

A production-ready tool that scans SQL-based codebases, extracts business rules, groups them functionally, maps relationships, and produces DMN-compliant Decision Requirements Documents (DRD) with full traceability back to source code.

## Features

- **Comprehensive Parsing**: Supports SQL queries, stored procedures, views, triggers, and application code (Python, Java, Node.js)
- **Intelligent Rule Extraction**: Identifies conditional logic, validations, constraints, and calculations
- **Semantic Grouping**: Uses embeddings and clustering to organize rules functionally (Pricing, Eligibility, etc.)
- **Relationship Mapping**: Builds dependency graphs showing rule interactions
- **DMN-Compliant Output**: Generates valid DMN XML with extension elements for traceability
- **Full Traceability**: Every DRD element links back to source file, line range, and code snippet
- **Modular Architecture**: Swap parsers, LLM models, or clustering algorithms easily

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Ingest    │────▶│   Parsing    │────▶│ Rule Extraction │
│   Layer     │     │    Layer     │     │     Layer       │
└─────────────┘     └──────────────┘     └─────────────────┘
                                                  │
                                                  ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  DMN/DRD    │◀────│  Grouping &  │◀────│   Enrichment    │
│  Generation │     │  Clustering  │     │     Layer       │
└─────────────┘     └──────────────┘     └─────────────────┘
```

## Installation

### Prerequisites
- Python >= 3.10
- Git

### Setup

1. Clone the repository:
```bash
cd rule-project
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### Run on Sample Repository

```bash
python -m src.cli analyze --repo sample_repos/sample_sql_app --out drd.xml --format dmn
```

This will:
- Parse SQL files and application code
- Extract business rules
- Group related rules
- Generate a DMN XML file with traceability

### View Results

The tool generates several outputs:
- `drd.xml`: DMN-compliant XML with decision model
- `drd_report.md`: Human-readable Markdown report
- `rules.json`: Extracted rules with metadata
- `graph.png`: Visual representation of rule relationships (if graphviz installed)

## Usage

### Command Line Interface

```bash
# Basic analysis
python -m src.cli analyze --repo /path/to/codebase --out results/drd.xml

# Dry run (statistics only, no output files)
python -m src.cli analyze --repo /path/to/codebase --dry-run

# Custom configuration
python -m src.cli analyze --repo /path/to/codebase --config custom_config.yml

# Export format options
python -m src.cli analyze --repo /path/to/codebase --format dmn --out drd.xml
python -m src.cli analyze --repo /path/to/codebase --format markdown --out report.md
python -m src.cli analyze --repo /path/to/codebase --format json --out rules.json
```

### Configuration

Create a `config.yml` file to customize behavior:

```yaml
llm:
  provider: "stub"  # Options: stub, anthropic, openai
  model: "claude-3-5-sonnet-20241022"
  api_key_env: "ANTHROPIC_API_KEY"

clustering:
  method: "kmeans"  # Options: kmeans, hierarchical, dbscan
  n_clusters: 5
  min_similarity: 0.7

parsing:
  sql_dialects: ["postgres", "mysql", "generic"]
  max_file_size_mb: 10

output:
  include_snippets: true
  max_snippet_lines: 20
  generate_graphs: true

traceability:
  validate_links: true
```

## Testing

### Run All Tests

```bash
pytest -v
```

### Run Specific Test Suites

```bash
# Unit tests only
pytest tests/test_sql_parser.py tests/test_rule_normalizer.py -v

# Integration tests
pytest tests/test_integration_end_to_end.py -v

# With coverage
pytest --cov=src --cov-report=html
```

### Validate Traceability

```bash
python -m src.utils.trace_validator --drd drd.xml --repo sample_repos/sample_sql_app
```

### Validate DMN Compliance

If you have xmllint installed:
```bash
xmllint --noout --schema schemas/dmn.xsd drd.xml
```

## Example

Given this SQL stored procedure:

```sql
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
```

The tool will:
1. Extract 3 business rules from the conditional logic
2. Group them into a "Pricing" decision
3. Generate a DMN decision node with traceability links
4. Map the decision to input data (`total`) and output (`discount`)

## Extending the Tool

### Add a New SQL Dialect

1. Implement parser in [src/extractor/sql_parser.py](src/extractor/sql_parser.py)
2. Register in [src/extractor/ingest.py](src/extractor/ingest.py)

```python
def parse_tsql(sql_content: str) -> List[Rule]:
    # Your T-SQL specific parsing logic
    pass
```

### Use Different LLM Provider

Set environment variables:
```bash
export ANTHROPIC_API_KEY="your-key"
```

Update config:
```yaml
llm:
  provider: "anthropic"
  model: "claude-3-5-sonnet-20241022"
```

### Custom Clustering Algorithm

Implement in [src/extractor/clusterer.py](src/extractor/clusterer.py):

```python
class CustomClusterer(BaseClusterer):
    def cluster(self, rules: List[Rule]) -> List[RuleGroup]:
        # Your clustering logic
        pass
```

## Project Structure

```
rule-project/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Project metadata
├── config.yml                  # Default configuration
├── src/
│   ├── cli.py                  # Command-line interface
│   ├── extractor/              # Core extraction modules
│   │   ├── __init__.py
│   │   ├── ingest.py           # Repository scanning
│   │   ├── sql_parser.py       # SQL parsing & AST analysis
│   │   ├── app_parser.py       # Application code parsing
│   │   ├── rule_normalizer.py  # Rule normalization
│   │   ├── enricher.py         # Semantic enrichment
│   │   ├── clusterer.py        # Rule grouping
│   │   └── drd_generator.py    # DMN/DRD generation
│   └── utils/                  # Utilities
│       ├── io.py               # File I/O helpers
│       ├── logging.py          # Logging configuration
│       └── trace_validator.py  # Traceability validation
├── tests/                      # Test suite
│   ├── test_sql_parser.py
│   ├── test_rule_normalizer.py
│   ├── test_clusterer.py
│   └── test_integration_end_to_end.py
├── sample_repos/               # Example codebases
│   └── sample_sql_app/
│       ├── schema.sql
│       ├── procedures.sql
│       └── app.py
└── .github/
    └── workflows/
        └── ci.yml              # GitHub Actions CI
```

## API Keys & External Services

The tool can work in three modes:

1. **Stub Mode (Default)**: Uses deterministic local embeddings, no external API calls
2. **Anthropic Mode**: Uses Claude for semantic analysis (requires `ANTHROPIC_API_KEY`)
3. **OpenAI Mode**: Uses OpenAI embeddings (requires `OPENAI_API_KEY`)

For testing and CI, stub mode is used automatically.

## Troubleshooting

### Parser Errors

If the SQL parser fails:
- Check SQL dialect in config matches your database
- Verify SQL syntax is valid
- Check logs for specific parsing errors

### Empty Results

If no rules are extracted:
- Verify input files contain SQL or procedural code
- Check file extensions are recognized (.sql, .psql, .py, .java, .js)
- Review logs for skipped files

### Clustering Issues

If rule grouping seems incorrect:
- Adjust `clustering.n_clusters` in config
- Increase `clustering.min_similarity` threshold
- Try different clustering method (hierarchical, dbscan)

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## References

- [DMN Specification (OMG)](https://www.omg.org/dmn/)
- [sqlglot Documentation](https://github.com/tobymao/sqlglot)
- [LangChain Documentation](https://python.langchain.com/)
- [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)

## Support

For issues, questions, or feature requests, please open an issue on the project repository.
