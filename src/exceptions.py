"""
공통 예외 클래스 정의

이 모듈은 프로젝트 전체에서 사용되는 예외 클래스를 정의합니다.
모든 커스텀 예외는 OracleAnalyzerError를 상속받습니다.
"""


class OracleAnalyzerError(Exception):
    """
    기본 예외 클래스
    
    모든 Oracle Analyzer 관련 예외의 기본 클래스입니다.
    이 클래스를 직접 사용하기보다는 더 구체적인 하위 예외 클래스를 사용하세요.
    """
    pass


class FileProcessingError(OracleAnalyzerError):
    """
    파일 처리 관련 예외
    
    파일 읽기, 쓰기, 접근 권한 등 파일 시스템 관련 오류입니다.
    
    예시:
        - 파일을 찾을 수 없음
        - 파일 읽기 권한 없음
        - 인코딩 오류
        - 파일 형식 오류
    
    Example:
        >>> try:
        ...     content = read_file("nonexistent.sql")
        ... except IOError as e:
        ...     raise FileProcessingError(f"파일을 읽을 수 없습니다: {e}") from e
    """
    pass


class ParsingError(OracleAnalyzerError):
    """
    파싱 관련 예외
    
    SQL, PL/SQL, AWR, Statspack 등의 파일을 파싱하는 과정에서 발생하는 오류입니다.
    
    예시:
        - 잘못된 SQL 구문
        - 지원하지 않는 문법
        - 필수 섹션 누락
        - 데이터 형식 오류
    
    Example:
        >>> try:
        ...     result = parse_sql(invalid_sql)
        ... except ValueError as e:
        ...     raise ParsingError(f"SQL 파싱 실패: {e}") from e
    """
    pass


class AnalysisError(OracleAnalyzerError):
    """
    분석 관련 예외
    
    복잡도 분석, 마이그레이션 난이도 평가 등 분석 과정에서 발생하는 오류입니다.
    
    예시:
        - 불충분한 데이터
        - 알 수 없는 데이터베이스 타입
        - 계산 오류
        - 분석 불가능한 코드
    
    Example:
        >>> if not data:
        ...     raise AnalysisError("분석에 필요한 데이터가 부족합니다")
    """
    pass


class ConfigurationError(OracleAnalyzerError):
    """
    설정 관련 예외
    
    환경 변수, 설정 파일, 명령줄 인자 등 설정 관련 오류입니다.
    
    예시:
        - 필수 환경 변수 누락
        - 잘못된 설정 값
        - 설정 파일 형식 오류
        - 호환되지 않는 옵션 조합
    
    Example:
        >>> if not api_key:
        ...     raise ConfigurationError("API_KEY 환경 변수가 설정되지 않았습니다")
    """
    pass
