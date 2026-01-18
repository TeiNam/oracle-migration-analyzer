"""
Statspack 파서 모듈

DBCSI Statspack 결과 파일(.out)을 파싱하여 구조화된 데이터로 변환합니다.
"""

from typing import List, Optional, Tuple

from .base_parser import BaseParser
from ..exceptions import StatspackParseError
from ..logging_config import get_logger

logger = get_logger("parser.statspack")


class StatspackParser(BaseParser):
    """
    Statspack 파일 파서
    
    섹션 마커(~~BEGIN-{SECTION}~~, ~~END-{SECTION}~~)를 기반으로
    Statspack 파일을 파싱하여 구조화된 데이터를 추출합니다.
    """
    
    def _parse_features(self, lines: List[str]) -> Tuple[list, Optional[str]]:
        """
        FEATURES 섹션 파싱
        
        Oracle 기능 사용 현황을 파싱합니다.
        NAME 필드는 고정 폭(64자)으로 되어 있습니다.
        
        Args:
            lines: FEATURES 섹션의 라인 리스트
            
        Returns:
            (FeatureUsage 객체 리스트, Character Set 정보)
        """
        from ..models import FeatureUsage
        
        features = []
        data_started = False
        current_feature = None
        character_set = None
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('---'):
                data_started = True
                continue
            
            if not data_started or not stripped:
                continue
            
            # NAME 필드는 고정 폭 64자
            if len(line) < 65:
                if current_feature and current_feature.feature_info:
                    current_feature.feature_info += " " + stripped
                continue
            
            name = line[:64].strip()
            remaining = line[64:].strip()
            parts = remaining.split()
            
            if len(parts) >= 3:
                try:
                    detected_usages = int(parts[0])
                    total_samples = int(parts[1])
                    currently_used = parts[2].upper() == "TRUE"
                    
                    if current_feature:
                        features.append(current_feature)
                    
                    aux_count = None
                    last_sample_date = None
                    feature_info = None
                    
                    if len(parts) > 3:
                        try:
                            aux_count = float(parts[3])
                            if len(parts) > 4:
                                date_parts = []
                                info_start_idx = 4
                                
                                for i in range(4, min(len(parts), 7)):
                                    part = parts[i]
                                    is_date_part = (
                                        part[0].isdigit() or
                                        part.startswith('-') or
                                        any('\uac00' <= c <= '\ud7a3' for c in part)
                                    )
                                    
                                    if is_date_part and not part.isupper():
                                        date_parts.append(part)
                                        info_start_idx = i + 1
                                    else:
                                        break
                                
                                if date_parts:
                                    last_sample_date = ' '.join(date_parts)
                                    if info_start_idx < len(parts):
                                        feature_info = ' '.join(parts[info_start_idx:])
                                else:
                                    last_sample_date = parts[4]
                                    if len(parts) > 5:
                                        feature_info = ' '.join(parts[5:])
                        except ValueError:
                            date_parts = []
                            info_start_idx = 3
                            
                            for i in range(3, min(len(parts), 6)):
                                part = parts[i]
                                is_date_part = (
                                    part[0].isdigit() or
                                    part.startswith('-') or
                                    any('\uac00' <= c <= '\ud7a3' for c in part)
                                )
                                
                                if is_date_part and not part.isupper():
                                    date_parts.append(part)
                                    info_start_idx = i + 1
                                else:
                                    break
                            
                            if date_parts:
                                last_sample_date = ' '.join(date_parts)
                                if info_start_idx < len(parts):
                                    feature_info = ' '.join(parts[info_start_idx:])
                            else:
                                last_sample_date = parts[3]
                                if len(parts) > 4:
                                    feature_info = ' '.join(parts[4:])
                    
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
                    if current_feature and current_feature.feature_info:
                        current_feature.feature_info += " " + stripped
                    continue
            else:
                if current_feature and current_feature.feature_info:
                    current_feature.feature_info += " " + stripped
        
        if current_feature:
            features.append(current_feature)
        
        return features, character_set
    
    def _parse_sga_advice(self, lines: List[str]) -> list:
        """SGA-ADVICE 섹션 파싱"""
        from ..models import SGAAdvice
        
        sga_advice = []
        data_started = False
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('---'):
                data_started = True
                continue
            
            if not data_started or not stripped:
                continue
            
            parts = stripped.split()
            
            if len(parts) >= 7:
                try:
                    sga_advice.append(SGAAdvice(
                        inst_id=int(parts[0]),
                        sga_size=int(parts[1]),
                        sga_size_factor=float(parts[2]),
                        estd_db_time=int(parts[3]),
                        estd_db_time_factor=int(parts[4]),
                        estd_physical_reads=int(parts[5]),
                        sga_target=int(parts[6])
                    ))
                except (ValueError, IndexError):
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
        from ..models import StatspackData, OSInformation
        
        lines = self._read_file()
        
        has_section = any(
            line.strip().startswith("~~BEGIN-") 
            for line in lines
        )
        
        if not has_section:
            raise StatspackParseError(
                f"No valid section markers found in file: {self.filepath}"
            )
        
        # 각 섹션 파싱
        os_info_lines = self._extract_section(lines, "OS-INFORMATION")
        os_info_dict = self._parse_os_information(os_info_lines)
        
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
            character_set=None,
            raw_data=os_info_dict
        )
        
        memory_lines = self._extract_section(lines, "MEMORY")
        memory_metrics = self._parse_memory(memory_lines)
        
        disk_lines = self._extract_section(lines, "SIZE-ON-DISK")
        disk_sizes = self._parse_size_on_disk(disk_lines)
        
        main_metrics_lines = self._extract_section(lines, "MAIN-METRICS")
        main_metrics = self._parse_main_metrics(main_metrics_lines)
        
        wait_events_lines = self._extract_section(lines, "TOP-N-TIMED-EVENTS")
        wait_events = self._parse_wait_events(wait_events_lines)
        
        sysstat_lines = self._extract_section(lines, "SYSSTAT")
        system_stats = self._parse_sysstat(sysstat_lines)
        
        features_lines = self._extract_section(lines, "FEATURES")
        features, character_set = self._parse_features(features_lines)
        
        if character_set:
            os_info.character_set = character_set
        
        sga_advice_lines = self._extract_section(lines, "SGA-ADVICE")
        sga_advice = self._parse_sga_advice(sga_advice_lines)
        
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
        
        logger.info(f"Statspack parsing complete for: {self.filepath}")
        return statspack_data
