"""Clustering and grouping of business rules."""

import logging
from typing import List, Dict
import numpy as np
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

from . import Rule, RuleGroup


logger = logging.getLogger(__name__)


class RuleClusterer:
    """Cluster rules into functional groups."""

    def __init__(self, config: Dict):
        """
        Initialize clusterer.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.clustering_config = config.get("clustering", {})

    def cluster_rules(self, rules: List[Rule]) -> List[RuleGroup]:
        """
        Cluster rules into functional groups.

        Args:
            rules: List of rules to cluster

        Returns:
            List of rule groups
        """
        if len(rules) == 0:
            return []

        logger.info(f"Clustering {len(rules)} rules")

        # Extract embeddings
        embeddings = self._extract_embeddings(rules)

        if embeddings is None:
            logger.warning("No embeddings available, using metadata-based grouping")
            return self._cluster_by_metadata(rules)

        # Perform clustering
        method = self.clustering_config.get("method", "kmeans")

        if method == "kmeans":
            labels = self._cluster_kmeans(embeddings)
        elif method == "hierarchical":
            labels = self._cluster_hierarchical(embeddings)
        elif method == "dbscan":
            labels = self._cluster_dbscan(embeddings)
        else:
            logger.warning(f"Unknown clustering method {method}, using kmeans")
            labels = self._cluster_kmeans(embeddings)

        # Create rule groups
        groups = self._create_groups(rules, labels, embeddings)

        logger.info(f"Created {len(groups)} rule groups")
        return groups

    def _extract_embeddings(self, rules: List[Rule]) -> np.ndarray:
        """Extract embeddings from rules."""
        embeddings = []

        for rule in rules:
            if rule.embedding is not None:
                embeddings.append(rule.embedding)
            else:
                return None

        return np.array(embeddings)

    def _cluster_kmeans(self, embeddings: np.ndarray) -> np.ndarray:
        """Cluster using K-means."""
        n_clusters = min(
            self.clustering_config.get("n_clusters", 5),
            len(embeddings)
        )

        logger.info(f"Clustering with K-means (k={n_clusters})")

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)

        return labels

    def _cluster_hierarchical(self, embeddings: np.ndarray) -> np.ndarray:
        """Cluster using hierarchical clustering."""
        n_clusters = min(
            self.clustering_config.get("n_clusters", 5),
            len(embeddings)
        )

        logger.info(f"Clustering with hierarchical (k={n_clusters})")

        clusterer = AgglomerativeClustering(n_clusters=n_clusters)
        labels = clusterer.fit_predict(embeddings)

        return labels

    def _cluster_dbscan(self, embeddings: np.ndarray) -> np.ndarray:
        """Cluster using DBSCAN."""
        eps = self.clustering_config.get("eps", 0.3)
        min_samples = self.clustering_config.get("min_samples", 2)

        logger.info(f"Clustering with DBSCAN (eps={eps}, min_samples={min_samples})")

        clusterer = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
        labels = clusterer.fit_predict(embeddings)

        return labels

    def _cluster_by_metadata(self, rules: List[Rule]) -> List[RuleGroup]:
        """Fallback clustering using metadata."""
        groups_dict = {}

        for rule in rules:
            # Group by file path and rule type
            key = (rule.source.file_path, rule.rule_type.value)

            if key not in groups_dict:
                groups_dict[key] = []

            groups_dict[key].append(rule)

        # Create groups
        groups = []
        for i, ((file_path, rule_type), group_rules) in enumerate(groups_dict.items()):
            group = RuleGroup(
                id=f"group_{i}",
                name=f"{rule_type.title()} rules from {file_path}",
                description=f"Rules of type {rule_type} from {file_path}",
                rules=group_rules,
                category=self._infer_category(group_rules),
                confidence=0.7
            )
            groups.append(group)

        return groups

    def _create_groups(
        self, rules: List[Rule], labels: np.ndarray, embeddings: np.ndarray
    ) -> List[RuleGroup]:
        """Create rule groups from clustering labels."""
        groups_dict = {}

        # Group rules by label
        for rule, label in zip(rules, labels):
            label = int(label)  # Convert to Python int

            if label not in groups_dict:
                groups_dict[label] = []

            groups_dict[label].append(rule)

        # Create RuleGroup objects
        groups = []
        for label, group_rules in groups_dict.items():
            # Skip noise cluster from DBSCAN (-1)
            if label == -1:
                logger.info(f"Skipping {len(group_rules)} rules in noise cluster")
                continue

            # Calculate centroid
            group_embeddings = np.array([r.embedding for r in group_rules])
            centroid = np.mean(group_embeddings, axis=0)

            # Infer category and name
            category = self._infer_category(group_rules)
            name = self._infer_group_name(group_rules, category)

            # Calculate confidence based on intra-cluster similarity
            confidence = self._calculate_group_confidence(group_embeddings, centroid)

            group = RuleGroup(
                id=f"group_{label}",
                name=name,
                description=self._generate_group_description(group_rules),
                rules=group_rules,
                category=category,
                confidence=confidence,
                centroid_embedding=centroid.tolist()
            )
            groups.append(group)

        return groups

    def _infer_category(self, rules: List[Rule]) -> str:
        """Infer category from rules."""
        # Count domain concepts
        concept_counts = {}

        for rule in rules:
            concepts = rule.metadata.get("domain_concepts", [])
            for concept in concepts:
                concept_counts[concept] = concept_counts.get(concept, 0) + 1

        if concept_counts:
            # Return most common concept
            return max(concept_counts.items(), key=lambda x: x[1])[0].title()

        # Fallback to rule type
        return rules[0].rule_type.value.title() if rules else "General"

    def _infer_group_name(self, rules: List[Rule], category: str) -> str:
        """Infer group name."""
        # Get common tables
        table_counts = {}
        for rule in rules:
            for table in rule.tables:
                table_counts[table] = table_counts.get(table, 0) + 1

        if table_counts:
            common_table = max(table_counts.items(), key=lambda x: x[1])[0]
            return f"{category} - {common_table}"

        return f"{category} Rules"

    def _generate_group_description(self, rules: List[Rule]) -> str:
        """Generate description for group."""
        rule_types = set(r.rule_type.value for r in rules)
        tables = set()
        for r in rules:
            tables.update(r.tables)

        desc_parts = [
            f"Group of {len(rules)} rules",
            f"Types: {', '.join(rule_types)}",
        ]

        if tables:
            desc_parts.append(f"Tables: {', '.join(list(tables)[:3])}")

        return ". ".join(desc_parts)

    def _calculate_group_confidence(
        self, embeddings: np.ndarray, centroid: np.ndarray
    ) -> float:
        """Calculate confidence score for group."""
        if len(embeddings) == 0:
            return 0.0

        # Calculate average cosine similarity to centroid
        centroid_reshaped = centroid.reshape(1, -1)
        similarities = cosine_similarity(embeddings, centroid_reshaped)
        avg_similarity = np.mean(similarities)

        return float(avg_similarity)
