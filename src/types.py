"""
공통 타입 정의 모듈

프로젝트 전체에서 사용하는 타입 별칭을 정의합니다.
"""

from typing import Dict, Any, Union, List
from pathlib import Path

# 파일 경로 타입
FilePath = Union[str, Path]

# 분석 결과 타입 (SQL 또는 PL/SQL)
AnalysisResult = Dict[str, Any]

# 메트릭 딕셔너리 타입
MetricsDict = Dict[str, Union[int, float, str]]

# 설정 딕셔너리 타입
ConfigDict = Dict[str, Any]

# 배치 분석 결과 타입
BatchResults = Dict[str, AnalysisResult]

# 복잡도 분포 타입
ComplexityDistribution = Dict[str, int]

# 마이그레이션 분석 결과 타입
MigrationAnalysis = Dict[str, Any]

# JSON 직렬화 가능 타입
JSONSerializable = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
