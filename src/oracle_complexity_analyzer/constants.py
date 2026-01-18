"""
Oracle 특화 상수 정의 모듈

Oracle 특화 문법, 함수, 힌트 등의 상수를 정의합니다.
"""

# ============================================================================
# Oracle 특화 기능/함수/힌트 상수 정의
# Requirements 2.1-2.5, 3.1, 7.1을 구현합니다.
# ============================================================================

# Oracle 특화 문법 및 기능 (Requirements 2.1-2.5)
# 변환 난이도에 따라 가중치 상향 조정
ORACLE_SPECIFIC_SYNTAX = {
    'CONNECT BY': 2.0,          # 계층적 쿼리 (매우 어려움)
    'START WITH': 1.5,          # 계층적 쿼리 시작점
    'PRIOR': 1.5,               # 계층적 쿼리 부모 참조
    'MODEL': 2.5,               # MODEL 절 (매우 어려움)
    'PIVOT': 1.5,               # PIVOT 연산 (어려움)
    'UNPIVOT': 1.5,             # UNPIVOT 연산 (어려움)
    'FLASHBACK': 2.0,           # FLASHBACK 쿼리 (매우 어려움)
    'SYS_CONNECT_BY_PATH': 1.5, # 계층적 경로
    'ROWID': 1.5,               # 물리적 행 주소 (어려움)
    'ROWNUM': 1.5,              # 행 번호 (어려움)
    'LEVEL': 1.5,               # 계층적 레벨
    'MERGE': 2.0,               # MERGE 문 (어려움)
    '(+)': 1.5,                 # OUTER JOIN (구식 문법, 어려움)
    'NEXTVAL': 1.0,             # 시퀀스 다음 값
    'CURRVAL': 1.0,             # 시퀀스 현재 값
    'RETURNING': 1.0,           # RETURNING 절
    'DUAL': 0.5,                # DUAL 테이블 (쉬움)
}

# Oracle 특화 함수 (Requirements 3.1, 3.2)
# 변환 난이도에 따라 가중치 상향 조정
ORACLE_SPECIFIC_FUNCTIONS = {
    # 조건/변환 함수
    'DECODE': 0.8,              # DECODE 함수 (CASE 변환 필요)
    'NVL': 0.6,                 # NULL 처리
    'NVL2': 0.7,                # NULL 조건부 처리
    
    # 집계 함수
    'LISTAGG': 1.0,             # 문자열 집계 (어려움)
    
    # 정규식 함수
    'REGEXP_LIKE': 0.7,         # 정규식 매칭
    'REGEXP_SUBSTR': 0.8,       # 정규식 부분 문자열
    'REGEXP_REPLACE': 0.8,      # 정규식 치환
    'REGEXP_INSTR': 0.8,        # 정규식 위치
    
    # 시스템 함수
    'SYS_CONTEXT': 1.5,         # 시스템 컨텍스트 (매우 어려움)
    'EXTRACT': 0.6,             # 날짜/시간 추출
    
    # 변환 함수
    'TO_CHAR': 0.7,             # 문자열 변환 (포맷 차이)
    'TO_DATE': 0.7,             # 날짜 변환 (포맷 차이)
    'TO_NUMBER': 0.7,           # 숫자 변환 (포맷 차이)
    'TRUNC': 0.7,               # 절삭 (날짜/숫자 모두 처리)
    
    # 날짜 함수
    'ADD_MONTHS': 0.7,          # 월 더하기
    'MONTHS_BETWEEN': 0.7,      # 월 차이
    'NEXT_DAY': 0.8,            # 다음 요일
    'LAST_DAY': 0.7,            # 월 마지막 날
    'SYSDATE': 0.6,             # 시스템 날짜
    'SYSTIMESTAMP': 0.6,        # 시스템 타임스탬프
    'CURRENT_DATE': 0.5,        # 현재 날짜
    
    # 문자열 함수
    'SUBSTR': 0.6,              # 부분 문자열 (인덱스 차이)
    'INSTR': 0.6,               # 문자열 위치 (인덱스 차이)
    'CHR': 0.6,                 # 문자 코드 변환
    'TRANSLATE': 0.7,           # 문자 치환
}

# 분석 함수 (Requirements 2.2)
ANALYTIC_FUNCTIONS = [
    'ROW_NUMBER',               # 행 번호
    'RANK',                     # 순위 (동일 순위 건너뜀)
    'DENSE_RANK',               # 순위 (동일 순위 연속)
    'LAG',                      # 이전 행 값
    'LEAD',                     # 다음 행 값
    'FIRST_VALUE',              # 첫 번째 값
    'LAST_VALUE',               # 마지막 값
    'NTILE',                    # N분위수
    'CUME_DIST',                # 누적 분포
    'PERCENT_RANK',             # 백분위 순위
    'RATIO_TO_REPORT',          # 비율
]

# 집계 함수 (Requirements 4.1)
AGGREGATE_FUNCTIONS = [
    'COUNT',                    # 개수
    'SUM',                      # 합계
    'AVG',                      # 평균
    'MAX',                      # 최대값
    'MIN',                      # 최소값
    'LISTAGG',                  # 문자열 집계
    'XMLAGG',                   # XML 집계
    'MEDIAN',                   # 중앙값
    'PERCENTILE_CONT',          # 연속 백분위수
    'PERCENTILE_DISC',          # 이산 백분위수
]

# Oracle 힌트 (Requirements 7.1-7.5)
ORACLE_HINTS = [
    'INDEX',                    # 인덱스 사용
    'FULL',                     # 풀 스캔
    'PARALLEL',                 # 병렬 처리
    'USE_HASH',                 # 해시 조인
    'USE_NL',                   # 중첩 루프 조인
    'APPEND',                   # 직접 경로 삽입
    'NO_MERGE',                 # 뷰 병합 방지
    'LEADING',                  # 조인 순서 지정
    'ORDERED',                  # FROM 절 순서대로 조인
    'FIRST_ROWS',               # 첫 행 빠른 반환
    'ALL_ROWS',                 # 전체 처리량 최적화
    'RULE',                     # 규칙 기반 최적화
    'CHOOSE',                   # 옵티마이저 선택
    'DRIVING_SITE',             # DB Link 실행 위치
]

# PL/SQL 고급 기능 (Requirements 9.5)
PLSQL_ADVANCED_FEATURES = [
    'PIPELINED',                # 파이프라인 함수
    'REF CURSOR',               # 커서 변수
    'AUTONOMOUS_TRANSACTION',   # 자율 트랜잭션
    'PRAGMA',                   # 컴파일러 지시어
    'OBJECT TYPE',              # 객체 타입
    'VARRAY',                   # 가변 배열
    'NESTED TABLE',             # 중첩 테이블
]

# 외부 의존성 (Requirements 10.6)
EXTERNAL_DEPENDENCIES = [
    'UTL_FILE',                 # 파일 I/O
    'UTL_HTTP',                 # HTTP 통신
    'UTL_MAIL',                 # 이메일 발송
    'UTL_SMTP',                 # SMTP 통신
    'DBMS_SCHEDULER',           # 스케줄러
    'DBMS_JOB',                 # 작업 스케줄링
    'DBMS_LOB',                 # LOB 처리
    'DBMS_OUTPUT',              # 출력
    'DBMS_CRYPTO',              # 암호화
    'DBMS_SQL',                 # 동적 SQL
]

# ============================================================================
# 가중치 설정 (WeightConfig 인스턴스)
# ============================================================================

# WeightConfig는 data_models에서 import해야 하므로 여기서는 정의하지 않음
# 대신 oracle_complexity_analyzer.py에서 정의된 값을 사용
# 이 파일에서는 기본 점수와 페널티만 정의

# ============================================================================
# PL/SQL 오브젝트 기본 점수 및 페널티
# ============================================================================

# 주의: PLSQL_BASE_SCORES와 MYSQL_APP_MIGRATION_PENALTY는
# weights.py에 정의되어 있습니다. 여기서는 중복 정의하지 않습니다.
