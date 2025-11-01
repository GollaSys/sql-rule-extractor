"""SVG visualization for Decision Requirements Diagrams."""

import json
from pathlib import Path
from typing import Optional

import networkx as nx
import pygraphviz as pgv


class DRDVisualizer:
    """Generate SVG visualizations of DRD using Graphviz."""

    def __init__(self):
        """Initialize the visualizer."""
        pass

    def generate_svg_from_json(
        self,
        json_path: str,
        output_path: str,
        layout: str = "dot"
    ) -> None:
        """Generate SVG from JSON DRD data.

        Args:
            json_path: Path to JSON file containing DRD data
            output_path: Path to save SVG file
            layout: Graphviz layout engine (dot, neato, fdp, sfdp, circo, twopi)
        """
        # Load JSON data
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Create directed graph
        G = pgv.AGraph(directed=True, strict=False, rankdir='TB')

        # Set graph attributes for better visualization
        G.graph_attr.update({
            'fontname': 'Helvetica',
            'fontsize': '10',
            'bgcolor': 'white',
            'pad': '0.5',
            'ranksep': '1.0',
            'nodesep': '0.5'
        })

        G.node_attr.update({
            'fontname': 'Helvetica',
            'fontsize': '10',
            'shape': 'box',
            'style': 'rounded,filled',
            'fillcolor': '#e8f4f8',
            'color': '#4a90e2',
            'penwidth': '2'
        })

        G.edge_attr.update({
            'fontname': 'Helvetica',
            'fontsize': '8',
            'color': '#666666',
            'penwidth': '1.5',
            'arrowsize': '0.8'
        })

        # Add nodes for rule groups
        groups = data.get('groups', [])
        for group in groups:
            group_id = group['id']
            group_name = group['name']
            category = group.get('category', 'Unknown')
            num_rules = len(group.get('rules', []))
            confidence = group.get('confidence', 0.0)

            # Create node label with multiple lines
            label = f"{group_name}\\n"
            label += f"[{category}]\\n"
            label += f"{num_rules} rules | {confidence:.0%} conf"

            # Color by category
            color_map = {
                'Pricing': '#fff3e0',
                'Validation': '#e8f5e9',
                'Customer': '#f3e5f5',
                'Order': '#e3f2fd',
                'Inventory': '#fff9c4',
                'Payment': '#ffebee',
                'Eligibility': '#f1f8e9'
            }
            fillcolor = color_map.get(category, '#f5f5f5')

            G.add_node(
                group_id,
                label=label,
                fillcolor=fillcolor,
                shape='box',
                style='rounded,filled'
            )

        # Add edges for dependencies
        dependencies = data.get('dependencies', [])
        for dep in dependencies:
            source_id = dep['source_id']
            target_id = dep['target_id']
            dep_type = dep.get('dependency_type', 'dataflow')
            strength = dep.get('strength', 1.0)

            # Edge style based on strength
            if strength > 0.7:
                penwidth = '3'
                color = '#4a90e2'
            elif strength > 0.4:
                penwidth = '2'
                color = '#7fb3d5'
            else:
                penwidth = '1'
                color = '#aaaaaa'

            edge_label = f"{dep_type}\\n{strength:.2f}"

            G.add_edge(
                source_id,
                target_id,
                label=edge_label,
                penwidth=penwidth,
                color=color
            )

        # Layout and render
        G.layout(prog=layout)
        G.draw(output_path, format='svg')

        print(f"✓ SVG visualization saved to: {output_path}")
        print(f"  Groups: {len(groups)}")
        print(f"  Dependencies: {len(dependencies)}")
        print(f"  Layout: {layout}")

    def generate_rule_dependency_graph(
        self,
        json_path: str,
        output_path: str,
        max_rules: int = 50
    ) -> None:
        """Generate detailed rule-level dependency graph.

        Args:
            json_path: Path to JSON file containing DRD data
            output_path: Path to save SVG file
            max_rules: Maximum number of rules to visualize
        """
        # Load JSON data
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Create directed graph
        G = pgv.AGraph(directed=True, strict=False, rankdir='LR')

        # Set graph attributes
        G.graph_attr.update({
            'fontname': 'Helvetica',
            'fontsize': '10',
            'bgcolor': 'white',
            'pad': '0.5',
            'ranksep': '1.5'
        })

        G.node_attr.update({
            'fontname': 'Helvetica',
            'fontsize': '9',
            'shape': 'ellipse',
            'style': 'filled',
            'fillcolor': '#f0f0f0'
        })

        G.edge_attr.update({
            'fontname': 'Helvetica',
            'fontsize': '7',
            'color': '#888888',
            'arrowsize': '0.6'
        })

        # Add nodes for rules (limit to max_rules)
        rules = data.get('rules', [])[:max_rules]
        for rule in rules:
            rule_id = rule['id']
            rule_type = rule.get('rule_type', 'unknown')
            description = rule.get('description', '')[:50] + "..."

            # Truncate description
            label = f"{rule_id}\\n{description}"

            # Color by rule type
            type_colors = {
                'conditional': '#e3f2fd',
                'validation': '#e8f5e9',
                'calculation': '#fff3e0',
                'constraint': '#ffebee',
                'trigger': '#f3e5f5'
            }
            fillcolor = type_colors.get(rule_type, '#f5f5f5')

            G.add_node(
                rule_id,
                label=label,
                fillcolor=fillcolor,
                shape='box',
                style='rounded,filled'
            )

        # Add edges based on shared tables/columns
        for i, rule1 in enumerate(rules):
            tables1 = set(rule1.get('tables', []))
            columns1 = set(rule1.get('columns', []))

            for rule2 in rules[i+1:]:
                tables2 = set(rule2.get('tables', []))
                columns2 = set(rule2.get('columns', []))

                shared_tables = tables1 & tables2
                shared_columns = columns1 & columns2

                if shared_tables or shared_columns:
                    label = ""
                    if shared_tables:
                        label = f"Tables: {', '.join(list(shared_tables)[:2])}"

                    G.add_edge(
                        rule1['id'],
                        rule2['id'],
                        label=label,
                        dir='none'  # Undirected for shared resources
                    )

        # Layout and render
        G.layout(prog='fdp')  # Force-directed layout for rule graphs
        G.draw(output_path, format='svg')

        print(f"✓ Rule dependency graph saved to: {output_path}")
        print(f"  Rules: {len(rules)}")
        print(f"  (showing first {max_rules} rules)")


def main():
    """CLI for SVG visualization."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate SVG visualizations of Decision Requirements Diagrams"
    )
    parser.add_argument(
        '--json',
        required=True,
        help='Path to DRD JSON file'
    )
    parser.add_argument(
        '--out',
        required=True,
        help='Output SVG file path'
    )
    parser.add_argument(
        '--type',
        choices=['groups', 'rules'],
        default='groups',
        help='Visualization type: groups (default) or rules'
    )
    parser.add_argument(
        '--layout',
        choices=['dot', 'neato', 'fdp', 'sfdp', 'circo', 'twopi'],
        default='dot',
        help='Graphviz layout engine (default: dot)'
    )
    parser.add_argument(
        '--max-rules',
        type=int,
        default=50,
        help='Maximum rules to show in rule graph (default: 50)'
    )

    args = parser.parse_args()

    visualizer = DRDVisualizer()

    if args.type == 'groups':
        visualizer.generate_svg_from_json(
            args.json,
            args.out,
            layout=args.layout
        )
    else:
        visualizer.generate_rule_dependency_graph(
            args.json,
            args.out,
            max_rules=args.max_rules
        )


if __name__ == '__main__':
    main()
