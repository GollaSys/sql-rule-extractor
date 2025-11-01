# Quick Start Guide

Get up and running with SQL Rule Extractor in 5 minutes!

## Installation

```bash
# Clone or navigate to the project
cd rule-project

# Run setup script
./setup.sh

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

## Basic Usage

### Analyze the Sample Repository

```bash
python -m src.cli analyze \
  --repo sample_repos/sample_sql_app \
  --out results/drd.xml \
  --format all
```

This will generate:
- `results/drd.xml` - DMN-compliant decision model
- `results/drd.md` - Human-readable report
- `results/drd.json` - Structured data

### View Results

```bash
# View the markdown report
cat results/drd.md

# Or open in your editor
code results/drd.md
```

### Validate Traceability

```bash
python -m src.utils.trace_validator \
  --drd results/drd.xml \
  --repo sample_repos/sample_sql_app
```

## Analyze Your Own Codebase

```bash
python -m src.cli analyze \
  --repo /path/to/your/sql/codebase \
  --out output/drd.xml \
  --format all \
  --verbose
```

## Configuration

Create a custom `config.yml`:

```yaml
llm:
  provider: "stub"  # Use "anthropic" with API key for better results

clustering:
  method: "kmeans"
  n_clusters: 5  # Adjust based on your codebase size

parsing:
  sql_dialects: ["postgres", "mysql"]
  max_file_size_mb: 10
```

Use custom config:
```bash
python -m src.cli analyze \
  --repo /path/to/repo \
  --config my_config.yml \
  --out output/drd.xml
```

## Run Tests

```bash
# All tests
pytest -v

# Specific test file
pytest tests/test_sql_parser.py -v

# With coverage
pytest --cov=src --cov-report=html
```

## Programmatic Usage

```python
from src.extractor.ingest import RepositoryIngestor
from src.extractor.rule_normalizer import RuleNormalizer
from src.extractor.enricher import RuleEnricher
from src.extractor.clusterer import RuleClusterer
from src.extractor.drd_generator import DRDGenerator
from src.extractor import DecisionModel
from src.utils.io import load_config

# Load config
config = load_config("config.yml")

# Ingest repository
ingestor = RepositoryIngestor(config)
rules = ingestor.ingest_repository("/path/to/repo")

# Normalize
normalizer = RuleNormalizer()
rules = normalizer.normalize_rules(rules)
rules = normalizer.deduplicate_rules(rules)

# Enrich
enricher = RuleEnricher(config)
rules = enricher.enrich_rules(rules)

# Cluster
clusterer = RuleClusterer(config)
groups = clusterer.cluster_rules(rules)

# Generate DRD
model = DecisionModel(rules=rules, groups=groups, dependencies=[])
generator = DRDGenerator(config)
dmn_xml = generator.generate_drd(model)

# Save
with open("output.xml", "w") as f:
    f.write(dmn_xml)
```

## Common Options

### Dry Run
See what would be extracted without generating files:
```bash
python -m src.cli analyze --repo /path/to/repo --dry-run
```

### Output Formats
```bash
# DMN XML only (default)
--format dmn

# Markdown only
--format markdown

# JSON only
--format json

# All formats
--format all
```

### Verbose Output
```bash
--verbose  # Show detailed progress and debug information
```

## What Gets Extracted?

The tool extracts:
- ✅ SQL CASE expressions
- ✅ WHERE and HAVING clauses
- ✅ CHECK constraints
- ✅ Stored procedures (IF/ELSIF/ELSE)
- ✅ Triggers
- ✅ Functions
- ✅ Embedded SQL in Python/Java/JavaScript
- ✅ Conditional logic in application code

## Understanding Results

### Rule Types
- **conditional** - IF/CASE logic
- **validation** - WHERE clauses, data validation
- **constraint** - CHECK constraints
- **calculation** - Computed values
- **trigger** - Database triggers

### Rule Groups
Rules are automatically grouped by:
- Semantic similarity (using embeddings)
- Shared tables/columns
- File location
- Domain concepts (pricing, eligibility, etc.)

### Traceability
Every rule includes:
- Source file path
- Start/end line numbers
- Code snippet
- Confidence score

## Next Steps

1. **Customize Configuration** - Adjust clustering parameters for your codebase size
2. **Add Your API Key** - Use Anthropic Claude for better semantic analysis
3. **Review Results** - Check the generated groups and adjust thresholds
4. **Integrate into CI/CD** - Add automated rule extraction to your pipeline
5. **Extend the Tool** - Add support for new SQL dialects or languages

## Troubleshooting

### No Rules Extracted
- Check file extensions in `config.yml`
- Verify repository path is correct
- Look for parsing errors in logs with `--verbose`

### Too Many/Few Groups
- Adjust `clustering.n_clusters` in config
- Try different clustering methods (kmeans, hierarchical, dbscan)

### Low Confidence Scores
- Rules with confidence < 0.7 may need manual review
- Use `--verbose` to see why confidence is low

## Getting Help

- 📖 Read the full [README.md](README.md)
- 🐛 Report issues on GitHub
- 💬 Check existing documentation
- 📝 See [CONTRIBUTING.md](CONTRIBUTING.md) for development

Happy rule extracting! 🚀
