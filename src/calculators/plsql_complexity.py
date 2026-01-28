"""
PL/SQL 복잡도 계산

PL/SQL 오브젝트의 복잡도를 계산하는 메서드들을 제공합니다.
"""

import logging
from src.oracle_complexity_analyzer import (
    TargetDatabase,
    PLSQLAnalysisResult,
    PLSQLObjectType,
    PLSQL_BASE_SCORES,
    MYSQL_APP_MIGRATION_PENALTY,
)
from src.oracle_complexity_analyzer.constants import EXTERNAL_DEPENDENCY_SCORES
from src.parsers.plsql import PLSQLParser

# 로거 초기화
logger = logging.getLogger(__name__)


class PLSQLComplexityCalculator:
    """PL/SQL 복잡도 계산 믹스인 클래스"""
    
    def calculate_plsql_complexity(self, parser: PLSQLParser) -> PLSQLAnalysisResult:
        """PL/SQL 오브젝트 복잡도 계산
        
        Requirements 12.2를 구현합니다.
        
        Args:
            parser: PL/SQL 파서 객체
            
        Returns:
            PLSQLAnalysisResult: PL/SQL 분석 결과
        """
        logger.info(f"PL/SQL 복잡도 계산 시작 (타겟: {self.target.value})")
        
        # 오브젝트 타입 감지
        object_type = parser.detect_object_type()
        logger.info(f"PL/SQL 오브젝트 타입: {object_type.value}")
        
        # 기본 점수 (Enum 값으로 비교하여 순환 import 문제 회피)
        # self.target의 value를 사용하여 PLSQL_BASE_SCORES에서 찾기
        target_key = None
        for key in PLSQL_BASE_SCORES.keys():
            if key.value == self.target.value:
                target_key = key
                break
        
        if target_key is None:
            raise ValueError(f"지원하지 않는 타겟 데이터베이스: {self.target}")
        
        base_score = PLSQL_BASE_SCORES[target_key][object_type]
        
        # 코드 복잡도 점수
        logger.info("PL/SQL 코드 복잡도 계산 중")
        code_complexity = self._calculate_plsql_code_complexity(parser)
        
        # Oracle 특화 기능 점수
        logger.info("PL/SQL Oracle 특화 기능 점수 계산 중")
        oracle_features = self._calculate_plsql_oracle_features(parser)
        
        # 비즈니스 로직 복잡도 점수
        logger.info("PL/SQL 비즈니스 로직 복잡도 계산 중")
        business_logic = self._calculate_plsql_business_logic(parser)
        
        # 변환 난이도 점수
        logger.info("PL/SQL 변환 난이도 계산 중")
        conversion_difficulty = self._calculate_plsql_conversion_difficulty(parser)
        
        # MySQL 특화 제약 점수 (MySQL 타겟만)
        mysql_constraints = 0.0
        app_migration_penalty = 0.0
        if self.target == TargetDatabase.MYSQL:
            logger.info("MySQL 특화 제약 점수 계산 중")
            mysql_constraints = self._calculate_mysql_constraints(parser, object_type)
            app_migration_penalty = MYSQL_APP_MIGRATION_PENALTY[object_type]
        
        # 총점 계산
        total_score = (
            base_score +
            code_complexity +
            oracle_features +
            business_logic +
            conversion_difficulty +
            mysql_constraints +
            app_migration_penalty
        )
        
        # 점수 정규화 및 레벨 분류
        normalized_score = self._normalize_plsql_score(total_score)
        complexity_level = self._get_complexity_level(normalized_score)
        recommendation = self._get_recommendation(complexity_level)
        
        logger.info(f"PL/SQL 복잡도 계산 완료 (정규화 점수: {normalized_score:.2f}, 레벨: {complexity_level.value})")
        
        # 결과 객체 생성
        result = PLSQLAnalysisResult(
            code=parser.code,
            object_type=object_type,
            target_database=self.target,
            total_score=total_score,
            normalized_score=normalized_score,
            complexity_level=complexity_level,
            recommendation=recommendation,
            base_score=base_score,
            code_complexity=code_complexity,
            oracle_features=oracle_features,
            business_logic=business_logic,
            conversion_difficulty=conversion_difficulty,
            mysql_constraints=mysql_constraints,
            app_migration_penalty=app_migration_penalty,
            detected_oracle_features=parser.detect_advanced_features(),
            detected_external_dependencies=parser.detect_external_dependencies(),
            line_count=parser.count_lines(),
            cursor_count=parser.count_cursors(),
            exception_blocks=parser.count_exception_blocks(),
            nesting_depth=parser.calculate_nesting_depth(),
            bulk_operations_count=parser.count_bulk_operations(),
            dynamic_sql_count=parser.count_dynamic_sql(),
        )
        
        return result
    
    def _calculate_plsql_code_complexity(self, parser: PLSQLParser) -> float:
        """PL/SQL 코드 복잡도 점수 계산
        
        PLSQL_COMPLEXITY_SCORE_IMPROVEMENT.md 기반 개선:
        - 8.2: 코드 라인 수 (세분화)
        - 8.3: 커서 개수 (상향: min(2.0, count*0.5))
        - 8.4: 예외 처리 블록 (상향: min(1.0, count*0.4))
        - 8.5: 중첩 깊이에 따른 점수
        
        Args:
            parser: PL/SQL 파서 객체
            
        Returns:
            float: 코드 복잡도 점수
        """
        score = 0.0
        
        # 8.2: 코드 라인 수 (세분화)
        line_count = parser.count_lines()
        if line_count < 50:
            score += 0.3
        elif line_count < 100:
            score += 0.5
        elif line_count < 300:
            score += 1.0
        elif line_count < 500:
            score += 1.5
        elif line_count < 1000:
            score += 2.0
        elif line_count < 2000:
            score += 2.5
        elif line_count < 5000:
            score += 3.0
        else:
            score += 3.5
        
        # 8.3: 커서 개수 (상향 조정: 0.3→0.5, 최대 1.0→2.0)
        cursor_count = parser.count_cursors()
        score += min(2.0, cursor_count * 0.5)
        
        # 8.4: 예외 처리 블록 (상향 조정: 0.2→0.4, 최대 0.5→1.0)
        exception_blocks = parser.count_exception_blocks()
        score += min(1.0, exception_blocks * 0.4)
        
        # 8.5: 중첩 깊이
        nesting_depth = parser.calculate_nesting_depth()
        if nesting_depth <= 2:
            pass  # 0점
        elif nesting_depth <= 4:
            score += 0.5
        elif nesting_depth <= 6:
            score += 1.0
        else:
            score += 1.5
        
        return min(score, 4.0)  # 최대 4.0점 (기존 3.0점에서 상향)
    
    def _calculate_plsql_oracle_features(self, parser: PLSQLParser) -> float:
        """PL/SQL Oracle 특화 기능 점수 계산
        
        PLSQL_COMPLEXITY_SCORE_IMPROVEMENT.md 기반 개선:
        - 9.1: 패키지 의존성 (min(2.0, count*0.5))
        - 9.2: DB Link (min(1.5, count*1.0))
        - 9.3: 동적 SQL (상향: min(2.0, count*0.8))
        - 9.4: BULK 연산 (PostgreSQL: min(1.0, count*0.4), MySQL: min(0.8, count*0.3))
        - 9.5: 고급 기능 (min(1.5, count*0.5))
        - 신규: 타입 참조, 사용자 정의 타입, RETURNING INTO, 조건부 컴파일
        
        Args:
            parser: PL/SQL 파서 객체
            
        Returns:
            float: Oracle 특화 기능 점수
        """
        score = 0.0
        
        # 9.1: 패키지 의존성
        package_calls = parser.count_package_calls()
        score += min(2.0, package_calls * 0.5)
        
        # 9.2: DB Link
        dblink_count = parser.count_dblinks()
        score += min(1.5, dblink_count * 1.0)
        
        # 9.3: 동적 SQL (상향 조정: 0.5→0.8, 최대 1.0→2.0)
        dynamic_sql_count = parser.count_dynamic_sql()
        score += min(2.0, dynamic_sql_count * 0.8)
        
        # 9.3.1: 동적 DDL 추가 점수 (신규)
        dynamic_ddl_count = parser.count_dynamic_ddl()
        score += min(1.0, dynamic_ddl_count * 0.5)
        
        # 9.4: BULK 연산
        bulk_operations_count = parser.count_bulk_operations()
        if self.target == TargetDatabase.POSTGRESQL:
            score += min(1.0, bulk_operations_count * 0.4)
        else:  # MySQL
            score += min(0.8, bulk_operations_count * 0.3)
        
        # 9.5: 고급 기능
        advanced_features = parser.detect_advanced_features()
        score += min(1.5, len(advanced_features) * 0.5)
        
        # 신규: 타입 참조 (%TYPE, %ROWTYPE)
        type_refs = parser.count_type_references()
        if self.target == TargetDatabase.POSTGRESQL:
            score += min(1.0, type_refs['type'] * 0.3)
            score += min(1.5, type_refs['rowtype'] * 0.5)
        else:  # MySQL
            score += min(1.0, type_refs['type'] * 0.5)
            score += min(1.5, type_refs['rowtype'] * 0.8)
        
        # 신규: 사용자 정의 타입 (RECORD, TABLE OF, VARRAY, INDEX BY)
        user_types = parser.count_user_defined_types()
        if self.target == TargetDatabase.POSTGRESQL:
            score += min(1.5, user_types['record'] * 0.5)
            score += min(2.0, user_types['table_of'] * 0.8)
            score += min(2.0, user_types['varray'] * 0.8)
            score += min(2.0, user_types['index_by'] * 1.0)
        else:  # MySQL
            score += min(1.5, user_types['record'] * 0.8)
            score += min(2.0, user_types['table_of'] * 1.2)
            score += min(2.0, user_types['varray'] * 1.2)
            score += min(2.0, user_types['index_by'] * 1.5)
        
        # 신규: RETURNING INTO
        returning_into_count = parser.count_returning_into()
        if self.target == TargetDatabase.POSTGRESQL:
            score += min(1.0, returning_into_count * 0.3)
        else:  # MySQL
            score += min(2.0, returning_into_count * 0.8)
        
        # 신규: 조건부 컴파일
        conditional_compilation = parser.count_conditional_compilation()
        score += min(1.5, conditional_compilation * 0.5)
        
        return min(score, 5.0)  # 최대 5.0점 (기존 3.0점에서 상향)
    
    def _calculate_plsql_business_logic(self, parser: PLSQLParser) -> float:
        """PL/SQL 비즈니스 로직 복잡도 점수 계산
        
        PLSQL_COMPLEXITY_SCORE_IMPROVEMENT.md 기반 개선:
        - 10.1: 트랜잭션 처리 (0.5-0.8점)
        - 10.2: 복잡한 계산 (min(1.0, count*0.3))
        - 10.3: 데이터 검증 (min(0.5, count*0.2))
        - 10.4: 컨텍스트 의존성 (min(1.0, count*0.5))
        - 10.5: 패키지 변수 (0.8점)
        - 신규: RAISE_APPLICATION_ERROR, Oracle 전용 예외, SQLCODE/SQLERRM
        
        Args:
            parser: PL/SQL 파서 객체
            
        Returns:
            float: 비즈니스 로직 복잡도 점수
        """
        score = 0.0
        
        # 10.1: 트랜잭션 처리
        transaction_control = parser.has_transaction_control()
        if transaction_control.get('savepoint', False):
            score += 0.8  # SAVEPOINT, ROLLBACK TO SAVEPOINT
        elif transaction_control.get('rollback', False) or transaction_control.get('commit', False):
            score += 0.5
        
        # 10.2: 복잡한 계산 (간단한 휴리스틱: 산술 연산자 개수)
        complex_calc_count = parser.upper_code.count('+') + parser.upper_code.count('-') + \
                            parser.upper_code.count('*') + parser.upper_code.count('/')
        score += min(1.0, (complex_calc_count // 10) * 0.3)  # 10개당 0.3점
        
        # 10.3: 데이터 검증 (IF 문 개수로 추정)
        validation_checks = parser.upper_code.count('IF ')
        score += min(0.5, validation_checks * 0.2)
        
        # 10.4: 컨텍스트 의존성
        context_features = parser.detect_context_dependencies()
        score += min(1.0, len(context_features) * 0.5)
        
        # 10.5: 패키지 변수
        if parser.has_package_variables():
            score += 0.8
        
        # 신규: RAISE_APPLICATION_ERROR
        raise_app_error_count = parser.count_raise_application_error()
        if self.target == TargetDatabase.POSTGRESQL:
            score += min(1.0, raise_app_error_count * 0.3)
        else:  # MySQL
            score += min(1.5, raise_app_error_count * 0.5)
        
        # 신규: Oracle 전용 예외 사용
        oracle_exceptions = parser.detect_oracle_specific_exceptions()
        score += min(0.5, len(oracle_exceptions) * 0.1)
        
        # 신규: SQLCODE/SQLERRM 사용
        sqlcode_sqlerrm = parser.has_sqlcode_sqlerrm()
        if sqlcode_sqlerrm['sqlcode'] or sqlcode_sqlerrm['sqlerrm']:
            score += 0.2
        
        return min(score, 3.0)  # 최대 3.0점 (기존 2.0점에서 상향)
    
    def _calculate_plsql_conversion_difficulty(self, parser: PLSQLParser) -> float:
        """PL/SQL 변환 난이도 점수 계산
        
        PLSQL_COMPLEXITY_SCORE_IMPROVEMENT.md 기반 개선:
        - 10.6: 외부 의존성 (차등 점수 적용, 최대 3.0점)
        
        Args:
            parser: PL/SQL 파서 객체
            
        Returns:
            float: 변환 난이도 점수
        """
        score = 0.0
        
        # 10.6: 외부 의존성 (차등 점수 적용)
        external_deps = parser.detect_external_dependencies()
        
        for dep in external_deps:
            # 패키지별 차등 점수 적용 (기본값 0.5)
            dep_score = EXTERNAL_DEPENDENCY_SCORES.get(dep, 0.5)
            score += dep_score
        
        return min(score, 3.0)  # 최대 3.0점 (기존 2.0점에서 상향)
    
    def _calculate_mysql_constraints(self, parser: PLSQLParser, object_type: PLSQLObjectType) -> float:
        """MySQL 특화 제약 점수 계산
        
        Requirements 11.1-11.3을 구현합니다.
        - 11.1: 데이터 타입 변환 이슈
        - 11.2: 트리거 제약
        - 11.3: 뷰 제약
        
        Args:
            parser: PL/SQL 파서 객체
            object_type: PL/SQL 오브젝트 타입
            
        Returns:
            float: MySQL 특화 제약 점수
        """
        score = 0.0
        
        # 11.1: 데이터 타입 변환 이슈
        if 'NUMBER' in parser.upper_code:
            score += 0.5  # NUMBER 정밀도 이슈
        if 'CLOB' in parser.upper_code or 'BLOB' in parser.upper_code:
            score += 0.3
        if 'VARCHAR2' in parser.upper_code:
            score += 0.3  # 빈 문자열 처리 차이
        
        # 11.2: 트리거 제약
        if object_type == PLSQLObjectType.TRIGGER:
            if 'INSTEAD OF' in parser.upper_code:
                score += 0.5
            if 'COMPOUND' in parser.upper_code:
                score += 0.5
        
        # 11.3: 뷰 제약
        if object_type == PLSQLObjectType.VIEW:
            if 'UPDATE' in parser.upper_code or 'INSERT' in parser.upper_code:
                score += 0.3  # 업데이트 가능 뷰
        
        if object_type == PLSQLObjectType.MATERIALIZED_VIEW:
            score += 0.5
        
        return min(score, 1.5)  # 최대 1.5점
