"""
데이터 모델 테스트

SQLAnalysisResult, PLSQLAnalysisResult, WeightConfig 데이터클래스의 기본 동작을 검증합니다.
"""

import pytest
from src.oracle_complexity_analyzer import (
    SQLAnalysisResult,
    PLSQLAnalysisResult,
    WeightConfig,
    TargetDatabase,
    ComplexityLevel,
    PLSQLObjectType,
    POSTGRESQL_WEIGHTS,
    MYSQL_WEIGHTS,
)


class TestSQLAnalysisResult:
    """SQLAnalysisResult 데이터클래스 테스트"""
    
    def test_create_sql_analysis_result_with_required_fields(self):
        """필수 필드만으로 SQLAnalysisResult 생성 테스트"""
        result = SQLAnalysisResult(
            query="SELECT * FROM users",
            target_database=TargetDatabase.POSTGRESQL,
            total_score=5.5,
            normalized_score=4.0,
            complexity_level=ComplexityLevel.MODERATE,
            recommendation="부분 재작성",
            structural_complexity=1.5,
            oracle_specific_features=1.0,
            functions_expressions=0.5,
            data_volume=1.0,
            execution_complexity=0.5,
            conversion_difficulty=1.0,
        )
        
        assert result.query == "SELECT * FROM users"
        assert result.target_database == TargetDatabase.POSTGRESQL
        assert result.total_score == 5.5
        assert result.normalized_score == 4.0
        assert result.complexity_level == ComplexityLevel.MODERATE
        assert result.recommendation == "부분 재작성"
        
    def test_sql_analysis_result_default_fields(self):
        """기본값이 있는 필드들이 올바르게 초기화되는지 테스트"""
        result = SQLAnalysisResult(
            query="SELECT * FROM users",
            target_database=TargetDatabase.MYSQL,
            total_score=3.0,
            normalized_score=2.5,
            complexity_level=ComplexityLevel.SIMPLE,
            recommendation="함수 대체",
            structural_complexity=1.0,
            oracle_specific_features=0.5,
            functions_expressions=0.5,
            data_volume=0.5,
            execution_complexity=0.3,
            conversion_difficulty=0.2,
        )
        
        # 기본값 검증
        assert result.detected_oracle_features == []
        assert result.detected_oracle_functions == []
        assert result.detected_hints == []
        assert result.join_count == 0
        assert result.subquery_depth == 0
        assert result.cte_count == 0
        assert result.set_operators_count == 0
        assert result.conversion_guides == {}
        
    def test_sql_analysis_result_with_detected_features(self):
        """감지된 Oracle 기능이 포함된 SQLAnalysisResult 테스트"""
        result = SQLAnalysisResult(
            query="SELECT * FROM users WHERE ROWNUM <= 10",
            target_database=TargetDatabase.POSTGRESQL,
            total_score=6.0,
            normalized_score=5.0,
            complexity_level=ComplexityLevel.COMPLEX,
            recommendation="상당한 재작성",
            structural_complexity=1.5,
            oracle_specific_features=2.0,
            functions_expressions=1.0,
            data_volume=0.5,
            execution_complexity=0.5,
            conversion_difficulty=0.5,
            detected_oracle_features=["ROWNUM", "DECODE"],
            detected_oracle_functions=["NVL", "TO_CHAR"],
            detected_hints=["INDEX", "FULL"],
            join_count=2,
            subquery_depth=1,
            cte_count=0,
            set_operators_count=0,
            conversion_guides={"ROWNUM": "LIMIT/OFFSET", "NVL": "COALESCE"},
        )
        
        assert len(result.detected_oracle_features) == 2
        assert "ROWNUM" in result.detected_oracle_features
        assert "DECODE" in result.detected_oracle_features
        
        assert len(result.detected_oracle_functions) == 2
        assert "NVL" in result.detected_oracle_functions
        assert "TO_CHAR" in result.detected_oracle_functions
        
        assert len(result.detected_hints) == 2
        assert "INDEX" in result.detected_hints
        
        assert result.join_count == 2
        assert result.subquery_depth == 1
        
        assert "ROWNUM" in result.conversion_guides
        assert result.conversion_guides["ROWNUM"] == "LIMIT/OFFSET"
        
    def test_sql_analysis_result_six_detail_scores(self):
        """Requirements 13.1: 6가지 세부 점수가 모두 포함되는지 검증"""
        result = SQLAnalysisResult(
            query="SELECT * FROM users",
            target_database=TargetDatabase.POSTGRESQL,
            total_score=10.0,
            normalized_score=8.0,
            complexity_level=ComplexityLevel.VERY_COMPLEX,
            recommendation="대부분 재작성",
            structural_complexity=2.0,
            oracle_specific_features=2.5,
            functions_expressions=1.5,
            data_volume=1.5,
            execution_complexity=1.5,
            conversion_difficulty=1.0,
        )
        
        # 6가지 세부 점수 검증
        assert hasattr(result, 'structural_complexity')
        assert hasattr(result, 'oracle_specific_features')
        assert hasattr(result, 'functions_expressions')
        assert hasattr(result, 'data_volume')
        assert hasattr(result, 'execution_complexity')
        assert hasattr(result, 'conversion_difficulty')
        
        # 점수 값 검증
        assert result.structural_complexity == 2.0
        assert result.oracle_specific_features == 2.5
        assert result.functions_expressions == 1.5
        assert result.data_volume == 1.5
        assert result.execution_complexity == 1.5
        assert result.conversion_difficulty == 1.0



class TestPLSQLAnalysisResult:
    """PLSQLAnalysisResult 데이터클래스 테스트"""
    
    def test_create_plsql_analysis_result_with_required_fields(self):
        """필수 필드만으로 PLSQLAnalysisResult 생성 테스트"""
        result = PLSQLAnalysisResult(
            code="CREATE OR REPLACE PROCEDURE test_proc IS BEGIN NULL; END;",
            object_type=PLSQLObjectType.PROCEDURE,
            target_database=TargetDatabase.POSTGRESQL,
            total_score=8.0,
            normalized_score=6.5,
            complexity_level=ComplexityLevel.COMPLEX,
            recommendation="상당한 재작성",
            base_score=5.0,
            code_complexity=1.0,
            oracle_features=1.0,
            business_logic=0.5,
            ai_difficulty=0.5,
        )
        
        assert result.code == "CREATE OR REPLACE PROCEDURE test_proc IS BEGIN NULL; END;"
        assert result.object_type == PLSQLObjectType.PROCEDURE
        assert result.target_database == TargetDatabase.POSTGRESQL
        assert result.total_score == 8.0
        assert result.normalized_score == 6.5
        assert result.complexity_level == ComplexityLevel.COMPLEX
        assert result.recommendation == "상당한 재작성"
        
    def test_plsql_analysis_result_default_fields(self):
        """기본값이 있는 필드들이 올바르게 초기화되는지 테스트"""
        result = PLSQLAnalysisResult(
            code="CREATE FUNCTION test_func RETURN NUMBER IS BEGIN RETURN 1; END;",
            object_type=PLSQLObjectType.FUNCTION,
            target_database=TargetDatabase.MYSQL,
            total_score=7.0,
            normalized_score=5.5,
            complexity_level=ComplexityLevel.COMPLEX,
            recommendation="상당한 재작성",
            base_score=5.0,
            code_complexity=1.0,
            oracle_features=0.5,
            business_logic=0.3,
            ai_difficulty=0.2,
        )
        
        # 기본값 검증
        assert result.mysql_constraints == 0.0
        assert result.app_migration_penalty == 0.0
        assert result.detected_oracle_features == []
        assert result.detected_external_dependencies == []
        assert result.line_count == 0
        assert result.cursor_count == 0
        assert result.exception_blocks == 0
        assert result.nesting_depth == 0
        assert result.bulk_operations_count == 0
        assert result.dynamic_sql_count == 0
        assert result.conversion_guides == {}
        
    def test_plsql_analysis_result_with_mysql_specific_fields(self):
        """MySQL 타겟 특화 필드가 포함된 PLSQLAnalysisResult 테스트"""
        result = PLSQLAnalysisResult(
            code="CREATE OR REPLACE PACKAGE test_pkg IS END;",
            object_type=PLSQLObjectType.PACKAGE,
            target_database=TargetDatabase.MYSQL,
            total_score=12.0,
            normalized_score=9.0,
            complexity_level=ComplexityLevel.EXTREMELY_COMPLEX,
            recommendation="완전 재설계",
            base_score=8.0,
            code_complexity=1.5,
            oracle_features=1.0,
            business_logic=0.5,
            ai_difficulty=0.5,
            mysql_constraints=0.5,
            app_migration_penalty=2.0,
        )
        
        assert result.mysql_constraints == 0.5
        assert result.app_migration_penalty == 2.0
        assert result.target_database == TargetDatabase.MYSQL
        
    def test_plsql_analysis_result_with_detected_features(self):
        """감지된 Oracle 기능과 외부 의존성이 포함된 PLSQLAnalysisResult 테스트"""
        result = PLSQLAnalysisResult(
            code="CREATE TRIGGER test_trg BEFORE INSERT ON users FOR EACH ROW BEGIN NULL; END;",
            object_type=PLSQLObjectType.TRIGGER,
            target_database=TargetDatabase.POSTGRESQL,
            total_score=9.0,
            normalized_score=7.0,
            complexity_level=ComplexityLevel.VERY_COMPLEX,
            recommendation="대부분 재작성",
            base_score=6.0,
            code_complexity=1.5,
            oracle_features=1.0,
            business_logic=0.3,
            ai_difficulty=0.2,
            detected_oracle_features=["BULK COLLECT", "FORALL", "REF CURSOR"],
            detected_external_dependencies=["UTL_FILE", "DBMS_SCHEDULER"],
            line_count=150,
            cursor_count=3,
            exception_blocks=2,
            nesting_depth=4,
            bulk_operations_count=2,
            dynamic_sql_count=1,
            conversion_guides={
                "BULK COLLECT": "순수 SQL/Chunked Batch",
                "UTL_FILE": "파일 시스템 접근 재설계",
            },
        )
        
        assert len(result.detected_oracle_features) == 3
        assert "BULK COLLECT" in result.detected_oracle_features
        assert "FORALL" in result.detected_oracle_features
        assert "REF CURSOR" in result.detected_oracle_features
        
        assert len(result.detected_external_dependencies) == 2
        assert "UTL_FILE" in result.detected_external_dependencies
        assert "DBMS_SCHEDULER" in result.detected_external_dependencies
        
        assert result.line_count == 150
        assert result.cursor_count == 3
        assert result.exception_blocks == 2
        assert result.nesting_depth == 4
        assert result.bulk_operations_count == 2
        assert result.dynamic_sql_count == 1
        
        assert "BULK COLLECT" in result.conversion_guides
        assert result.conversion_guides["BULK COLLECT"] == "순수 SQL/Chunked Batch"
        
    def test_plsql_analysis_result_five_to_seven_detail_scores(self):
        """Requirements 13.2: 5-7가지 세부 점수가 모두 포함되는지 검증"""
        # PostgreSQL 타겟 (5가지 세부 점수)
        pg_result = PLSQLAnalysisResult(
            code="CREATE PROCEDURE test IS BEGIN NULL; END;",
            object_type=PLSQLObjectType.PROCEDURE,
            target_database=TargetDatabase.POSTGRESQL,
            total_score=8.0,
            normalized_score=6.0,
            complexity_level=ComplexityLevel.COMPLEX,
            recommendation="상당한 재작성",
            base_score=5.0,
            code_complexity=1.5,
            oracle_features=1.0,
            business_logic=0.3,
            ai_difficulty=0.2,
        )
        
        # 5가지 기본 세부 점수 검증
        assert hasattr(pg_result, 'base_score')
        assert hasattr(pg_result, 'code_complexity')
        assert hasattr(pg_result, 'oracle_features')
        assert hasattr(pg_result, 'business_logic')
        assert hasattr(pg_result, 'ai_difficulty')
        
        assert pg_result.base_score == 5.0
        assert pg_result.code_complexity == 1.5
        assert pg_result.oracle_features == 1.0
        assert pg_result.business_logic == 0.3
        assert pg_result.ai_difficulty == 0.2
        
        # MySQL 타겟 (7가지 세부 점수)
        mysql_result = PLSQLAnalysisResult(
            code="CREATE PROCEDURE test IS BEGIN NULL; END;",
            object_type=PLSQLObjectType.PROCEDURE,
            target_database=TargetDatabase.MYSQL,
            total_score=10.0,
            normalized_score=8.0,
            complexity_level=ComplexityLevel.VERY_COMPLEX,
            recommendation="대부분 재작성",
            base_score=6.0,
            code_complexity=1.5,
            oracle_features=1.0,
            business_logic=0.3,
            ai_difficulty=0.2,
            mysql_constraints=0.5,
            app_migration_penalty=2.0,
        )
        
        # 7가지 세부 점수 검증 (MySQL 특화 필드 포함)
        assert hasattr(mysql_result, 'base_score')
        assert hasattr(mysql_result, 'code_complexity')
        assert hasattr(mysql_result, 'oracle_features')
        assert hasattr(mysql_result, 'business_logic')
        assert hasattr(mysql_result, 'ai_difficulty')
        assert hasattr(mysql_result, 'mysql_constraints')
        assert hasattr(mysql_result, 'app_migration_penalty')
        
        assert mysql_result.mysql_constraints == 0.5
        assert mysql_result.app_migration_penalty == 2.0
        
    def test_plsql_analysis_result_all_object_types(self):
        """모든 PL/SQL 오브젝트 타입에 대한 테스트"""
        object_types = [
            PLSQLObjectType.PACKAGE,
            PLSQLObjectType.PROCEDURE,
            PLSQLObjectType.FUNCTION,
            PLSQLObjectType.TRIGGER,
            PLSQLObjectType.VIEW,
            PLSQLObjectType.MATERIALIZED_VIEW,
        ]
        
        for obj_type in object_types:
            result = PLSQLAnalysisResult(
                code=f"CREATE {obj_type.value.upper()} test IS BEGIN NULL; END;",
                object_type=obj_type,
                target_database=TargetDatabase.POSTGRESQL,
                total_score=5.0,
                normalized_score=4.0,
                complexity_level=ComplexityLevel.MODERATE,
                recommendation="부분 재작성",
                base_score=3.0,
                code_complexity=1.0,
                oracle_features=0.5,
                business_logic=0.3,
                ai_difficulty=0.2,
            )
            
            assert result.object_type == obj_type


class TestWeightConfig:
    """WeightConfig 데이터클래스 테스트"""
    
    def test_create_weight_config_with_required_fields(self):
        """필수 필드만으로 WeightConfig 생성 테스트"""
        config = WeightConfig(
            max_structural=2.5,
            join_thresholds=[(0, 0.0), (3, 0.5)],
            subquery_thresholds=[(0, 0.0), (1, 0.5)],
            cte_coefficient=0.5,
            cte_max=1.0,
            set_operator_coefficient=0.5,
            set_operator_max=1.5,
        )
        
        assert config.max_structural == 2.5
        assert len(config.join_thresholds) == 2
        assert config.cte_coefficient == 0.5
        assert config.cte_max == 1.0
        
    def test_weight_config_default_fields(self):
        """기본값이 있는 필드들이 올바르게 초기화되는지 테스트"""
        config = WeightConfig(
            max_structural=2.5,
            join_thresholds=[(0, 0.0)],
            subquery_thresholds=[(0, 0.0)],
            cte_coefficient=0.5,
            cte_max=1.0,
            set_operator_coefficient=0.5,
            set_operator_max=1.5,
        )
        
        # 기본값 검증
        assert config.fullscan_penalty == 0.0
        assert config.data_volume_scores == {}
        assert config.execution_scores == {}
        assert config.max_total_score == 0.0
        
    def test_postgresql_weights_configuration(self):
        """PostgreSQL 가중치 설정이 올바르게 정의되었는지 테스트"""
        # Requirements 1.1-1.5, 3.1, 5.1-5.4, 6.1-6.5 검증
        
        # 구조적 복잡성 최대 점수
        assert POSTGRESQL_WEIGHTS.max_structural == 2.5
        
        # JOIN 임계값 검증 (Requirements 1.1)
        assert len(POSTGRESQL_WEIGHTS.join_thresholds) == 4
        assert POSTGRESQL_WEIGHTS.join_thresholds[0] == (0, 0.0)
        assert POSTGRESQL_WEIGHTS.join_thresholds[1] == (3, 0.5)
        assert POSTGRESQL_WEIGHTS.join_thresholds[2] == (5, 1.0)
        assert POSTGRESQL_WEIGHTS.join_thresholds[3] == (float('inf'), 1.5)
        
        # 서브쿼리 임계값 검증 (Requirements 1.2)
        assert len(POSTGRESQL_WEIGHTS.subquery_thresholds) == 3
        assert POSTGRESQL_WEIGHTS.subquery_thresholds[0] == (0, 0.0)
        assert POSTGRESQL_WEIGHTS.subquery_thresholds[1] == (1, 0.5)
        assert POSTGRESQL_WEIGHTS.subquery_thresholds[2] == (2, 1.0)
        
        # CTE 설정 검증 (Requirements 1.3)
        assert POSTGRESQL_WEIGHTS.cte_coefficient == 0.5
        assert POSTGRESQL_WEIGHTS.cte_max == 1.0
        
        # 집합 연산자 설정 검증 (Requirements 1.4)
        assert POSTGRESQL_WEIGHTS.set_operator_coefficient == 0.5
        assert POSTGRESQL_WEIGHTS.set_operator_max == 1.5
        
        # 풀스캔 페널티 검증 (PostgreSQL은 페널티 없음)
        assert POSTGRESQL_WEIGHTS.fullscan_penalty == 0.0
        
        # 데이터 볼륨 점수 검증 (Requirements 5.1-5.4)
        assert POSTGRESQL_WEIGHTS.data_volume_scores['small'] == 0.5
        assert POSTGRESQL_WEIGHTS.data_volume_scores['medium'] == 1.0
        assert POSTGRESQL_WEIGHTS.data_volume_scores['large'] == 1.5
        assert POSTGRESQL_WEIGHTS.data_volume_scores['xlarge'] == 2.0
        
        # 실행 복잡성 점수 검증 (Requirements 6.1, 6.3-6.5)
        assert POSTGRESQL_WEIGHTS.execution_scores['order_by'] == 0.2
        assert POSTGRESQL_WEIGHTS.execution_scores['group_by'] == 0.2
        assert POSTGRESQL_WEIGHTS.execution_scores['having'] == 0.2
        assert POSTGRESQL_WEIGHTS.execution_scores['join_depth'] == 0.5
        
        # 최대 점수 검증
        assert POSTGRESQL_WEIGHTS.max_total_score == 13.5
        
    def test_mysql_weights_configuration(self):
        """MySQL 가중치 설정이 올바르게 정의되었는지 테스트"""
        # Requirements 1.1-1.5, 3.2, 5.1-5.4, 6.1-6.7 검증
        
        # 구조적 복잡성 최대 점수
        assert MYSQL_WEIGHTS.max_structural == 4.5
        
        # JOIN 임계값 검증 (Requirements 1.1)
        assert len(MYSQL_WEIGHTS.join_thresholds) == 5
        assert MYSQL_WEIGHTS.join_thresholds[0] == (0, 0.0)
        assert MYSQL_WEIGHTS.join_thresholds[1] == (2, 1.0)
        assert MYSQL_WEIGHTS.join_thresholds[2] == (4, 2.0)
        assert MYSQL_WEIGHTS.join_thresholds[3] == (6, 3.0)
        assert MYSQL_WEIGHTS.join_thresholds[4] == (float('inf'), 4.0)
        
        # 서브쿼리 임계값 검증 (Requirements 1.2)
        assert len(MYSQL_WEIGHTS.subquery_thresholds) == 3
        assert MYSQL_WEIGHTS.subquery_thresholds[0] == (0, 0.0)
        assert MYSQL_WEIGHTS.subquery_thresholds[1] == (1, 1.5)
        assert MYSQL_WEIGHTS.subquery_thresholds[2] == (2, 3.0)
        
        # CTE 설정 검증 (Requirements 1.3)
        assert MYSQL_WEIGHTS.cte_coefficient == 0.8
        assert MYSQL_WEIGHTS.cte_max == 2.0
        
        # 집합 연산자 설정 검증 (Requirements 1.4)
        assert MYSQL_WEIGHTS.set_operator_coefficient == 0.8
        assert MYSQL_WEIGHTS.set_operator_max == 2.0
        
        # 풀스캔 페널티 검증 (Requirements 1.5)
        assert MYSQL_WEIGHTS.fullscan_penalty == 1.0
        
        # 데이터 볼륨 점수 검증 (Requirements 5.1-5.4)
        assert MYSQL_WEIGHTS.data_volume_scores['small'] == 0.5
        assert MYSQL_WEIGHTS.data_volume_scores['medium'] == 1.2
        assert MYSQL_WEIGHTS.data_volume_scores['large'] == 2.0
        assert MYSQL_WEIGHTS.data_volume_scores['xlarge'] == 2.5
        
        # 실행 복잡성 점수 검증 (Requirements 6.1-6.7)
        assert MYSQL_WEIGHTS.execution_scores['order_by'] == 0.5
        assert MYSQL_WEIGHTS.execution_scores['group_by'] == 0.5
        assert MYSQL_WEIGHTS.execution_scores['having'] == 0.5
        assert MYSQL_WEIGHTS.execution_scores['join_depth'] == 1.5
        assert MYSQL_WEIGHTS.execution_scores['derived_table'] == 0.5
        assert MYSQL_WEIGHTS.execution_scores['distinct'] == 0.3
        assert MYSQL_WEIGHTS.execution_scores['or_conditions'] == 0.3
        assert MYSQL_WEIGHTS.execution_scores['like_pattern'] == 0.3
        assert MYSQL_WEIGHTS.execution_scores['function_in_where'] == 0.5
        assert MYSQL_WEIGHTS.execution_scores['count_no_where'] == 0.5
        
        # 최대 점수 검증
        assert MYSQL_WEIGHTS.max_total_score == 18.0
        
    def test_postgresql_vs_mysql_weights_differences(self):
        """PostgreSQL과 MySQL 가중치 설정의 차이점 검증"""
        # MySQL이 PostgreSQL보다 더 엄격한 가중치를 가져야 함
        
        # 구조적 복잡성 최대 점수
        assert MYSQL_WEIGHTS.max_structural > POSTGRESQL_WEIGHTS.max_structural
        
        # CTE 계수
        assert MYSQL_WEIGHTS.cte_coefficient > POSTGRESQL_WEIGHTS.cte_coefficient
        
        # 집합 연산자 계수
        assert MYSQL_WEIGHTS.set_operator_coefficient > POSTGRESQL_WEIGHTS.set_operator_coefficient
        
        # 풀스캔 페널티 (MySQL만 있음)
        assert MYSQL_WEIGHTS.fullscan_penalty > POSTGRESQL_WEIGHTS.fullscan_penalty
        
        # 데이터 볼륨 점수 (MySQL이 더 높음)
        assert MYSQL_WEIGHTS.data_volume_scores['medium'] > POSTGRESQL_WEIGHTS.data_volume_scores['medium']
        assert MYSQL_WEIGHTS.data_volume_scores['large'] > POSTGRESQL_WEIGHTS.data_volume_scores['large']
        assert MYSQL_WEIGHTS.data_volume_scores['xlarge'] > POSTGRESQL_WEIGHTS.data_volume_scores['xlarge']
        
        # 실행 복잡성 점수 (MySQL이 더 높음)
        assert MYSQL_WEIGHTS.execution_scores['order_by'] > POSTGRESQL_WEIGHTS.execution_scores['order_by']
        assert MYSQL_WEIGHTS.execution_scores['group_by'] > POSTGRESQL_WEIGHTS.execution_scores['group_by']
        assert MYSQL_WEIGHTS.execution_scores['having'] > POSTGRESQL_WEIGHTS.execution_scores['having']
        assert MYSQL_WEIGHTS.execution_scores['join_depth'] > POSTGRESQL_WEIGHTS.execution_scores['join_depth']
        
        # MySQL 전용 실행 복잡성 점수 존재 확인
        assert 'derived_table' in MYSQL_WEIGHTS.execution_scores
        assert 'distinct' in MYSQL_WEIGHTS.execution_scores
        assert 'or_conditions' in MYSQL_WEIGHTS.execution_scores
        assert 'like_pattern' in MYSQL_WEIGHTS.execution_scores
        assert 'function_in_where' in MYSQL_WEIGHTS.execution_scores
        assert 'count_no_where' in MYSQL_WEIGHTS.execution_scores
        
        # PostgreSQL에는 MySQL 전용 점수가 없어야 함
        assert 'derived_table' not in POSTGRESQL_WEIGHTS.execution_scores
        
        # 최대 점수 (MySQL이 더 높음)
        assert MYSQL_WEIGHTS.max_total_score > POSTGRESQL_WEIGHTS.max_total_score
        
    def test_weight_config_with_custom_values(self):
        """커스텀 값으로 WeightConfig 생성 테스트"""
        custom_config = WeightConfig(
            max_structural=3.0,
            join_thresholds=[(0, 0.0), (2, 0.8), (4, 1.5)],
            subquery_thresholds=[(0, 0.0), (1, 0.7)],
            cte_coefficient=0.6,
            cte_max=1.2,
            set_operator_coefficient=0.7,
            set_operator_max=1.8,
            fullscan_penalty=0.5,
            data_volume_scores={'small': 0.3, 'large': 1.8},
            execution_scores={'order_by': 0.3, 'custom_penalty': 0.8},
            max_total_score=15.0,
        )
        
        assert custom_config.max_structural == 3.0
        assert custom_config.fullscan_penalty == 0.5
        assert custom_config.data_volume_scores['small'] == 0.3
        assert custom_config.execution_scores['custom_penalty'] == 0.8
        assert custom_config.max_total_score == 15.0



class TestOracleConstants:
    """Oracle 특화 기능/함수/힌트 상수 테스트"""
    
    def test_oracle_specific_syntax_constants(self):
        """Oracle 특화 문법 상수가 올바르게 정의되었는지 테스트 (Requirements 2.1-2.5)"""
        from src.oracle_complexity_analyzer import ORACLE_SPECIFIC_SYNTAX
        
        # 필수 Oracle 특화 문법 검증
        assert 'CONNECT BY' in ORACLE_SPECIFIC_SYNTAX
        assert 'START WITH' in ORACLE_SPECIFIC_SYNTAX
        assert 'PRIOR' in ORACLE_SPECIFIC_SYNTAX
        assert 'MODEL' in ORACLE_SPECIFIC_SYNTAX
        assert 'PIVOT' in ORACLE_SPECIFIC_SYNTAX
        assert 'UNPIVOT' in ORACLE_SPECIFIC_SYNTAX
        assert 'ROWNUM' in ORACLE_SPECIFIC_SYNTAX
        assert 'ROWID' in ORACLE_SPECIFIC_SYNTAX
        assert 'LEVEL' in ORACLE_SPECIFIC_SYNTAX
        assert 'MERGE' in ORACLE_SPECIFIC_SYNTAX
        assert 'DUAL' in ORACLE_SPECIFIC_SYNTAX
        
        # 점수 검증
        assert ORACLE_SPECIFIC_SYNTAX['CONNECT BY'] == 1.0
        assert ORACLE_SPECIFIC_SYNTAX['MERGE'] == 1.5
        assert ORACLE_SPECIFIC_SYNTAX['DUAL'] == 0.3
        assert ORACLE_SPECIFIC_SYNTAX['NEXTVAL'] == 0.8
        assert ORACLE_SPECIFIC_SYNTAX['CURRVAL'] == 0.8
        
    def test_oracle_specific_functions_constants(self):
        """Oracle 특화 함수 상수가 올바르게 정의되었는지 테스트 (Requirements 3.1, 3.2)"""
        from src.oracle_complexity_analyzer import ORACLE_SPECIFIC_FUNCTIONS
        
        # 조건/변환 함수
        assert 'DECODE' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'NVL' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'NVL2' in ORACLE_SPECIFIC_FUNCTIONS
        
        # 집계 함수
        assert 'LISTAGG' in ORACLE_SPECIFIC_FUNCTIONS
        
        # 정규식 함수
        assert 'REGEXP_LIKE' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'REGEXP_SUBSTR' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'REGEXP_REPLACE' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'REGEXP_INSTR' in ORACLE_SPECIFIC_FUNCTIONS
        
        # 시스템 함수
        assert 'SYS_CONTEXT' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'EXTRACT' in ORACLE_SPECIFIC_FUNCTIONS
        
        # 변환 함수
        assert 'TO_CHAR' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'TO_DATE' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'TO_NUMBER' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'TRUNC' in ORACLE_SPECIFIC_FUNCTIONS
        
        # 날짜 함수
        assert 'ADD_MONTHS' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'MONTHS_BETWEEN' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'SYSDATE' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'SYSTIMESTAMP' in ORACLE_SPECIFIC_FUNCTIONS
        
        # 문자열 함수
        assert 'SUBSTR' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'INSTR' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'CHR' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'TRANSLATE' in ORACLE_SPECIFIC_FUNCTIONS
        
        # 모든 함수가 0.5점인지 검증
        for func, score in ORACLE_SPECIFIC_FUNCTIONS.items():
            assert score == 0.5, f"{func} 함수의 점수가 0.5가 아닙니다: {score}"
            
    def test_analytic_functions_constants(self):
        """분석 함수 상수가 올바르게 정의되었는지 테스트 (Requirements 2.2)"""
        from src.oracle_complexity_analyzer import ANALYTIC_FUNCTIONS
        
        # 필수 분석 함수 검증
        assert 'ROW_NUMBER' in ANALYTIC_FUNCTIONS
        assert 'RANK' in ANALYTIC_FUNCTIONS
        assert 'DENSE_RANK' in ANALYTIC_FUNCTIONS
        assert 'LAG' in ANALYTIC_FUNCTIONS
        assert 'LEAD' in ANALYTIC_FUNCTIONS
        assert 'FIRST_VALUE' in ANALYTIC_FUNCTIONS
        assert 'LAST_VALUE' in ANALYTIC_FUNCTIONS
        assert 'NTILE' in ANALYTIC_FUNCTIONS
        assert 'CUME_DIST' in ANALYTIC_FUNCTIONS
        assert 'PERCENT_RANK' in ANALYTIC_FUNCTIONS
        assert 'RATIO_TO_REPORT' in ANALYTIC_FUNCTIONS
        
        # 총 11개의 분석 함수가 정의되어 있는지 검증
        assert len(ANALYTIC_FUNCTIONS) == 11
        
    def test_aggregate_functions_constants(self):
        """집계 함수 상수가 올바르게 정의되었는지 테스트 (Requirements 4.1)"""
        from src.oracle_complexity_analyzer import AGGREGATE_FUNCTIONS
        
        # 필수 집계 함수 검증
        assert 'COUNT' in AGGREGATE_FUNCTIONS
        assert 'SUM' in AGGREGATE_FUNCTIONS
        assert 'AVG' in AGGREGATE_FUNCTIONS
        assert 'MAX' in AGGREGATE_FUNCTIONS
        assert 'MIN' in AGGREGATE_FUNCTIONS
        assert 'LISTAGG' in AGGREGATE_FUNCTIONS
        assert 'XMLAGG' in AGGREGATE_FUNCTIONS
        assert 'MEDIAN' in AGGREGATE_FUNCTIONS
        assert 'PERCENTILE_CONT' in AGGREGATE_FUNCTIONS
        assert 'PERCENTILE_DISC' in AGGREGATE_FUNCTIONS
        
        # 총 10개의 집계 함수가 정의되어 있는지 검증
        assert len(AGGREGATE_FUNCTIONS) == 10
        
    def test_oracle_hints_constants(self):
        """Oracle 힌트 상수가 올바르게 정의되었는지 테스트 (Requirements 7.1-7.5)"""
        from src.oracle_complexity_analyzer import ORACLE_HINTS
        
        # 필수 힌트 검증
        assert 'INDEX' in ORACLE_HINTS
        assert 'FULL' in ORACLE_HINTS
        assert 'PARALLEL' in ORACLE_HINTS
        assert 'USE_HASH' in ORACLE_HINTS
        assert 'USE_NL' in ORACLE_HINTS
        assert 'APPEND' in ORACLE_HINTS
        assert 'NO_MERGE' in ORACLE_HINTS
        assert 'LEADING' in ORACLE_HINTS
        assert 'ORDERED' in ORACLE_HINTS
        assert 'FIRST_ROWS' in ORACLE_HINTS
        assert 'ALL_ROWS' in ORACLE_HINTS
        assert 'RULE' in ORACLE_HINTS
        assert 'CHOOSE' in ORACLE_HINTS
        assert 'DRIVING_SITE' in ORACLE_HINTS
        
        # 총 14개의 힌트가 정의되어 있는지 검증
        assert len(ORACLE_HINTS) == 14
        
    def test_plsql_advanced_features_constants(self):
        """PL/SQL 고급 기능 상수가 올바르게 정의되었는지 테스트 (Requirements 9.5)"""
        from src.oracle_complexity_analyzer import PLSQL_ADVANCED_FEATURES
        
        # 필수 고급 기능 검증
        assert 'PIPELINED' in PLSQL_ADVANCED_FEATURES
        assert 'REF CURSOR' in PLSQL_ADVANCED_FEATURES
        assert 'AUTONOMOUS_TRANSACTION' in PLSQL_ADVANCED_FEATURES
        assert 'PRAGMA' in PLSQL_ADVANCED_FEATURES
        assert 'OBJECT TYPE' in PLSQL_ADVANCED_FEATURES
        assert 'VARRAY' in PLSQL_ADVANCED_FEATURES
        assert 'NESTED TABLE' in PLSQL_ADVANCED_FEATURES
        
        # 총 7개의 고급 기능이 정의되어 있는지 검증
        assert len(PLSQL_ADVANCED_FEATURES) == 7
        
    def test_external_dependencies_constants(self):
        """외부 의존성 상수가 올바르게 정의되었는지 테스트 (Requirements 10.6)"""
        from src.oracle_complexity_analyzer import EXTERNAL_DEPENDENCIES
        
        # 필수 외부 의존성 검증
        assert 'UTL_FILE' in EXTERNAL_DEPENDENCIES
        assert 'UTL_HTTP' in EXTERNAL_DEPENDENCIES
        assert 'UTL_MAIL' in EXTERNAL_DEPENDENCIES
        assert 'UTL_SMTP' in EXTERNAL_DEPENDENCIES
        assert 'DBMS_SCHEDULER' in EXTERNAL_DEPENDENCIES
        assert 'DBMS_JOB' in EXTERNAL_DEPENDENCIES
        assert 'DBMS_LOB' in EXTERNAL_DEPENDENCIES
        assert 'DBMS_OUTPUT' in EXTERNAL_DEPENDENCIES
        assert 'DBMS_CRYPTO' in EXTERNAL_DEPENDENCIES
        assert 'DBMS_SQL' in EXTERNAL_DEPENDENCIES
        
        # 총 10개의 외부 의존성이 정의되어 있는지 검증
        assert len(EXTERNAL_DEPENDENCIES) == 10
        
    def test_plsql_base_scores_constants(self):
        """PL/SQL 오브젝트 기본 점수 상수가 올바르게 정의되었는지 테스트 (Requirements 8.1)"""
        from src.oracle_complexity_analyzer import PLSQL_BASE_SCORES
        
        # PostgreSQL 기본 점수 검증
        pg_scores = PLSQL_BASE_SCORES[TargetDatabase.POSTGRESQL]
        assert pg_scores[PLSQLObjectType.PACKAGE] == 7.0
        assert pg_scores[PLSQLObjectType.PROCEDURE] == 5.0
        assert pg_scores[PLSQLObjectType.FUNCTION] == 4.0
        assert pg_scores[PLSQLObjectType.TRIGGER] == 6.0
        assert pg_scores[PLSQLObjectType.VIEW] == 2.0
        assert pg_scores[PLSQLObjectType.MATERIALIZED_VIEW] == 4.0
        
        # MySQL 기본 점수 검증
        mysql_scores = PLSQL_BASE_SCORES[TargetDatabase.MYSQL]
        assert mysql_scores[PLSQLObjectType.PACKAGE] == 8.0
        assert mysql_scores[PLSQLObjectType.PROCEDURE] == 6.0
        assert mysql_scores[PLSQLObjectType.FUNCTION] == 5.0
        assert mysql_scores[PLSQLObjectType.TRIGGER] == 7.0
        assert mysql_scores[PLSQLObjectType.VIEW] == 2.0
        assert mysql_scores[PLSQLObjectType.MATERIALIZED_VIEW] == 5.0
        
        # MySQL이 PostgreSQL보다 높은 점수를 가져야 함
        for obj_type in PLSQLObjectType:
            assert mysql_scores[obj_type] >= pg_scores[obj_type], \
                f"{obj_type.value}의 MySQL 점수가 PostgreSQL 점수보다 낮습니다"
                
    def test_mysql_app_migration_penalty_constants(self):
        """MySQL 애플리케이션 이관 페널티 상수가 올바르게 정의되었는지 테스트 (Requirements 11.4, 11.5)"""
        from src.oracle_complexity_analyzer import MYSQL_APP_MIGRATION_PENALTY
        
        # 페널티 검증
        assert MYSQL_APP_MIGRATION_PENALTY[PLSQLObjectType.PACKAGE] == 2.0
        assert MYSQL_APP_MIGRATION_PENALTY[PLSQLObjectType.PROCEDURE] == 2.0
        assert MYSQL_APP_MIGRATION_PENALTY[PLSQLObjectType.FUNCTION] == 2.0
        assert MYSQL_APP_MIGRATION_PENALTY[PLSQLObjectType.TRIGGER] == 1.5
        assert MYSQL_APP_MIGRATION_PENALTY[PLSQLObjectType.VIEW] == 0.0
        assert MYSQL_APP_MIGRATION_PENALTY[PLSQLObjectType.MATERIALIZED_VIEW] == 0.0
        
        # Package, Procedure, Function이 가장 높은 페널티를 가져야 함
        assert MYSQL_APP_MIGRATION_PENALTY[PLSQLObjectType.PACKAGE] == 2.0
        assert MYSQL_APP_MIGRATION_PENALTY[PLSQLObjectType.PROCEDURE] == 2.0
        assert MYSQL_APP_MIGRATION_PENALTY[PLSQLObjectType.FUNCTION] == 2.0
        
        # View와 Materialized View는 페널티가 없어야 함
        assert MYSQL_APP_MIGRATION_PENALTY[PLSQLObjectType.VIEW] == 0.0
        assert MYSQL_APP_MIGRATION_PENALTY[PLSQLObjectType.MATERIALIZED_VIEW] == 0.0
        
    def test_constants_consistency(self):
        """상수들 간의 일관성 검증"""
        from src.oracle_complexity_analyzer import (
            ORACLE_SPECIFIC_SYNTAX,
            ORACLE_SPECIFIC_FUNCTIONS,
            ANALYTIC_FUNCTIONS,
            AGGREGATE_FUNCTIONS,
            ORACLE_HINTS,
            PLSQL_ADVANCED_FEATURES,
            EXTERNAL_DEPENDENCIES,
        )
        
        # 모든 상수가 비어있지 않은지 검증
        assert len(ORACLE_SPECIFIC_SYNTAX) > 0
        assert len(ORACLE_SPECIFIC_FUNCTIONS) > 0
        assert len(ANALYTIC_FUNCTIONS) > 0
        assert len(AGGREGATE_FUNCTIONS) > 0
        assert len(ORACLE_HINTS) > 0
        assert len(PLSQL_ADVANCED_FEATURES) > 0
        assert len(EXTERNAL_DEPENDENCIES) > 0
        
        # LISTAGG가 ORACLE_SPECIFIC_FUNCTIONS와 AGGREGATE_FUNCTIONS 모두에 있는지 검증
        assert 'LISTAGG' in ORACLE_SPECIFIC_FUNCTIONS
        assert 'LISTAGG' in AGGREGATE_FUNCTIONS
