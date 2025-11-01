# Architecture Documentation

## System Overview

The SQL Rule Extractor follows a pipeline architecture where data flows through several processing stages, each responsible for a specific transformation.

```
┌──────────────────────────────────────────────────────────────────┐
│                      SQL Rule Extractor                          │
└──────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Input     │────▶│   Parsing    │────▶│ Rule Extraction │
│   Layer     │     │    Layer     │     │     Layer       │
└─────────────┘     └──────────────┘     └─────────────────┘
     │                     │                       │
     │                     │                       ▼
     │                     │              ┌─────────────────┐
     │                     │              │ Normalization   │
     │                     │              │     Layer       │
     │                     │              └─────────────────┘
     │                     │                       │
     │                     │                       ▼
     │                     │              ┌─────────────────┐
     │                     └─────────────▶│   Enrichment    │
     │                                    │     Layer       │
     │                                    └─────────────────┘
     │                                             │
     │                                             ▼
     │                                    ┌─────────────────┐
     │                                    │  Grouping &     │
     └───────────────────────────────────▶│  Clustering     │
                                          └─────────────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │  DMN/DRD        │
                                          │  Generation     │
                                          └─────────────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │    Output       │
                                          │   (XML/MD/JSON) │
                                          └─────────────────┘
```

## Layer Details

### 1. Input Layer (`src/extractor/ingest.py`)

**Responsibility**: Scan repository and identify files to process.

**Components**:
- `RepositoryIngestor`: Main orchestrator
- File type detection
- Ignore pattern matching
- File size validation

**Input**: Repository path (string)

**Output**: List of file paths with metadata

**Configuration**:
```yaml
parsing:
  file_extensions:
    sql: [".sql", ".psql"]
    python: [".py"]
  ignore_patterns:
    - "*/node_modules/*"
  max_file_size_mb: 10
```

### 2. Parsing Layer

**Responsibility**: Parse files and extract syntax elements.

**Components**:

#### SQL Parser (`src/extractor/sql_parser.py`)
- Uses `sqlglot` for AST parsing
- Fallback to `sqlparse` for complex SQL
- Regex-based parsing for procedural SQL (PL/pgSQL)

**Handles**:
- SELECT/INSERT/UPDATE/DELETE statements
- CASE expressions
- WHERE/HAVING clauses
- CHECK constraints
- Stored procedures
- Functions
- Triggers

#### Application Code Parser (`src/extractor/app_parser.py`)
- Regex-based extraction
- Language-specific patterns (Python, Java, JavaScript)

**Handles**:
- Embedded SQL strings
- Conditional statements (if/else)
- Business logic patterns

**Input**: File path + content

**Output**: Raw syntax elements (not yet rules)

### 3. Rule Extraction Layer (Integrated in parsers)

**Responsibility**: Convert syntax elements into structured rules.

**Process**:
1. Identify rule patterns (IF, CASE, WHERE, CHECK)
2. Extract components (condition, action, variables)
3. Determine rule type
4. Calculate initial confidence score
5. Track source location

**Output**: `List[Rule]`

**Rule Structure**:
```python
Rule:
  id: str                    # Unique identifier (hash-based)
  rule_type: RuleType        # conditional, validation, constraint, etc.
  description: str           # Human-readable description
  normalized_expression: str # Normalized logic
  variables: List[str]       # Variables used
  tables: List[str]          # Tables referenced
  columns: List[str]         # Columns referenced
  source: SourceLocation     # File, line range, snippet
  confidence: float          # 0.0 to 1.0
  metadata: Dict             # Additional info
  embedding: List[float]     # Semantic embedding (added later)
```

### 4. Normalization Layer (`src/extractor/rule_normalizer.py`)

**Responsibility**: Clean and standardize rules.

**Operations**:
- Whitespace normalization
- Operator standardization (`==` → `=`)
- Identifier lowercasing
- Duplicate removal
- Low-quality filtering

**Input**: `List[Rule]` (raw)

**Output**: `List[Rule]` (normalized)

**Example**:
```
Input:  "total    >   1000   AND   Status  =  'active'"
Output: "total > 1000 AND status = 'active'"
```

### 5. Enrichment Layer (`src/extractor/enricher.py`)

**Responsibility**: Add semantic information using LLM.

**Components**:

#### LLM Adapters
```
LLMAdapter (interface)
├── StubLLMAdapter          # Deterministic (for testing)
├── AnthropicLLMAdapter     # Claude integration
└── OpenAILLMAdapter        # GPT integration (future)
```

**Operations**:
1. Generate embeddings for semantic similarity
2. Enhance descriptions (optional, with real LLM)
3. Map to domain concepts (pricing, eligibility, etc.)
4. Add metadata

**Input**: `List[Rule]` (normalized)

**Output**: `List[Rule]` (enriched with embeddings)

**Configuration**:
```yaml
llm:
  provider: "stub"  # or "anthropic"
  model: "claude-3-5-sonnet-20241022"
  api_key_env: "ANTHROPIC_API_KEY"
enrichment:
  enable_domain_mapping: true
  enable_semantic_analysis: true
```

### 6. Grouping & Clustering Layer (`src/extractor/clusterer.py`)

**Responsibility**: Group related rules into functional categories.

**Algorithms**:
- K-means (default)
- Hierarchical clustering
- DBSCAN
- Metadata-based fallback (no embeddings)

**Features**:
1. Semantic similarity (embedding-based)
2. Structural similarity (shared tables/columns)
3. Location-based grouping (same file/module)

**Input**: `List[Rule]` (enriched)

**Output**: `List[RuleGroup]`

**RuleGroup Structure**:
```python
RuleGroup:
  id: str
  name: str                      # "Pricing Rules - orders table"
  description: str               # Auto-generated summary
  rules: List[Rule]              # Rules in this group
  category: str                  # "Pricing", "Eligibility", etc.
  confidence: float              # Intra-cluster similarity
  centroid_embedding: List[float] # Group centroid
```

**Configuration**:
```yaml
clustering:
  method: "kmeans"
  n_clusters: 5
  min_similarity: 0.7
```

### 7. Dependency Analysis (In CLI)

**Responsibility**: Infer relationships between rule groups.

**Heuristics**:
- Shared tables → dataflow dependency
- Shared columns → data dependency
- Temporal ordering (if available)

**Output**: `List[RuleDependency]`

### 8. DMN/DRD Generation Layer (`src/extractor/drd_generator.py`)

**Responsibility**: Generate DMN-compliant XML and reports.

**Components**:

#### DMN Generator
- Creates XML structure using `lxml`
- Maps groups → Decisions
- Maps variables → Input Data
- Maps files → Knowledge Sources
- Adds traceability extensions

**DMN Elements Created**:
```xml
<definitions>
  <decision id="Decision_group_0" name="Pricing Rules">
    <decisionTable>
      <input id="input_1"/>
      <output id="output_1"/>
      <rule id="rule_1">
        <inputEntry><text>total > 1000</text></inputEntry>
        <outputEntry><text>0.10</text></outputEntry>
      </rule>
    </decisionTable>
    <extensionElements>
      <ext:traceability>
        <ext:source ruleId="rule_abc123"
                    file="procedures.sql"
                    startLine="5"
                    endLine="7"
                    confidence="0.9">
          <ext:snippet>IF total > 1000 THEN...</ext:snippet>
        </ext:source>
      </ext:traceability>
    </extensionElements>
  </decision>
</definitions>
```

#### Report Generator
- Markdown with human-readable format
- JSON for programmatic access
- Statistics tables

**Input**: `DecisionModel`

**Output**: DMN XML, Markdown, JSON

## Data Flow

### Complete Pipeline Example

```python
# 1. Ingest
ingestor = RepositoryIngestor(config)
rules = ingestor.ingest_repository("/path/to/repo")
# Output: [Rule, Rule, Rule, ...]

# 2. Normalize
normalizer = RuleNormalizer()
rules = normalizer.normalize_rules(rules)
rules = normalizer.deduplicate_rules(rules)
# Output: [Rule (normalized), ...]

# 3. Enrich
enricher = RuleEnricher(config)
rules = enricher.enrich_rules(rules)
# Output: [Rule (with embeddings), ...]

# 4. Cluster
clusterer = RuleClusterer(config)
groups = clusterer.cluster_rules(rules)
# Output: [RuleGroup, RuleGroup, ...]

# 5. Build model
model = DecisionModel(rules=rules, groups=groups, dependencies=deps)

# 6. Generate
generator = DRDGenerator(config)
dmn_xml = generator.generate_drd(model)
markdown = generator.generate_markdown_report(model)
# Output: XML string, Markdown string
```

## Key Design Decisions

### 1. Pydantic for Data Models
**Why**: Type safety, validation, serialization

### 2. Pipeline Architecture
**Why**: Clear separation of concerns, testability, modularity

### 3. Pluggable Adapters
**Why**: Easy to swap LLMs, parsers, or clustering algorithms

### 4. Configuration-Driven
**Why**: Flexibility without code changes

### 5. Stub LLM for Testing
**Why**: Deterministic tests without API calls or costs

### 6. Embedding-Based Clustering
**Why**: Captures semantic similarity better than keywords

### 7. DMN Standard
**Why**: Industry standard, interoperable, tool support

### 8. Full Traceability
**Why**: Critical for validation, debugging, compliance

## Extension Points

### Adding a New SQL Dialect

```python
# In sql_parser.py
class SQLParser:
    def __init__(self, dialect: str = "postgres"):
        self.dialect = dialect
        # Add new dialect support in sqlglot
```

### Adding a New LLM Provider

```python
# In enricher.py
class CustomLLMAdapter(LLMAdapter):
    def generate_embedding(self, text: str) -> List[float]:
        # Your implementation
        pass

    def generate_description(self, rule: Rule) -> str:
        # Your implementation
        pass
```

### Adding a New Clustering Method

```python
# In clusterer.py
def _cluster_custom(self, embeddings: np.ndarray) -> np.ndarray:
    # Your clustering logic
    return labels
```

### Adding a New Output Format

```python
# In drd_generator.py
def generate_bpmn(self, model: DecisionModel) -> str:
    # BPMN generation logic
    pass
```

## Performance Considerations

### Bottlenecks
1. **File I/O**: Mitigated with streaming and parallel processing
2. **Parsing**: Cached results, skip large files
3. **Embeddings**: Batch processing, use stub for testing
4. **Clustering**: Scales to ~10K rules efficiently

### Optimization Strategies
- Parallel file processing (`max_workers` config)
- Lazy loading of file contents
- Embedding caching
- Incremental processing (future)

## Error Handling

### Strategy
- Fail gracefully at file level (continue with others)
- Log errors with context
- Return partial results
- Provide dry-run mode for validation

### Error Types
1. **Parse errors**: Log and skip file
2. **Configuration errors**: Fail fast with clear message
3. **LLM errors**: Fall back to stub
4. **XML generation errors**: Validate and report

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock external dependencies (LLM, file system)
- Focus on edge cases

### Integration Tests
- Test full pipeline on sample repo
- Verify outputs are valid
- Check traceability links

### Test Data
- `sample_repos/sample_sql_app`: Realistic e-commerce example
- Covers all major rule types
- Known expected outputs for validation

## Security Considerations

### API Keys
- Never log or store API keys
- Use environment variables
- Support for secrets management (future)

### Code Injection
- No `eval()` or `exec()` used
- SQL parsing is read-only
- No execution of extracted code

### Data Privacy
- All processing is local by default
- LLM calls are optional
- No data sent to external services without explicit config

## Monitoring & Observability

### Logging
- Structured logging at INFO level
- DEBUG level for troubleshooting
- Progress indicators for long operations

### Metrics
- Rules extracted per file
- Processing time per stage
- Confidence score distributions
- Clustering quality metrics

### Outputs
- Statistics report
- Processing logs
- Validation results

## Future Architecture Enhancements

### Web Service Layer
```
FastAPI REST API
├── POST /analyze
├── GET /status/{job_id}
├── GET /results/{job_id}
└── WebSocket /progress
```

### Distributed Processing
- Celery for task queue
- Redis for caching
- PostgreSQL for results storage

### Real-time Analysis
- File system watcher
- Incremental updates
- Change detection

### Advanced Analytics
- Rule complexity metrics
- Change impact analysis
- Dependency graphs visualization
- Time-series analysis of rule evolution

---

**Last Updated**: 2025

**Architecture Version**: 1.0
