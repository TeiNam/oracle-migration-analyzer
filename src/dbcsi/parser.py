"""
Statspack 파일 파서 모듈

DBCSI Statspack 결과 파일(.out)을 파싱하여 구조화된 데이터로 변환합니다.
"""

import os
from typing import List, Optional
from pathlib import Path

from .exceptions import StatspackParseError, StatspackFileError
from .logging_config import get_logger

# 로거 초기화
logger = get_logger("parser")


class StatspackParser:
    """
    Statspack 파일 파서
    
    섹션 마커(~~BEGIN-{SECTION}~~, ~~END-{SECTION}~~)를 기반으로
    Statspack 파일을 파싱하여 구조화된 데이터를 추출합니다.
    """
    
    def __init__(self, filepath: str):
        """
        Statspack 파서 초기화
        
        Args:
            filepath: Statspack 파일 경로 (.out 파일)
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
        """
        self.filepath = Path(filepath)
        
        # 파일 존재 확인
        if not self.filepath.exists():
            logger.error(f"File not found: {filepath}")
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # 파일이 디렉토리인지 확인
        if self.filepath.is_dir():
            logger.error(f"Path is a directory, not a file: {filepath}")
            raise StatspackFileError(f"Path is a directory, not a file: {filepath}")
        
        logger.info(f"Initialized StatspackParser for file: {filepath}")
    
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
            # UTF-8 인코딩으로 시도
            logger.debug(f"Attempting to read file with UTF-8 encoding: {self.filepath}")
            with open(self.filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            logger.info(f"Successfully read file with UTF-8 encoding: {len(lines)} lines")
            return lines
        except UnicodeDecodeError:
            # UTF-8 실패 시 Latin-1로 폴백
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
            raise StatspackFileError(
                f"Permission denied: {self.filepath}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error reading file: {self.filepath} - {str(e)}")
            raise StatspackFileError(
                f"Failed to read file: {self.filepath}"
            ) from e
    
    def _extract_section(self, lines: List[str], section_name: str) -> List[str]:
        """
        섹션 마커 사이의 데이터 추출
        
        ~~BEGIN-{section_name}~~와 ~~END-{section_name}~~ 사이의
        데이터를 추출합니다. 마커 라인은 제외하고, 빈 라인과 공백만 있는
        라인도 제거합니다.
        
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
            
            # 시작 마커 확인 (정상 또는 대체 형식)
            if stripped == begin_marker or stripped == begin_marker_alt:
                in_section = True
                continue
            
            # 종료 마커 확인
            if stripped == end_marker:
                in_section = False
                break
            
            # 다른 섹션의 시작 마커를 만나면 현재 섹션 종료
            if in_section and stripped.startswith("~~BEGIN-"):
                break
            
            # 섹션 내부의 데이터 수집
            if in_section:
                # 빈 라인과 공백만 있는 라인 제거
                if stripped:
                    section_lines.append(line.rstrip('\n\r'))
        
        return section_lines
    
    def _parse_os_information(self, lines: List[str]) -> dict:
        """
        OS-INFORMATION 섹션 파싱
        
        STAT_NAME과 STAT_VALUE 쌍을 파싱하여 딕셔너리로 반환합니다.
        숫자 값은 적절한 타입으로 변환하고, 불린 값도 변환합니다.
        
        Args:
            lines: OS-INFORMATION 섹션의 라인 리스트
            
        Returns:
            파싱된 OS 정보 딕셔너리
        """
        os_info = {}
        
        # 헤더 라인 건너뛰기
        data_started = False
        
        for line in lines:
            stripped = line.strip()
            
            # 헤더 구분선 확인
            if stripped.startswith('---'):
                data_started = True
                continue
            
            # 헤더 라인 건너뛰기
            if not data_started:
                continue
            
            # 빈 라인 건너뛰기
            if not stripped:
                continue
            
            # STAT_NAME과 STAT_VALUE 분리 (공백으로 구분)
            parts = stripped.split(None, 1)  # 최대 2개로 분리
            
            if len(parts) >= 1:
                stat_name = parts[0]
                stat_value = parts[1] if len(parts) == 2 else ""
                
                # 타입 변환 시도 (DB_NAME은 항상 문자열로 유지)
                if stat_name == "DB_NAME":
                    converted_value = stat_value.strip()
                else:
                    converted_value = self._convert_value(stat_value)
                os_info[stat_name] = converted_value
        
        return os_info
    
    def _convert_value(self, value: str):
        """
        문자열 값을 적절한 타입으로 변환
        
        Args:
            value: 변환할 문자열 값
            
        Returns:
            변환된 값 (int, float, bool, 또는 str)
        """
        value = value.strip()
        
        # 빈 문자열
        if not value:
            return None
        
        # 불린 값 변환
        if value.upper() == "YES" or value.upper() == "TRUE":
            return True
        if value.upper() == "NO" or value.upper() == "FALSE":
            return False
        
        # 정수 변환 시도
        try:
            # 소수점이 없으면 정수로 변환
            if '.' not in value:
                return int(value)
        except ValueError:
            pass
        
        # 실수 변환 시도
        try:
            return float(value)
        except ValueError:
            pass
        
        # 변환 실패 시 원본 문자열 반환
        return value
    
    def _parse_memory(self, lines: List[str]) -> list:
        """
        MEMORY 섹션 파싱
        
        스냅샷별 메모리 메트릭(SGA, PGA, TOTAL)을 파싱합니다.
        
        Args:
            lines: MEMORY 섹션의 라인 리스트
            
        Returns:
            MemoryMetric 객체 리스트
        """
        from .data_models import MemoryMetric
        
        memory_metrics = []
        data_started = False
        
        for line in lines:
            stripped = line.strip()
            
            # 헤더 구분선 확인
            if stripped.startswith('---'):
                data_started = True
                continue
            
            # 헤더 라인 건너뛰기
            if not data_started:
                continue
            
            # 빈 라인 건너뛰기
            if not stripped:
                continue
            
            # 데이터 라인 파싱
            parts = stripped.split()
            
            if len(parts) >= 5:
                try:
                    snap_id = int(parts[0])
                    instance_number = int(parts[1])
                    sga_gb = float(parts[2])
                    pga_gb = float(parts[3])
                    total_gb = float(parts[4])
                    
                    memory_metrics.append(MemoryMetric(
                        snap_id=snap_id,
                        instance_number=instance_number,
                        sga_gb=sga_gb,
                        pga_gb=pga_gb,
                        total_gb=total_gb
                    ))
                except (ValueError, IndexError):
                    # 파싱 실패 시 해당 라인 건너뛰기
                    continue
        
        return memory_metrics
    
    def _parse_size_on_disk(self, lines: List[str]) -> list:
        """
        SIZE-ON-DISK 섹션 파싱
        
        스냅샷별 디스크 크기를 파싱합니다.
        
        Args:
            lines: SIZE-ON-DISK 섹션의 라인 리스트
            
        Returns:
            DiskSize 객체 리스트
        """
        from .data_models import DiskSize
        
        disk_sizes = []
        data_started = False
        
        for line in lines:
            stripped = line.strip()
            
            # 헤더 구분선 확인
            if stripped.startswith('---'):
                data_started = True
                continue
            
            # 헤더 라인 건너뛰기
            if not data_started:
                continue
            
            # 빈 라인 건너뛰기
            if not stripped:
                continue
            
            # 데이터 라인 파싱
            parts = stripped.split()
            
            if len(parts) >= 2:
                try:
                    snap_id = int(parts[0])
                    size_gb = float(parts[1])
                    
                    disk_sizes.append(DiskSize(
                        snap_id=snap_id,
                        size_gb=size_gb
                    ))
                except (ValueError, IndexError):
                    # 파싱 실패 시 해당 라인 건너뛰기
                    continue
        
        return disk_sizes
    
    def _parse_main_metrics(self, lines: List[str]) -> list:
        """
        MAIN-METRICS 섹션 파싱
        
        스냅샷별 주요 성능 메트릭을 파싱합니다.
        
        Args:
            lines: MAIN-METRICS 섹션의 라인 리스트
            
        Returns:
            MainMetric 객체 리스트
        """
        from .data_models import MainMetric
        
        main_metrics = []
        data_started = False
        
        for line in lines:
            stripped = line.strip()
            
            # 헤더 구분선 확인
            if stripped.startswith('---'):
                data_started = True
                continue
            
            # 헤더 라인 건너뛰기
            if not data_started:
                continue
            
            # 빈 라인 건너뛰기
            if not stripped:
                continue
            
            # 데이터 라인 파싱
            parts = stripped.split()
            
            # 최소 10개 필드 필요 (날짜/시간이 분리될 수 있음)
            if len(parts) >= 10:
                try:
                    snap = int(parts[0])
                    dur_m = float(parts[1])
                    
                    # end 필드는 날짜/시간이 공백으로 분리될 수 있음
                    # 예: "26/01/13 05:43" 또는 "26/01/13"
                    # 네 번째 필드가 숫자가 아니면 날짜/시간이 분리된 것
                    try:
                        # 세 번째 필드가 inst인지 확인
                        inst = int(parts[2])
                        # 날짜만 있는 경우 (inst가 세 번째 필드)
                        # 이 경우는 없을 것으로 예상
                        end = "unknown"
                        offset = -1
                    except ValueError:
                        # 세 번째 필드가 날짜
                        try:
                            # 네 번째 필드가 inst인지 확인
                            inst = int(parts[3])
                            # 날짜만 있는 경우
                            end = parts[2]
                            offset = 0
                        except ValueError:
                            # 네 번째 필드도 숫자가 아니면 날짜와 시간이 분리된 경우
                            end = parts[2] + " " + parts[3]
                            inst = int(parts[4])
                            offset = 1
                    
                    cpu_per_s = float(parts[4 + offset])
                    read_iops = float(parts[5 + offset])
                    read_mb_s = float(parts[6 + offset])
                    write_iops = float(parts[7 + offset])
                    write_mb_s = float(parts[8 + offset])
                    commits_s = float(parts[9 + offset])
                    
                    main_metrics.append(MainMetric(
                        snap=snap,
                        dur_m=dur_m,
                        end=end,
                        inst=inst,
                        cpu_per_s=cpu_per_s,
                        read_iops=read_iops,
                        read_mb_s=read_mb_s,
                        write_iops=write_iops,
                        write_mb_s=write_mb_s,
                        commits_s=commits_s
                    ))
                except (ValueError, IndexError):
                    # 파싱 실패 시 해당 라인 건너뛰기
                    continue
        
        return main_metrics
    
    def _parse_wait_events(self, lines: List[str]) -> list:
        """
        TOP-N-TIMED-EVENTS 섹션 파싱
        
        대기 이벤트 정보를 파싱합니다.
        
        Args:
            lines: TOP-N-TIMED-EVENTS 섹션의 라인 리스트
            
        Returns:
            WaitEvent 객체 리스트
        """
        from .data_models import WaitEvent
        
        wait_events = []
        data_started = False
        
        for line in lines:
            stripped = line.strip()
            
            # 헤더 구분선 확인
            if stripped.startswith('---'):
                data_started = True
                continue
            
            # 헤더 라인 건너뛰기
            if not data_started:
                continue
            
            # 빈 라인 건너뛰기
            if not stripped:
                continue
            
            # 데이터 라인 파싱
            parts = stripped.split()
            
            if len(parts) >= 4:
                try:
                    snap_id = int(parts[0])
                    wait_class = parts[1]
                    
                    # 마지막 두 개는 숫자 (PCTDBT, TOTAL_TIME_S)
                    total_time_s = float(parts[-1])
                    pctdbt = float(parts[-2])
                    
                    # 나머지는 EVENT_NAME (wait_class 다음부터 마지막 두 개 전까지)
                    event_name = ' '.join(parts[2:-2])
                    
                    wait_events.append(WaitEvent(
                        snap_id=snap_id,
                        wait_class=wait_class,
                        event_name=event_name,
                        pctdbt=pctdbt,
                        total_time_s=total_time_s
                    ))
                except (ValueError, IndexError):
                    # 파싱 실패 시 해당 라인 건너뛰기
                    continue
        
        return wait_events
    
    def _parse_sysstat(self, lines: List[str]) -> list:
        """
        SYSSTAT 섹션 파싱
        
        시스템 통계 정보를 파싱합니다.
        
        Args:
            lines: SYSSTAT 섹션의 라인 리스트
            
        Returns:
            SystemStat 객체 리스트
        """
        from .data_models import SystemStat
        
        system_stats = []
        data_started = False
        
        for line in lines:
            stripped = line.strip()
            
            # 헤더 구분선 확인
            if stripped.startswith('---'):
                data_started = True
                continue
            
            # 헤더 라인 건너뛰기
            if not data_started:
                continue
            
            # 빈 라인 건너뛰기
            if not stripped:
                continue
            
            # 데이터 라인 파싱
            parts = stripped.split()
            
            if len(parts) >= 20:
                try:
                    snap = int(parts[0])
                    cell_flash_hits = int(parts[1])
                    read_iops = float(parts[2])
                    write_iops = float(parts[3])
                    read_mb = float(parts[4])
                    read_mb_opt = float(parts[5])
                    read_nt_iops = float(parts[6])
                    write_nt_iops = float(parts[7])
                    read_nt_mb = float(parts[8])
                    write_nt_mb = float(parts[9])
                    cell_int_mb = float(parts[10])
                    cell_int_ss_mb = float(parts[11])
                    cell_si_save_mb = float(parts[12])
                    cell_bytes_elig_mb = float(parts[13])
                    cell_hcc_bytes_mb = float(parts[14])
                    read_multi_iops = float(parts[15])
                    read_temp_iops = float(parts[16])
                    write_temp_iops = float(parts[17])
                    network_incoming_mb = float(parts[18])
                    network_outgoing_mb = float(parts[19])
                    
                    system_stats.append(SystemStat(
                        snap=snap,
                        cell_flash_hits=cell_flash_hits,
                        read_iops=read_iops,
                        write_iops=write_iops,
                        read_mb=read_mb,
                        read_mb_opt=read_mb_opt,
                        read_nt_iops=read_nt_iops,
                        write_nt_iops=write_nt_iops,
                        read_nt_mb=read_nt_mb,
                        write_nt_mb=write_nt_mb,
                        cell_int_mb=cell_int_mb,
                        cell_int_ss_mb=cell_int_ss_mb,
                        cell_si_save_mb=cell_si_save_mb,
                        cell_bytes_elig_mb=cell_bytes_elig_mb,
                        cell_hcc_bytes_mb=cell_hcc_bytes_mb,
                        read_multi_iops=read_multi_iops,
                        read_temp_iops=read_temp_iops,
                        write_temp_iops=write_temp_iops,
                        network_incoming_mb=network_incoming_mb,
                        network_outgoing_mb=network_outgoing_mb
                    ))
                except (ValueError, IndexError):
                    # 파싱 실패 시 해당 라인 건너뛰기
                    continue
        
        return system_stats
    
    def _parse_features(self, lines: List[str]) -> list:
        """
        FEATURES 섹션 파싱
        
        Oracle 기능 사용 현황을 파싱합니다.
        여러 줄에 걸친 FEATURE_INFO도 처리합니다.
        NAME 필드는 고정 폭(64자)으로 되어 있습니다.
        
        Args:
            lines: FEATURES 섹션의 라인 리스트
            
        Returns:
            FeatureUsage 객체 리스트와 Character Set 정보
        """
        from .data_models import FeatureUsage
        
        features = []
        data_started = False
        current_feature = None
        character_set = None
        
        for line in lines:
            stripped = line.strip()
            
            # 헤더 구분선 확인
            if stripped.startswith('---'):
                data_started = True
                continue
            
            # 헤더 라인 건너뛰기
            if not data_started:
                continue
            
            # 빈 라인 건너뛰기
            if not stripped:
                continue
            
            # NAME 필드는 고정 폭 64자
            # 라인 길이가 충분한지 확인
            if len(line) < 65:
                # 짧은 라인은 이전 레코드의 연속으로 간주
                if current_feature and current_feature.feature_info:
                    current_feature.feature_info += " " + stripped
                continue
            
            # NAME 필드 추출 (0-64자)
            name = line[:64].strip()
            
            # 나머지 필드 추출 (65자부터)
            remaining = line[64:].strip()
            parts = remaining.split()
            
            if len(parts) >= 3:
                try:
                    detected_usages = int(parts[0])
                    total_samples = int(parts[1])
                    currently_used = parts[2].upper() == "TRUE"
                    
                    # 새로운 레코드 시작
                    if current_feature:
                        features.append(current_feature)
                    
                    # AUX_COUNT 파싱 (선택적, 숫자일 수도 있고 아닐 수도 있음)
                    aux_count = None
                    last_sample_date = None
                    feature_info = None
                    
                    if len(parts) > 3:
                        try:
                            aux_count = float(parts[3])
                            # AUX_COUNT가 숫자면 다음은 LAST_SAMPLE_DATE
                            if len(parts) > 4:
                                last_sample_date = parts[4]
                            if len(parts) > 5:
                                feature_info = ' '.join(parts[5:])
                        except ValueError:
                            # AUX_COUNT가 숫자가 아니면 LAST_SAMPLE_DATE부터 시작
                            last_sample_date = parts[3]
                            if len(parts) > 4:
                                feature_info = ' '.join(parts[4:])
                    
                    # Character Set 특별 처리
                    if name == "Character Set" and feature_info:
                        character_set = feature_info
                    
                    current_feature = FeatureUsage(
                        name=name,
                        detected_usages=detected_usages,
                        total_samples=total_samples,
                        currently_used=currently_used,
                        aux_count=aux_count,
                        last_sample_date=last_sample_date,
                        feature_info=feature_info
                    )
                    
                except (ValueError, IndexError):
                    # 파싱 실패 시 이전 레코드의 연속으로 간주
                    if current_feature and current_feature.feature_info:
                        current_feature.feature_info += " " + stripped
                    continue
            else:
                # 필드가 부족하면 이전 레코드의 연속으로 간주
                if current_feature and current_feature.feature_info:
                    current_feature.feature_info += " " + stripped
        
        # 마지막 레코드 추가
        if current_feature:
            features.append(current_feature)
        
        return features, character_set
    
    def _parse_sga_advice(self, lines: List[str]) -> list:
        """
        SGA-ADVICE 섹션 파싱
        
        SGA 조정 권장사항을 파싱합니다.
        
        Args:
            lines: SGA-ADVICE 섹션의 라인 리스트
            
        Returns:
            SGAAdvice 객체 리스트
        """
        from .data_models import SGAAdvice
        
        sga_advice = []
        data_started = False
        
        for line in lines:
            stripped = line.strip()
            
            # 헤더 구분선 확인
            if stripped.startswith('---'):
                data_started = True
                continue
            
            # 헤더 라인 건너뛰기
            if not data_started:
                continue
            
            # 빈 라인 건너뛰기
            if not stripped:
                continue
            
            # 데이터 라인 파싱
            parts = stripped.split()
            
            if len(parts) >= 7:
                try:
                    inst_id = int(parts[0])
                    sga_size = int(parts[1])
                    sga_size_factor = float(parts[2])
                    estd_db_time = int(parts[3])
                    estd_db_time_factor = int(parts[4])
                    estd_physical_reads = int(parts[5])
                    sga_target = int(parts[6])
                    
                    sga_advice.append(SGAAdvice(
                        inst_id=inst_id,
                        sga_size=sga_size,
                        sga_size_factor=sga_size_factor,
                        estd_db_time=estd_db_time,
                        estd_db_time_factor=estd_db_time_factor,
                        estd_physical_reads=estd_physical_reads,
                        sga_target=sga_target
                    ))
                except (ValueError, IndexError):
                    # 파싱 실패 시 해당 라인 건너뛰기
                    continue
        
        return sga_advice
    
    def parse(self):
        """
        전체 파일을 파싱하여 StatspackData 반환
        
        Returns:
            StatspackData: 파싱된 Statspack 데이터
            
        Raises:
            StatspackParseError: 파싱 실패 시
        """
        from .data_models import StatspackData, OSInformation
        
        # 파일 읽기
        lines = self._read_file()
        
        # 최소한 하나의 섹션이라도 있는지 확인
        has_section = any(
            line.strip().startswith("~~BEGIN-") 
            for line in lines
        )
        
        if not has_section:
            raise StatspackParseError(
                f"No valid section markers found in file: {self.filepath}"
            )
        
        # OS-INFORMATION 섹션 파싱
        os_info_lines = self._extract_section(lines, "OS-INFORMATION")
        os_info_dict = self._parse_os_information(os_info_lines)
        
        # OSInformation 객체 생성
        os_info = OSInformation(
            statspack_version=os_info_dict.get("STATSPACK_MINER_VER"),
            num_cpus=os_info_dict.get("NUM_CPUS"),
            num_cpu_cores=os_info_dict.get("NUM_CPU_CORES"),
            physical_memory_gb=os_info_dict.get("PHYSICAL_MEMORY_GB"),
            platform_name=os_info_dict.get("PLATFORM_NAME"),
            version=os_info_dict.get("VERSION"),
            db_name=os_info_dict.get("DB_NAME"),
            dbid=os_info_dict.get("DBID"),
            banner=os_info_dict.get("BANNER"),
            instances=os_info_dict.get("INSTANCES"),
            is_rds=os_info_dict.get("IS_RDS"),
            total_db_size_gb=os_info_dict.get("TOTAL_DB_SIZE_GB"),
            count_lines_plsql=os_info_dict.get("COUNT_LINES_PLSQL"),
            count_schemas=os_info_dict.get("COUNT_SCHEMAS"),
            count_tables=os_info_dict.get("COUNT_TABLE"),
            count_packages=os_info_dict.get("COUNT_PACKAGE"),
            count_procedures=os_info_dict.get("COUNT_PROCEDURE"),
            count_functions=os_info_dict.get("COUNT_FUNCTION"),
            character_set=None,  # FEATURES 섹션에서 추출 예정
            raw_data=os_info_dict
        )
        
        # MEMORY 섹션 파싱
        memory_lines = self._extract_section(lines, "MEMORY")
        memory_metrics = self._parse_memory(memory_lines)
        
        # SIZE-ON-DISK 섹션 파싱
        disk_lines = self._extract_section(lines, "SIZE-ON-DISK")
        disk_sizes = self._parse_size_on_disk(disk_lines)
        
        # MAIN-METRICS 섹션 파싱
        main_metrics_lines = self._extract_section(lines, "MAIN-METRICS")
        main_metrics = self._parse_main_metrics(main_metrics_lines)
        
        # TOP-N-TIMED-EVENTS 섹션 파싱
        wait_events_lines = self._extract_section(lines, "TOP-N-TIMED-EVENTS")
        wait_events = self._parse_wait_events(wait_events_lines)
        
        # SYSSTAT 섹션 파싱
        sysstat_lines = self._extract_section(lines, "SYSSTAT")
        system_stats = self._parse_sysstat(sysstat_lines)
        
        # FEATURES 섹션 파싱
        features_lines = self._extract_section(lines, "FEATURES")
        features, character_set = self._parse_features(features_lines)
        
        # Character Set 정보를 OSInformation에 추가
        if character_set:
            os_info.character_set = character_set
        
        # SGA-ADVICE 섹션 파싱
        sga_advice_lines = self._extract_section(lines, "SGA-ADVICE")
        sga_advice = self._parse_sga_advice(sga_advice_lines)
        
        # StatspackData 생성
        statspack_data = StatspackData(
            os_info=os_info,
            memory_metrics=memory_metrics,
            disk_sizes=disk_sizes,
            main_metrics=main_metrics,
            wait_events=wait_events,
            system_stats=system_stats,
            features=features,
            sga_advice=sga_advice
        )
        
        return statspack_data


class AWRParser(StatspackParser):
    """
    AWR 파일 파서 - Statspack 파서를 확장
    
    AWR 특화 섹션(IOSTAT-FUNCTION, PERCENT-CPU, PERCENT-IO, WORKLOAD, BUFFER-CACHE)을
    추가로 파싱하여 더 상세한 성능 분석을 제공합니다.
    """
    
    def __init__(self, filepath: str):
        """
        AWR 파서 초기화
        
        Args:
            filepath: AWR 파일 경로 (.out 파일)
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
        """
        super().__init__(filepath)
        logger.info(f"Initialized AWRParser for file: {filepath}")
    
    def parse(self):
        """
        전체 파일을 파싱하여 AWRData 반환
        
        Returns:
            AWRData: 파싱된 AWR 데이터 (Statspack 데이터 포함)
            
        Raises:
            StatspackParseError: 파싱 실패 시
        """
        from .data_models import AWRData
        
        # 기본 Statspack 섹션 파싱
        statspack_data = super().parse()
        
        # 파일 읽기
        lines = self._read_file()
        
        # AWR 특화 섹션 파싱
        iostat_functions = self._parse_iostat_function(lines)
        percentile_cpu = self._parse_percentile_cpu(lines)
        percentile_io = self._parse_percentile_io(lines)
        workload_profiles = self._parse_workload(lines)
        buffer_cache_stats = self._parse_buffer_cache(lines)
        
        # AWRData 객체 생성
        awr_data = AWRData(
            os_info=statspack_data.os_info,
            memory_metrics=statspack_data.memory_metrics,
            disk_sizes=statspack_data.disk_sizes,
            main_metrics=statspack_data.main_metrics,
            wait_events=statspack_data.wait_events,
            system_stats=statspack_data.system_stats,
            features=statspack_data.features,
            sga_advice=statspack_data.sga_advice,
            iostat_functions=iostat_functions,
            percentile_cpu=percentile_cpu,
            percentile_io=percentile_io,
            workload_profiles=workload_profiles,
            buffer_cache_stats=buffer_cache_stats
        )
        
        logger.info(f"AWR parsing complete. AWR-specific sections found: {awr_data.is_awr()}")
        
        return awr_data
    
    def _parse_iostat_function(self, lines: List[str]) -> List:
        """
        IOSTAT-FUNCTION 섹션 파싱
        
        함수별 I/O 통계를 파싱합니다.
        
        Args:
            lines: 파일의 전체 라인 리스트
            
        Returns:
            IOStatFunction 객체 리스트
        """
        from .data_models import IOStatFunction
        
        section_lines = self._extract_section(lines, "IOSTAT-FUNCTION")
        iostat_functions = []
        data_started = False
        
        for line in section_lines:
            stripped = line.strip()
            
            # 헤더 구분선 확인
            if stripped.startswith('---'):
                data_started = True
                continue
            
            # 헤더 라인 건너뛰기
            if not data_started:
                continue
            
            # 빈 라인 건너뛰기
            if not stripped:
                continue
            
            # 데이터 라인 파싱
            parts = stripped.split()
            
            if len(parts) >= 3:
                try:
                    snap_id = int(parts[0])
                    # FUNCTION_NAME은 여러 단어일 수 있음 (예: "Direct Writes")
                    # 마지막 필드는 megabytes_per_s
                    megabytes_per_s = float(parts[-1])
                    # 나머지는 function_name
                    function_name = ' '.join(parts[1:-1])
                    
                    iostat_functions.append(IOStatFunction(
                        snap_id=snap_id,
                        function_name=function_name,
                        megabytes_per_s=megabytes_per_s
                    ))
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse IOSTAT-FUNCTION line: {stripped} - {e}")
                    continue
        
        logger.info(f"Parsed {len(iostat_functions)} IOSTAT-FUNCTION records")
        return iostat_functions
    
    def _parse_percentile_cpu(self, lines: List[str]) -> dict:
        """
        PERCENT-CPU 섹션 파싱
        
        CPU 백분위수 통계를 파싱합니다.
        
        Args:
            lines: 파일의 전체 라인 리스트
            
        Returns:
            백분위수별 PercentileCPU 객체 딕셔너리 (key: metric name)
        """
        from .data_models import PercentileCPU
        
        section_lines = self._extract_section(lines, "PERCENT-CPU")
        percentile_cpu = {}
        data_started = False
        
        for line in section_lines:
            stripped = line.strip()
            
            # 헤더 구분선 확인
            if stripped.startswith('---'):
                data_started = True
                continue
            
            # 헤더 라인 건너뛰기
            if not data_started:
                continue
            
            # 빈 라인 건너뛰기
            if not stripped:
                continue
            
            # 데이터 라인 파싱
            parts = stripped.split()
            
            # 최소 14개 필드 필요 (날짜와 시간이 분리되어 있음)
            if len(parts) < 14:
                logger.warning(f"Not enough fields in PERCENT-CPU line: {len(parts)} < 14")
                continue
            
            try:
                # DBID는 건너뛰기 (parts[0])
                # ORDER_BY는 건너뛰기 (parts[1])
                metric = parts[2]
                
                # INSTANCE_NUMBER는 선택적 (빈 값일 수 있음)
                # parts[3]이 숫자인지 확인
                try:
                    instance_number = int(parts[3])
                    field_offset = 4  # INSTANCE_NUMBER가 있으면 4번째 인덱스부터 시작
                except ValueError:
                    # INSTANCE_NUMBER가 없으면 parts[3]이 ON_CPU
                    instance_number = None
                    field_offset = 3  # INSTANCE_NUMBER가 없으면 3번째 인덱스부터 시작
                
                # 나머지 필드 파싱
                on_cpu = int(parts[field_offset])
                on_cpu_and_resmgr = int(parts[field_offset + 1])
                resmgr_cpu_quantum = int(parts[field_offset + 2])
                # 날짜와 시간 필드를 합침
                begin_interval = f"{parts[field_offset + 3]} {parts[field_offset + 4]}"
                end_interval = f"{parts[field_offset + 5]} {parts[field_offset + 6]}"
                snap_shots = int(parts[field_offset + 7])
                days = float(parts[field_offset + 8])
                avg_snaps_per_day = float(parts[field_offset + 9])
                
                # 인스턴스별 또는 전체 DB 레벨로 키 생성
                key = f"{metric}_{instance_number}" if instance_number else metric
                
                # 중복 키 처리: 인스턴스별 데이터가 있으면 전체 DB 레벨 데이터는 무시
                if key not in percentile_cpu:
                    percentile_cpu[key] = PercentileCPU(
                        metric=metric,
                        instance_number=instance_number,
                        on_cpu=on_cpu,
                        on_cpu_and_resmgr=on_cpu_and_resmgr,
                        resmgr_cpu_quantum=resmgr_cpu_quantum,
                        begin_interval=begin_interval,
                        end_interval=end_interval,
                        snap_shots=snap_shots,
                        days=days,
                        avg_snaps_per_day=avg_snaps_per_day
                    )
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse PERCENT-CPU line: {stripped} - {e}")
                continue
        
        logger.info(f"Parsed {len(percentile_cpu)} PERCENT-CPU records")
        return percentile_cpu
    
    def _parse_percentile_io(self, lines: List[str]) -> dict:
        """
        PERCENT-IO 섹션 파싱
        
        I/O 백분위수 통계를 파싱합니다.
        
        Args:
            lines: 파일의 전체 라인 리스트
            
        Returns:
            백분위수별 PercentileIO 객체 딕셔너리 (key: metric name)
        """
        from .data_models import PercentileIO
        
        section_lines = self._extract_section(lines, "PERCENT-IO")
        percentile_io = {}
        data_started = False
        
        for line in section_lines:
            stripped = line.strip()
            
            # 헤더 구분선 확인
            if stripped.startswith('---'):
                data_started = True
                continue
            
            # 헤더 라인 건너뛰기
            if not data_started:
                continue
            
            # 빈 라인 건너뛰기
            if not stripped:
                continue
            
            # 데이터 라인 파싱
            parts = stripped.split()
            
            if len(parts) >= 14:
                try:
                    # DBID는 건너뛰기
                    metric = parts[1]
                    
                    # INSTANCE_NUMBER는 선택적 (빈 값일 수 있음)
                    try:
                        instance_number = int(parts[2])
                    except ValueError:
                        instance_number = None
                    
                    rw_iops = int(parts[3])
                    r_iops = int(parts[4])
                    w_iops = int(parts[5])
                    rw_mbps = int(parts[6])
                    r_mbps = int(parts[7])
                    w_mbps = int(parts[8])
                    begin_interval = parts[9]
                    end_interval = parts[10]
                    snap_shots = int(parts[11])
                    days = float(parts[12])
                    avg_snaps_per_day = float(parts[13])
                    
                    # 인스턴스별 또는 전체 DB 레벨로 키 생성
                    key = f"{metric}_{instance_number}" if instance_number else metric
                    
                    # 중복 키 처리: 인스턴스별 데이터가 있으면 전체 DB 레벨 데이터는 무시
                    if key not in percentile_io:
                        percentile_io[key] = PercentileIO(
                            metric=metric,
                            instance_number=instance_number,
                            rw_iops=rw_iops,
                            r_iops=r_iops,
                            w_iops=w_iops,
                            rw_mbps=rw_mbps,
                            r_mbps=r_mbps,
                            w_mbps=w_mbps,
                            begin_interval=begin_interval,
                            end_interval=end_interval,
                            snap_shots=snap_shots,
                            days=days,
                            avg_snaps_per_day=avg_snaps_per_day
                        )
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse PERCENT-IO line: {stripped} - {e}")
                    continue
        
        logger.info(f"Parsed {len(percentile_io)} PERCENT-IO records")
        return percentile_io
    
    def _parse_workload(self, lines: List[str]) -> List:
        """
        WORKLOAD 섹션 파싱
        
        시간대별 워크로드 프로파일을 파싱합니다.
        
        Args:
            lines: 파일의 전체 라인 리스트
            
        Returns:
            WorkloadProfile 객체 리스트
        """
        from .data_models import WorkloadProfile
        
        section_lines = self._extract_section(lines, "WORKLOAD")
        workload_profiles = []
        data_started = False
        
        for line in section_lines:
            stripped = line.strip()
            
            # 헤더 구분선 확인
            if stripped.startswith('---'):
                data_started = True
                continue
            
            # 헤더 라인 건너뛰기
            if not data_started:
                continue
            
            # 빈 라인 건너뛰기
            if not stripped:
                continue
            
            # 데이터 라인 파싱 - 고정 폭 필드 사용
            # 실제 AWR 파일 형식:
            # SAMPLESTART (23자) TOPN (15자) MODULE (64자) PROGRAM (64자) EVENT (64자) + 나머지 숫자 필드들
            
            try:
                # 원본 라인이 충분히 긴지 확인
                if len(line) < 235:
                    logger.warning(f"WORKLOAD line too short: {len(line)} chars")
                    continue
                
                # 고정 위치에서 필드 추출
                sample_start = line[0:23].strip()  # "11-1월 -26 00:00:00"
                topn_str = line[23:39].strip()
                module = line[39:104].strip()
                program = line[104:169].strip()
                event = line[169:234].strip()
                
                # 나머지 숫자 필드들은 공백으로 분리
                remaining = line[234:].strip()
                if not remaining:
                    logger.warning(f"No numeric fields found in WORKLOAD line")
                    continue
                
                parts = remaining.split()
                
                # 최소 14개의 숫자 필드가 필요
                if len(parts) < 14:
                    logger.warning(f"Not enough numeric fields: {len(parts)} < 14")
                    continue
                
                # 숫자 필드 파싱 (순서대로)
                total_dbtime_sum = int(parts[0])
                aas_comp = float(parts[1])
                aas_contribution_pct = float(parts[2])
                tot_contributions = int(parts[3])
                session_type = parts[4]  # 문자열 필드
                wait_class = parts[5] if len(parts) > 5 else ""  # 문자열 필드 (선택적)
                
                # wait_class가 있는 경우와 없는 경우 처리
                if wait_class and not wait_class[0].isdigit():
                    # wait_class가 문자열인 경우
                    offset = 6
                else:
                    # wait_class가 없거나 숫자인 경우
                    wait_class = ""
                    offset = 5
                
                # 나머지 숫자 필드들
                if len(parts) < offset + 10:
                    logger.warning(f"Not enough numeric fields after wait_class: {len(parts)} < {offset + 10}")
                    continue
                
                delta_read_io_requests = int(parts[offset])
                delta_write_io_requests = int(parts[offset + 1])
                delta_read_io_bytes = int(parts[offset + 2])
                delta_write_io_bytes = int(parts[offset + 3])
                rior_pct = float(parts[offset + 4])
                wior_pct = float(parts[offset + 5])
                riob_pct = float(parts[offset + 6])
                wiob_pct = float(parts[offset + 7])
                rior_tot = int(parts[offset + 8])
                wior_tot = int(parts[offset + 9])
                riob_tot = int(parts[offset + 10])
                wiob_tot = int(parts[offset + 11])
                
                topn = int(topn_str)
                
                workload_profiles.append(WorkloadProfile(
                    sample_start=sample_start,
                    topn=topn,
                    module=module,
                    program=program,
                    event=event,
                    total_dbtime_sum=total_dbtime_sum,
                    aas_comp=aas_comp,
                    aas_contribution_pct=aas_contribution_pct,
                    tot_contributions=tot_contributions,
                    session_type=session_type,
                    wait_class=wait_class,
                    delta_read_io_requests=delta_read_io_requests,
                    delta_write_io_requests=delta_write_io_requests,
                    delta_read_io_bytes=delta_read_io_bytes,
                    delta_write_io_bytes=delta_write_io_bytes
                ))
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse WORKLOAD line: {stripped} - {e}")
                continue
        
        logger.info(f"Parsed {len(workload_profiles)} WORKLOAD records")
        return workload_profiles
    
    def _parse_buffer_cache(self, lines: List[str]) -> List:
        """
        BUFFER-CACHE 섹션 파싱
        
        버퍼 캐시 통계를 파싱합니다.
        
        Args:
            lines: 파일의 전체 라인 리스트
            
        Returns:
            BufferCacheStats 객체 리스트
        """
        from .data_models import BufferCacheStats
        
        section_lines = self._extract_section(lines, "BUFFER-CACHE")
        buffer_cache_stats = []
        data_started = False
        
        for line in section_lines:
            stripped = line.strip()
            
            # 헤더 구분선 확인
            if stripped.startswith('---'):
                data_started = True
                continue
            
            # 헤더 라인 건너뛰기
            if not data_started:
                continue
            
            # 빈 라인 건너뛰기
            if not stripped:
                continue
            
            # 데이터 라인 파싱
            parts = stripped.split()
            
            if len(parts) >= 9:
                try:
                    snap_id = int(parts[0])
                    instance_number = int(parts[1])
                    block_size = int(parts[2])
                    db_cache_gb = float(parts[3])
                    dsk_reads = int(parts[4])
                    block_gets = int(parts[5])
                    consistent = int(parts[6])
                    buf_got_gb = float(parts[7])
                    hit_ratio = float(parts[8])
                    
                    buffer_cache_stats.append(BufferCacheStats(
                        snap_id=snap_id,
                        instance_number=instance_number,
                        block_size=block_size,
                        db_cache_gb=db_cache_gb,
                        dsk_reads=dsk_reads,
                        block_gets=block_gets,
                        consistent=consistent,
                        buf_got_gb=buf_got_gb,
                        hit_ratio=hit_ratio
                    ))
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse BUFFER-CACHE line: {stripped} - {e}")
                    continue
        
        logger.info(f"Parsed {len(buffer_cache_stats)} BUFFER-CACHE records")
        return buffer_cache_stats
