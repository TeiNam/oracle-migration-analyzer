"""
Oracle Complexity Analyzer CLI 모듈

CLI 관련 기능을 제공합니다.
"""

from .parser import create_parser
from .utils import normalize_target, is_all_targets
from .console_output import (
    print_result_console,
    print_batch_result_console,
    print_batch_analysis_summary
)
from .single_file import analyze_single_file, analyze_single_file_all_targets
from .directory import analyze_directory, analyze_directory_all_targets

__all__ = [
    "create_parser",
    "normalize_target",
    "is_all_targets",
    "print_result_console",
    "print_batch_result_console",
    "print_batch_analysis_summary",
    "analyze_single_file",
    "analyze_single_file_all_targets",
    "analyze_directory",
    "analyze_directory_all_targets",
]
