"""
DBCSI CLI 모듈

Statspack/AWR 분석 도구의 CLI 인터페이스를 제공합니다.
"""

from .argument_parser import create_parser, validate_args, get_target_databases
from .command_handlers import (
    detect_and_parse,
    process_single_file,
    process_directory,
    process_compare
)
from .__main__ import main

# Public API
__all__ = [
    'create_parser',
    'validate_args',
    'get_target_databases',
    'detect_and_parse',
    'process_single_file',
    'process_directory',
    'process_compare',
    'main'
]
