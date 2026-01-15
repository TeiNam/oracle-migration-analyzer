"""
ResultFormatter 테스트

Requirements 14.1, 14.2, 14.3, 14.4, 14.5를 검증합니다.
"""

import json
import pytest

from src.oracle_complexity_analyzer import (
    SQLAnalysisResult,
    PLSQLAnalysisResult,
    TargetDatabase,
    ComplexityLevel,
    PLSQLObjectType
)
from src.formatters.result_formatter import ResultFormatter


class TestResultFormatterSQL:
    """SQL 분석 결과 포맷터 테스트"""
    
    def test_sql_to_json(self):
        """SQL 분석 결과를 JSON으로 변환 (Requirements 14.1)"""
        result = SQLAnalysisResult(
            query="SELECT * FROM users WHERE id = 1",
            target_database=TargetDatabase.POSTGRESQL,
            total_score=5.5,
            normalized_score=4.1,
            complexity_level=ComplexityLevel.MODERATE,
            recommendation="부분 재작성",
            structural_complexity=1.5,
            oracle_specific_features=1.0,
            functions_expressions=0.5,
            data_volume=0.5,
            execution_complexity=1.0,
            conversion_difficulty=1.0,
            detected_oracle_features=["ROWNUM", "DECODE"],
            detected_oracle_functions=["NVL", "TO_CHAR"],
            detected_hints=["INDEX"],
            join_count=2,
            subquery_depth=1,
            cte_count=0,
            set_operators_count=0,
            conversion_guides={"ROWNUM": "LIMIT/OFFSET", "DECODE": "CASE"}
        )
        
        json_str = ResultFormatter.to_json(result)
        
        # JSON 파싱 가능 확인
        data = json.loads(json_str)
        
        # 주요 필드 확인
        assert data['query'] == "SELECT * FROM users WHERE id = 1"
        assert data['target_database'] == "postgresql"
        assert data['total_score'] == 5.5
        assert data['normalized_score'] == 4.1
        assert data['complexity_level'] == "중간"
        assert data['recommendation'] == "부분 재작성"
        assert data['structural_complexity'] == 1.5
        assert data['oracle_specific_features'] == 1.0
        assert data['detected_oracle_features'] == ["ROWNUM", "DECODE"]
        assert data['detected_oracle_functions'] == ["NVL", "TO_CHAR"]
        assert data['result_type'] == 'sql'
    
    def test_sql_from_json(self):
        """JSON을 SQL 분석 결과로 변환 (Requirements 14.3)"""
        json_str = '''
        {
            "query": "SELECT * FROM users",
            "target_database": "postgresql",
            "total_score": 3.0,
            "normalized_score": 2.2,
            "complexity_level": "간단",
            "recommendation": "함수 대체",
            "structural_complexity": 1.0,
            "oracle_specific_features": 0.5,
            "functions_expressions": 0.5,
            "data_volume": 0.5,
            "execution_complexity": 0.5,
            "conversion_difficulty": 0.0,
            "detected_oracle_features": ["ROWNUM"],
            "detected_oracle_functions": [],
            "detected_hints": [],
            "join_count": 0,
            "subquery_depth": 0,
            "cte_count": 0,
            "set_operators_count": 0,
            "conversion_guides": {},
            "result_type": "sql"
        }
        '''
        
        result = ResultFormatter.from_json(json_str, 'sql')
        
        assert isinstance(result, SQLAnalysisResult)
        assert result.query == "SELECT * FROM users"
        assert result.target_database == TargetDatabase.POSTGRESQL
        assert result.total_score == 3.0
        assert result.normalized_score == 2.2
        assert result.complexity_level == ComplexityLevel.SIMPLE
        assert result.recommendation == "함수 대체"
        assert result.detected_oracle_features == ["ROWNUM"]
    
    def test_sql_json_round_trip(self):
        """SQL 분석 결과 JSON Round-Trip (Requirements 14.4)"""
        original = SQLAnalysisResult(
            query="SELECT * FROM orders",
            target_database=TargetDatabase.MYSQL,
            total_score=7.5,
            normalized_score=6.2,
            complexity_level=ComplexityLevel.COMPLEX,
            recommendation="상당한 재작성",
            structural_complexity=2.0,
            oracle_specific_features=2.0,
            functions_expressions=1.5,
            data_volume=1.0,
            execution_complexity=1.0,
            conversion_difficulty=0.0,
            detected_oracle_features=["CONNECT BY", "PIVOT"],
            detected_oracle_functions=["LISTAGG"],
            detected_hints=[],
            join_count=5,
            subquery_depth=2,
            cte_count=1,
            set_operators_count=0,
            conversion_guides={"CONNECT BY": "WITH RECURSIVE"}
        )
        
        # JSON으로 변환 후 다시 객체로 변환
        json_str = ResultFormatter.to_json(original)
        restored = ResultFormatter.from_json(json_str, 'sql')
        
        # 주요 필드 비교
        assert restored.query == original.query
        assert restored.target_database == original.target_database
        assert restored.total_score == original.total_score
        assert restored.normalized_score == original.normalized_score
        assert restored.complexity_level == original.complexity_level
        assert restored.recommendation == original.recommendation
        assert restored.structural_complexity == original.structural_complexity
        assert restored.detected_oracle_features == original.detected_oracle_features
        assert restored.detected_oracle_functions == original.detected_oracle_functions
        assert restored.join_count == original.join_count
        assert restored.conversion_guides == original.conversion_guides
    
    def test_sql_to_markdown(self):
        """SQL 분석 결과를 Markdown으로 변환 (Requirements 14.2, 14.5)"""
        result = SQLAnalysisResult(
            query="SELECT * FROM users WHERE id = 1",
            target_database=TargetDatabase.POSTGRESQL,
            total_score=5.5,
            normalized_score=4.1,
            complexity_level=ComplexityLevel.MODERATE,
            recommendation="부분 재작성",
            structural_complexity=1.5,
            oracle_specific_features=1.0,
            functions_expressions=0.5,
            data_volume=0.5,
            execution_complexity=1.0,
            conversion_difficulty=1.0,
            detected_oracle_features=["ROWNUM", "DECODE"],
            detected_oracle_functions=["NVL", "TO_CHAR"],
            detected_hints=["INDEX"],
            join_count=2,
            subquery_depth=1,
            cte_count=0,
            set_operators_count=0,
            conversion_guides={"ROWNUM": "LIMIT/OFFSET", "DECODE": "CASE"}
        )
        
        markdown = ResultFormatter.to_markdown(result)
        
        # 필수 섹션 확인 (Requirements 14.5)
        assert "# Oracle SQL 복잡도 분석 결과" in markdown
        assert "## 복잡도 점수 요약" in markdown
        assert "## 세부 점수" in markdown
        assert "## 분석 메타데이터" in markdown
        assert "## 감지된 Oracle 특화 기능" in markdown
        assert "## 감지된 Oracle 특화 함수" in markdown
        assert "## 감지된 힌트" in markdown
        assert "## 변환 가이드" in markdown
        assert "## 원본 쿼리" in markdown
        
        # 주요 내용 확인
        assert "postgresql".upper() in markdown
        assert "4.1" in markdown
        assert "중간" in markdown
        assert "부분 재작성" in markdown
        assert "ROWNUM" in markdown
        assert "NVL" in markdown
        assert "INDEX" in markdown
        assert "LIMIT/OFFSET" in markdown
        assert "SELECT * FROM users WHERE id = 1" in markdown


class TestResultFormatterPLSQL:
    """PL/SQL 분석 결과 포맷터 테스트"""
    
    def test_plsql_to_json(self):
        """PL/SQL 분석 결과를 JSON으로 변환 (Requirements 14.1)"""
        result = PLSQLAnalysisResult(
            code="CREATE OR REPLACE PROCEDURE test_proc IS BEGIN NULL; END;",
            object_type=PLSQLObjectType.PROCEDURE,
            target_database=TargetDatabase.POSTGRESQL,
            total_score=8.5,
            normalized_score=6.5,
            complexity_level=ComplexityLevel.COMPLEX,
            recommendation="상당한 재작성",
            base_score=5.0,
            code_complexity=1.5,
            oracle_features=1.0,
            business_logic=0.5,
            conversion_difficulty=0.5,
            mysql_constraints=0.0,
            app_migration_penalty=0.0,
            detected_oracle_features=["BULK COLLECT", "FORALL"],
            detected_external_dependencies=["UTL_FILE"],
            line_count=50,
            cursor_count=2,
            exception_blocks=1,
            nesting_depth=3,
            bulk_operations_count=2,
            dynamic_sql_count=1,
            conversion_guides={"BULK COLLECT": "순수 SQL/Chunked Batch"}
        )
        
        json_str = ResultFormatter.to_json(result)
        
        # JSON 파싱 가능 확인
        data = json.loads(json_str)
        
        # 주요 필드 확인
        assert data['object_type'] == "procedure"
        assert data['target_database'] == "postgresql"
        assert data['total_score'] == 8.5
        assert data['normalized_score'] == 6.5
        assert data['complexity_level'] == "복잡"
        assert data['base_score'] == 5.0
        assert data['code_complexity'] == 1.5
        assert data['detected_oracle_features'] == ["BULK COLLECT", "FORALL"]
        assert data['detected_external_dependencies'] == ["UTL_FILE"]
        assert data['result_type'] == 'plsql'
    
    def test_plsql_from_json(self):
        """JSON을 PL/SQL 분석 결과로 변환 (Requirements 14.3)"""
        json_str = '''
        {
            "code": "CREATE FUNCTION test_func RETURN NUMBER IS BEGIN RETURN 1; END;",
            "object_type": "function",
            "target_database": "mysql",
            "total_score": 10.0,
            "normalized_score": 7.5,
            "complexity_level": "매우 복잡",
            "recommendation": "대부분 재작성",
            "base_score": 5.0,
            "code_complexity": 2.0,
            "oracle_features": 1.5,
            "business_logic": 0.5,
            "conversion_difficulty": 0.5,
            "mysql_constraints": 0.5,
            "app_migration_penalty": 2.0,
            "detected_oracle_features": ["PIPELINED"],
            "detected_external_dependencies": [],
            "line_count": 100,
            "cursor_count": 3,
            "exception_blocks": 2,
            "nesting_depth": 4,
            "bulk_operations_count": 0,
            "dynamic_sql_count": 0,
            "conversion_guides": {},
            "result_type": "plsql"
        }
        '''
        
        result = ResultFormatter.from_json(json_str, 'plsql')
        
        assert isinstance(result, PLSQLAnalysisResult)
        assert result.object_type == PLSQLObjectType.FUNCTION
        assert result.target_database == TargetDatabase.MYSQL
        assert result.total_score == 10.0
        assert result.normalized_score == 7.5
        assert result.complexity_level == ComplexityLevel.VERY_COMPLEX
        assert result.base_score == 5.0
        assert result.mysql_constraints == 0.5
        assert result.app_migration_penalty == 2.0
    
    def test_plsql_json_round_trip(self):
        """PL/SQL 분석 결과 JSON Round-Trip (Requirements 14.4)"""
        original = PLSQLAnalysisResult(
            code="CREATE PACKAGE test_pkg IS END;",
            object_type=PLSQLObjectType.PACKAGE,
            target_database=TargetDatabase.MYSQL,
            total_score=12.0,
            normalized_score=8.5,
            complexity_level=ComplexityLevel.VERY_COMPLEX,
            recommendation="대부분 재작성",
            base_score=8.0,
            code_complexity=2.0,
            oracle_features=1.5,
            business_logic=0.5,
            conversion_difficulty=0.5,
            mysql_constraints=1.0,
            app_migration_penalty=2.0,
            detected_oracle_features=["AUTONOMOUS_TRANSACTION"],
            detected_external_dependencies=["DBMS_SCHEDULER"],
            line_count=200,
            cursor_count=5,
            exception_blocks=3,
            nesting_depth=5,
            bulk_operations_count=3,
            dynamic_sql_count=2,
            conversion_guides={"AUTONOMOUS_TRANSACTION": "별도 트랜잭션 처리"}
        )
        
        # JSON으로 변환 후 다시 객체로 변환
        json_str = ResultFormatter.to_json(original)
        restored = ResultFormatter.from_json(json_str, 'plsql')
        
        # 주요 필드 비교
        assert restored.code == original.code
        assert restored.object_type == original.object_type
        assert restored.target_database == original.target_database
        assert restored.total_score == original.total_score
        assert restored.normalized_score == original.normalized_score
        assert restored.complexity_level == original.complexity_level
        assert restored.base_score == original.base_score
        assert restored.mysql_constraints == original.mysql_constraints
        assert restored.app_migration_penalty == original.app_migration_penalty
        assert restored.detected_oracle_features == original.detected_oracle_features
        assert restored.line_count == original.line_count
    
    def test_plsql_to_markdown(self):
        """PL/SQL 분석 결과를 Markdown으로 변환 (Requirements 14.2, 14.5)"""
        result = PLSQLAnalysisResult(
            code="CREATE OR REPLACE PROCEDURE test_proc IS BEGIN NULL; END;",
            object_type=PLSQLObjectType.PROCEDURE,
            target_database=TargetDatabase.MYSQL,
            total_score=10.0,
            normalized_score=7.5,
            complexity_level=ComplexityLevel.VERY_COMPLEX,
            recommendation="대부분 재작성",
            base_score=6.0,
            code_complexity=2.0,
            oracle_features=1.5,
            business_logic=0.5,
            conversion_difficulty=0.5,
            mysql_constraints=1.0,
            app_migration_penalty=2.0,
            detected_oracle_features=["BULK COLLECT", "REF CURSOR"],
            detected_external_dependencies=["UTL_FILE", "DBMS_SCHEDULER"],
            line_count=150,
            cursor_count=4,
            exception_blocks=2,
            nesting_depth=4,
            bulk_operations_count=3,
            dynamic_sql_count=1,
            conversion_guides={"BULK COLLECT": "루프 처리 (미지원)"}
        )
        
        markdown = ResultFormatter.to_markdown(result)
        
        # 필수 섹션 확인 (Requirements 14.5)
        assert "# Oracle PL/SQL 복잡도 분석 결과" in markdown
        assert "## 복잡도 점수 요약" in markdown
        assert "## 세부 점수" in markdown
        assert "## 분석 메타데이터" in markdown
        assert "## 감지된 Oracle 특화 기능" in markdown
        assert "## 감지된 외부 의존성" in markdown
        assert "## 변환 가이드" in markdown
        assert "## 원본 코드" in markdown
        
        # MySQL 타겟 특화 필드 확인
        assert "MySQL 제약" in markdown
        assert "애플리케이션 이관 페널티" in markdown
        
        # 주요 내용 확인
        assert "PROCEDURE" in markdown
        assert "mysql".upper() in markdown
        assert "7.5" in markdown
        assert "매우 복잡" in markdown
        assert "대부분 재작성" in markdown
        assert "BULK COLLECT" in markdown
        assert "UTL_FILE" in markdown
        assert "루프 처리 (미지원)" in markdown
        assert "CREATE OR REPLACE PROCEDURE test_proc IS BEGIN NULL; END;" in markdown


class TestResultFormatterEdgeCases:
    """ResultFormatter 엣지 케이스 테스트"""
    
    def test_empty_lists(self):
        """빈 리스트 처리"""
        result = SQLAnalysisResult(
            query="SELECT 1 FROM DUAL",
            target_database=TargetDatabase.POSTGRESQL,
            total_score=0.5,
            normalized_score=0.4,
            complexity_level=ComplexityLevel.VERY_SIMPLE,
            recommendation="자동 변환",
            structural_complexity=0.0,
            oracle_specific_features=0.3,
            functions_expressions=0.0,
            data_volume=0.2,
            execution_complexity=0.0,
            conversion_difficulty=0.0,
            detected_oracle_features=[],
            detected_oracle_functions=[],
            detected_hints=[],
            join_count=0,
            subquery_depth=0,
            cte_count=0,
            set_operators_count=0,
            conversion_guides={}
        )
        
        # JSON 변환
        json_str = ResultFormatter.to_json(result)
        data = json.loads(json_str)
        assert data['detected_oracle_features'] == []
        assert data['detected_oracle_functions'] == []
        assert data['conversion_guides'] == {}
        
        # Markdown 변환 (빈 섹션은 표시되지 않음)
        markdown = ResultFormatter.to_markdown(result)
        assert "## 감지된 Oracle 특화 기능" not in markdown
        assert "## 감지된 Oracle 특화 함수" not in markdown
        assert "## 변환 가이드" not in markdown
    
    def test_invalid_json(self):
        """잘못된 JSON 처리"""
        with pytest.raises(ValueError, match="JSON 파싱 실패"):
            ResultFormatter.from_json("invalid json", 'sql')
    
    def test_invalid_result_type(self):
        """잘못된 result_type 처리"""
        json_str = '{"result_type": "invalid"}'
        with pytest.raises(ValueError, match="지원하지 않는 result_type"):
            ResultFormatter.from_json(json_str, 'invalid')
    
    def test_korean_characters(self):
        """한글 문자 처리"""
        result = SQLAnalysisResult(
            query="SELECT * FROM 사용자 WHERE 이름 = '홍길동'",
            target_database=TargetDatabase.POSTGRESQL,
            total_score=1.0,
            normalized_score=0.7,
            complexity_level=ComplexityLevel.VERY_SIMPLE,
            recommendation="자동 변환",
            structural_complexity=0.5,
            oracle_specific_features=0.0,
            functions_expressions=0.0,
            data_volume=0.5,
            execution_complexity=0.0,
            conversion_difficulty=0.0,
            detected_oracle_features=[],
            detected_oracle_functions=[],
            detected_hints=[],
            join_count=0,
            subquery_depth=0,
            cte_count=0,
            set_operators_count=0,
            conversion_guides={}
        )
        
        # JSON 변환 (한글이 유니코드 이스케이프되지 않아야 함)
        json_str = ResultFormatter.to_json(result)
        assert "사용자" in json_str
        assert "홍길동" in json_str
        
        # Round-trip 테스트
        restored = ResultFormatter.from_json(json_str, 'sql')
        assert restored.query == result.query
