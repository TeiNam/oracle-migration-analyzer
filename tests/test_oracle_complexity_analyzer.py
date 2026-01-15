"""
OracleComplexityAnalyzer 메인 클래스 테스트

Requirements 전체를 검증합니다.
"""

import pytest
import os
import json
from pathlib import Path
from datetime import datetime

from src.oracle_complexity_analyzer import (
    OracleComplexityAnalyzer,
    TargetDatabase,
    SQLAnalysisResult,
    PLSQLAnalysisResult,
)


class TestOracleComplexityAnalyzer:
    """OracleComplexityAnalyzer 메인 클래스 테스트"""
    
    def test_init_default(self):
        """기본 초기화 테스트"""
        analyzer = OracleComplexityAnalyzer()
        
        assert analyzer.target == TargetDatabase.POSTGRESQL
        assert analyzer.output_dir == Path("reports")
        assert analyzer.calculator is not None
        assert analyzer.guide_provider is not None
    
    def test_init_custom(self):
        """커스텀 초기화 테스트"""
        analyzer = OracleComplexityAnalyzer(
            target_database=TargetDatabase.MYSQL,
            output_dir="custom_reports"
        )
        
        assert analyzer.target == TargetDatabase.MYSQL
        assert analyzer.output_dir == Path("custom_reports")
    
    def test_get_date_folder(self):
        """날짜 폴더 생성 테스트 (Requirements 14.6, 14.7)"""
        analyzer = OracleComplexityAnalyzer(output_dir="test_reports")
        
        # 날짜 폴더 생성
        date_folder = analyzer._get_date_folder()
        
        # 폴더가 생성되었는지 확인
        assert date_folder.exists()
        assert date_folder.is_dir()
        
        # 폴더 이름이 YYYYMMDD 형식인지 확인
        expected_date = datetime.now().strftime("%Y%m%d")
        assert date_folder.name == expected_date
        
        # 정리
        import shutil
        shutil.rmtree("test_reports")
    
    def test_analyze_sql_simple(self):
        """간단한 SQL 쿼리 분석 테스트 (Requirements 1.1-7.5, 12.1, 13.1)"""
        analyzer = OracleComplexityAnalyzer()
        
        query = "SELECT * FROM employees WHERE department_id = 10"
        result = analyzer.analyze_sql(query)
        
        # 결과 타입 확인
        assert isinstance(result, SQLAnalysisResult)
        
        # 기본 필드 확인
        assert result.query == query
        assert result.target_database == TargetDatabase.POSTGRESQL
        assert result.total_score >= 0
        assert 0 <= result.normalized_score <= 10
        assert result.complexity_level is not None
        assert result.recommendation is not None
        
        # 세부 점수 확인 (Requirements 13.1)
        assert result.structural_complexity >= 0
        assert result.oracle_specific_features >= 0
        assert result.functions_expressions >= 0
        assert result.data_volume >= 0
        assert result.execution_complexity >= 0
        assert result.conversion_difficulty >= 0
    
    def test_analyze_sql_empty(self):
        """빈 SQL 쿼리 분석 테스트"""
        analyzer = OracleComplexityAnalyzer()
        
        with pytest.raises(ValueError, match="빈 쿼리는 분석할 수 없습니다"):
            analyzer.analyze_sql("")
    
    def test_analyze_plsql_simple(self):
        """간단한 PL/SQL 코드 분석 테스트 (Requirements 8.1-11.5, 12.2, 13.2)"""
        analyzer = OracleComplexityAnalyzer()
        
        code = """
        CREATE OR REPLACE PROCEDURE test_proc IS
        BEGIN
            NULL;
        END;
        """
        
        result = analyzer.analyze_plsql(code)
        
        # 결과 타입 확인
        assert isinstance(result, PLSQLAnalysisResult)
        
        # 기본 필드 확인 (코드는 strip()되므로 원본과 다를 수 있음)
        assert result.code.strip() == code.strip()
        assert result.target_database == TargetDatabase.POSTGRESQL
        assert result.total_score >= 0
        assert 0 <= result.normalized_score <= 10
        assert result.complexity_level is not None
        assert result.recommendation is not None
        
        # 세부 점수 확인 (Requirements 13.2)
        assert result.base_score >= 0
        assert result.code_complexity >= 0
        assert result.oracle_features >= 0
        assert result.business_logic >= 0
        assert result.conversion_difficulty >= 0
    
    def test_analyze_plsql_empty(self):
        """빈 PL/SQL 코드 분석 테스트"""
        analyzer = OracleComplexityAnalyzer()
        
        with pytest.raises(ValueError, match="빈 코드는 분석할 수 없습니다"):
            analyzer.analyze_plsql("")
    
    def test_is_plsql_detection(self):
        """PL/SQL 감지 테스트"""
        analyzer = OracleComplexityAnalyzer()
        
        # PL/SQL 코드
        plsql_code = "CREATE OR REPLACE PROCEDURE test_proc IS BEGIN NULL; END;"
        assert analyzer._is_plsql(plsql_code) is True
        
        # SQL 쿼리
        sql_query = "SELECT * FROM employees"
        assert analyzer._is_plsql(sql_query) is False
    
    def test_export_json(self):
        """JSON 내보내기 테스트 (Requirements 14.1, 14.6, 14.7)"""
        analyzer = OracleComplexityAnalyzer(output_dir="test_reports")
        
        # 간단한 분석 수행
        query = "SELECT * FROM employees"
        result = analyzer.analyze_sql(query)
        
        # JSON 파일로 저장
        filename = "test_result.json"
        saved_path = analyzer.export_json(result, filename)
        
        # 파일이 생성되었는지 확인
        assert os.path.exists(saved_path)
        
        # JSON 파일 내용 확인
        with open(saved_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'query' in data
        assert 'total_score' in data
        assert 'normalized_score' in data
        
        # 정리
        import shutil
        shutil.rmtree("test_reports")
    
    def test_export_markdown(self):
        """Markdown 내보내기 테스트 (Requirements 14.2, 14.6, 14.7)"""
        analyzer = OracleComplexityAnalyzer(output_dir="test_reports")
        
        # 간단한 분석 수행
        query = "SELECT * FROM employees"
        result = analyzer.analyze_sql(query)
        
        # Markdown 파일로 저장
        filename = "test_report.md"
        saved_path = analyzer.export_markdown(result, filename)
        
        # 파일이 생성되었는지 확인
        assert os.path.exists(saved_path)
        
        # Markdown 파일 내용 확인
        with open(saved_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 필수 섹션 확인 (Requirements 14.5)
        assert '# Oracle SQL 복잡도 분석 결과' in content
        assert '## 복잡도 점수 요약' in content
        assert '## 세부 점수' in content
        assert '## 원본 쿼리' in content
        
        # 정리
        import shutil
        shutil.rmtree("test_reports")
    
    def test_mysql_app_migration_message(self):
        """MySQL 애플리케이션 이관 메시지 테스트 (Requirements 15.3)"""
        analyzer = OracleComplexityAnalyzer(target_database=TargetDatabase.MYSQL)
        
        # UTL_FILE을 사용하는 코드로 변경 (외부 의존성이 감지되도록)
        code = """
        CREATE OR REPLACE PACKAGE test_pkg IS
            PROCEDURE test_proc;
        END;
        /
        CREATE OR REPLACE PACKAGE BODY test_pkg IS
            PROCEDURE test_proc IS
                v_file UTL_FILE.FILE_TYPE;
            BEGIN
                v_file := UTL_FILE.FOPEN('DIR', 'file.txt', 'W');
                UTL_FILE.PUT_LINE(v_file, 'test');
                UTL_FILE.FCLOSE(v_file);
            END;
        END;
        """
        
        result = analyzer.analyze_plsql(code)
        
        # MySQL 타겟이므로 애플리케이션 이관 페널티가 적용되어야 함
        assert result.app_migration_penalty > 0
        
        # 변환 가이드에 UTL_FILE 관련 가이드가 포함되어야 함
        assert 'UTL_FILE' in result.conversion_guides
        assert '애플리케이션' in result.conversion_guides['UTL_FILE']
        
        # 애플리케이션 이관 메시지가 변환 가이드에 포함되어 있는지 확인
        # (외부 의존성이 감지되면 변환 가이드가 생성되고, MySQL 타겟이면 특별 메시지 추가)
        if '⚠️ 중요' in result.conversion_guides:
            assert '애플리케이션 레벨' in result.conversion_guides['⚠️ 중요']
    
    def test_analyze_file_not_found(self):
        """존재하지 않는 파일 분석 테스트"""
        analyzer = OracleComplexityAnalyzer()
        
        with pytest.raises(FileNotFoundError):
            analyzer.analyze_file("nonexistent_file.sql")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
