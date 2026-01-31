"""
Markdown 리포트 파서

DBCSI 및 SQL 복잡도 분석 MD 리포트를 파싱합니다.
"""

import re
import logging
from typing import List, Optional, Dict, Any, Tuple

from ...oracle_complexity_analyzer.data_models import SQLAnalysisResult, PLSQLAnalysisResult
from ...oracle_complexity_analyzer.enums import TargetDatabase, ComplexityLevel, PLSQLObjectType
from .utils import parse_number_with_comma

logger = logging.getLogger(__name__)


class MarkdownReportParser:
    """Markdown 리포트 파서
    
    DBCSI 및 SQL 복잡도 분석 MD 리포트를 파싱합니다.
    """
    
    def parse_dbcsi_markdown(self, report_path: str) -> Optional[Dict[str, Any]]:
        """DBCSI MD 리포트에서 필요한 메트릭을 추출합니다."""
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metrics: Dict[str, Any] = {}
            
            # 리포트 타입 감지
            if 'AWR 분석 보고서' in content or 'AWR Analysis Report' in content:
                metrics['report_type'] = 'awr'
            else:
                metrics['report_type'] = 'statspack'
            
            # 데이터베이스 기본 정보 추출
            metrics['db_name'] = self._extract_table_value(content, '데이터베이스 이름')
            metrics['db_version'] = self._extract_table_value(content, 'Oracle 버전')
            metrics['platform_name'] = self._extract_table_value(content, '플랫폼')
            metrics['character_set'] = self._extract_table_value(content, '문자셋')
            
            # 인스턴스 수 추출
            instance_str = self._extract_table_value(content, '인스턴스 수')
            if instance_str:
                match = re.search(r'(\d+)', instance_str)
                metrics['instance_count'] = int(match.group(1)) if match else 1
            else:
                metrics['instance_count'] = 1
            
            metrics['is_rac'] = metrics['instance_count'] > 1
            metrics['rac_detected'] = metrics['is_rac']
            
            # 크기 및 리소스 정보 추출
            db_size_str = self._extract_table_value(content, '전체 DB 크기')
            if db_size_str:
                metrics['total_db_size_gb'] = parse_number_with_comma(db_size_str)
            
            memory_str = self._extract_table_value(content, '물리 메모리')
            if memory_str:
                metrics['physical_memory_gb'] = parse_number_with_comma(memory_str)
            
            cpu_cores_str = self._extract_table_value(content, 'CPU 코어 수')
            if cpu_cores_str:
                parsed = parse_number_with_comma(cpu_cores_str)
                metrics['cpu_cores'] = int(parsed) if parsed else None
            
            cpu_str = self._extract_table_value(content, 'CPU 수')
            if cpu_str:
                parsed = parse_number_with_comma(cpu_str)
                metrics['num_cpus'] = int(parsed) if parsed else None
            
            # PL/SQL 통계 추출
            metrics['awr_plsql_lines'] = self._extract_plsql_lines(content)
            metrics['awr_package_count'] = self._extract_object_count(content, '패키지')
            metrics['awr_procedure_count'] = self._extract_object_count(content, '프로시저')
            metrics['awr_function_count'] = self._extract_object_count(content, '함수')
            
            # 스키마 오브젝트 통계 추출
            metrics['count_schemas'] = self._extract_schema_object_count(content, '스키마')
            metrics['count_tables'] = self._extract_schema_object_count(content, '테이블')
            metrics['count_views'] = self._extract_schema_object_count(content, '뷰')
            metrics['count_indexes'] = self._extract_schema_object_count(content, '인덱스')
            
            # 성능 메트릭 파싱
            metrics['avg_cpu_usage'] = self._extract_cpu_usage(content)
            metrics['avg_io_load'] = self._extract_io_load(content)
            metrics['avg_memory_usage'] = self._extract_memory_usage(content)
            
            # 피크 메트릭 파싱
            metrics['peak_cpu_usage'] = self._extract_peak_cpu(content)
            metrics['peak_io_load'] = self._extract_peak_io(content)
            metrics['peak_memory_usage'] = self._extract_peak_memory(content)
            
            # SGA 권장사항 파싱
            sga_advice = self._extract_sga_advice(content)
            metrics['current_sga_gb'] = sga_advice.get('current_sga_gb')
            metrics['recommended_sga_gb'] = sga_advice.get('recommended_sga_gb')
            
            logger.info(f"DBCSI MD 파싱 완료: {metrics.get('db_name')} ({metrics.get('report_type')})")
            return metrics
            
        except Exception as e:
            logger.error(f"DBCSI MD 파싱 실패 ({report_path}): {e}", exc_info=True)
            return None
    
    def _extract_table_value(self, content: str, key: str) -> Optional[str]:
        """마크다운 테이블에서 키에 해당하는 값 추출"""
        pattern = rf'\|\s*{re.escape(key)}\s*\|\s*([^|]+)\s*\|'
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_plsql_lines(self, content: str) -> Optional[int]:
        """총 PL/SQL 라인 수 추출"""
        pattern = r'총 PL/SQL 라인 수[^|]*\|\s*\*?\*?([\d,]+)\*?\*?'
        match = re.search(pattern, content)
        if match:
            return int(match.group(1).replace(',', ''))
        return None
    
    def _extract_object_count(self, content: str, object_type: str) -> Optional[int]:
        """오브젝트 타입별 개수 추출"""
        pattern = rf'\|\s*{re.escape(object_type)}\s*\|\s*(\d+)\s*\|'
        match = re.search(pattern, content)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_schema_object_count(self, content: str, object_type: str) -> Optional[int]:
        """스키마 오브젝트 개수 추출"""
        pattern = rf'\|\s*{re.escape(object_type)}\s*\|\s*([\d,]+)\s*\|'
        match = re.search(pattern, content)
        if match:
            return int(match.group(1).replace(',', ''))
        return None
    
    def _extract_cpu_usage(self, content: str) -> float:
        """평균 CPU 사용량 추출"""
        patterns = [
            r'\|\s*평균 CPU/s\s*\|\s*([\d,]+\.?\d*)\s*\|',
            r'\|\s*Average CPU/s\s*\|\s*([\d,]+\.?\d*)\s*\|',
            r'평균 CPU 사용률[^:]*:\s*([\d,]+\.?\d*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', ''))
        return 0.0
    
    def _extract_peak_cpu(self, content: str) -> float:
        """피크 CPU 사용량 추출"""
        patterns = [
            r'\|\s*최대 CPU/s\s*\|\s*([\d,]+\.?\d*)\s*\|',
            r'\|\s*Max(?:imum)? CPU/s\s*\|\s*([\d,]+\.?\d*)\s*\|',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', ''))
        return 0.0
    
    def _extract_io_load(self, content: str) -> float:
        """평균 I/O 부하 추출 (IOPS)"""
        patterns = [
            r'\|\s*평균 IOPS\s*\|\s*[\d,]+\.?\d*\s*\|\s*[\d,]+\.?\d*\s*\|\s*([\d,]+\.?\d*)\s*\|',
            r'\|\s*Average IOPS\s*\|\s*[\d,]+\.?\d*\s*\|\s*[\d,]+\.?\d*\s*\|\s*([\d,]+\.?\d*)\s*\|',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', ''))
        return 0.0
    
    def _extract_peak_io(self, content: str) -> float:
        """피크 I/O 부하 추출 (IOPS)"""
        patterns = [
            r'\|\s*최대 IOPS\s*\|\s*[\d,]+\.?\d*\s*\|\s*[\d,]+\.?\d*\s*\|\s*([\d,]+\.?\d*)\s*\|',
            r'\|\s*Max(?:imum)? IOPS\s*\|\s*[\d,]+\.?\d*\s*\|\s*[\d,]+\.?\d*\s*\|\s*([\d,]+\.?\d*)\s*\|',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', ''))
        return 0.0
    
    def _extract_memory_usage(self, content: str) -> float:
        """평균 메모리 사용량 추출 (GB)"""
        patterns = [
            r'\*\*평균 메모리 사용량\*\*:\s*([\d,]+\.?\d*)\s*GB',
            r'\*\*Average Memory Usage\*\*:\s*([\d,]+\.?\d*)\s*GB',
            r'평균 메모리 사용량[^:]*:\s*([\d,]+\.?\d*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', ''))
        return 0.0
    
    def _extract_peak_memory(self, content: str) -> float:
        """피크 메모리 사용량 추출 (GB)"""
        patterns = [
            r'\*\*최소/최대\*\*:\s*[\d,]+\.?\d*\s*GB\s*/\s*([\d,]+\.?\d*)\s*GB',
            r'\*\*Min/Max\*\*:\s*[\d,]+\.?\d*\s*GB\s*/\s*([\d,]+\.?\d*)\s*GB',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', ''))
        return 0.0
    
    def _extract_sga_advice(self, content: str) -> Dict[str, Any]:
        """SGA 권장사항 추출"""
        result: Dict[str, Any] = {
            'current_sga_mb': None,
            'recommended_sga_mb': None,
            'current_sga_gb': None,
            'recommended_sga_gb': None
        }
        
        current_patterns = [
            r'\|\s*현재 SGA 크기\s*\|\s*([\d,]+)\s*MB',
            r'현재 SGA 크기[^|]*\|\s*([\d,]+)\s*MB',
        ]
        for pattern in current_patterns:
            match = re.search(pattern, content)
            if match:
                current_mb = int(match.group(1).replace(',', ''))
                result['current_sga_mb'] = current_mb
                result['current_sga_gb'] = current_mb / 1024.0
                break
        
        recommended_patterns = [
            r'\|\s*\*?\*?권장 SGA 크기\*?\*?\s*\|\s*\*?\*?([\d,]+)\s*MB\*?\*?',
            r'권장 SGA 크기[^|]*\|\s*\*?\*?([\d,]+)\s*MB',
        ]
        for pattern in recommended_patterns:
            match = re.search(pattern, content)
            if match:
                recommended_mb = int(match.group(1).replace(',', ''))
                result['recommended_sga_mb'] = recommended_mb
                result['recommended_sga_gb'] = recommended_mb / 1024.0
                break
        
        # RAC 환경에서 여러 인스턴스의 권장 SGA 중 최대값 찾기
        instance_pattern = r'###\s*인스턴스\s*\d+.*?(?=###\s*인스턴스|\Z)'
        instance_matches = re.findall(instance_pattern, content, re.DOTALL)
        
        if len(instance_matches) > 1:
            max_recommended_mb = 0
            max_current_mb = 0
            
            for instance_content in instance_matches:
                for pattern in recommended_patterns:
                    match = re.search(pattern, instance_content)
                    if match:
                        rec_mb = int(match.group(1).replace(',', ''))
                        if rec_mb > max_recommended_mb:
                            max_recommended_mb = rec_mb
                        break
                
                for pattern in current_patterns:
                    match = re.search(pattern, instance_content)
                    if match:
                        cur_mb = int(match.group(1).replace(',', ''))
                        if cur_mb > max_current_mb:
                            max_current_mb = cur_mb
                        break
            
            if max_recommended_mb > 0:
                result['recommended_sga_mb'] = max_recommended_mb
                result['recommended_sga_gb'] = max_recommended_mb / 1024.0
            if max_current_mb > 0:
                result['current_sga_mb'] = max_current_mb
                result['current_sga_gb'] = max_current_mb / 1024.0
        
        return result
    
    def extract_oracle_features_summary(self, content: str) -> List[str]:
        """전체 리포트에서 감지된 Oracle 특화 기능 목록 추출"""
        features: List[str] = []
        
        pattern = r'## 감지된 Oracle 특화 기능\s*\n((?:- [^\n]+\n?)+)'
        match = re.search(pattern, content)
        if match:
            features_text = match.group(1)
            for line in features_text.strip().split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    features.append(line[2:].strip())
        
        return features
    
    def extract_external_dependencies_summary(self, content: str) -> List[str]:
        """전체 리포트에서 감지된 외부 의존성 목록 추출"""
        dependencies: List[str] = []
        
        pattern = r'## 감지된 외부 의존성\s*\n((?:- [^\n]+\n?)+)'
        match = re.search(pattern, content)
        if match:
            deps_text = match.group(1)
            for line in deps_text.strip().split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    dependencies.append(line[2:].strip())
        
        return dependencies
    
    def extract_conversion_guide(self, content: str) -> Dict[str, str]:
        """전체 리포트에서 변환 가이드 테이블 추출"""
        guide: Dict[str, str] = {}
        
        pattern = r'## 변환 가이드\s*\n\n?\|[^\n]+\|\s*\n\|[-|]+\|\s*\n((?:\|[^\n]+\|\s*\n?)+)'
        match = re.search(pattern, content)
        if match:
            table_rows = match.group(1)
            for line in table_rows.strip().split('\n'):
                row_match = re.match(r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|', line)
                if row_match:
                    oracle_feature = row_match.group(1).strip()
                    replacement = row_match.group(2).strip()
                    if oracle_feature and replacement:
                        guide[oracle_feature] = replacement
        
        return guide
