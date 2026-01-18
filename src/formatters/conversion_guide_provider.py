"""
Oracle → 타겟 DB 변환 가이드 제공 모듈

Requirements 15.1, 15.2, 15.3을 구현합니다.
- 15.1: PostgreSQL 타겟에서 Oracle 기능 대체 방법 제공
- 15.2: MySQL 타겟에서 Oracle 기능 대체 방법 제공
- 15.3: MySQL 타겟에서 PL/SQL 오브젝트 애플리케이션 이관 권장
"""

from typing import Dict, List

from src.oracle_complexity_analyzer import TargetDatabase


class ConversionGuideProvider:
    """Oracle → 타겟 DB 변환 가이드 제공 클래스
    
    감지된 Oracle 특화 기능에 대해 타겟 데이터베이스별로
    적절한 변환 가이드를 제공합니다.
    
    Requirements:
    - 15.1: PostgreSQL 변환 매핑
    - 15.2: MySQL 변환 매핑
    - 15.3: MySQL PL/SQL 애플리케이션 이관 권장
    """
    
    # PostgreSQL 변환 매핑 (Requirement 15.1)
    POSTGRESQL_MAPPINGS = {
        # 기본 문법
        'ROWNUM': 'LIMIT/OFFSET 또는 ROW_NUMBER() OVER()',
        'CONNECT BY': 'WITH RECURSIVE (재귀 CTE)',
        'START WITH': 'WITH RECURSIVE의 초기 쿼리',
        'PRIOR': 'WITH RECURSIVE의 재귀 참조',
        'LEVEL': 'WITH RECURSIVE의 깊이 계산',
        
        # 함수
        'DECODE': 'CASE WHEN ... THEN ... END',
        'NVL': 'COALESCE(expr, default)',
        'NVL2': 'CASE WHEN expr IS NOT NULL THEN val1 ELSE val2 END',
        
        # 날짜/시간
        'SYSDATE': 'CURRENT_TIMESTAMP 또는 NOW()',
        'SYSTIMESTAMP': 'CURRENT_TIMESTAMP',
        'CURRENT_DATE': 'CURRENT_DATE (동일)',
        'TO_CHAR': 'TO_CHAR (동일, 포맷 차이 주의)',
        'TO_DATE': 'TO_DATE 또는 TO_TIMESTAMP',
        'TO_NUMBER': 'CAST(expr AS NUMERIC)',
        'TRUNC': 'DATE_TRUNC(unit, timestamp)',
        'ADD_MONTHS': "expr + INTERVAL 'n months'",
        'MONTHS_BETWEEN': "EXTRACT(YEAR FROM AGE(date1, date2)) * 12 + EXTRACT(MONTH FROM AGE(date1, date2))",
        'NEXT_DAY': '커스텀 함수 필요',
        'LAST_DAY': "(DATE_TRUNC('month', date) + INTERVAL '1 month - 1 day')::DATE",
        
        # DML
        'MERGE': 'INSERT ... ON CONFLICT DO UPDATE',
        'RETURNING': 'RETURNING (동일)',
        
        # 고급 기능
        'PIVOT': "crosstab() 확장 함수 또는 CASE + GROUP BY",
        'UNPIVOT': 'UNION ALL 또는 LATERAL JOIN',
        'MODEL': '복잡한 쿼리 재작성 필요',
        '(+)': 'LEFT JOIN 또는 RIGHT JOIN',
        
        # 시퀀스
        'NEXTVAL': "nextval('sequence_name')",
        'CURRVAL': "currval('sequence_name')",
        'SEQUENCE.NEXTVAL': "nextval('sequence_name')",
        'SEQUENCE.CURRVAL': "currval('sequence_name')",
        
        # 집계 함수
        'LISTAGG': 'STRING_AGG(expr, delimiter ORDER BY ...)',
        'MEDIAN': 'PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY expr)',
        'PERCENTILE_CONT': 'PERCENTILE_CONT (동일)',
        'PERCENTILE_DISC': 'PERCENTILE_DISC (동일)',
        'XMLAGG': 'XMLAGG (동일, xml2 확장 필요)',
        'KEEP': '서브쿼리 또는 FILTER 절로 재작성',
        
        # 분석 함수
        'ROW_NUMBER': 'ROW_NUMBER() (동일)',
        'RANK': 'RANK() (동일)',
        'DENSE_RANK': 'DENSE_RANK() (동일)',
        'LAG': 'LAG() (동일)',
        'LEAD': 'LEAD() (동일)',
        'FIRST_VALUE': 'FIRST_VALUE() (동일)',
        'LAST_VALUE': 'LAST_VALUE() (동일)',
        'NTILE': 'NTILE() (동일)',
        'CUME_DIST': 'CUME_DIST() (동일)',
        'PERCENT_RANK': 'PERCENT_RANK() (동일)',
        'RATIO_TO_REPORT': 'expr / SUM(expr) OVER()',
        
        # 문자열 함수
        'SUBSTR': 'SUBSTR 또는 SUBSTRING',
        'INSTR': 'POSITION(substring IN string)',
        'CHR': 'CHR (동일)',
        'TRANSLATE': 'TRANSLATE (동일)',
        
        # 정규식
        'REGEXP_LIKE': 'expr ~ pattern (정규식 연산자)',
        'REGEXP_SUBSTR': 'SUBSTRING(expr FROM pattern)',
        'REGEXP_REPLACE': 'REGEXP_REPLACE (동일)',
        'REGEXP_INSTR': '커스텀 함수 필요',
        
        # 시스템 함수
        'SYS_CONTEXT': 'current_setting() / set_config()',
        'EXTRACT': 'EXTRACT (동일)',
        
        # 기타
        'DUAL': '불필요 (FROM 절 생략 가능)',
        'ROWID': 'ctid (내부 행 식별자, 사용 비권장)',
        'FLASHBACK': 'Point-in-Time Recovery 또는 타임스탬프 기반 쿼리',
        'SYS_CONNECT_BY_PATH': 'WITH RECURSIVE에서 경로 문자열 생성',
        
        # PL/SQL 관련
        'BULK COLLECT': '순수 SQL 또는 배치 처리 (COPY, INSERT ... SELECT)',
        'FORALL': '순수 SQL 또는 배치 처리',
        'PIPELINED': 'RETURN NEXT / RETURN QUERY (테이블 반환 함수)',
        'REF CURSOR': 'REFCURSOR 타입 (유사)',
        'AUTONOMOUS_TRANSACTION': '별도 연결 또는 DBLINK',
        'PRAGMA': '대부분 불필요 또는 함수 속성으로 대체',
        'OBJECT TYPE': 'COMPOSITE TYPE 또는 TABLE',
        'VARRAY': 'ARRAY 타입',
        'NESTED TABLE': 'ARRAY 또는 별도 테이블',
        
        # 외부 의존성
        'UTL_FILE': 'COPY, pg_read_file(), pg_write_file() 또는 외부 스크립트',
        'UTL_HTTP': 'http 확장 (http_get, http_post 등)',
        'UTL_MAIL': '외부 스크립트 또는 애플리케이션',
        'UTL_SMTP': '외부 스크립트 또는 애플리케이션',
        'DBMS_SCHEDULER': 'pg_cron 확장',
        'DBMS_JOB': 'pg_cron 확장',
        'DBMS_LOB': 'bytea 타입 및 내장 함수',
        'DBMS_OUTPUT': 'RAISE NOTICE',
        'DBMS_CRYPTO': 'pgcrypto 확장',
        'DBMS_SQL': 'EXECUTE 동적 SQL',
        
        # 트랜잭션
        'SAVEPOINT': 'SAVEPOINT (동일)',
        'ROLLBACK TO SAVEPOINT': 'ROLLBACK TO SAVEPOINT (동일)',
        
        # 오브젝트 타입
        'Package': 'SCHEMA 또는 여러 함수/프로시저로 분리',
        'Procedure': 'PROCEDURE 또는 FUNCTION (OUT 파라미터)',
        'Function': 'FUNCTION (동일)',
        'Trigger': 'TRIGGER (동일, 일부 제약 있음)',
        'View': 'VIEW (동일)',
        'Materialized View': 'MATERIALIZED VIEW (동일)',
    }
    
    # MySQL 변환 매핑 (Requirement 15.2)
    MYSQL_MAPPINGS = {
        # 기본 문법
        'ROWNUM': 'LIMIT 또는 사용자 변수 (@rownum := @rownum + 1)',
        'CONNECT BY': '재귀 쿼리 (MySQL 8.0+) 또는 애플리케이션 로직',
        'START WITH': '재귀 CTE의 초기 쿼리 (MySQL 8.0+)',
        'PRIOR': '재귀 CTE의 재귀 참조 (MySQL 8.0+)',
        'LEVEL': '재귀 CTE에서 깊이 계산 (MySQL 8.0+)',
        
        # 함수
        'DECODE': 'CASE WHEN ... THEN ... END',
        'NVL': 'IFNULL(expr, default) 또는 COALESCE',
        'NVL2': 'IF(expr IS NOT NULL, val1, val2)',
        
        # 날짜/시간
        'SYSDATE': 'NOW() 또는 CURRENT_TIMESTAMP',
        'SYSTIMESTAMP': 'NOW(6) (마이크로초 포함)',
        'CURRENT_DATE': 'CURDATE() 또는 CURRENT_DATE',
        'TO_CHAR': 'DATE_FORMAT(date, format)',
        'TO_DATE': 'STR_TO_DATE(str, format)',
        'TO_NUMBER': 'CAST(expr AS DECIMAL) 또는 CONVERT',
        'TRUNC': 'DATE(datetime) 또는 FLOOR(number)',
        'ADD_MONTHS': 'DATE_ADD(date, INTERVAL n MONTH)',
        'MONTHS_BETWEEN': 'TIMESTAMPDIFF(MONTH, date1, date2)',
        'NEXT_DAY': '복잡한 계산 필요',
        'LAST_DAY': 'LAST_DAY(date)',
        
        # DML
        'MERGE': 'INSERT ... ON DUPLICATE KEY UPDATE',
        'RETURNING': '미지원 (LAST_INSERT_ID() 사용)',
        
        # 고급 기능
        'PIVOT': 'GROUP BY + CASE WHEN (수동 작성)',
        'UNPIVOT': 'UNION ALL',
        'MODEL': '미지원 (애플리케이션 로직으로 이관)',
        '(+)': 'LEFT JOIN 또는 RIGHT JOIN',
        
        # 시퀀스
        'NEXTVAL': 'AUTO_INCREMENT 또는 별도 테이블',
        'CURRVAL': '미지원 (LAST_INSERT_ID() 사용)',
        'SEQUENCE.NEXTVAL': 'AUTO_INCREMENT',
        'SEQUENCE.CURRVAL': 'LAST_INSERT_ID()',
        
        # 집계 함수
        'LISTAGG': 'GROUP_CONCAT(expr ORDER BY ... SEPARATOR delimiter) - 길이 제한 주의 (기본 1024)',
        'MEDIAN': '복잡한 서브쿼리 필요 (미지원)',
        'PERCENTILE_CONT': '복잡한 서브쿼리 필요 (미지원)',
        'PERCENTILE_DISC': '복잡한 서브쿼리 필요 (미지원)',
        'XMLAGG': '미지원',
        'KEEP': '서브쿼리로 재작성',
        
        # 분석 함수 (MySQL 8.0+)
        'ROW_NUMBER': 'ROW_NUMBER() (MySQL 8.0+)',
        'RANK': 'RANK() (MySQL 8.0+)',
        'DENSE_RANK': 'DENSE_RANK() (MySQL 8.0+)',
        'LAG': 'LAG() (MySQL 8.0+)',
        'LEAD': 'LEAD() (MySQL 8.0+)',
        'FIRST_VALUE': 'FIRST_VALUE() (MySQL 8.0+)',
        'LAST_VALUE': 'LAST_VALUE() (MySQL 8.0+)',
        'NTILE': 'NTILE() (MySQL 8.0+)',
        'CUME_DIST': 'CUME_DIST() (MySQL 8.0+)',
        'PERCENT_RANK': 'PERCENT_RANK() (MySQL 8.0+)',
        'RATIO_TO_REPORT': '수동 계산 필요',
        
        # 문자열 함수
        'SUBSTR': 'SUBSTRING(str, pos, len)',
        'INSTR': 'INSTR(str, substr) 또는 LOCATE',
        'CHR': 'CHAR(n USING utf8mb4)',
        'TRANSLATE': '복잡한 REPLACE 체인 필요',
        
        # 정규식 (MySQL 8.0+)
        'REGEXP_LIKE': 'REGEXP (MySQL 8.0+)',
        'REGEXP_SUBSTR': 'REGEXP_SUBSTR() (MySQL 8.0+)',
        'REGEXP_REPLACE': 'REGEXP_REPLACE() (MySQL 8.0+)',
        'REGEXP_INSTR': 'REGEXP_INSTR() (MySQL 8.0+)',
        
        # 시스템 함수
        'SYS_CONTEXT': '세션 변수 (@variable) 또는 애플리케이션',
        'EXTRACT': 'EXTRACT (동일)',
        
        # 기타
        'DUAL': '불필요 (FROM 절 생략 가능)',
        'ROWID': '미지원 (PRIMARY KEY 사용)',
        'FLASHBACK': '미지원 (바이너리 로그 기반 복구)',
        'SYS_CONNECT_BY_PATH': '재귀 CTE에서 경로 생성 (MySQL 8.0+)',
        
        # PL/SQL 관련 (Requirement 15.3 - 애플리케이션 이관 권장)
        'BULK COLLECT': '미지원 - 루프 처리 또는 애플리케이션 이관 권장',
        'FORALL': '미지원 - 루프 처리 또는 애플리케이션 이관 권장',
        'PIPELINED': '미지원 - 임시 테이블 또는 애플리케이션 이관 권장',
        'REF CURSOR': '미지원 - 임시 테이블 또는 애플리케이션 이관 권장',
        'AUTONOMOUS_TRANSACTION': '미지원 - 별도 연결 또는 애플리케이션 이관 권장',
        'PRAGMA': '미지원',
        'OBJECT TYPE': '미지원 - JSON 또는 별도 테이블',
        'VARRAY': '미지원 - JSON 배열',
        'NESTED TABLE': '미지원 - JSON 또는 별도 테이블',
        
        # 외부 의존성
        'UTL_FILE': '미지원 - 애플리케이션 이관 필수',
        'UTL_HTTP': '미지원 - 애플리케이션 이관 필수',
        'UTL_MAIL': '미지원 - 애플리케이션 이관 필수',
        'UTL_SMTP': '미지원 - 애플리케이션 이관 필수',
        'DBMS_SCHEDULER': '미지원 - 외부 스케줄러 (cron 등) 사용',
        'DBMS_JOB': '미지원 - 외부 스케줄러 (cron 등) 사용',
        'DBMS_LOB': 'BLOB/TEXT 타입 및 내장 함수',
        'DBMS_OUTPUT': '미지원 - 로그 테이블 또는 애플리케이션',
        'DBMS_CRYPTO': '미지원 - 애플리케이션 암호화',
        'DBMS_SQL': 'PREPARE/EXECUTE 동적 SQL',
        
        # 트랜잭션
        'SAVEPOINT': 'SAVEPOINT (동일)',
        'ROLLBACK TO SAVEPOINT': 'ROLLBACK TO SAVEPOINT (동일)',
        
        # 오브젝트 타입 (Requirement 15.3)
        'Package': '미지원 - 애플리케이션 레벨 이관 필수',
        'Procedure': 'PROCEDURE (제한적 지원) - 애플리케이션 레벨 이관 권장',
        'Function': 'FUNCTION (제한적 지원) - 애플리케이션 레벨 이관 권장',
        'Trigger': 'TRIGGER (제한적 지원) - 복잡한 로직은 애플리케이션 이관 권장',
        'View': 'VIEW (동일)',
        'Materialized View': '미지원 - 일반 테이블 + 스케줄러',
    }
    
    def __init__(self, target_database):
        """ConversionGuideProvider 초기화
        
        Args:
            target_database: 타겟 데이터베이스 (PostgreSQL 또는 MySQL) - TargetDatabase Enum 또는 문자열
        """
        # 문자열인 경우 TargetDatabase Enum으로 변환
        if isinstance(target_database, str):
            # "<TargetDatabase.POSTGRESQL: 'postgresql'>" 형식의 문자열 처리
            if target_database.startswith("<TargetDatabase."):
                # 'postgresql' 부분 추출
                target_value = target_database.split("'")[1]
                if target_value == "postgresql":
                    target_database = TargetDatabase.POSTGRESQL
                elif target_value == "mysql":
                    target_database = TargetDatabase.MYSQL
                else:
                    raise ValueError(f"지원하지 않는 타겟 데이터베이스: {target_database}")
            # "TargetDatabase.POSTGRESQL" 형식의 문자열 처리
            elif target_database.startswith("TargetDatabase."):
                enum_name = target_database.split(".")[-1]
                target_database = TargetDatabase[enum_name]
            else:
                # 일반 문자열 처리
                target_lower = target_database.lower()
                if target_lower in ['postgresql', 'pg']:
                    target_database = TargetDatabase.POSTGRESQL
                elif target_lower in ['mysql', 'my']:
                    target_database = TargetDatabase.MYSQL
                else:
                    raise ValueError(f"지원하지 않는 타겟 데이터베이스: {target_database}")
        
        self.target = target_database
        
        # Enum 값의 문자열 비교를 사용하여 순환 참조 문제 회피
        target_value = target_database.value if hasattr(target_database, 'value') else str(target_database)
        
        self.mappings = (
            self.POSTGRESQL_MAPPINGS 
            if target_value == "postgresql"
            else self.MYSQL_MAPPINGS
        )
    
    def get_conversion_guide(self, detected_features: List[str]) -> Dict[str, str]:
        """감지된 Oracle 기능에 대한 변환 가이드 반환
        
        Requirements 15.1, 15.2, 15.3을 구현합니다.
        
        Args:
            detected_features: 감지된 Oracle 특화 기능 목록
        
        Returns:
            Dict[str, str]: {기능명: 변환 가이드} 매핑
        
        Example:
            >>> provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
            >>> features = ['ROWNUM', 'DECODE', 'NVL']
            >>> guides = provider.get_conversion_guide(features)
            >>> print(guides['ROWNUM'])
            'LIMIT/OFFSET 또는 ROW_NUMBER() OVER()'
        """
        guides = {}
        
        for feature in detected_features:
            # 대소문자 구분 없이 매칭
            feature_upper = feature.upper()
            
            # 직접 매칭 시도
            if feature_upper in self.mappings:
                guides[feature] = self.mappings[feature_upper]
            else:
                # 부분 매칭 시도 (예: "SEQUENCE.NEXTVAL" → "NEXTVAL")
                matched = False
                for key, value in self.mappings.items():
                    if key in feature_upper or feature_upper in key:
                        guides[feature] = value
                        matched = True
                        break
                
                # 부분 매칭도 실패한 경우, 원본 feature로 한 번 더 시도
                # (예: 'Package' → 'PACKAGE')
                if not matched:
                    # 정확히 일치하는 키를 찾기 위해 대소문자 무시하고 검색
                    for key, value in self.mappings.items():
                        if key.upper() == feature_upper:
                            guides[feature] = value
                            break
        
        return guides
    
    def get_all_mappings(self) -> Dict[str, str]:
        """현재 타겟 DB의 모든 변환 매핑 반환
        
        Returns:
            Dict[str, str]: 전체 변환 매핑
        """
        return self.mappings.copy()
    
    def has_mapping(self, feature: str) -> bool:
        """특정 기능에 대한 변환 가이드 존재 여부 확인
        
        Args:
            feature: Oracle 기능명
        
        Returns:
            bool: 변환 가이드 존재 여부
        """
        feature_upper = feature.upper()
        return feature_upper in self.mappings
    
    def get_mysql_app_migration_message(self) -> str:
        """MySQL 타겟에서 PL/SQL 애플리케이션 이관 권장 메시지 반환
        
        Requirement 15.3을 구현합니다.
        
        Returns:
            str: 애플리케이션 이관 권장 메시지
        """
        if self.target == TargetDatabase.MYSQL:
            return (
                "⚠️ MySQL은 PL/SQL을 제한적으로 지원합니다. "
                "복잡한 비즈니스 로직은 애플리케이션 레벨로 이관하는 것을 강력히 권장합니다."
            )
        return ""
