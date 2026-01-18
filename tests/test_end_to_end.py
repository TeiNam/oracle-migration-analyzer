"""
엔드투엔드 통합 테스트

실제 Statspack 파일을 사용하여 전체 플로우를 테스트합니다.
- 파일 파싱
- 마이그레이션 분석
- 결과 포맷팅 및 저장
- 모든 타겟 DB 분석
"""

import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path

from src.dbcsi.parser import StatspackParser
from src.dbcsi.migration_analyzer import MigrationAnalyzer
from src.dbcsi.result_formatter import StatspackResultFormatter
from src.dbcsi.models import TargetDatabase


class TestEndToEnd:
    """엔드투엔드 통합 테스트"""
    
    @pytest.fixture
    def sample_statspack_file(self):
        """실제 샘플 Statspack 파일 경로"""
        return "sample_code/dbcsi_statspack_sample01.out"
    
    @pytest.fixture
    def temp_output_dir(self):
        """임시 출력 디렉토리"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_full_pipeline_single_file(self, sample_statspack_file):
        """
        전체 파이프라인 테스트: 단일 파일
        - 파일 파싱
        - 데이터 검증
        - 마이그레이션 분석
        - 결과 포맷팅
        """
        # 1. 파일 파싱
        parser = StatspackParser(sample_statspack_file)
        statspack_data = parser.parse()
        
        # 2. 파싱 결과 검증
        assert statspack_data is not None
        assert statspack_data.os_info is not None
        assert statspack_data.os_info.db_name == "ORCL01"
        assert statspack_data.os_info.banner is not None
        assert "Standard Edition 2" in statspack_data.os_info.banner
        assert len(statspack_data.memory_metrics) > 0
        assert len(statspack_data.main_metrics) > 0
        assert len(statspack_data.wait_events) > 0
        
        # 3. 마이그레이션 분석
        analyzer = MigrationAnalyzer(statspack_data)
        analysis_results = analyzer.analyze()
        
        # 4. 분석 결과 검증
        assert len(analysis_results) == 3  # RDS Oracle, Aurora MySQL, Aurora PostgreSQL
        assert TargetDatabase.RDS_ORACLE in analysis_results
        assert TargetDatabase.AURORA_MYSQL in analysis_results
        assert TargetDatabase.AURORA_POSTGRESQL in analysis_results
        
        # 각 타겟별 결과 검증
        for target, complexity in analysis_results.items():
            assert 0 <= complexity.score <= 10
            assert complexity.level is not None
            assert len(complexity.factors) > 0
            assert len(complexity.recommendations) > 0
            # RDS Oracle만 인스턴스 추천이 있음 (난이도 <= 7)
            if target == TargetDatabase.RDS_ORACLE:
                assert complexity.instance_recommendation is not None
                assert complexity.instance_recommendation.instance_type.startswith("db.r6i.")
        
        # 5. JSON 포맷팅
        json_output = StatspackResultFormatter.to_json(statspack_data)
        assert json_output is not None
        assert len(json_output) > 0
        
        # JSON 파싱 가능 여부 확인
        parsed_json = json.loads(json_output)
        assert "os_info" in parsed_json
        
        # 6. Markdown 포맷팅
        markdown_output = StatspackResultFormatter.to_markdown(statspack_data, analysis_results)
        assert markdown_output is not None
        assert "# Statspack" in markdown_output  # 한국어 또는 영어 제목
        assert "System" in markdown_output or "시스템" in markdown_output
        assert "Migration" in markdown_output or "마이그레이션" in markdown_output
        assert "ORCL01" in markdown_output
    
    def test_all_target_databases(self, sample_statspack_file):
        """
        모든 타겟 DB에 대한 분석 테스트
        - RDS for Oracle
        - Aurora MySQL 8.0
        - Aurora PostgreSQL 16
        """
        parser = StatspackParser(sample_statspack_file)
        statspack_data = parser.parse()
        
        analyzer = MigrationAnalyzer(statspack_data)
        
        # 각 타겟별로 개별 분석
        for target in [TargetDatabase.RDS_ORACLE, 
                      TargetDatabase.AURORA_MYSQL, 
                      TargetDatabase.AURORA_POSTGRESQL]:
            result = analyzer.analyze(target=target)
            
            assert target in result
            complexity = result[target]
            
            # 기본 검증
            assert 0 <= complexity.score <= 10
            assert complexity.level.startswith("매우 간단") or \
                   complexity.level.startswith("간단") or \
                   complexity.level.startswith("중간") or \
                   complexity.level.startswith("복잡") or \
                   complexity.level.startswith("매우 복잡")
            assert complexity.target == target
            
            # RDS Oracle은 가장 낮은 난이도를 가져야 함
            if target == TargetDatabase.RDS_ORACLE:
                assert complexity.score < 5  # Standard Edition 2이므로 비교적 간단
            
            # 인스턴스 추천 검증 (RDS Oracle만)
            if target == TargetDatabase.RDS_ORACLE:
                assert complexity.instance_recommendation is not None
                rec = complexity.instance_recommendation
                assert rec.vcpu > 0
                assert rec.memory_gib > 0
                assert rec.instance_type in MigrationAnalyzer.R6I_INSTANCES
    
    def test_report_generation_and_saving(self, sample_statspack_file, temp_output_dir):
        """
        리포트 생성 및 저장 테스트
        - JSON 저장
        - Markdown 저장
        - 파일 존재 확인
        """
        parser = StatspackParser(sample_statspack_file)
        statspack_data = parser.parse()
        
        analyzer = MigrationAnalyzer(statspack_data)
        analysis_results = analyzer.analyze()
        
        # JSON 저장
        json_content = StatspackResultFormatter.to_json(statspack_data)
        json_path = os.path.join(temp_output_dir, "test_report.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_content)
        
        assert os.path.exists(json_path)
        assert os.path.getsize(json_path) > 0
        
        # JSON 파일 읽기 및 검증
        with open(json_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        assert "os_info" in loaded_data
        
        # Markdown 저장
        markdown_content = StatspackResultFormatter.to_markdown(statspack_data, analysis_results)
        markdown_path = os.path.join(temp_output_dir, "test_report.md")
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        assert os.path.exists(markdown_path)
        assert os.path.getsize(markdown_path) > 0
        
        # Markdown 파일 읽기 및 검증
        with open(markdown_path, "r", encoding="utf-8") as f:
            loaded_markdown = f.read()
        assert "# Statspack" in loaded_markdown  # 한국어 또는 영어 제목
        assert "ORCL01" in loaded_markdown
    
    def test_character_set_detection(self, sample_statspack_file):
        """
        캐릭터셋 감지 및 변환 필요성 테스트
        """
        parser = StatspackParser(sample_statspack_file)
        statspack_data = parser.parse()
        
        # 샘플 파일은 AL32UTF8 사용
        assert statspack_data.os_info.character_set == "AL32UTF8"
        
        analyzer = MigrationAnalyzer(statspack_data)
        
        # AL32UTF8이므로 변환 불필요
        assert not analyzer._requires_charset_conversion()
        
        # 변환 복잡도는 0이어야 함
        charset_complexity = analyzer._calculate_charset_complexity()
        assert charset_complexity == 0.0
    
    def test_oracle_edition_detection(self, sample_statspack_file):
        """
        Oracle 에디션 감지 테스트
        """
        parser = StatspackParser(sample_statspack_file)
        statspack_data = parser.parse()
        
        analyzer = MigrationAnalyzer(statspack_data)
        edition = analyzer._detect_oracle_edition()
        
        # 샘플 파일은 Standard Edition 2
        from src.dbcsi.models import OracleEdition
        assert edition == OracleEdition.STANDARD_2
    
    def test_rac_detection(self, sample_statspack_file):
        """
        RAC 환경 감지 테스트
        """
        parser = StatspackParser(sample_statspack_file)
        statspack_data = parser.parse()
        
        analyzer = MigrationAnalyzer(statspack_data)
        is_rac = analyzer._detect_rac()
        
        # 샘플 파일은 Single Instance (INSTANCES=1)
        assert not is_rac
    
    def test_resource_usage_analysis(self, sample_statspack_file):
        """
        리소스 사용량 분석 테스트
        """
        parser = StatspackParser(sample_statspack_file)
        statspack_data = parser.parse()
        
        analyzer = MigrationAnalyzer(statspack_data)
        resource_usage = analyzer._analyze_resource_usage()
        
        # 리소스 사용량 정보 검증
        assert "cpu_p99_pct" in resource_usage or "cpu_p99" in resource_usage
        assert "memory_avg_gb" in resource_usage
        assert "disk_size_gb" in resource_usage
        assert "total_iops_p99" in resource_usage or "iops_p99" in resource_usage
        
        # CPU 값 확인
        cpu_key = "cpu_p99_pct" if "cpu_p99_pct" in resource_usage else "cpu_p99"
        assert resource_usage[cpu_key] > 0
        assert resource_usage["memory_avg_gb"] > 0
        assert resource_usage["disk_size_gb"] > 0
    
    def test_wait_events_analysis(self, sample_statspack_file):
        """
        대기 이벤트 분석 테스트
        """
        parser = StatspackParser(sample_statspack_file)
        statspack_data = parser.parse()
        
        analyzer = MigrationAnalyzer(statspack_data)
        wait_analysis = analyzer._analyze_wait_events()
        
        # 대기 이벤트 분석 결과 검증
        assert "db_cpu_pct" in wait_analysis
        assert "user_io_pct" in wait_analysis
        assert "top_events" in wait_analysis
        
        assert wait_analysis["db_cpu_pct"] >= 0
        assert len(wait_analysis["top_events"]) > 0
    
    def test_plsql_complexity_evaluation(self, sample_statspack_file):
        """
        PL/SQL 코드 복잡도 평가 테스트
        """
        parser = StatspackParser(sample_statspack_file)
        statspack_data = parser.parse()
        
        # PL/SQL 라인 수 확인
        assert statspack_data.os_info.count_lines_plsql == 6165
        assert statspack_data.os_info.count_packages == 1
        
        analyzer = MigrationAnalyzer(statspack_data)
        analysis_results = analyzer.analyze()
        
        # Aurora PostgreSQL과 MySQL은 PL/SQL 변환으로 인해 더 높은 난이도
        pg_complexity = analysis_results[TargetDatabase.AURORA_POSTGRESQL]
        mysql_complexity = analysis_results[TargetDatabase.AURORA_MYSQL]
        oracle_complexity = analysis_results[TargetDatabase.RDS_ORACLE]
        
        # PL/SQL 변환이 필요한 타겟이 더 높은 난이도를 가져야 함
        assert pg_complexity.score > oracle_complexity.score
        assert mysql_complexity.score > oracle_complexity.score
        
        # MySQL이 PostgreSQL보다 PL/SQL 변환이 더 어려움
        assert mysql_complexity.score >= pg_complexity.score
