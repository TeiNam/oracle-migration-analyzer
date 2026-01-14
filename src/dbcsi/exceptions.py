"""
Statspack 분석기 예외 클래스 정의

이 모듈은 Statspack 분석 과정에서 발생할 수 있는 모든 예외를 정의합니다.
"""


class StatspackError(Exception):
    """
    Statspack 관련 기본 예외
    
    모든 Statspack 관련 예외의 기본 클래스입니다.
    """
    pass


class StatspackParseError(StatspackError):
    """
    파싱 오류
    
    Statspack 파일을 파싱하는 과정에서 발생하는 오류입니다.
    예: 잘못된 형식, 필수 섹션 누락, 데이터 형식 오류 등
    """
    pass


class StatspackFileError(StatspackError):
    """
    파일 관련 오류
    
    파일 읽기, 쓰기, 접근 권한 등 파일 시스템 관련 오류입니다.
    예: 파일 없음, 권한 오류, 인코딩 오류 등
    """
    pass


class MigrationAnalysisError(StatspackError):
    """
    마이그레이션 분석 오류
    
    마이그레이션 난이도 분석 과정에서 발생하는 오류입니다.
    예: 불충분한 데이터, 알 수 없는 Oracle 에디션, 계산 오류 등
    """
    pass
