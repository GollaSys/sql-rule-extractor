"""DMN-compliant DRD (Decision Requirements Diagram) generation."""

import logging
from typing import List, Dict, Set
from datetime import datetime
from lxml import etree as ET
import networkx as nx

from . import Rule, RuleGroup, RuleDependency, DecisionModel


logger = logging.getLogger(__name__)


class DRDGenerator:
    """Generate DMN-compliant Decision Requirements Documents."""

    def __init__(self, config: Dict):
        """
        Initialize DRD generator.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.dmn_config = config.get("dmn", {})

        # DMN namespaces
        self.namespaces = {
            "dmn": "https://www.omg.org/spec/DMN/20191111/MODEL/",
            "dmndi": "https://www.omg.org/spec/DMN/20191111/DMNDI/",
            "dc": "http://www.omg.org/spec/DMN/20180521/DC/",
            "di": "http://www.omg.org/spec/DMN/20180521/DI/",
            "ext": self.dmn_config.get("namespace", "http://sql-rule-extractor/dmn")
        }

    def generate_drd(self, decision_model: DecisionModel) -> str:
        """
        Generate DMN XML from decision model.

        Args:
            decision_model: Complete decision model

        Returns:
            DMN XML string
        """
        logger.info("Generating DMN/DRD")

        # Create root element
        root = self._create_root()

        # Create decision graph
        graph = self._build_decision_graph(decision_model)

        # Add decisions (one per rule group)
        for group in decision_model.groups:
            self._add_decision(root, group, decision_model)

        # Add input data elements
        input_data_elements = self._identify_input_data(decision_model)
        for input_data in input_data_elements:
            self._add_input_data(root, input_data)

        # Add knowledge sources (files)
        knowledge_sources = self._identify_knowledge_sources(decision_model)
        for ks in knowledge_sources:
            self._add_knowledge_source(root, ks)

        # Convert to string
        xml_str = self._to_xml_string(root)

        return xml_str

    def _create_root(self) -> ET.Element:
        """Create root DMN element."""
        # Register namespaces
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix, uri)

        # Create root
        root = ET.Element(
            f"{{{self.namespaces['dmn']}}}definitions",
            nsmap=self.namespaces,
            attrib={
                "id": "sql_rule_extractor_drd",
                "name": "SQL Codebase Business Rules",
                "namespace": self.namespaces["ext"],
                "exporter": self.dmn_config.get("exporter", "SQL Rule Extractor"),
                "exporterVersion": self.dmn_config.get("exporter_version", "1.0.0")
            }
        )

        return root

    def _add_decision(
        self, root: ET.Element, group: RuleGroup, model: DecisionModel
    ) -> None:
        """Add a decision element for a rule group."""
        decision_id = f"{self.dmn_config.get('decision_prefix', 'Decision_')}{group.id}"

        decision = ET.SubElement(
            root,
            f"{{{self.namespaces['dmn']}}}decision",
            attrib={
                "id": decision_id,
                "name": group.name
            }
        )

        # Add description
        desc = ET.SubElement(decision, f"{{{self.namespaces['dmn']}}}description")
        desc.text = group.description

        # Add variable
        variable = ET.SubElement(
            decision,
            f"{{{self.namespaces['dmn']}}}variable",
            attrib={
                "id": f"var_{decision_id}",
                "name": group.name.replace(" ", "_").lower()
            }
        )

        # Add decision table or literal expression
        self._add_decision_logic(decision, group)

        # Add information requirements (dependencies)
        for dep in model.dependencies:
            if dep.source_id == group.id:
                info_req = ET.SubElement(
                    decision,
                    f"{{{self.namespaces['dmn']}}}informationRequirement"
                )
                required_decision = ET.SubElement(
                    info_req,
                    f"{{{self.namespaces['dmn']}}}requiredDecision",
                    attrib={"href": f"#Decision_{dep.target_id}"}
                )

        # Add traceability extension
        if self.dmn_config.get("include_extensions", True):
            self._add_traceability_extension(decision, group)

    def _add_decision_logic(self, decision: ET.Element, group: RuleGroup) -> None:
        """Add decision logic (decision table or literal expression)."""
        if len(group.rules) <= 3:
            # Use literal expression for simple decisions
            expr = ET.SubElement(
                decision,
                f"{{{self.namespaces['dmn']}}}literalExpression",
                attrib={"id": f"expr_{group.id}"}
            )

            # Combine rules into expression
            text_parts = []
            for rule in group.rules:
                text_parts.append(rule.normalized_expression)

            text_elem = ET.SubElement(expr, f"{{{self.namespaces['dmn']}}}text")
            text_elem.text = "\n".join(text_parts)
        else:
            # Use decision table for complex decisions
            table = ET.SubElement(
                decision,
                f"{{{self.namespaces['dmn']}}}decisionTable",
                attrib={
                    "id": f"table_{group.id}",
                    "hitPolicy": "FIRST"
                }
            )

            # Add input (simplified)
            input_elem = ET.SubElement(
                table,
                f"{{{self.namespaces['dmn']}}}input",
                attrib={"id": f"input_{group.id}"}
            )

            # Add output
            output_elem = ET.SubElement(
                table,
                f"{{{self.namespaces['dmn']}}}output",
                attrib={"id": f"output_{group.id}", "name": "result"}
            )

            # Add rules
            for i, rule in enumerate(group.rules[:10]):  # Limit to 10 for brevity
                rule_elem = ET.SubElement(
                    table,
                    f"{{{self.namespaces['dmn']}}}rule",
                    attrib={"id": f"rule_{group.id}_{i}"}
                )

                # Input entry
                input_entry = ET.SubElement(
                    rule_elem,
                    f"{{{self.namespaces['dmn']}}}inputEntry",
                    attrib={"id": f"input_entry_{group.id}_{i}"}
                )
                input_text = ET.SubElement(input_entry, f"{{{self.namespaces['dmn']}}}text")
                input_text.text = rule.normalized_expression[:100]

                # Output entry
                output_entry = ET.SubElement(
                    rule_elem,
                    f"{{{self.namespaces['dmn']}}}outputEntry",
                    attrib={"id": f"output_entry_{group.id}_{i}"}
                )
                output_text = ET.SubElement(output_entry, f"{{{self.namespaces['dmn']}}}text")
                output_text.text = "true"

    def _add_traceability_extension(
        self, decision: ET.Element, group: RuleGroup
    ) -> None:
        """Add custom extension elements for traceability."""
        ext_elements = ET.SubElement(
            decision,
            f"{{{self.namespaces['dmn']}}}extensionElements"
        )

        traceability = ET.SubElement(
            ext_elements,
            f"{{{self.namespaces['ext']}}}traceability"
        )

        # Add source information for each rule
        for rule in group.rules:
            source_elem = ET.SubElement(
                traceability,
                f"{{{self.namespaces['ext']}}}source",
                attrib={
                    "ruleId": rule.id,
                    "file": rule.source.file_path,
                    "startLine": str(rule.source.start_line),
                    "endLine": str(rule.source.end_line),
                    "confidence": str(rule.confidence)
                }
            )

            # Add code snippet
            snippet_elem = ET.SubElement(
                source_elem,
                f"{{{self.namespaces['ext']}}}snippet"
            )
            snippet_elem.text = rule.source.snippet

    def _add_input_data(self, root: ET.Element, input_data: Dict) -> None:
        """Add input data element."""
        input_id = f"{self.dmn_config.get('input_data_prefix', 'InputData_')}{input_data['name']}"

        input_elem = ET.SubElement(
            root,
            f"{{{self.namespaces['dmn']}}}inputData",
            attrib={
                "id": input_id,
                "name": input_data["name"]
            }
        )

        # Add variable
        variable = ET.SubElement(
            input_elem,
            f"{{{self.namespaces['dmn']}}}variable",
            attrib={
                "id": f"var_{input_id}",
                "name": input_data["name"]
            }
        )

    def _add_knowledge_source(self, root: ET.Element, ks: Dict) -> None:
        """Add knowledge source element."""
        ks_id = f"KnowledgeSource_{ks['id']}"

        ks_elem = ET.SubElement(
            root,
            f"{{{self.namespaces['dmn']}}}knowledgeSource",
            attrib={
                "id": ks_id,
                "name": ks["name"]
            }
        )

        # Add description with file path
        desc = ET.SubElement(ks_elem, f"{{{self.namespaces['dmn']}}}description")
        desc.text = f"Source file: {ks['file_path']}"

    def _identify_input_data(self, model: DecisionModel) -> List[Dict]:
        """Identify input data elements from rules."""
        input_data_set = set()

        for group in model.groups:
            for rule in group.rules:
                # Add columns as input data
                for column in rule.columns:
                    input_data_set.add(column)

        return [{"name": name, "id": name} for name in sorted(input_data_set)]

    def _identify_knowledge_sources(self, model: DecisionModel) -> List[Dict]:
        """Identify knowledge sources (source files)."""
        files = set()

        for group in model.groups:
            for rule in group.rules:
                files.add(rule.source.file_path)

        return [
            {"id": f"file_{i}", "name": f"File {i+1}", "file_path": fp}
            for i, fp in enumerate(sorted(files))
        ]

    def _build_decision_graph(self, model: DecisionModel) -> nx.DiGraph:
        """Build directed graph of decision dependencies."""
        graph = nx.DiGraph()

        # Add nodes for each group
        for group in model.groups:
            graph.add_node(group.id, data=group)

        # Add edges for dependencies
        for dep in model.dependencies:
            graph.add_edge(dep.source_id, dep.target_id, weight=dep.strength)

        return graph

    def _to_xml_string(self, root: ET.Element) -> str:
        """Convert element tree to formatted XML string."""
        pretty_print = self.config.get("output", {}).get("pretty_print_xml", True)

        xml_bytes = ET.tostring(
            root,
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=pretty_print
        )

        return xml_bytes.decode("utf-8")

    def generate_markdown_report(self, model: DecisionModel) -> str:
        """Generate human-readable Markdown report."""
        lines = []

        lines.append("# Business Rules Report")
        lines.append("")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- Total Rules: {len(model.rules)}")
        lines.append(f"- Rule Groups: {len(model.groups)}")
        lines.append(f"- Dependencies: {len(model.dependencies)}")
        lines.append("")

        # Groups
        lines.append("## Rule Groups")
        lines.append("")

        for group in model.groups:
            lines.append(f"### {group.name}")
            lines.append("")
            lines.append(f"**Category:** {group.category}")
            lines.append(f"**Confidence:** {group.confidence:.2f}")
            lines.append(f"**Rules:** {len(group.rules)}")
            lines.append("")
            lines.append(group.description)
            lines.append("")

            # List rules
            lines.append("#### Rules:")
            for rule in group.rules[:5]:  # Show first 5
                lines.append(f"- [{rule.id}]({rule.source.file_path}#L{rule.source.start_line}): {rule.description}")

            if len(group.rules) > 5:
                lines.append(f"- ... and {len(group.rules) - 5} more")

            lines.append("")

        return "\n".join(lines)
