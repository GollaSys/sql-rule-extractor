"""File I/O utilities."""

import json
from pathlib import Path
from typing import Any, Dict
import yaml


def load_config(config_path: str) -> Dict:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def save_json(data: Any, output_path: str, pretty: bool = True) -> None:
    """
    Save data as JSON.

    Args:
        data: Data to save
        output_path: Output file path
        pretty: Whether to pretty-print
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        if pretty:
            json.dump(data, f, indent=2, default=str)
        else:
            json.dump(data, f, default=str)


def load_json(input_path: str) -> Any:
    """
    Load data from JSON file.

    Args:
        input_path: Input file path

    Returns:
        Loaded data
    """
    with open(input_path, 'r') as f:
        return json.load(f)


def save_text(content: str, output_path: str) -> None:
    """
    Save text content to file.

    Args:
        content: Text content
        output_path: Output file path
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(content)


def ensure_dir(path: str) -> None:
    """
    Ensure directory exists.

    Args:
        path: Directory path
    """
    Path(path).mkdir(parents=True, exist_ok=True)
