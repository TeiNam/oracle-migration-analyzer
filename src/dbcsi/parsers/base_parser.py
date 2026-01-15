"""
기본 파서 모듈

Statspack/AWR 파일의 공통 파싱 로직을 제공합니다.
"""

from typing import List, Optional
from pathlib import Path

from ..exceptions import StatspackParseError, StatspackFileError
from ..logging_config import get_logger

logger = get_logger("parser.base")


class BaseParser:
    """
    기본 파서 클래스
    
    Statspack/AWR 파일의 공통 파싱 로직을 제공합니다.
    섹션 마커(~~BEGIN-{SECTION}~~, ~~END-{SECTION}~~)를 기반으로 파싱합니다.
    """
    
    def __init__(self, filepath: str):
        """
        파서 초기화
        
        Args:
            filepath: 파일 경로 (.out 파일)
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            StatspackFileError: 경로가 디렉토리인 경우
        """
        self.filepath = Path(filepath)
        
        if not self.filepath.exists():
            logger.error(f"File not found: {filepath}")
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if self.filepath.is_dir():
            logger.error(f"Path is a directory, not a file: {filepath}")
            raise StatspackFileError(f"Path is a directory, not a file: {filepath}")
        
        logger.info(f"Initialized {self.__class__.__name__} for file: {filepath}")
    
    def _read_file(self) -> List[str]:
        """
        파일을 읽고 라인 리스트 반환
        
        UTF-8 인코딩을 먼저 시도하고, 실패하면 Latin-1로 폴백합니다.
        
        Returns:
            파일의 각 라인을 담은 리스트
            
        Raises:
            StatspackFileError: 파일 읽기 실패 시
        """
        try:
            logger.debug(f"Attempting to read file with UTF-8 encoding: {self.filepath}")
            with open(self.filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            logger.info(f"Successfully read file with UTF-8 encoding: {len(lines)} lines")
            return lines
        except UnicodeDecodeError:
            logger.warning(f"UTF-8 decoding failed, falling back to Latin-1: {self.filepath}")
            try:
                with open(self.filepath, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
                logger.info(f"Successfully read file with Latin-1 encoding: {len(lines)} lines")
                return lines
            except Exception as e:
                logger.error(f"Failed to read file with both UTF-8 and Latin-1 encoding: {self.filepath}")
                raise StatspackFileError(
                    f"Failed to read file with UTF-8 or Latin-1 encoding: {self.filepath}"
                ) from e
        except PermissionError as e:
            logger.error(f"Permission denied: {self.filepath}")
            raise StatspackFileError(f"Permission denied: {self.filepath}") from e
        except Exception as e:
            logger.error(f"Unexpected error reading file: {self.filepath} - {str(e)}")
            raise StatspackFileError(f"Failed to read file: {self.filepath}") from e
    
    def _extract_section(self, lines: List[str], section_name: str) -> List[str]:
        """
        섹션 마커 사이의 데이터 추출
        
        ~~BEGIN-{section_name}~~와 ~~END-{section_name}~~ 사이의
        데이터를 추출합니다.
        
        Args:
            lines: 파일의 전체 라인 리스트
            section_name: 추출할 섹션 이름 (예: "OS-INFORMATION")
            
        Returns:
            섹션 데이터 라인 리스트 (빈 라인 제거됨)
        """
        begin_marker = f"~~BEGIN-{section_name}~~"
        begin_marker_alt = f"~~BEGIN-{section_name}~"  # 마지막 ~ 하나 빠진 경우
        end_marker = f"~~END-{section_name}~~"
        
        section_lines = []
        in_section = False
        
        for line in lines:
            stripped = line.strip()
            
            if stripped == begin_marker or stripped == begin_marker_alt:
                in_section = True
                continue
            
            if stripped == end_marker:
                in_section = False
                break
            
            if in_section and stripped.startswith("~~BEGIN-"):
                break
            
            if in_section and stripped:
                section_lines.append(line.rstrip('\n\r'))
        
        return section_lines
    
    def _convert_value(self, value: str):
        """
        문자열 값을 적절한 타입으로 변환
        
        Args:
            value: 변환할 문자열 값
            
        Returns:
            변환된 값 (int, float, bool, 또는 str)
        """
        value = value.strip()
        
        if not value:
            return None
        
        if value.upper() in ("YES", "TRUE"):
            return True
        if value.upper() in ("NO", "FALSE"):
            return False
        
        try:
            if '.' not in value:
                return int(value)
        except ValueError:
            pass
        
        try:
            return float(value)
        except ValueError:
            pass
        
        return value
    
    def _parse_os_information(self, lines: List[str]) -> dict:
        """
        OS-INFORMATION 섹션 파싱
        
        Args:
            lines: OS-INFORMATION 섹션의 라인 리스트
            
        Returns:
            파싱된 OS 정보 딕셔너리
        """
        os_info = {}
        data_started = False
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('---'):
                data_started = True
                continue
            
            if not data_started or not stripped:
                continue
            
            parts = stripped.split()
            
            if len(parts) >= 1:
                if len(parts) >= 2 and parts[0] == "COUNT_TABLE" and parts[1] == "PARTITION":
                    continue
                
                stat_name = parts[0]
                stat_value = " ".join(parts[1:]) if len(parts) > 1 else ""
                
                if stat_name == "DB_NAME":
                    converted_value = stat_value.strip()
                else:
                    converted_value = self._convert_value(stat_value)
                os_info[stat_name] = converted_value
        
        return os_info
    
    def _parse_memory(self, lines: List[str]) -> list:
        """MEMORY 섹션 파싱"""
        from ..data_models import MemoryMetric
        
        memory_metrics = []
        data_started = False
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('---'):
                data_started = True
                continue
            
            if not data_started or not stripped:
                continue
            
            parts = stripped.split()
            
            if len(parts) >= 5:
                try:
                    memory_metrics.append(MemoryMetric(
                        snap_id=int(parts[0]),
                        instance_number=int(parts[1]),
                        sga_gb=float(parts[2]),
                        pga_gb=float(parts[3]),
                        total_gb=float(parts[4])
                    ))
                except (ValueError, IndexError):
                    continue
        
        return memory_metrics
    
    def _parse_size_on_disk(self, lines: List[str]) -> list:
        """SIZE-ON-DISK 섹션 파싱"""
        from ..data_models import DiskSize
        
        disk_sizes = []
        data_started = False
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('---'):
                data_started = True
                continue
            
            if not data_started or not stripped:
                continue
            
            parts = stripped.split()
            
            if len(parts) >= 2:
                try:
                    disk_sizes.append(DiskSize(
                        snap_id=int(parts[0]),
                        size_gb=float(parts[1])
                    ))
                except (ValueError, IndexError):
                    continue
        
        return disk_sizes
    
    def _parse_main_metrics(self, lines: List[str]) -> list:
        """MAIN-METRICS 섹션 파싱"""
        from ..data_models import MainMetric
        
        main_metrics = []
        data_started = False
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('---'):
                data_started = True
                continue
            
            if not data_started or not stripped:
                continue
            
            parts = stripped.split()
            
            if len(parts) >= 10:
                try:
                    snap = int(parts[0])
                    dur_m = float(parts[1])
                    
                    try:
                        inst = int(parts[2])
                        end = "unknown"
                        offset = -1
                    except ValueError:
                        try:
                            inst = int(parts[3])
                            end = parts[2]
                            offset = 0
                        except ValueError:
                            end = parts[2] + " " + parts[3]
                            inst = int(parts[4])
                            offset = 1
                    
                    main_metrics.append(MainMetric(
                        snap=snap,
                        dur_m=dur_m,
                        end=end,
                        inst=inst,
                        cpu_per_s=float(parts[4 + offset]),
                        read_iops=float(parts[5 + offset]),
                        read_mb_s=float(parts[6 + offset]),
                        write_iops=float(parts[7 + offset]),
                        write_mb_s=float(parts[8 + offset]),
                        commits_s=float(parts[9 + offset])
                    ))
                except (ValueError, IndexError):
                    continue
        
        return main_metrics
    
    def _parse_wait_events(self, lines: List[str]) -> list:
        """TOP-N-TIMED-EVENTS 섹션 파싱"""
        from ..data_models import WaitEvent
        
        wait_events = []
        data_started = False
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('---'):
                data_started = True
                continue
            
            if not data_started or not stripped:
                continue
            
            parts = stripped.split()
            
            if len(parts) >= 4:
                try:
                    snap_id = int(parts[0])
                    wait_class = parts[1]
                    total_time_s = float(parts[-1])
                    pctdbt = float(parts[-2])
                    event_name = ' '.join(parts[2:-2])
                    
                    wait_events.append(WaitEvent(
                        snap_id=snap_id,
                        wait_class=wait_class,
                        event_name=event_name,
                        pctdbt=pctdbt,
                        total_time_s=total_time_s
                    ))
                except (ValueError, IndexError):
                    continue
        
        return wait_events
    
    def _parse_sysstat(self, lines: List[str]) -> list:
        """SYSSTAT 섹션 파싱"""
        from ..data_models import SystemStat
        
        system_stats = []
        data_started = False
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('---'):
                data_started = True
                continue
            
            if not data_started or not stripped:
                continue
            
            parts = stripped.split()
            
            if len(parts) >= 20:
                try:
                    system_stats.append(SystemStat(
                        snap=int(parts[0]),
                        cell_flash_hits=int(parts[1]),
                        read_iops=float(parts[2]),
                        write_iops=float(parts[3]),
                        read_mb=float(parts[4]),
                        read_mb_opt=float(parts[5]),
                        read_nt_iops=float(parts[6]),
                        write_nt_iops=float(parts[7]),
                        read_nt_mb=float(parts[8]),
                        write_nt_mb=float(parts[9]),
                        cell_int_mb=float(parts[10]),
                        cell_int_ss_mb=float(parts[11]),
                        cell_si_save_mb=float(parts[12]),
                        cell_bytes_elig_mb=float(parts[13]),
                        cell_hcc_bytes_mb=float(parts[14]),
                        read_multi_iops=float(parts[15]),
                        read_temp_iops=float(parts[16]),
                        write_temp_iops=float(parts[17]),
                        network_incoming_mb=float(parts[18]),
                        network_outgoing_mb=float(parts[19])
                    ))
                except (ValueError, IndexError):
                    continue
        
        return system_stats
