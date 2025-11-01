"""Core extraction modules."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class RuleType(str, Enum):
    """Types of business rules."""
    CONDITIONAL = "conditional"
    VALIDATION = "validation"
    CALCULATION = "calculation"
    CONSTRAINT = "constraint"
    TRIGGER = "trigger"


class SourceLocation(BaseModel):
    """Location of code in source repository."""
    file_path: str
    start_line: int
    end_line: int
    snippet: str
    git_info: Optional[Dict[str, str]] = None


class Rule(BaseModel):
    """Extracted business rule."""
    id: str
    rule_type: RuleType
    description: str
    normalized_expression: str
    variables: List[str] = Field(default_factory=list)
    tables: List[str] = Field(default_factory=list)
    columns: List[str] = Field(default_factory=list)
    source: SourceLocation
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None


class RuleGroup(BaseModel):
    """Group of related rules."""
    id: str
    name: str
    description: str
    rules: List[Rule]
    category: str  # e.g., "Pricing", "Eligibility", "Authorization"
    confidence: float
    centroid_embedding: Optional[List[float]] = None


class RuleDependency(BaseModel):
    """Dependency between rules or rule groups."""
    source_id: str
    target_id: str
    dependency_type: str  # "dataflow", "precedence", "conditional"
    strength: float = 1.0


class DecisionModel(BaseModel):
    """Complete decision model with rules, groups, and relationships."""
    rules: List[Rule]
    groups: List[RuleGroup]
    dependencies: List[RuleDependency]
    metadata: Dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "RuleType",
    "SourceLocation",
    "Rule",
    "RuleGroup",
    "RuleDependency",
    "DecisionModel",
]
