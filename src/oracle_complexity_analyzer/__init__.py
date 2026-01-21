"""
Oracle Complexity Analyzer

Oracle SQL 및 PL/SQL 코드의 복잡도를 분석하여 PostgreSQL 또는 MySQL로의 
마이그레이션 난이도를 0-10 척도로 평가하는 도구입니다.

이 패키지는 다음과 같은 주요 기능을 제공합니다:
- SQL 쿼리 복잡도 분석
- PL/SQL 오브젝트 복잡도 분석
- 배치 파일 분석
- 타겟 데이터베이스별 마이그레이션 난이도 평가
- JSON/Markdown 형식의 분석 결과 출력

사용 예시:
    >>> from oracle_complexity_analyzer import OracleComplexityAnalyzer, TargetDatabase
    >>> analyzer = OracleComplexityAnalyzer(target_database=TargetDatabase.POSTGRESQL)
    >>> result = analyzer.analyze_sql("SELECT * FROM users WHERE id = 1")
    >>> print(result.normalized_score)
"""

from typing import Union

# Enum 타입
from .enums import (
    TargetDatabase,
    ComplexityLevel,
    PLSQLObjectType,
)

# 데이터 모델
from .data_models import (
    SQLAnalysisResult,
    PLSQLAnalysisResult,
    BatchAnalysisResult,
    WeightConfig,
)

# 상수 (constants.py에서 import)
from .constants import (
    ORACLE_SPECIFIC_SYNTAX,
    ORACLE_SPECIFIC_FUNCTIONS,
    ANALYTIC_FUNCTIONS,
    AGGREGATE_FUNCTIONS,
    ORACLE_HINTS,
    PLSQL_ADVANCED_FEATURES,
    EXTERNAL_DEPENDENCIES,
)

# 가중치 설정 (weights.py에서 import)
from .weights import (
    POSTGRESQL_WEIGHTS,
    MYSQL_WEIGHTS,
    PLSQL_BASE_SCORES,
    MYSQL_APP_MIGRATION_PENALTY,
)

# 메인 분석기
from .analyzer import OracleComplexityAnalyzer

# 배치 분석기
from .batch_analyzer import BatchAnalyzer

# 파일 감지 유틸리티
from .file_detector import (
    is_plsql,
    is_batch_plsql,
    detect_file_type,
)

# 내보내기 유틸리티
from .export_utils import (
    get_date_folder,
    export_json,
    export_markdown,
    export_json_string,
    export_markdown_string,
)

# CLI 진입점
from .__main__ import main

# 버전 정보
__version__ = "0.1.0"

# Public API 정의
__all__ = [
    # Enums
    "TargetDatabase",
    "ComplexityLevel",
    "PLSQLObjectType",
    # Data Models
    "SQLAnalysisResult",
    "PLSQLAnalysisResult",
    "BatchAnalysisResult",
    "WeightConfig",
    # Constants
    "ORACLE_SPECIFIC_SYNTAX",
    "ORACLE_SPECIFIC_FUNCTIONS",
    "ANALYTIC_FUNCTIONS",
    "AGGREGATE_FUNCTIONS",
    "ORACLE_HINTS",
    "PLSQL_ADVANCED_FEATURES",
    "EXTERNAL_DEPENDENCIES",
    # Weights and Scores
    "POSTGRESQL_WEIGHTS",
    "MYSQL_WEIGHTS",
    "PLSQL_BASE_SCORES",
    "MYSQL_APP_MIGRATION_PENALTY",
    # Analyzers
    "OracleComplexityAnalyzer",
    "BatchAnalyzer",
    # File Detection Utilities
    "is_plsql",
    "is_batch_plsql",
    "detect_file_type",
    # Export Utilities
    "get_date_folder",
    "export_json",
    "export_markdown",
    "export_json_string",
    "export_markdown_string",
    # CLI
    "main",
    # Version
    "__version__",
]

