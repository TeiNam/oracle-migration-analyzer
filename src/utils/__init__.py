"""
공통 유틸리티 모듈

이 패키지는 프로젝트 전반에서 사용되는 공통 유틸리티 함수들을 제공합니다.

Modules:
    cli_helpers: CLI 관련 헬퍼 함수들
    file_utils: 파일 처리 유틸리티
    logging_utils: 로깅 설정 및 유틸리티
"""

from .cli_helpers import detect_file_type, generate_output_path, print_progress
from .file_utils import find_files_by_extension, read_file_with_encoding

__version__ = "1.0.0"
__all__ = [
    "detect_file_type",
    "generate_output_path",
    "print_progress",
    "find_files_by_extension",
    "read_file_with_encoding",
]
