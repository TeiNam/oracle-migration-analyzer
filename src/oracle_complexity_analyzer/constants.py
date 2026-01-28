"""
Oracle 특화 상수 정의 모듈

Oracle 특화 문법, 함수, 힌트 등의 상수를 정의합니다.

개선 이력:
- 2026-01-28: SQL_COMPLEXITY_SCORE_IMPROVEMENT.md 기반 점수 조정
  - ROWNUM 점수 하향 (1.5 → 0.5)
  - CURRVAL 점수 상향 (1.0 → 1.5)
  - 신규 Oracle 기능 추가 (KEEP, WITHIN GROUP, XML/JSON, Flashback 등)
"""

# ============================================================================
# Oracle 특화 기능/함수/힌트 상수 정의
# Requirements 2.1-2.5, 3.1, 7.1을 구현합니다.
# SQL_COMPLEXITY_SCORE_IMPROVEMENT.md 기반 점수 조정 반영
# ============================================================================

# Oracle 특화 문법 및 기능 (Requirements 2.1-2.5)
# 변환 난이도에 따라 가중치 조정 (SQL_COMPLEXITY_SCORE_IMPROVEMENT.md 반영)
ORACLE_SPECIFIC_SYNTAX = {
    # 계층적 쿼리 관련
    'CONNECT BY': 2.0,          # 계층적 쿼리 (매우 어려움)
    'START WITH': 1.5,          # 계층적 쿼리 시작점
    'PRIOR': 1.5,               # 계층적 쿼리 부모 참조
    'SYS_CONNECT_BY_PATH': 1.5, # 계층적 경로
    'CONNECT_BY_ISLEAF': 1.0,   # 계층 쿼리 리프 노드 (신규)
    'CONNECT_BY_ISCYCLE': 1.0,  # 계층 쿼리 순환 감지 (신규)
    'CONNECT_BY_ROOT': 1.0,     # 계층 쿼리 루트 값 (신규)
    'LEVEL': 1.5,               # 계층적 레벨
    
    # MODEL 절
    'MODEL': 2.5,               # MODEL 절 (매우 어려움)
    
    # PIVOT/UNPIVOT
    'PIVOT': 1.5,               # PIVOT 연산 (어려움)
    'UNPIVOT': 1.5,             # UNPIVOT 연산 (어려움)
    
    # Flashback 관련 (신규)
    'FLASHBACK': 2.0,           # FLASHBACK 쿼리 (매우 어려움)
    'VERSIONS BETWEEN': 2.5,    # Flashback 버전 쿼리 (신규)
    'AS OF TIMESTAMP': 2.5,     # Flashback 시점 쿼리 (신규)
    'AS OF SCN': 2.5,           # Flashback SCN 쿼리 (신규)
    
    # 집계 관련 (신규)
    'KEEP': 2.0,                # KEEP (DENSE_RANK FIRST/LAST) (신규)
    'WITHIN GROUP': 1.0,        # 정렬 집계 (신규)
    
    # XML/JSON 처리 (신규)
    'XMLTABLE': 2.5,            # XML 데이터를 테이블로 변환 (신규)
    'XMLQUERY': 2.0,            # XML 쿼리 (신규)
    'XMLEXISTS': 2.0,           # XML 존재 확인 (신규)
    'JSON_TABLE': 1.5,          # JSON을 테이블로 변환 (신규)
    'JSON_VALUE': 1.0,          # JSON 값 추출 (신규)
    'JSON_QUERY': 1.0,          # JSON 쿼리 (신규)
    'JSON_EXISTS': 1.0,         # JSON 존재 확인 (신규)
    
    # 샘플링 (신규)
    'SAMPLE': 2.0,              # 테이블 샘플링 (신규)
    'SAMPLE BLOCK': 2.0,        # 블록 샘플링 (신규)
    
    # 패턴 매칭 (신규)
    'MATCH_RECOGNIZE': 3.0,     # 패턴 매칭 (신규)
    
    # 조인 관련 (신규)
    'LATERAL': 1.0,             # Lateral 조인 (신규)
    'CROSS APPLY': 1.5,         # 적용 조인 (신규)
    'OUTER APPLY': 1.5,         # 외부 적용 조인 (신규)
    
    # 컬렉션 관련 (신규)
    'TABLE(': 2.0,              # 컬렉션을 테이블로 변환 (신규)
    'MULTISET': 2.5,            # 컬렉션 연산 (신규)
    'COLLECT': 2.0,             # 컬렉션 집계 (신규)
    
    # 기타 Oracle 특화 문법
    'ROWID': 1.5,               # 물리적 행 주소 (어려움)
    'ROWNUM': 0.5,              # 행 번호 - 단순 패턴 (기존 1.5 → 0.5 하향)
    'MERGE': 2.0,               # MERGE 문 (어려움)
    '(+)': 1.5,                 # OUTER JOIN (구식 문법, 어려움)
    'NEXTVAL': 0.8,             # 시퀀스 다음 값 (기존 1.0 → 0.8 하향)
    'CURRVAL': 1.5,             # 시퀀스 현재 값 - 세션 의존성 (기존 1.0 → 1.5 상향)
    'RETURNING': 1.0,           # RETURNING 절
    'DUAL': 0.5,                # DUAL 테이블 (쉬움)
    
    # 트랜잭션 옵션 (신규)
    'FOR UPDATE': 0.3,          # 기본 FOR UPDATE (신규)
    'SKIP LOCKED': 0.5,         # SKIP LOCKED 옵션 (신규)
    'NOWAIT': 0.5,              # NOWAIT 옵션 (신규)
    'WAIT': 1.5,                # FOR UPDATE WAIT N (신규)
}

# Oracle 특화 함수 (Requirements 3.1, 3.2)
# 변환 난이도에 따라 가중치 조정 (SQL_COMPLEXITY_SCORE_IMPROVEMENT.md 반영)
ORACLE_SPECIFIC_FUNCTIONS = {
    # 조건/변환 함수
    'DECODE': 1.2,              # DECODE 함수 - 중첩 DECODE 고려 (기존 0.8 → 1.2 상향)
    'NVL': 0.6,                 # NULL 처리 (COALESCE로 쉽게 변환)
    'NVL2': 0.7,                # NULL 조건부 처리
    'LNNVL': 1.5,               # NULL 안전 비교 (신규)
    
    # 집계 함수
    'LISTAGG': 1.5,             # 문자열 집계 - MySQL 제한 고려 (기존 1.0 → 1.5 상향)
    'WM_CONCAT': 1.5,           # 문자열 집계 (비공식, 많이 사용) (신규)
    'STRAGG': 1.5,              # 문자열 집계 (비공식) (신규)
    
    # 정규식 함수
    'REGEXP_LIKE': 0.7,         # 정규식 매칭
    'REGEXP_SUBSTR': 0.8,       # 정규식 부분 문자열
    'REGEXP_REPLACE': 0.8,      # 정규식 치환
    'REGEXP_INSTR': 0.8,        # 정규식 위치
    'REGEXP_COUNT': 0.8,        # 정규식 매칭 개수 (신규)
    
    # 시스템 함수
    'SYS_CONTEXT': 1.5,         # 시스템 컨텍스트 (매우 어려움)
    'EXTRACT': 0.6,             # 날짜/시간 추출
    
    # 변환 함수 - 포맷 차이로 버그 빈번 (점수 상향)
    'TO_CHAR': 1.0,             # 문자열 변환 (기존 0.7 → 1.0 상향)
    'TO_DATE': 1.0,             # 날짜 변환 (기존 0.7 → 1.0 상향)
    'TO_NUMBER': 0.7,           # 숫자 변환 (포맷 차이)
    'TO_TIMESTAMP': 0.8,        # 타임스탬프 변환 (신규)
    'TRUNC': 0.7,               # 절삭 (날짜/숫자 모두 처리)
    
    # 날짜 함수
    'ADD_MONTHS': 0.7,          # 월 더하기
    'MONTHS_BETWEEN': 0.7,      # 월 차이
    'NEXT_DAY': 0.8,            # 다음 요일
    'LAST_DAY': 0.7,            # 월 마지막 날
    'SYSDATE': 0.6,             # 시스템 날짜
    'SYSTIMESTAMP': 0.6,        # 시스템 타임스탬프
    'CURRENT_DATE': 0.5,        # 현재 날짜
    
    # 타임존 관련 (신규)
    'TO_TIMESTAMP_TZ': 1.2,     # 타임존 타임스탬프 (신규)
    'FROM_TZ': 1.0,             # 타임존 변환 (신규)
    'SESSIONTIMEZONE': 1.0,     # 세션 타임존 (신규)
    'DBTIMEZONE': 1.0,          # DB 타임존 (신규)
    'TZ_OFFSET': 1.0,           # 타임존 오프셋 (신규)
    
    # 간격 관련 (신규)
    'TO_DSINTERVAL': 1.0,       # 일-초 간격 (신규)
    'TO_YMINTERVAL': 1.0,       # 년-월 간격 (신규)
    'NUMTODSINTERVAL': 1.0,     # 숫자→간격 (신규)
    'NUMTOYMINTERVAL': 1.0,     # 숫자→년월간격 (신규)
    
    # 문자열 함수
    'SUBSTR': 0.6,              # 부분 문자열 (인덱스 차이)
    'INSTR': 0.6,               # 문자열 위치 (인덱스 차이)
    'CHR': 0.6,                 # 문자 코드 변환
    'TRANSLATE': 0.7,           # 문자 치환
    
    # NULL 처리 관련 - NULL 처리 차이 주의 (신규)
    'GREATEST': 0.8,            # 최대값 - NULL 처리 차이 (신규)
    'LEAST': 0.8,               # 최소값 - NULL 처리 차이 (신규)
    
    # 분석 함수 (신규)
    'NTH_VALUE': 0.8,           # N번째 값 (신규)
    'STDDEV': 0.5,              # 표준편차 (신규)
    'VARIANCE': 0.5,            # 분산 (신규)
    'STDDEV_POP': 0.7,          # 모집단 표준편차 (신규)
    'STDDEV_SAMP': 0.7,         # 표본 표준편차 (신규)
    'VAR_POP': 0.7,             # 모집단 분산 (신규)
    'VAR_SAMP': 0.7,            # 표본 분산 (신규)
    'COVAR_POP': 0.8,           # 공분산 (신규)
    'COVAR_SAMP': 0.8,          # 표본 공분산 (신규)
    'CORR': 0.8,                # 상관계수 (신규)
}

# 분석 함수 (Requirements 2.2)
# 신규 분석 함수 추가 (SQL_COMPLEXITY_SCORE_IMPROVEMENT.md 반영)
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
    'NTH_VALUE',                # N번째 값 (신규)
    'LISTAGG',                  # 윈도우 LISTAGG (신규)
    'PERCENTILE_CONT',          # 윈도우 백분위수 (신규)
    'PERCENTILE_DISC',          # 윈도우 이산 백분위수 (신규)
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
# 힌트 목록 확장 (SQL_COMPLEXITY_SCORE_IMPROVEMENT.md 반영)
ORACLE_HINTS = [
    # 기존 힌트
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
    
    # 인덱스 관련 (신규)
    'NO_INDEX',                 # 인덱스 사용 금지 (신규)
    'INDEX_FFS',                # Fast Full Scan (신규)
    'INDEX_SS',                 # Skip Scan (신규)
    'INDEX_JOIN',               # 인덱스 조인 (신규)
    'INDEX_COMBINE',            # 비트맵 인덱스 결합 (신규)
    
    # 조인 관련 (신규)
    'USE_MERGE',                # 머지 조인 (신규)
    'NO_USE_HASH',              # 해시 조인 금지 (신규)
    'NO_USE_NL',                # 중첩 루프 금지 (신규)
    'NO_USE_MERGE',             # 머지 조인 금지 (신규)
    
    # 서브쿼리/뷰 관련 (신규)
    'PUSH_PRED',                # 조건 푸시 (신규)
    'NO_PUSH_PRED',             # 조건 푸시 금지 (신규)
    'PUSH_SUBQ',                # 서브쿼리 푸시 (신규)
    'NO_PUSH_SUBQ',             # 서브쿼리 푸시 금지 (신규)
    'UNNEST',                   # 서브쿼리 언네스트 (신규)
    'NO_UNNEST',                # 언네스트 금지 (신규)
    'MATERIALIZE',              # 서브쿼리 구체화 (신규)
    'INLINE',                   # 인라인 처리 (신규)
    
    # 옵티마이저 관련 (신규)
    'CARDINALITY',              # 카디널리티 힌트 (신규)
    'OPT_ESTIMATE',             # 옵티마이저 추정 (신규)
    'DYNAMIC_SAMPLING',         # 동적 샘플링 (신규)
    'OPTIMIZER_FEATURES_ENABLE', # 옵티마이저 버전 (신규)
    'QB_NAME',                  # 쿼리 블록 이름 (신규)
    
    # 캐시/병렬 관련 (신규)
    'RESULT_CACHE',             # 결과 캐시 (신규)
    'NO_RESULT_CACHE',          # 결과 캐시 금지 (신규)
    'NO_PARALLEL',              # 병렬 금지 (신규)
    'PQ_DISTRIBUTE',            # 병렬 분배 (신규)
    
    # 기타 (신규)
    'STAR_TRANSFORMATION',      # 스타 변환 (신규)
    'FACT',                     # 팩트 테이블 힌트 (신규)
    'NO_FACT',                  # 팩트 테이블 힌트 금지 (신규)
    'CURSOR_SHARING_EXACT',     # 커서 공유 (신규)
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
    'DBMS_PIPE',                # 프로세스 간 통신
    'DBMS_ALERT',               # 데이터베이스 알림
    'DBMS_LOCK',                # 사용자 정의 락
    'DBMS_AQ',                  # Advanced Queuing
    'DBMS_XMLGEN',              # XML 생성
    'DBMS_XMLPARSER',           # XML 파싱
    'DBMS_METADATA',            # 메타데이터 추출
    'DBMS_STATS',               # 통계 관리
    'DBMS_PROFILER',            # 프로파일링
    'DBMS_TRACE',               # 트레이싱
    'UTL_RAW',                  # RAW 데이터 처리
    'UTL_ENCODE',               # 인코딩
    'UTL_COMPRESS',             # 압축
    'UTL_I18N',                 # 국제화
]

# 외부 의존성 차등 점수 (PLSQL_COMPLEXITY_SCORE_IMPROVEMENT.md 기반)
# 패키지별 실제 변환 난이도를 반영한 차등 점수
EXTERNAL_DEPENDENCY_SCORES = {
    # 🔴 매우 어려움 - 완전 재설계 필요
    'UTL_FILE': 1.5,           # 파일 I/O → 애플리케이션 파일 처리
    'UTL_HTTP': 1.5,           # HTTP → 애플리케이션 HTTP 클라이언트
    'UTL_MAIL': 1.2,           # 메일 → 애플리케이션 메일 서비스
    'UTL_SMTP': 1.2,           # SMTP → 애플리케이션 SMTP 클라이언트
    'DBMS_SCHEDULER': 1.5,     # 스케줄러 → cron, pg_cron, 외부 스케줄러
    'DBMS_PIPE': 2.0,          # 프로세스 간 통신 → 메시지 큐
    'DBMS_ALERT': 1.5,         # 알림 → 이벤트 시스템
    'DBMS_LOCK': 1.5,          # 락 관리 → Advisory Lock 또는 애플리케이션 락
    'DBMS_AQ': 2.0,            # Advanced Queuing → 메시지 큐 시스템
    
    # 🟠 어려움 - 상당한 변경 필요
    'DBMS_JOB': 1.0,           # 작업 스케줄링 (구버전)
    'DBMS_CRYPTO': 1.0,        # 암호화 → pgcrypto 또는 애플리케이션 암호화
    'DBMS_SQL': 0.8,           # 동적 SQL (이미 별도 계산되므로 낮게)
    'DBMS_XMLGEN': 1.0,        # XML 생성
    'DBMS_XMLPARSER': 1.0,     # XML 파싱
    'DBMS_METADATA': 1.5,      # 메타데이터 추출
    'DBMS_STATS': 1.0,         # 통계 관리
    'DBMS_PROFILER': 1.0,      # 프로파일링
    'DBMS_TRACE': 1.0,         # 트레이싱
    'UTL_RAW': 0.8,            # RAW 데이터 처리
    'UTL_ENCODE': 0.8,         # 인코딩
    'UTL_COMPRESS': 1.0,       # 압축
    'UTL_I18N': 1.0,           # 국제화
    
    # 🟡 중간 - 부분 변경 필요
    'DBMS_LOB': 0.5,           # LOB 처리 → 네이티브 LOB 함수
    'DBMS_RANDOM': 0.3,        # 난수 생성 → random() 함수
    'DBMS_UTILITY': 0.5,       # 유틸리티 함수
    
    # 🟢 쉬움 - 간단한 대체
    'DBMS_OUTPUT': 0.2,        # 디버그 출력 → RAISE NOTICE
}

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
