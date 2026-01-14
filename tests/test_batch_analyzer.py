"""
BatchAnalyzer 테스트

Requirements:
- 전체: 폴더 일괄 분석 및 병렬 처리 테스트
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from src.oracle_complexity_analyzer import (
    OracleComplexityAnalyzer,
    BatchAnalyzer,
    BatchAnalysisResult,
    TargetDatabase,
    ComplexityLevel
)


class TestBatchAnalyzer:
    """BatchAnalyzer 클래스 테스트"""
    
    @pytest.fixture
    def temp_folder(self):
        """임시 폴더 생성"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def analyzer(self):
        """OracleComplexityAnalyzer 인스턴스 생성"""
        return OracleComplexityAnalyzer(TargetDatabase.POSTGRESQL)
    
    @pytest.fixture
    def batch_analyzer(self, analyzer):
        """BatchAnalyzer 인스턴스 생성"""
        return BatchAnalyzer(analyzer, max_workers=2)
    
    def test_find_sql_files_empty_folder(self, batch_analyzer, temp_folder):
        """빈 폴더에서 파일 검색 테스트"""
        files = batch_analyzer.find_sql_files(temp_folder)
        assert len(files) == 0
    
    def test_find_sql_files_with_sql_files(self, batch_analyzer, temp_folder):
        """SQL 파일이 있는 폴더에서 파일 검색 테스트"""
        # 테스트 파일 생성
        test_files = [
            "test1.sql",
            "test2.pls",
            "test3.pkb",
            "test4.pks",
            "test5.txt",  # 지원하지 않는 확장자
        ]
        
        for filename in test_files:
            file_path = Path(temp_folder) / filename
            file_path.write_text("SELECT 1 FROM DUAL;")
        
        # 파일 검색
        files = batch_analyzer.find_sql_files(temp_folder)
        
        # 지원하는 확장자만 찾아야 함
        assert len(files) == 4
        assert all(f.suffix in BatchAnalyzer.SUPPORTED_EXTENSIONS for f in files)
    
    def test_find_sql_files_recursive(self, batch_analyzer, temp_folder):
        """하위 폴더 재귀 검색 테스트"""
        # 하위 폴더 생성
        sub_folder = Path(temp_folder) / "subfolder"
        sub_folder.mkdir()
        
        # 파일 생성
        (Path(temp_folder) / "test1.sql").write_text("SELECT 1 FROM DUAL;")
        (sub_folder / "test2.sql").write_text("SELECT 2 FROM DUAL;")
        
        # 파일 검색
        files = batch_analyzer.find_sql_files(temp_folder)
        
        # 하위 폴더 파일도 찾아야 함
        assert len(files) == 2
    
    def test_analyze_folder_empty(self, batch_analyzer, temp_folder):
        """빈 폴더 분석 테스트"""
        result = batch_analyzer.analyze_folder(temp_folder)
        
        assert isinstance(result, BatchAnalysisResult)
        assert result.total_files == 0
        assert result.success_count == 0
        assert result.failure_count == 0
    
    def test_analyze_folder_with_valid_files(self, batch_analyzer, temp_folder):
        """유효한 SQL 파일이 있는 폴더 분석 테스트"""
        # 간단한 SQL 파일 생성
        sql_files = [
            ("test1.sql", "SELECT * FROM users WHERE id = 1;"),
            ("test2.sql", "SELECT COUNT(*) FROM orders;"),
        ]
        
        for filename, content in sql_files:
            file_path = Path(temp_folder) / filename
            file_path.write_text(content)
        
        # 폴더 분석
        result = batch_analyzer.analyze_folder(temp_folder)
        
        # 검증
        assert result.total_files == 2
        assert result.success_count == 2
        assert result.failure_count == 0
        assert len(result.results) == 2
        assert result.average_score >= 0
    
    def test_analyze_folder_with_invalid_files(self, batch_analyzer, temp_folder):
        """유효하지 않은 파일이 있는 폴더 분석 테스트"""
        # 빈 파일 생성 (분석 실패 예상)
        file_path = Path(temp_folder) / "empty.sql"
        file_path.write_text("")
        
        # 폴더 분석
        result = batch_analyzer.analyze_folder(temp_folder)
        
        # 검증
        assert result.total_files == 1
        assert result.failure_count == 1
        assert len(result.failed_files) == 1
    
    def test_get_top_complex_files(self, batch_analyzer, temp_folder):
        """복잡도 높은 파일 Top N 추출 테스트"""
        # 다양한 복잡도의 SQL 파일 생성
        sql_files = [
            ("simple.sql", "SELECT 1 FROM DUAL;"),
            ("complex.sql", """
                SELECT a.*, b.*, c.*
                FROM table1 a
                JOIN table2 b ON a.id = b.id
                JOIN table3 c ON b.id = c.id
                WHERE a.status = 'active'
                  AND b.created_at > SYSDATE - 30
                  AND c.amount > 1000
                ORDER BY a.created_at DESC;
            """),
        ]
        
        for filename, content in sql_files:
            file_path = Path(temp_folder) / filename
            file_path.write_text(content)
        
        # 폴더 분석
        result = batch_analyzer.analyze_folder(temp_folder)
        
        # Top N 추출
        top_files = batch_analyzer.get_top_complex_files(result, top_n=2)
        
        # 검증
        assert len(top_files) == 2
        assert top_files[0][1] >= top_files[1][1]  # 점수 내림차순
    
    def test_export_batch_json(self, batch_analyzer, temp_folder, analyzer):
        """배치 결과 JSON 저장 테스트"""
        # SQL 파일 생성
        file_path = Path(temp_folder) / "test.sql"
        file_path.write_text("SELECT * FROM users;")
        
        # 폴더 분석
        result = batch_analyzer.analyze_folder(temp_folder)
        
        # JSON 저장
        json_path = batch_analyzer.export_batch_json(result)
        
        # 검증
        assert Path(json_path).exists()
        assert json_path.endswith(".json")
    
    def test_export_batch_markdown(self, batch_analyzer, temp_folder, analyzer):
        """배치 결과 Markdown 저장 테스트"""
        # SQL 파일 생성
        file_path = Path(temp_folder) / "test.sql"
        file_path.write_text("SELECT * FROM users;")
        
        # 폴더 분석
        result = batch_analyzer.analyze_folder(temp_folder)
        
        # Markdown 저장
        md_path = batch_analyzer.export_batch_markdown(result)
        
        # 검증
        assert Path(md_path).exists()
        assert md_path.endswith(".md")
    
    def test_complexity_distribution(self, batch_analyzer, temp_folder):
        """복잡도 레벨별 분포 집계 테스트"""
        # 다양한 복잡도의 SQL 파일 생성
        sql_files = [
            ("simple1.sql", "SELECT 1 FROM DUAL;"),
            ("simple2.sql", "SELECT 2 FROM DUAL;"),
            ("complex.sql", """
                SELECT a.*, b.*, c.*, d.*
                FROM table1 a
                JOIN table2 b ON a.id = b.id
                JOIN table3 c ON b.id = c.id
                JOIN table4 d ON c.id = d.id
                WHERE a.status IN (SELECT status FROM status_table)
                  AND b.created_at > SYSDATE - 30
                ORDER BY a.created_at DESC;
            """),
        ]
        
        for filename, content in sql_files:
            file_path = Path(temp_folder) / filename
            file_path.write_text(content)
        
        # 폴더 분석
        result = batch_analyzer.analyze_folder(temp_folder)
        
        # 검증
        assert result.total_files == 3
        assert result.success_count == 3
        
        # 복잡도 분포 확인
        total_distributed = sum(result.complexity_distribution.values())
        assert total_distributed == result.success_count
    
    def test_batch_analysis_result_structure(self, batch_analyzer, temp_folder):
        """BatchAnalysisResult 구조 검증"""
        # SQL 파일 생성
        file_path = Path(temp_folder) / "test.sql"
        file_path.write_text("SELECT * FROM users;")
        
        # 폴더 분석
        result = batch_analyzer.analyze_folder(temp_folder)
        
        # 구조 검증
        assert hasattr(result, 'total_files')
        assert hasattr(result, 'success_count')
        assert hasattr(result, 'failure_count')
        assert hasattr(result, 'complexity_distribution')
        assert hasattr(result, 'average_score')
        assert hasattr(result, 'results')
        assert hasattr(result, 'failed_files')
        assert hasattr(result, 'target_database')
        assert hasattr(result, 'analysis_time')
        
        # 타입 검증
        assert isinstance(result.total_files, int)
        assert isinstance(result.success_count, int)
        assert isinstance(result.failure_count, int)
        assert isinstance(result.complexity_distribution, dict)
        assert isinstance(result.average_score, float)
        assert isinstance(result.results, dict)
        assert isinstance(result.failed_files, dict)
        assert isinstance(result.target_database, TargetDatabase)
        assert isinstance(result.analysis_time, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
