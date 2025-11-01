# DRD Viewing Guide

Complete guide to viewing and visualizing the Decision Requirements Diagram (DRD) output.

## Quick Start

After running the analyzer:
```bash
python -m src.cli analyze --repo sample_repos/sample_sql_app --out results/drd.xml --format all
```

You'll get three output files:
- `results/drd.xml` - DMN-compliant XML
- `results/drd.md` - Human-readable Markdown
- `results/drd.json` - Structured JSON data

## Viewing Options

### 1. 📄 Markdown Report (Easiest)

**Best for:** Quick review, sharing with non-technical stakeholders

**How to view:**
```bash
# In terminal
cat results/drd.md

# In VS Code
code results/drd.md

# In your default editor/browser
open results/drd.md
```

**What you get:**
- Summary statistics (total rules, groups, dependencies)
- Rule groups organized by category
- Individual rules with descriptions
- Clickable links to source code (in supported editors)

**Example output:**
```markdown
### Pricing - orders
**Category:** Pricing
**Confidence:** 0.35
**Rules:** 10

#### Rules:
- rule_abc123: Procedural IF: total > 1000
  Source: procedures.sql#L7
```

---

### 2. 🖼️ SVG Visualization (Graph View)

**Best for:** Visual graph representation, presentations, publications

**How to use:**

1. **Generate SVG from JSON:**
   ```bash
   # Group-level dependency graph (hierarchical)
   python -m src.utils.svg_visualizer --json results/drd.json --out results/drd_groups.svg --type groups --layout dot

   # Circular layout for groups
   python -m src.utils.svg_visualizer --json results/drd.json --out results/drd_groups_circo.svg --type groups --layout circo

   # Rule-level dependency graph (first 30 rules)
   python -m src.utils.svg_visualizer --json results/drd.json --out results/drd_rules.svg --type rules --max-rules 30
   ```

2. **View the SVG:**
   ```bash
   # Open in default viewer
   open results/drd_groups.svg

   # Or in browser
   open -a "Google Chrome" results/drd_groups.svg

   # Or in VS Code
   code results/drd_groups.svg
   ```

**Prerequisites:**
- Requires Graphviz installed: `brew install graphviz`
- Requires pygraphviz: `pip install pygraphviz`

**Layout options:**
- `dot` - Hierarchical (default, best for decision flows)
- `circo` - Circular (good for showing relationships)
- `neato` - Spring model (force-directed)
- `fdp` - Force-directed (used for rule graphs)
- `sfdp` - Scalable force-directed (for large graphs)
- `twopi` - Radial layout

**Features:**
- ✅ High-quality vector graphics (scalable)
- ✅ Color-coded by category
- ✅ Shows dependency strength
- ✅ Multiple layout algorithms
- ✅ Ready for presentations/documents

**Example output:**
- Groups are shown as rounded boxes
- Color indicates category (Pricing, Validation, etc.)
- Arrows show dependencies with strength labels
- Edge thickness indicates dependency strength

---

### 3. 🌐 HTML Viewer (Interactive)

**Best for:** Interactive exploration, presentations

**How to use:**
1. Open `view_drd.html` in any web browser:
   ```bash
   open view_drd.html
   ```

2. Click "Choose File" and select `results/drd.json`

3. Explore the interactive view with:
   - Summary statistics cards
   - Expandable rule groups
   - Color-coded categories
   - Confidence scores
   - Source links

**Features:**
- ✅ Works offline (no internet required)
- ✅ Beautiful, responsive design
- ✅ No installation needed
- ✅ Works in any modern browser

---

### 4. 🎨 Professional DMN Tools

**Best for:** Professional DMN modeling, compliance documentation

#### Option A: Camunda Modeler (Recommended - Free & Offline)

1. **Download:**
   - Visit: https://camunda.com/download/modeler/
   - Download for your OS (macOS/Windows/Linux)

2. **Install:**
   ```bash
   # macOS
   open ~/Downloads/camunda-modeler-*.dmg
   # Drag to Applications

   # Or with Homebrew
   brew install --cask camunda-modeler
   ```

3. **Open your DRD:**
   - Launch Camunda Modeler
   - File → Open → Select `results/drd.xml`
   - View visual decision diagram
   - Edit if needed

**What you get:**
- Professional DMN 1.3 compliant viewer
- Visual decision diagram
- Decision table editor
- DMN validation
- Export to PDF/SVG

#### Option B: bpmn.io DMN Viewer (Online - Free)

1. **Visit:** https://demo.bpmn.io/dmn

2. **Load your DRD:**
   - Drag and drop `results/drd.xml` onto the page
   - Or click "Open file" and select it

3. **Explore:**
   - View decision graphs
   - Inspect decision tables
   - Navigate requirements

**Advantages:**
- ✅ No installation
- ✅ Quick and easy
- ✅ DMN 1.3 compliant

**Limitations:**
- ❌ Requires internet
- ❌ Limited editing features

#### Option C: Trisotech Digital Enterprise Suite

**For enterprise users:**
- Visit: https://www.trisotech.com/
- Free trial available
- Professional DMN authoring and simulation
- Advanced features for governance

---

### 5. 📊 JSON Data (Programmatic)

**Best for:** Custom visualization, data analysis, integration

**View in terminal:**
```bash
# Pretty print with jq
cat results/drd.json | jq '.' | less

# View specific sections
cat results/drd.json | jq '.groups[] | {name, category, rules: (.rules | length)}'

# Get summary
cat results/drd.json | jq '{
  total_rules: (.rules | length),
  total_groups: (.groups | length),
  total_deps: (.dependencies | length)
}'
```

**View in VS Code:**
```bash
code results/drd.json
```

**Structure:**
```json
{
  "rules": [
    {
      "id": "rule_abc123",
      "rule_type": "conditional",
      "description": "...",
      "normalized_expression": "...",
      "source": {
        "file_path": "...",
        "start_line": 10,
        "end_line": 15,
        "snippet": "..."
      }
    }
  ],
  "groups": [...],
  "dependencies": [...]
}
```

**Use cases:**
- Custom visualization with D3.js, Chart.js
- Import into BI tools (Tableau, Power BI)
- Integration with other systems
- Custom analysis scripts

---

### 6. 🔍 XML Inspection

**Best for:** Technical inspection, DMN validation

**View in terminal:**
```bash
# Pretty print XML
xmllint --format results/drd.xml | less

# Validate against DMN schema (if you have the schema)
xmllint --noout --schema dmn.xsd results/drd.xml
```

**View in VS Code:**
```bash
code results/drd.xml
```

**View in browser:**
```bash
open results/drd.xml
```
Most browsers will show formatted XML with syntax highlighting.

**What to look for:**
- `<decision>` elements for each rule group
- `<inputData>` elements for variables
- `<knowledgeSource>` elements for source files
- `<extensionElements>` with traceability info

---

## Comparison Table

| Method | Ease of Use | Features | Offline | Best For |
|--------|-------------|----------|---------|----------|
| Markdown | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | Quick review |
| SVG Visualization | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | Graph visualization |
| HTML Viewer | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | Interactive exploration |
| Camunda | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | Professional DMN |
| bpmn.io | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | Quick online viewing |
| JSON | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | Custom development |
| XML | ⭐⭐ | ⭐⭐⭐ | ✅ | Technical inspection |

---

## Creating Custom Visualizations

### With Python (Matplotlib/NetworkX)

```python
import json
import matplotlib.pyplot as plt
import networkx as nx

# Load data
with open('results/drd.json') as f:
    data = json.load(f)

# Create graph
G = nx.DiGraph()

# Add nodes for groups
for group in data['groups']:
    G.add_node(group['id'],
               label=group['name'],
               category=group['category'])

# Add edges for dependencies
for dep in data['dependencies']:
    G.add_edge(dep['source_id'], dep['target_id'])

# Plot
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color='lightblue',
        node_size=3000, font_size=10, arrows=True)
plt.savefig('drd_graph.png')
plt.show()
```

### With JavaScript (D3.js)

```javascript
// Load JSON
fetch('results/drd.json')
  .then(response => response.json())
  .then(data => {
    // Create visualization with D3.js
    // See: https://d3js.org/
  });
```

---

## Sharing Your DRD

### For Technical Teams
- Share the `drd.xml` (DMN standard)
- Include link to source repository
- Reference specific rules by ID

### For Business Stakeholders
- Share the `drd.md` (most readable)
- Export HTML viewer to PDF
- Include summary statistics

### For Documentation
- Include all three formats
- Add screenshots from Camunda Modeler
- Link to source code in git

---

## Troubleshooting

### "XML is not well-formed"
- Regenerate with `--format dmn`
- Check for special characters in source code
- Validate with `xmllint`

### "Can't open in Camunda Modeler"
- Ensure DMN 1.3 compatibility
- Check XML syntax errors
- Try bpmn.io online viewer first

### "HTML viewer doesn't work"
- Ensure JavaScript is enabled
- Check browser console for errors
- Try a different browser (Chrome recommended)

### "Markdown links don't work"
- Links work in VS Code, GitHub, and some editors
- Use relative paths in config
- Check file paths are correct

---

## Tips & Best Practices

1. **Always generate all formats:**
   ```bash
   --format all
   ```

2. **Use meaningful output names:**
   ```bash
   --out reports/2024-Q4-rules.xml
   ```

3. **Version control your outputs:**
   ```bash
   git add reports/*.xml reports/*.md
   git commit -m "Update business rules documentation"
   ```

4. **Automate in CI/CD:**
   ```yaml
   # .github/workflows/rules-doc.yml
   - name: Generate DRD
     run: |
       python -m src.cli analyze --repo . --out drd.xml --format all
       git add drd.*
   ```

5. **Schedule regular updates:**
   - Weekly for active projects
   - Monthly for stable codebases
   - After major changes

---

## Further Reading

- [DMN Specification](https://www.omg.org/dmn/)
- [Camunda DMN Tutorial](https://camunda.com/bpmn/reference/#dmn-decision-model-and-notation)
- [bpmn.io Documentation](https://bpmn.io/toolkit/dmn-js/)

---

**Need help?** Check the main [README.md](README.md) or open an issue.
