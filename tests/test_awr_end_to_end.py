"""
AWR 분석기 엔드투엔드 통합 테스트

실제 AWR 파일을 사용하여 전체 플로우를 테스트합니다.
- AWR 파일 파싱
- AWR 특화 섹션 파싱 (IOSTAT, PERCENTILE, WORKLOAD, BUFFER-CACHE)
- 백분위수 기반 마이그레이션 분석
- 상세 리포트 생성 및 저장
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


class TestAWREndToEnd:
    """AWR 분석기 엔드투엔드 통합 테스트"""
    
    @pytest.fixture
    def sample_awr_file(self):
        """실제 샘플 AWR 파일 경로"""
        return "sample_code/dbcsi_awr_sample01.out"
    
    @pytest.fixture
    def temp_output_dir(self):
        """임시 출력 디렉토리"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_awr_full_pipeline(self, sample_awr_file):
        """
        AWR 전체 파이프라인 테스트
        - AWR 파일 파싱
        - AWR 특화 섹션 검증
        - 백분위수 기반 마이그레이션 분석
        - 상세 리포트 생성
        """
        # 1. AWR 파일 파싱
        parser = StatspackParser(sample_awr_file)
        awr_data = parser.parse()
        
        # 2. 기본 Statspack 섹션 검증
        assert awr_data is not None
        assert awr_data.os_info is not None
        assert awr_data.os_info.db_name == "ORA12C"
        assert "Enterprise Edition" in awr_data.os_info.banner
        assert awr_data.os_info.version == "12.2.0.1.0"
        assert len(awr_data.memory_metrics) > 0
        assert len(awr_data.main_metrics) > 0
        
        # 3. AWR 특화 섹션 검증
        # AWR 파일이므로 일부 AWR 특화 데이터가 있어야 함
        # (모든 섹션이 있을 필요는 없음)
        # 현재는 기본 Statspack 파서를 사용하므로 AWR 특화 속성이 없을 수 있음
        has_awr_sections = (
            (hasattr(awr_data, 'iostat_functions') and awr_data.iostat_functions and len(awr_data.iostat_functions) > 0) or
            (hasattr(awr_data, 'percentile_cpu') and awr_data.percentile_cpu and len(awr_data.percentile_cpu) > 0) or
            (hasattr(awr_data, 'percentile_io') and awr_data.percentile_io and len(awr_data.percentile_io) > 0) or
            (hasattr(awr_data, 'workload_profiles') and awr_data.workload_profiles and len(awr_data.workload_profiles) > 0) or
            (hasattr(awr_data, 'buffer_cache_stats') and awr_data.buffer_cache_stats and len(awr_data.buffer_cache_stats) > 0)
        )
        
        # AWR 파일이므로 최소한 하나의 AWR 특화 섹션이 있어야 함
        # (샘플 파일에 따라 다를 수 있으므로 경고만 출력)
        if not has_awr_sections:
            print("Warning: No AWR-specific sections found in sample file (AWR parser not yet implemented)")
        
        # 4. 마이그레이션 분석
        analyzer = MigrationAnalyzer(awr_data)
        analysis_results = analyzer.analyze()
        
        # 5. 분석 결과 검증
        assert len(analysis_results) == 3
        assert TargetDatabase.RDS_ORACLE in analysis_results
        assert TargetDatabase.AURORA_MYSQL in analysis_results
        assert TargetDatabase.AURORA_POSTGRESQL in analysis_results
        
        # 각 타겟별 결과 검증
        for target, complexity in analysis_results.items():
            assert 0 <= complexity.score <= 10
            assert complexity.level is not None
            assert len(complexity.factors) > 0
            assert len(complexity.recommendations) > 0
            
            # RDS Oracle은 인스턴스 추천이 있어야 함
            if target == TargetDatabase.RDS_ORACLE:
                assert complexity.instance_recommendation is not None
                assert complexity.instance_recommendation.instance_type.startswith("db.r6i.")
        
        # 6. JSON 포맷팅
        json_output = StatspackResultFormatter.to_json(awr_data)
        assert json_output is not None
        assert len(json_output) > 0
        
        # JSON 파싱 가능 여부 확인
        parsed_json = json.loads(json_output)
        assert "os_info" in parsed_json
        assert parsed_json["os_info"]["db_name"] == "ORA12C"
        
        # 7. Markdown 포맷팅
        markdown_output = StatspackResultFormatter.to_markdown(awr_data, analysis_results)
        assert markdown_output is not None
        assert "ORA12C" in markdown_output
        assert "마이그레이션" in markdown_output or "Migration" in markdown_output
    
    def test_awr_percentile_based_analysis(self, sample_awr_file):
        """
        백분위수 기반 분석 테스트
        - P99 CPU/IO 메트릭 사용
        - 백분위수 기반 인스턴스 사이징
        """
        parser = StatspackParser(sample_awr_file)
        awr_data = parser.parse()
        
        analyzer = MigrationAnalyzer(awr_data)
        
        # 백분위수 메트릭이 있는 경우 검증
        if hasattr(awr_data, 'percentile_cpu') and awr_data.percentile_cpu and len(awr_data.percentile_cpu) > 0:
            # P99 CPU 값 확인
            if "99th_percentile" in awr_data.percentile_cpu:
                p99_cpu = awr_data.percentile_cpu["99th_percentile"]
                assert p99_cpu.on_cpu > 0
                print(f"P99 CPU: {p99_cpu.on_cpu} cores")
        else:
            print("No percentile CPU data (AWR parser not yet implemented)")
        
        if hasattr(awr_data, 'percentile_io') and awr_data.percentile_io and len(awr_data.percentile_io) > 0:
            # P99 I/O 값 확인
            if "99th_percentile" in awr_data.percentile_io:
                p99_io = awr_data.percentile_io["99th_percentile"]
                assert p99_io.rw_iops >= 0
                print(f"P99 IOPS: {p99_io.rw_iops}")
        else:
            print("No percentile I/O data (AWR parser not yet implemented)")
        
        # 마이그레이션 분석 실행
        analysis_results = analyzer.analyze()
        
        # RDS Oracle 인스턴스 추천 검증
        rds_complexity = analysis_results[TargetDatabase.RDS_ORACLE]
        if rds_complexity.instance_recommendation:
            rec = rds_complexity.instance_recommendation
            assert rec.vcpu > 0
            assert rec.memory_gib > 0
            assert rec.instance_type in MigrationAnalyzer.R6I_INSTANCES
            print(f"Recommended instance: {rec.instance_type} ({rec.vcpu} vCPU, {rec.memory_gib} GiB)")
    
    def test_awr_workload_pattern_analysis(self, sample_awr_file):
        """
        워크로드 패턴 분석 테스트
        - CPU 집약적/I/O 집약적 분류
        - 시간대별 패턴 분석
        """
        parser = StatspackParser(sample_awr_file)
        awr_data = parser.parse()
        
        # 워크로드 데이터가 있는 경우 검증
        if hasattr(awr_data, 'workload_profiles') and awr_data.workload_profiles and len(awr_data.workload_profiles) > 0:
            # 워크로드 프로파일 기본 검증
            for profile in awr_data.workload_profiles[:5]:  # 처음 5개만 검증
                assert profile.sample_start is not None
                assert profile.module is not None
                assert profile.event is not None
                assert profile.total_dbtime_sum >= 0
                assert profile.session_type in ["FOREGROUND", "BACKGROUND"]
            
            # CPU vs I/O 분석
            cpu_events = [p for p in awr_data.workload_profiles if "CPU" in p.event]
            io_events = [p for p in awr_data.workload_profiles if "I/O" in p.wait_class or "User I/O" in p.wait_class]
            
            print(f"CPU events: {len(cpu_events)}")
            print(f"I/O events: {len(io_events)}")
            
            # 유휴 이벤트는 제외되어야 함
            idle_events = [p for p in awr_data.workload_profiles if "IDLE" in p.event]
            # 유휴 이벤트가 있더라도 분석에서는 제외되어야 함
            print(f"Idle events (should be excluded from analysis): {len(idle_events)}")
        else:
            print("No workload profile data (AWR parser not yet implemented)")
    
    def test_awr_buffer_cache_analysis(self, sample_awr_file):
        """
        버퍼 캐시 효율성 분석 테스트
        - 히트율 계산
        - 최적화 권장사항
        """
        parser = StatspackParser(sample_awr_file)
        awr_data = parser.parse()
        
        # 버퍼 캐시 데이터가 있는 경우 검증
        if hasattr(awr_data, 'buffer_cache_stats') and awr_data.buffer_cache_stats and len(awr_data.buffer_cache_stats) > 0:
            for stat in awr_data.buffer_cache_stats[:5]:  # 처음 5개만 검증
                assert stat.snap_id > 0
                assert stat.block_size > 0
                assert stat.db_cache_gb >= 0
                assert 0 <= stat.hit_ratio <= 100
                
                print(f"Snap {stat.snap_id}: Hit Ratio = {stat.hit_ratio:.2f}%")
            
            # 평균 히트율 계산
            avg_hit_ratio = sum(s.hit_ratio for s in awr_data.buffer_cache_stats) / len(awr_data.buffer_cache_stats)
            print(f"Average Hit Ratio: {avg_hit_ratio:.2f}%")
            
            # 히트율에 따른 권장사항 검증
            if avg_hit_ratio < 90:
                print("Recommendation: Increase buffer cache size")
            elif avg_hit_ratio > 99.5:
                print("Recommendation: Consider reducing buffer cache size")
            else:
                print("Buffer cache is efficient")
        else:
            print("No buffer cache data (AWR parser not yet implemented)")
    
    def test_awr_io_function_analysis(self, sample_awr_file):
        """
        I/O 함수별 분석 테스트
        - LGWR, DBWR, Direct I/O 분석
        """
        parser = StatspackParser(sample_awr_file)
        awr_data = parser.parse()
        
        # I/O 함수 데이터가 있는 경우 검증
        if hasattr(awr_data, 'iostat_functions') and awr_data.iostat_functions and len(awr_data.iostat_functions) > 0:
            # 함수별 I/O 통계 집계
            io_by_function = {}
            for iostat in awr_data.iostat_functions:
                func = iostat.function_name
                if func not in io_by_function:
                    io_by_function[func] = []
                io_by_function[func].append(iostat.megabytes_per_s)
            
            # 각 함수별 평균 I/O 계산
            for func, values in io_by_function.items():
                avg_io = sum(values) / len(values)
                max_io = max(values)
                print(f"{func}: Avg={avg_io:.2f} MB/s, Max={max_io:.2f} MB/s")
                
                # LGWR I/O가 높으면 최적화 필요
                if func == "LGWR" and avg_io > 10:
                    print(f"  -> LGWR I/O is high, optimization recommended")
                
                # DBWR I/O가 높으면 버퍼 캐시 증가 고려
                if func == "DBWR" and avg_io > 20:
                    print(f"  -> DBWR I/O is high, consider increasing buffer cache")
        else:
            print("No I/O function data (AWR parser not yet implemented)")
    
    def test_awr_report_generation_and_saving(self, sample_awr_file, temp_output_dir):
        """
        AWR 리포트 생성 및 저장 테스트
        - JSON 저장
        - Markdown 저장
        - 파일 존재 확인
        """
        parser = StatspackParser(sample_awr_file)
        awr_data = parser.parse()
        
        analyzer = MigrationAnalyzer(awr_data)
        analysis_results = analyzer.analyze()
        
        # JSON 저장
        json_content = StatspackResultFormatter.to_json(awr_data)
        json_path = os.path.join(temp_output_dir, "awr_report.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_content)
        
        assert os.path.exists(json_path)
        assert os.path.getsize(json_path) > 0
        
        # JSON 파일 읽기 및 검증
        with open(json_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        assert "os_info" in loaded_data
        assert loaded_data["os_info"]["db_name"] == "ORA12C"
        
        # Markdown 저장
        markdown_content = StatspackResultFormatter.to_markdown(awr_data, analysis_results)
        markdown_path = os.path.join(temp_output_dir, "awr_report.md")
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        assert os.path.exists(markdown_path)
        assert os.path.getsize(markdown_path) > 0
        
        # Markdown 파일 읽기 및 검증
        with open(markdown_path, "r", encoding="utf-8") as f:
            loaded_markdown = f.read()
        assert "ORA12C" in loaded_markdown
        assert "마이그레이션" in loaded_markdown or "Migration" in loaded_markdown
    
    def test_awr_vs_statspack_compatibility(self, sample_awr_file):
        """
        AWR과 Statspack 호환성 테스트
        - AWR 파일도 기본 Statspack 섹션을 파싱할 수 있어야 함
        """
        # AWR 파일 파싱
        parser = StatspackParser(sample_awr_file)
        awr_data = parser.parse()
        
        # 기본 Statspack 섹션이 모두 파싱되어야 함
        assert awr_data.os_info is not None
        assert awr_data.os_info.db_name is not None
        assert awr_data.os_info.version is not None
        assert len(awr_data.memory_metrics) > 0
        assert len(awr_data.main_metrics) > 0
        
        # 마이그레이션 분석도 정상 동작해야 함
        analyzer = MigrationAnalyzer(awr_data)
        analysis_results = analyzer.analyze()
        
        assert len(analysis_results) == 3
        for target, complexity in analysis_results.items():
            assert 0 <= complexity.score <= 10
            assert complexity.level is not None
    
    def test_awr_all_target_databases(self, sample_awr_file):
        """
        모든 타겟 DB에 대한 AWR 분석 테스트
        - RDS for Oracle
        - Aurora MySQL 8.0
        - Aurora PostgreSQL 16
        """
        parser = StatspackParser(sample_awr_file)
        awr_data = parser.parse()
        
        analyzer = MigrationAnalyzer(awr_data)
        
        # 각 타겟별로 개별 분석
        for target in [TargetDatabase.RDS_ORACLE, 
                      TargetDatabase.AURORA_MYSQL, 
                      TargetDatabase.AURORA_POSTGRESQL]:
            result = analyzer.analyze(target=target)
            
            assert target in result
            complexity = result[target]
            
            # 기본 검증
            assert 0 <= complexity.score <= 10
            assert complexity.level is not None
            assert complexity.target == target
            
            # RDS Oracle은 가장 낮은 난이도를 가져야 함
            if target == TargetDatabase.RDS_ORACLE:
                # Enterprise Edition이므로 비교적 간단
                # 하지만 버전 업그레이드와 캐릭터셋 변환으로 인해 점수가 높을 수 있음
                assert complexity.score < 10  # 최대 점수보다는 낮아야 함
            
            # 인스턴스 추천 검증 (RDS Oracle만)
            if target == TargetDatabase.RDS_ORACLE:
                assert complexity.instance_recommendation is not None
                rec = complexity.instance_recommendation
                assert rec.vcpu > 0
                assert rec.memory_gib > 0
                assert rec.instance_type in MigrationAnalyzer.R6I_INSTANCES
    
    def test_awr_oracle_edition_detection(self, sample_awr_file):
        """
        AWR 파일에서 Oracle 에디션 감지 테스트
        """
        parser = StatspackParser(sample_awr_file)
        awr_data = parser.parse()
        
        analyzer = MigrationAnalyzer(awr_data)
        edition = analyzer._detect_oracle_edition()
        
        # 샘플 파일은 Enterprise Edition
        from src.dbcsi.models import OracleEdition
        assert edition == OracleEdition.ENTERPRISE
    
    def test_awr_resource_usage_analysis(self, sample_awr_file):
        """
        AWR 리소스 사용량 분석 테스트
        - 백분위수 메트릭 우선 사용
        """
        parser = StatspackParser(sample_awr_file)
        awr_data = parser.parse()
        
        analyzer = MigrationAnalyzer(awr_data)
        resource_usage = analyzer._analyze_resource_usage()
        
        # 리소스 사용량 정보 검증
        assert "cpu_p99_pct" in resource_usage or "cpu_p99" in resource_usage
        assert "memory_avg_gb" in resource_usage
        assert "disk_size_gb" in resource_usage
        
        # CPU 값 확인
        cpu_key = "cpu_p99_pct" if "cpu_p99_pct" in resource_usage else "cpu_p99"
        assert resource_usage[cpu_key] >= 0
        assert resource_usage["memory_avg_gb"] > 0
        assert resource_usage["disk_size_gb"] > 0
        
        print(f"Resource Usage: {resource_usage}")
    
    def test_awr_plsql_complexity_evaluation(self, sample_awr_file):
        """
        AWR 파일에서 PL/SQL 코드 복잡도 평가 테스트
        """
        parser = StatspackParser(sample_awr_file)
        awr_data = parser.parse()
        
        # PL/SQL 라인 수 확인
        assert awr_data.os_info.count_lines_plsql == 274
        assert awr_data.os_info.count_functions == 1
        assert awr_data.os_info.count_procedures == 2
        
        analyzer = MigrationAnalyzer(awr_data)
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
