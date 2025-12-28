"""
Shared TNSNamesParser Instance
전역적으로 공유되는 TNSNamesParser 싱글톤 인스턴스
"""

import importlib.util
from pathlib import Path
from typing import Any

# Import TNSNamesParser from mcp directory using importlib
project_root = Path(__file__).parent.parent.parent.parent
mcp_path = project_root / "mcp"

tnsnames_parser_spec = importlib.util.spec_from_file_location(
    "tnsnames_parser",
    mcp_path / "tnsnames_parser.py"
)
if tnsnames_parser_spec and tnsnames_parser_spec.loader:
    tnsnames_parser_module = importlib.util.module_from_spec(tnsnames_parser_spec)
    tnsnames_parser_spec.loader.exec_module(tnsnames_parser_module)
    TNSNamesParser: Any = tnsnames_parser_module.TNSNamesParser  # type: ignore
else:
    raise ImportError("Failed to load tnsnames_parser module")

# Global shared instance
_tnsnames_parser_instance = None


def get_tnsnames_parser() -> TNSNamesParser:
    """
    Get or create the shared TNSNamesParser instance

    Returns:
        TNSNamesParser: 공유 인스턴스
    """
    global _tnsnames_parser_instance

    if _tnsnames_parser_instance is None:
        _tnsnames_parser_instance = TNSNamesParser()

    return _tnsnames_parser_instance
