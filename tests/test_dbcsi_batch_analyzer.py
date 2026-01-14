"""
Statspack BatchAnalyzer 단위 테스트

Requirements 12.1~12.5, 17.1~17.3을 검증합니다.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.dbcsi.batch_analyzer import (
    BatchAnalyzer, BatchAnalysisResult, BatchFileResult,
    TrendAnalysisResult, TrendMetrics, Anomaly
)
from src.dbcsi.data_models import TargetDatabase


class TestBatchAnalyzer:
    """BatchAnalyzer 클래스 테스트"""
    
    @pytest.fixture
    def temp_dir(self):
        """임시 디렉토리 생성"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def sample_statspack_content(self):
        """샘플 Statspack 파일 내용"""
        return """~~BEGIN-OS-INFORMATION~~
STAT_NAME                                                        STAT_VALUE
---------------------------------------------------------------- ----------------------------------------------------------------
STATSPACK_MINER_VER                                              1.0.0
NUM_CPUS                                                         4
NUM_CPU_CORES                                                    2
PHYSICAL_MEMORY_GB                                               16.0
DB_NAME                                                          TESTDB
DBID                                                             123456789
VERSION                                                          19.0.0.0.0
BANNER                                                           Oracle Database 19c Enterprise Edition
INSTANCES                                                        1
IS_RDS                                                           NO
TOTAL_DB_SIZE_GB                                                 100.5
~~END-OS-INFORMATION~~

~~BEGIN-MEMORY~~
SNAP_ID INST SGA PGA TOTAL
------- ---- --- --- -----
1       1    8.0 2.0 10.0
2       1    8.5 2.5 11.0
~~END-MEMORY~~

~~BEGIN-SIZE-ON-DISK~~
SNAP_ID SIZE_GB
------- -------
1       100.0
2       100.5
~~END-SIZE-ON-DISK~~

~~BEGIN-MAIN-METRICS~~
snap dur_m end inst cpu_per_s read_iops read_mb_s write_iops write_mb_s commits_s
---- ----- --- ---- --------- --------- --------- ---------- ---------- ---------
1    60.0  2024-01-01 1 2.5 100.0 50.0 20.0 10.0 5.0
2    60.0  2024-01-02 1 3.0 120.0 60.0 25.0 12.0 6.0
~~END-MAIN-METRICS~~

~~BEGIN-TOP-N-TIMED-EVENTS~~
SNAP_ID WAIT_CLASS EVENT_NAME PCTDBT TOTAL_TIME_S
------- ---------- ---------- ------ ------------
1       User_I/O   db_file_sequential_read 25.5 100.0
2       User_I/O   db_file_sequential_read 30.0 120.0
~~END-TOP-N-TIMED-EVENTS~~

~~BEGIN-SYSSTAT~~
SNAP cell_flash_hits read_iops write_iops read_mb read_mb_opt read_nt_iops write_nt_iops read_nt_mb write_nt_mb cell_int_mb cell_int_ss_mb cell_si_save_mb cell_bytes_elig_mb cell_hcc_bytes_mb read_multi_iops read_temp_iops write_temp_iops network_incoming_mb network_outgoing_mb
---- ---------------- --------- ---------- ------- ----------- ------------ ------------- ---------- ----------- ----------- -------------- --------------- ------------------ ----------------- --------------- -------------- --------------- ------------------- -------------------
1    0                100.0     20.0       50.0    0.0         0.0          0.0           0.0        0.0         0.0         0.0            0.0             0.0                0.0               0.0             0.0            0.0             10.0                5.0
~~END-SYSSTAT~~

~~BEGIN-FEATURES~~
NAME                                                             DETECTED_USAGES TOTAL_SAMPLES CURRENTLY_USED AUX_COUNT LAST_SAMPLE_DATE FEATURE_INFO
---------------------------------------------------------------- --------------- ------------- -------------- --------- ---------------- ------------
Partitioning                                                     10              100           TRUE           5.0       2024-01-01       Table partitioning
~~END-FEATURES~~

~~BEGIN-SGA-ADVICE~~
INST_ID SGA_SIZE SGA_SIZE_FACTOR ESTD_DB_TIME ESTD_DB_TIME_FACTOR ESTD_PHYSICAL_READS SGA_TARGET
------- -------- --------------- ------------ ------------------- ------------------- ----------
1       8192     1.0             1000         1                   10000               8192
~~END-SGA-ADVICE~~
"""
    
    def test_init_with_valid_directory(self, temp_dir):
        """유효한 디렉토리로 초기화 테스트
        
        Requirements 12.1을 검증합니다.
        """
        analyzer = BatchAnalyzer(temp_dir)
        assert analyzer.directory == Path(temp_dir)
    
    def test_init_with_nonexistent_directory(self):
        """존재하지 않는 디렉토리로 초기화 시 예외 발생 테스트"""
        with pytest.raises(FileNotFoundError):
            BatchAnalyzer("/nonexistent/directory")
    
    def test_init_with_file_path(self, temp_dir):
        """파일 경로로 초기화 시 예외 발생 테스트"""
        # 임시 파일 생성
        file_path = Path(temp_dir) / "test.txt"
        file_path.write_text("test")
        
        with pytest.raises(NotADirectoryError):
            BatchAnalyzer(str(file_path))
    
    def test_find_statspack_files_empty_directory(self, temp_dir):
        """빈 디렉토리에서 파일 찾기 테스트
        
        Requirements 12.1을 검증합니다.
        """
        analyzer = BatchAnalyzer(temp_dir)
        files = analyzer.find_statspack_files()
        
        assert isinstance(files, list)
        assert len(files) == 0
    
    def test_find_statspack_files_with_out_files(self, temp_dir, sample_statspack_content):
        """디렉토리에 .out 파일이 있을 때 파일 찾기 테스트
        
        Requirements 12.1을 검증합니다.
        """
        # .out 파일 생성
        file1 = Path(temp_dir) / "statspack1.out"
        file2 = Path(temp_dir) / "statspack2.out"
        file3 = Path(temp_dir) / "other.txt"  # .out이 아닌 파일
        
        file1.write_text(sample_statspack_content)
        file2.write_text(sample_statspack_content)
        file3.write_text("not a statspack file")
        
        analyzer = BatchAnalyzer(temp_dir)
        files = analyzer.find_statspack_files()
        
        # .out 파일만 찾아야 함
        assert len(files) == 2
        assert all(f.suffix == ".out" for f in files)
    
    def test_find_statspack_files_sorted(self, temp_dir, sample_statspack_content):
        """파일 목록이 정렬되는지 테스트
        
        Requirements 12.1을 검증합니다.
        """
        # 파일명이 다른 .out 파일 생성
        file_c = Path(temp_dir) / "c_statspack.out"
        file_a = Path(temp_dir) / "a_statspack.out"
        file_b = Path(temp_dir) / "b_statspack.out"
        
        file_c.write_text(sample_statspack_content)
        file_a.write_text(sample_statspack_content)
        file_b.write_text(sample_statspack_content)
        
        analyzer = BatchAnalyzer(temp_dir)
        files = analyzer.find_statspack_files()
        
        # 파일명으로 정렬되어야 함
        assert len(files) == 3
        assert files[0].name == "a_statspack.out"
        assert files[1].name == "b_statspack.out"
        assert files[2].name == "c_statspack.out"
    
    def test_analyze_batch_empty_directory(self, temp_dir):
        """빈 디렉토리 배치 분석 테스트
        
        Requirements 12.2를 검증합니다.
        """
        analyzer = BatchAnalyzer(temp_dir)
        result = analyzer.analyze_batch()
        
        assert isinstance(result, BatchAnalysisResult)
        assert result.total_files == 0
        assert result.successful_files == 0
        assert result.failed_files == 0
        assert len(result.file_results) == 0
    
    def test_analyze_batch_with_valid_files(self, temp_dir, sample_statspack_content):
        """유효한 파일들로 배치 분석 테스트
        
        Requirements 12.2, 12.5를 검증합니다.
        """
        # 유효한 .out 파일 생성
        file1 = Path(temp_dir) / "statspack1.out"
        file2 = Path(temp_dir) / "statspack2.out"
        
        file1.write_text(sample_statspack_content)
        file2.write_text(sample_statspack_content)
        
        analyzer = BatchAnalyzer(temp_dir)
        result = analyzer.analyze_batch()
        
        # 모든 파일이 성공적으로 파싱되어야 함
        assert result.total_files == 2
        assert result.successful_files == 2
        assert result.failed_files == 0
        assert len(result.file_results) == 2
        
        # 각 파일 결과 확인
        for file_result in result.file_results:
            assert isinstance(file_result, BatchFileResult)
            assert file_result.success is True
            assert file_result.statspack_data is not None
            assert file_result.error_message is None
    
    def test_analyze_batch_with_invalid_file(self, temp_dir, sample_statspack_content):
        """유효하지 않은 파일이 포함된 배치 분석 테스트
        
        Requirements 12.3, 12.4를 검증합니다.
        - 오류 발생 시 건너뛰기
        - 성공/실패 파일 목록 관리
        """
        # 유효한 파일과 유효하지 않은 파일 생성
        valid_file = Path(temp_dir) / "valid.out"
        invalid_file = Path(temp_dir) / "invalid.out"
        
        valid_file.write_text(sample_statspack_content)
        invalid_file.write_text("This is not a valid statspack file")
        
        analyzer = BatchAnalyzer(temp_dir)
        result = analyzer.analyze_batch()
        
        # 하나는 성공, 하나는 실패해야 함
        assert result.total_files == 2
        assert result.successful_files == 1
        assert result.failed_files == 1
        
        # 성공한 파일 확인
        successful_results = [r for r in result.file_results if r.success]
        assert len(successful_results) == 1
        assert successful_results[0].filename == "valid.out"
        assert successful_results[0].statspack_data is not None
        
        # 실패한 파일 확인
        failed_results = [r for r in result.file_results if not r.success]
        assert len(failed_results) == 1
        assert failed_results[0].filename == "invalid.out"
        assert failed_results[0].error_message is not None
        assert failed_results[0].statspack_data is None
    
    def test_analyze_batch_all_files_fail(self, temp_dir):
        """모든 파일이 실패하는 배치 분석 테스트
        
        Requirements 12.3, 12.4를 검증합니다.
        """
        # 유효하지 않은 파일들 생성
        file1 = Path(temp_dir) / "invalid1.out"
        file2 = Path(temp_dir) / "invalid2.out"
        
        file1.write_text("invalid content 1")
        file2.write_text("invalid content 2")
        
        analyzer = BatchAnalyzer(temp_dir)
        result = analyzer.analyze_batch()
        
        # 모든 파일이 실패해야 함
        assert result.total_files == 2
        assert result.successful_files == 0
        assert result.failed_files == 2
        
        # 모든 파일 결과가 실패 상태여야 함
        for file_result in result.file_results:
            assert file_result.success is False
            assert file_result.error_message is not None
    
    def test_analyze_batch_with_migration_analysis(self, temp_dir, sample_statspack_content):
        """마이그레이션 분석 포함 배치 분석 테스트
        
        Requirements 12.2를 검증합니다.
        """
        # 유효한 파일 생성
        file1 = Path(temp_dir) / "statspack1.out"
        file1.write_text(sample_statspack_content)
        
        analyzer = BatchAnalyzer(temp_dir)
        result = analyzer.analyze_batch(analyze_migration=True)
        
        # 마이그레이션 분석 결과가 포함되어야 함
        assert result.successful_files == 1
        successful_result = result.file_results[0]
        assert successful_result.migration_analysis is not None
        assert len(successful_result.migration_analysis) > 0
    
    def test_analyze_batch_with_specific_target(self, temp_dir, sample_statspack_content):
        """특정 타겟 데이터베이스로 배치 분석 테스트
        
        Requirements 12.2를 검증합니다.
        """
        # 유효한 파일 생성
        file1 = Path(temp_dir) / "statspack1.out"
        file1.write_text(sample_statspack_content)
        
        analyzer = BatchAnalyzer(temp_dir)
        result = analyzer.analyze_batch(
            analyze_migration=True,
            target=TargetDatabase.RDS_ORACLE
        )
        
        # 지정한 타겟만 분석되어야 함
        assert result.successful_files == 1
        successful_result = result.file_results[0]
        assert successful_result.migration_analysis is not None
        assert TargetDatabase.RDS_ORACLE in successful_result.migration_analysis
    
    def test_batch_analysis_result_structure(self, temp_dir, sample_statspack_content):
        """BatchAnalysisResult 구조 검증"""
        # 파일 생성
        file1 = Path(temp_dir) / "statspack1.out"
        file1.write_text(sample_statspack_content)
        
        analyzer = BatchAnalyzer(temp_dir)
        result = analyzer.analyze_batch()
        
        # 필수 필드 확인
        assert hasattr(result, 'total_files')
        assert hasattr(result, 'successful_files')
        assert hasattr(result, 'failed_files')
        assert hasattr(result, 'file_results')
        assert hasattr(result, 'analysis_timestamp')
        
        # 타입 확인
        assert isinstance(result.total_files, int)
        assert isinstance(result.successful_files, int)
        assert isinstance(result.failed_files, int)
        assert isinstance(result.file_results, list)
        assert isinstance(result.analysis_timestamp, str)
    
    def test_batch_file_result_structure(self, temp_dir, sample_statspack_content):
        """BatchFileResult 구조 검증"""
        # 파일 생성
        file1 = Path(temp_dir) / "statspack1.out"
        file1.write_text(sample_statspack_content)
        
        analyzer = BatchAnalyzer(temp_dir)
        result = analyzer.analyze_batch()
        
        file_result = result.file_results[0]
        
        # 필수 필드 확인
        assert hasattr(file_result, 'filepath')
        assert hasattr(file_result, 'filename')
        assert hasattr(file_result, 'success')
        assert hasattr(file_result, 'error_message')
        assert hasattr(file_result, 'statspack_data')
        assert hasattr(file_result, 'migration_analysis')
        
        # 타입 확인
        assert isinstance(file_result.filepath, str)
        assert isinstance(file_result.filename, str)
        assert isinstance(file_result.success, bool)
    
    def test_analyze_batch_with_trend_analysis(self, temp_dir, sample_statspack_content):
        """추세 분석 포함 배치 분석 테스트
        
        Requirements 17.1, 17.2를 검증합니다.
        """
        # 여러 파일 생성 (추세 분석을 위해 최소 2개 필요)
        file1 = Path(temp_dir) / "statspack1.out"
        file2 = Path(temp_dir) / "statspack2.out"
        
        file1.write_text(sample_statspack_content)
        file2.write_text(sample_statspack_content)
        
        analyzer = BatchAnalyzer(temp_dir)
        result = analyzer.analyze_batch(analyze_trends=True)
        
        # 추세 분석 결과가 포함되어야 함
        assert result.trend_analysis is not None
        assert isinstance(result.trend_analysis, TrendAnalysisResult)
    
    def test_trend_analysis_with_single_file(self, temp_dir, sample_statspack_content):
        """단일 파일로는 추세 분석이 수행되지 않음을 테스트
        
        Requirements 17.1을 검증합니다.
        """
        # 파일 1개만 생성
        file1 = Path(temp_dir) / "statspack1.out"
        file1.write_text(sample_statspack_content)
        
        analyzer = BatchAnalyzer(temp_dir)
        result = analyzer.analyze_batch(analyze_trends=True)
        
        # 추세 분석 결과가 None이어야 함 (파일이 2개 미만)
        assert result.trend_analysis is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
