"""
Statspack 섹션별 파서 단위 테스트

각 섹션의 파싱 정확성과 엣지 케이스를 검증합니다.
"""

import pytest
from src.dbcsi.parser import StatspackParser
from src.dbcsi.data_models import (
    OSInformation, MemoryMetric, DiskSize, MainMetric,
    WaitEvent, SystemStat, FeatureUsage, SGAAdvice
)
import tempfile
import os


class TestOSInformationParser:
    """OS-INFORMATION 섹션 파서 테스트"""
    
    def test_parse_os_information_basic(self):
        """기본 OS 정보 파싱 테스트"""
        content = """~~BEGIN-OS-INFORMATION~~
STAT_NAME                                                    STAT_VALUE
------------------------------------------------------------ ------------------------------------------------------------
NUM_CPUS                                                     2
PHYSICAL_MEMORY_GB                                           15.35
DB_NAME                                                      ORCL01
BANNER                                                       Oracle Database 19c Standard Edition 2 Release 19.0.0.0.0 - Production
INSTANCES                                                    1
IS_RDS                                                       YES
~~END-OS-INFORMATION~~
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as f:
            f.write(content)
            f.flush()
            
            try:
                parser = StatspackParser(f.name)
                result = parser.parse()
                
                assert result.os_info.num_cpus == 2
                assert result.os_info.physical_memory_gb == 15.35
                assert result.os_info.db_name == "ORCL01"
                assert result.os_info.instances == 1
                assert result.os_info.is_rds == True
            finally:
                os.unlink(f.name)
    
    def test_parse_os_information_type_conversion(self):
        """타입 변환 테스트"""
        content = """~~BEGIN-OS-INFORMATION~~
STAT_NAME                                                    STAT_VALUE
------------------------------------------------------------ ------------------------------------------------------------
NUM_CPUS                                                     4
PHYSICAL_MEMORY_GB                                           32.5
COUNT_LINES_PLSQL                                            6165
IS_RDS                                                       NO
~~END-OS-INFORMATION~~
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as f:
            f.write(content)
            f.flush()
            
            try:
                parser = StatspackParser(f.name)
                result = parser.parse()
                
                assert isinstance(result.os_info.num_cpus, int)
                assert isinstance(result.os_info.physical_memory_gb, float)
                assert isinstance(result.os_info.count_lines_plsql, int)
                assert result.os_info.is_rds == False
            finally:
                os.unlink(f.name)


class TestMemoryParser:
    """MEMORY 섹션 파서 테스트"""
    
    def test_parse_memory_basic(self):
        """기본 메모리 메트릭 파싱 테스트"""
        content = """~~BEGIN-OS-INFORMATION~~
STAT_NAME                                                    STAT_VALUE
------------------------------------------------------------ ------------------------------------------------------------
DB_NAME                                                      TEST
~~END-OS-INFORMATION~~

~~BEGIN-MEMORY~~

   SNAP_ID INSTANCE_NUMBER        SGA        PGA      TOTAL
---------- --------------- ---------- ---------- ----------
         2               1       11.1         .5       11.6
         3               1       11.2         .6       11.8

~~END-MEMORY~~
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as f:
            f.write(content)
            f.flush()
            
            try:
                parser = StatspackParser(f.name)
                result = parser.parse()
                
                assert len(result.memory_metrics) == 2
                assert result.memory_metrics[0].snap_id == 2
                assert result.memory_metrics[0].sga_gb == 11.1
                assert result.memory_metrics[0].pga_gb == 0.5
                assert result.memory_metrics[0].total_gb == 11.6
            finally:
                os.unlink(f.name)


class TestDiskSizeParser:
    """SIZE-ON-DISK 섹션 파서 테스트"""
    
    def test_parse_disk_size_basic(self):
        """기본 디스크 크기 파싱 테스트"""
        content = """~~BEGIN-OS-INFORMATION~~
STAT_NAME                                                    STAT_VALUE
------------------------------------------------------------ ------------------------------------------------------------
DB_NAME                                                      TEST
~~END-OS-INFORMATION~~

~~BEGIN-SIZE-ON-DISK~~

   SNAP_ID    SIZE_GB
---------- ----------
         2          2
         3          2.5

~~END-SIZE-ON-DISK~~
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as f:
            f.write(content)
            f.flush()
            
            try:
                parser = StatspackParser(f.name)
                result = parser.parse()
                
                assert len(result.disk_sizes) == 2
                assert result.disk_sizes[0].snap_id == 2
                assert result.disk_sizes[0].size_gb == 2.0
                assert result.disk_sizes[1].size_gb == 2.5
            finally:
                os.unlink(f.name)


class TestMainMetricsParser:
    """MAIN-METRICS 섹션 파서 테스트"""
    
    def test_parse_main_metrics_basic(self):
        """기본 주요 메트릭 파싱 테스트"""
        content = """~~BEGIN-OS-INFORMATION~~
STAT_NAME                                                    STAT_VALUE
------------------------------------------------------------ ------------------------------------------------------------
DB_NAME                                                      TEST
~~END-OS-INFORMATION~~

~~BEGIN-MAIN-METRICS~~

      snap      dur_m end                  inst  cpu_per_s  read_iops  read_mb_s write_iops write_mb_s  commits_s
---------- ---------- -------------- ---------- ---------- ---------- ---------- ---------- ---------- ----------
         2        8.5 26/01/13 05:43          1  .00629518        4.6         .1        1.2          0          0
         3       16.9 26/01/13 06:00          1  .00559768        4.5         .1        3.3          0          0

~~END-MAIN-METRICS~~
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as f:
            f.write(content)
            f.flush()
            
            try:
                parser = StatspackParser(f.name)
                result = parser.parse()
                
                assert len(result.main_metrics) == 2
                assert result.main_metrics[0].snap == 2
                assert result.main_metrics[0].dur_m == 8.5
                assert result.main_metrics[0].end == "26/01/13 05:43"  # 날짜와 시간 포함
                assert result.main_metrics[0].cpu_per_s == 0.00629518
                assert result.main_metrics[0].read_iops == 4.6
            finally:
                os.unlink(f.name)


class TestWaitEventsParser:
    """TOP-N-TIMED-EVENTS 섹션 파서 테스트"""
    
    def test_parse_wait_events_basic(self):
        """기본 대기 이벤트 파싱 테스트"""
        content = """~~BEGIN-OS-INFORMATION~~
STAT_NAME                                                    STAT_VALUE
------------------------------------------------------------ ------------------------------------------------------------
DB_NAME                                                      TEST
~~END-OS-INFORMATION~~

~~BEGIN-TOP-N-TIMED-EVENTS~~

   SNAP_ID WAIT_CLASS           EVENT_NAME                                                       PCTDBT TOTAL_TIME_S
---------- -------------------- ------------------------------------------------------------ ---------- ------------
         2 System I/O           control file sequential read                                      83.02      1627867
         2 DB CPU               DB CPU                                                            80.35      1575619

~~END-TOP-N-TIMED-EVENTS~~
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as f:
            f.write(content)
            f.flush()
            
            try:
                parser = StatspackParser(f.name)
                result = parser.parse()
                
                assert len(result.wait_events) == 2
                assert result.wait_events[0].snap_id == 2
                assert result.wait_events[0].wait_class == "System"
                assert "control file sequential read" in result.wait_events[0].event_name
                assert result.wait_events[0].pctdbt == 83.02
                assert result.wait_events[0].total_time_s == 1627867
            finally:
                os.unlink(f.name)


class TestSysstatParser:
    """SYSSTAT 섹션 파서 테스트"""
    
    def test_parse_sysstat_basic(self):
        """기본 시스템 통계 파싱 테스트"""
        content = """~~BEGIN-OS-INFORMATION~~
STAT_NAME                                                    STAT_VALUE
------------------------------------------------------------ ------------------------------------------------------------
DB_NAME                                                      TEST
~~END-OS-INFORMATION~~

~~BEGIN-SYSSTAT~~

      SNAP cell_flash_hits  read_iops write_iops    read_mb read_mb_opt read_nt_iops write_nt_iops read_nt_mb write_nt_mb cell_int_mb cell_int_ss_mb cell_si_save_mb cell_bytes_elig_mb cell_hcc_bytes_mb read_multi_iops read_temp_iops write_temp_iops network_incoming_mb network_outgoing_mb
---------- --------------- ---------- ---------- ---------- ----------- ------------ ------------- ---------- ----------- ----------- -------------- --------------- ------------------ ----------------- --------------- -------------- --------------- ------------------- -------------------
         2               0        4.6        1.2         .1           0            0            .1          0           0          .1              0               0                  0                 0              .1              0               0                   0                   0

~~END-SYSSTAT~~
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as f:
            f.write(content)
            f.flush()
            
            try:
                parser = StatspackParser(f.name)
                result = parser.parse()
                
                assert len(result.system_stats) == 1
                assert result.system_stats[0].snap == 2
                assert result.system_stats[0].read_iops == 4.6
                assert result.system_stats[0].write_iops == 1.2
            finally:
                os.unlink(f.name)


class TestFeaturesParser:
    """FEATURES 섹션 파서 테스트"""
    
    def test_parse_features_basic(self):
        """기본 기능 사용 현황 파싱 테스트"""
        content = """~~BEGIN-OS-INFORMATION~~
STAT_NAME                                                    STAT_VALUE
------------------------------------------------------------ ------------------------------------------------------------
DB_NAME                                                      TEST
~~END-OS-INFORMATION~~

~~BEGIN-FEATURES~~

NAME                                                             DETECTED_USAGES TOTAL_SAMPLES CURRE  AUX_COUNT LAST_SAMPLE_DATE     FEATURE_INFO
---------------------------------------------------------------- --------------- ------------- ----- ---------- -------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Partitioning                                                                   1             1 TRUE        8.44 09-JAN-2026          1:T:I::1048575:0:1:::::1::0:ON-0::N:N::0::0::::N

~~END-FEATURES~~
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as f:
            f.write(content)
            f.flush()
            
            try:
                parser = StatspackParser(f.name)
                result = parser.parse()
                
                # Partitioning 기능이 파싱되어야 함
                assert len(result.features) >= 1
                assert result.features[0].name == "Partitioning"
                assert result.features[0].detected_usages == 1
                assert result.features[0].currently_used == True
            finally:
                os.unlink(f.name)


class TestSGAAdviceParser:
    """SGA-ADVICE 섹션 파서 테스트"""
    
    def test_parse_sga_advice_basic(self):
        """기본 SGA 조정 권장사항 파싱 테스트"""
        content = """~~BEGIN-OS-INFORMATION~~
STAT_NAME                                                    STAT_VALUE
------------------------------------------------------------ ------------------------------------------------------------
DB_NAME                                                      TEST
~~END-OS-INFORMATION~~

~~BEGIN-SGA-ADVICE~~

   INST_ID   SGA_SIZE SGA_SIZE_FACTOR ESTD_DB_TIME ESTD_DB_TIME_FACTOR ESTD_PHYSICAL_READS SGA_TARGET
---------- ---------- --------------- ------------ ------------------- ------------------- ----------
         1       2912             .25         1595                   1               39565      11648
         1      11648               1         1595                   1               39565      11648

~~END-SGA-ADVICE~~
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as f:
            f.write(content)
            f.flush()
            
            try:
                parser = StatspackParser(f.name)
                result = parser.parse()
                
                assert len(result.sga_advice) == 2
                assert result.sga_advice[0].inst_id == 1
                assert result.sga_advice[0].sga_size == 2912
                assert result.sga_advice[0].sga_size_factor == 0.25
                assert result.sga_advice[1].sga_size_factor == 1.0
            finally:
                os.unlink(f.name)


class TestEdgeCases:
    """엣지 케이스 테스트"""
    
    def test_empty_sections(self):
        """빈 섹션 처리 테스트"""
        content = """~~BEGIN-OS-INFORMATION~~
STAT_NAME                                                    STAT_VALUE
------------------------------------------------------------ ------------------------------------------------------------
DB_NAME                                                      TEST
~~END-OS-INFORMATION~~

~~BEGIN-MEMORY~~

   SNAP_ID INSTANCE_NUMBER        SGA        PGA      TOTAL
---------- --------------- ---------- ---------- ----------

~~END-MEMORY~~
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as f:
            f.write(content)
            f.flush()
            
            try:
                parser = StatspackParser(f.name)
                result = parser.parse()
                
                # 빈 섹션은 빈 리스트로 반환되어야 함
                assert len(result.memory_metrics) == 0
            finally:
                os.unlink(f.name)
    
    def test_malformed_data_lines(self):
        """잘못된 형식의 데이터 라인 처리 테스트"""
        content = """~~BEGIN-OS-INFORMATION~~
STAT_NAME                                                    STAT_VALUE
------------------------------------------------------------ ------------------------------------------------------------
DB_NAME                                                      TEST
~~END-OS-INFORMATION~~

~~BEGIN-MEMORY~~

   SNAP_ID INSTANCE_NUMBER        SGA        PGA      TOTAL
---------- --------------- ---------- ---------- ----------
         2               1       11.1         .5       11.6
INVALID LINE
         3               1       11.2         .6       11.8

~~END-MEMORY~~
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False) as f:
            f.write(content)
            f.flush()
            
            try:
                parser = StatspackParser(f.name)
                result = parser.parse()
                
                # 잘못된 라인은 건너뛰고 유효한 데이터만 파싱
                assert len(result.memory_metrics) == 2
            finally:
                os.unlink(f.name)
