"""
마이그레이션 분석기 모듈

Statspack/AWR 데이터를 기반으로 타겟 데이터베이스별 마이그레이션 난이도를 분석합니다.

이 패키지는 다음과 같은 주요 기능을 제공합니다:
- 리소스 사용량 분석 (CPU, 메모리, I/O)
- 대기 이벤트 분석
- 기능 호환성 분석
- PL/SQL 복잡도 평가
- 타겟별 복잡도 계산 (MySQL, PostgreSQL)
- 캐릭터셋 분석
- RDS 인스턴스 추천

사용 예시:
    >>> from src.dbcsi.migration_analyzer import MigrationAnalyzer
    >>> analyzer = MigrationAnalyzer(statspack_data)
    >>> result = analyzer.analyze()
"""

# 메인 분석기
from .base_analyzer import MigrationAnalyzer
from .enhanced_analyzer import EnhancedMigrationAnalyzer

# 리소스 분석
from .resource_analyzer import analyze_resource_usage

# 대기 이벤트 분석
from .wait_event_analyzer import analyze_wait_events

# 기능 호환성 분석
from .feature_analyzer import analyze_feature_compatibility

# PL/SQL 평가
from .plsql_evaluator import evaluate_plsql_complexity

# 복잡도 계산
from .complexity_calculators import (
    calculate_charset_complexity,
    generate_charset_warnings,
    calculate_rds_oracle_complexity,
    calculate_aurora_postgresql_complexity,
    calculate_aurora_mysql_complexity,
)

# 캐릭터셋 분석
from .charset_analyzer import (
    detect_character_set,
    requires_charset_conversion,
    analyze_charset,
)

# 인스턴스 추천
from .instance_recommender import (
    select_instance_type,
    recommend_instance_size,
    R6I_INSTANCES,
)

# models에서 필요한 클래스들 import
from ..models import MigrationComplexity, TargetDatabase, InstanceRecommendation

# MigrationAnalyzer 클래스에 R6I_INSTANCES 속성 추가 (하위 호환성)
if not hasattr(MigrationAnalyzer, 'R6I_INSTANCES'):
    MigrationAnalyzer.R6I_INSTANCES = R6I_INSTANCES

# Public API 정의
__all__ = [
    # Main Analyzers
    'MigrationAnalyzer',
    'EnhancedMigrationAnalyzer',
    # Data Models
    'MigrationComplexity',
    'TargetDatabase',
    'InstanceRecommendation',
    # Resource Analysis
    'analyze_resource_usage',
    # Wait Event Analysis
    'analyze_wait_events',
    # Feature Analysis
    'analyze_feature_compatibility',
    # PL/SQL Evaluation
    'evaluate_plsql_complexity',
    # Complexity Calculation
    'calculate_charset_complexity',
    'generate_charset_warnings',
    'calculate_rds_oracle_complexity',
    'calculate_aurora_postgresql_complexity',
    'calculate_aurora_mysql_complexity',
    # Charset Analysis
    'detect_character_set',
    'requires_charset_conversion',
    'analyze_charset',
    # Instance Recommendation
    'select_instance_type',
    'recommend_instance_size',
    'R6I_INSTANCES',
]

# 버전 정보
__version__ = "2.0.0"
