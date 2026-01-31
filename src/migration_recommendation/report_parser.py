"""
리포트 파서

기존에 생성된 DBCSI 및 SQL 복잡도 분석 리포트(MD/JSON)를 파싱하여
마이그레이션 추천에 필요한 데이터를 추출합니다.

MD 파일 파싱을 우선하고, JSON은 폴백으로 사용합니다.

Note: 이 모듈은 하위 호환성을 위해 유지됩니다.
      실제 구현은 report_parser/ 패키지로 모듈화되었습니다.
"""

# 모듈화된 구현에서 re-export
from .report_parser import (
    MarkdownReportParser,
    ReportParser,
    find_reports_in_directory,
    find_reports_by_target,
)

# 내부 유틸리티 함수도 re-export (하위 호환성)
from .report_parser.utils import parse_number_with_comma as _parse_number_with_comma

__all__ = [
    "MarkdownReportParser",
    "ReportParser",
    "find_reports_in_directory",
    "find_reports_by_target",
    "_parse_number_with_comma",
]
