"""
리포트 파서

기존에 생성된 DBCSI 및 SQL 복잡도 분석 리포트(MD/JSON)를 파싱하여
마이그레이션 추천에 필요한 데이터를 추출합니다.

MD 파일 파싱을 우선하고, JSON은 폴백으로 사용합니다.
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from ..oracle_complexity_analyzer.data_models import SQLAnalysisResult, PLSQLAnalysisResult
from ..oracle_complexity_analyzer.enums import TargetDatabase, ComplexityLevel, PLSQLObjectType

logger = logging.getLogger(__name__)


class MarkdownReportParser:
    """Markdown 리포트 파서
    
    DBCSI 및 SQL 복잡도 분석 MD 리포트를 파싱합니다.
    """
    
    def parse_dbcsi_markdown(self, report_path: str) -> Optional[Dict[str, Any]]:
        """
        DBCSI MD 리포트에서 필요한 메트릭을 추출합니다.
        
        Args:
            report_path: DBCSI 리포트 파일 경로 (.md)
            
        Returns:
            메트릭 딕셔너리 또는 None
        """
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metrics: Dict[str, Any] = {}
            
            # 리포트 타입 감지 (AWR vs Statspack)
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
                match = re.search(r'([\d.]+)', db_size_str)
                metrics['total_db_size_gb'] = float(match.group(1)) if match else None
            
            memory_str = self._extract_table_value(content, '물리 메모리')
            if memory_str:
                match = re.search(r'([\d.]+)', memory_str)
                metrics['physical_memory_gb'] = float(match.group(1)) if match else None
            
            cpu_cores_str = self._extract_table_value(content, 'CPU 코어 수')
            if cpu_cores_str:
                match = re.search(r'(\d+)', cpu_cores_str)
                metrics['cpu_cores'] = int(match.group(1)) if match else None
            
            cpu_str = self._extract_table_value(content, 'CPU 수')
            if cpu_str:
                match = re.search(r'(\d+)', cpu_str)
                metrics['num_cpus'] = int(match.group(1)) if match else None
            
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
            
            logger.info(f"DBCSI MD 파싱 완료: {metrics.get('db_name')} ({metrics.get('report_type')})")
            return metrics
            
        except Exception as e:
            logger.error(f"DBCSI MD 파싱 실패 ({report_path}): {e}", exc_info=True)
            return None
    
    def _extract_table_value(self, content: str, key: str) -> Optional[str]:
        """마크다운 테이블에서 키에 해당하는 값 추출"""
        # | 키 | 값 | 형식
        pattern = rf'\|\s*{re.escape(key)}\s*\|\s*([^|]+)\s*\|'
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_plsql_lines(self, content: str) -> Optional[int]:
        """총 PL/SQL 라인 수 추출"""
        # **총 PL/SQL 라인 수** | **62,450** 형식
        pattern = r'총 PL/SQL 라인 수[^|]*\|\s*\*?\*?([\d,]+)\*?\*?'
        match = re.search(pattern, content)
        if match:
            return int(match.group(1).replace(',', ''))
        return None
    
    def _extract_object_count(self, content: str, object_type: str) -> Optional[int]:
        """오브젝트 타입별 개수 추출"""
        # | 패키지 | 318 | 형식
        pattern = rf'\|\s*{re.escape(object_type)}\s*\|\s*(\d+)\s*\|'
        match = re.search(pattern, content)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_schema_object_count(self, content: str, object_type: str) -> Optional[int]:
        """스키마 오브젝트 개수 추출 (스키마, 테이블, 뷰, 인덱스 등)
        
        스키마 오브젝트 테이블 형식:
        | 스키마 | 25 | SCT 자동 변환 | ... |
        | 테이블 | 680 | SCT 자동 변환 | ... |
        """
        # | 오브젝트 유형 | 개수 | 변환 방법 | 설명 | 형식
        pattern = rf'\|\s*{re.escape(object_type)}\s*\|\s*([\d,]+)\s*\|'
        match = re.search(pattern, content)
        if match:
            return int(match.group(1).replace(',', ''))
        return None
    
    def _extract_cpu_usage(self, content: str) -> float:
        """평균 CPU 사용량 추출
        
        형식: | 평균 CPU/s | 53.07 | 일반적인 부하 상태 |
        """
        patterns = [
            r'\|\s*평균 CPU/s\s*\|\s*([\d.]+)\s*\|',
            r'\|\s*Average CPU/s\s*\|\s*([\d.]+)\s*\|',
            r'평균 CPU 사용률[^:]*:\s*([\d.]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 0.0
    
    def _extract_peak_cpu(self, content: str) -> float:
        """피크 CPU 사용량 추출
        
        형식: | 최대 CPU/s | 58.20 | 가장 바쁜 시점 (피크) |
        """
        patterns = [
            r'\|\s*최대 CPU/s\s*\|\s*([\d.]+)\s*\|',
            r'\|\s*Max(?:imum)? CPU/s\s*\|\s*([\d.]+)\s*\|',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 0.0
    
    def _extract_io_load(self, content: str) -> float:
        """평균 I/O 부하 추출 (IOPS)
        
        형식: | 평균 IOPS | 78 | 16 | 93 | 일반적인 디스크 사용량 |
        """
        patterns = [
            # 합계 IOPS 추출 (읽기 + 쓰기)
            r'\|\s*평균 IOPS\s*\|\s*[\d.]+\s*\|\s*[\d.]+\s*\|\s*([\d.]+)\s*\|',
            r'\|\s*Average IOPS\s*\|\s*[\d.]+\s*\|\s*[\d.]+\s*\|\s*([\d.]+)\s*\|',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 0.0
    
    def _extract_peak_io(self, content: str) -> float:
        """피크 I/O 부하 추출 (IOPS)
        
        형식: | 최대 IOPS | 82 | 18 | 101 | 피크 시 디스크 사용량 |
        """
        patterns = [
            r'\|\s*최대 IOPS\s*\|\s*[\d.]+\s*\|\s*[\d.]+\s*\|\s*([\d.]+)\s*\|',
            r'\|\s*Max(?:imum)? IOPS\s*\|\s*[\d.]+\s*\|\s*[\d.]+\s*\|\s*([\d.]+)\s*\|',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 0.0
    
    def _extract_memory_usage(self, content: str) -> float:
        """평균 메모리 사용량 추출 (GB)
        
        형식: - **평균 메모리 사용량**: 48.06 GB (SGA: 45.20 GB, PGA: 2.86 GB)
        """
        patterns = [
            r'\*\*평균 메모리 사용량\*\*:\s*([\d.]+)\s*GB',
            r'\*\*Average Memory Usage\*\*:\s*([\d.]+)\s*GB',
            r'평균 메모리 사용량[^:]*:\s*([\d.]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 0.0
    
    def _extract_peak_memory(self, content: str) -> float:
        """피크 메모리 사용량 추출 (GB)
        
        형식: - **최소/최대**: 48.00 GB / 48.10 GB
        """
        patterns = [
            r'\*\*최소/최대\*\*:\s*[\d.]+\s*GB\s*/\s*([\d.]+)\s*GB',
            r'\*\*Min/Max\*\*:\s*[\d.]+\s*GB\s*/\s*([\d.]+)\s*GB',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 0.0
    
    def extract_oracle_features_summary(self, content: str) -> List[str]:
        """전체 리포트에서 감지된 Oracle 특화 기능 목록 추출
        
        형식:
        ## 감지된 Oracle 특화 기능
        
        - NESTED TABLE
        - OBJECT TYPE
        - VARRAY
        """
        features: List[str] = []
        
        # 섹션 찾기
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
        """전체 리포트에서 감지된 외부 의존성 목록 추출
        
        형식:
        ## 감지된 외부 의존성
        
        - DBMS_OUTPUT
        """
        dependencies: List[str] = []
        
        # 섹션 찾기
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
        """전체 리포트에서 변환 가이드 테이블 추출
        
        형식:
        ## 변환 가이드
        
        | Oracle 기능 | 대체 방법 |
        |------------|----------|
        | DBMS_OUTPUT | RAISE NOTICE |
        | NESTED TABLE | ARRAY 또는 별도 테이블 |
        """
        guide: Dict[str, str] = {}
        
        # 변환 가이드 테이블 찾기
        pattern = r'## 변환 가이드\s*\n\n?\|[^\n]+\|\s*\n\|[-|]+\|\s*\n((?:\|[^\n]+\|\s*\n?)+)'
        match = re.search(pattern, content)
        if match:
            table_rows = match.group(1)
            for line in table_rows.strip().split('\n'):
                # | Oracle 기능 | 대체 방법 | 형식 파싱
                row_match = re.match(r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|', line)
                if row_match:
                    oracle_feature = row_match.group(1).strip()
                    replacement = row_match.group(2).strip()
                    if oracle_feature and replacement:
                        guide[oracle_feature] = replacement
        
        return guide
    
    def parse_plsql_complexity_markdown_with_summary(
        self,
        report_path: str,
        target_db: str = "postgresql"
    ) -> Tuple[List[SQLAnalysisResult], List[PLSQLAnalysisResult], Dict[str, Any]]:
        """
        PL/SQL 복잡도 MD 리포트를 파싱하고 요약 정보도 반환합니다.
        
        Args:
            report_path: 리포트 파일 경로 (.md)
            target_db: 타겟 데이터베이스
            
        Returns:
            (sql_results, plsql_results, summary) 튜플
            summary에는 oracle_features, external_dependencies, conversion_guide 포함
        """
        sql_results, plsql_results = self.parse_plsql_complexity_markdown(
            report_path, target_db
        )
        
        summary: Dict[str, Any] = {
            'oracle_features': [],
            'external_dependencies': [],
            'conversion_guide': {}
        }
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            summary['oracle_features'] = self.extract_oracle_features_summary(content)
            summary['external_dependencies'] = self.extract_external_dependencies_summary(content)
            summary['conversion_guide'] = self.extract_conversion_guide(content)
            
        except Exception as e:
            logger.warning(f"요약 정보 추출 실패 ({report_path}): {e}")
        
        return sql_results, plsql_results, summary

    def parse_plsql_complexity_markdown(
        self,
        report_path: str,
        target_db: str = "postgresql"
    ) -> Tuple[List[SQLAnalysisResult], List[PLSQLAnalysisResult]]:
        """
        PL/SQL 복잡도 MD 리포트를 파싱합니다.
        
        Args:
            report_path: 리포트 파일 경로 (.md)
            target_db: 타겟 데이터베이스
            
        Returns:
            (sql_results, plsql_results) 튜플
        """
        sql_results: List[SQLAnalysisResult] = []
        plsql_results: List[PLSQLAnalysisResult] = []
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            target_db_enum = (
                TargetDatabase.POSTGRESQL 
                if target_db == "postgresql" 
                else TargetDatabase.MYSQL
            )
            
            # 요약 정보 추출
            avg_complexity = self._extract_avg_complexity(content)
            max_complexity = self._extract_max_complexity(content)
            total_count = self._extract_total_count(content)
            
            # 복잡도 분포 추출
            complexity_distribution = self._extract_complexity_distribution(content)
            
            # 개별 객체 분석 결과 파싱
            individual_results = self._extract_individual_results(content, target_db_enum)
            
            if individual_results:
                # 개별 결과가 있으면 사용
                plsql_results = individual_results
            else:
                # 개별 결과가 없으면 요약 정보 기반으로 더미 생성
                type_counts = self._extract_type_counts(content)
                
                for obj_type, count in type_counts.items():
                    plsql_type = self._parse_plsql_type(obj_type.lower())
                    
                    for i in range(count):
                        plsql_result = PLSQLAnalysisResult(
                            code=f"{obj_type}_{i+1}",
                            object_type=plsql_type,
                            target_database=target_db_enum,
                            total_score=avg_complexity or 1.0,
                            normalized_score=avg_complexity or 1.0,
                            complexity_level=ComplexityLevel.SIMPLE,
                            recommendation="",
                            base_score=1.0,
                            code_complexity=0.0,
                            oracle_features=0.0,
                            business_logic=0.0,
                            conversion_difficulty=0.0,
                            detected_oracle_features=[],
                            detected_external_dependencies=[],
                            line_count=0,
                            cursor_count=0,
                            exception_blocks=0,
                            nesting_depth=0,
                            bulk_operations_count=0
                        )
                        plsql_results.append(plsql_result)
            
            logger.info(f"PL/SQL MD 파싱 완료: {len(plsql_results)}개 객체, "
                       f"평균 복잡도: {avg_complexity}, 최대 복잡도: {max_complexity}")
            return sql_results, plsql_results
            
        except Exception as e:
            logger.warning(f"PL/SQL MD 파싱 실패 ({report_path}): {e}", exc_info=True)
            return sql_results, plsql_results
    
    def _extract_individual_results(
        self,
        content: str,
        target_db: TargetDatabase
    ) -> List[PLSQLAnalysisResult]:
        """개별 객체 분석 결과 파싱"""
        results: List[PLSQLAnalysisResult] = []
        
        # 개별 객체 섹션 패턴: ### 1. IX.ORDER_EVENT_TYP
        object_pattern = r'###\s*\d+\.\s*([^\n]+)\n(.*?)(?=###\s*\d+\.|$)'
        matches = re.findall(object_pattern, content, re.DOTALL)
        
        for obj_name, obj_content in matches:
            obj_name = obj_name.strip()
            
            # 타입 추출
            type_match = re.search(r'\*\*타입\*\*:\s*(\w+(?:\s+\w+)?)', obj_content)
            obj_type_str = type_match.group(1) if type_match else "PROCEDURE"
            plsql_type = self._parse_plsql_type(obj_type_str.lower())
            
            # 정규화 점수 추출 (예: **정규화 점수**: 1.65/10)
            score_match = re.search(r'\*\*정규화 점수\*\*:\s*([\d.]+)', obj_content)
            normalized_score = float(score_match.group(1)) if score_match else 1.0
            
            # 원점수 추출 (예: **원점수 (Raw Score)**: 3.30)
            raw_match = re.search(r'\*\*원점수.*?\*\*:\s*([\d.]+)', obj_content)
            total_score = float(raw_match.group(1)) if raw_match else normalized_score * 2
            
            # 복잡도 레벨 추출
            level_match = re.search(r'\*\*복잡도 레벨\*\*:\s*(\S+)', obj_content)
            level_str = level_match.group(1) if level_match else "간단"
            complexity_level = self._parse_complexity_level_str(level_str)
            
            # 세부 점수 추출
            base_match = re.search(r'\|\s*기본 점수\s*\|\s*([\d.]+)\s*\|', obj_content)
            code_match = re.search(r'\|\s*코드 복잡도\s*\|\s*([\d.]+)\s*\|', obj_content)
            oracle_match = re.search(r'\|\s*Oracle 특화 기능\s*\|\s*([\d.]+)\s*\|', obj_content)
            business_match = re.search(r'\|\s*비즈니스 로직\s*\|\s*([\d.]+)\s*\|', obj_content)
            conversion_match = re.search(r'\|\s*변환 난이도\s*\|\s*([\d.]+)\s*\|', obj_content)
            
            # Oracle 특화 기능 추출
            features: List[str] = []
            features_match = re.search(
                r'\*\*감지된 Oracle 특화 기능\*\*:\s*\n((?:- [^\n]+\n?)+)', 
                obj_content
            )
            if features_match:
                features = [
                    f.strip('- \n') 
                    for f in features_match.group(1).strip().split('\n')
                    if f.strip()
                ]
            
            plsql_result = PLSQLAnalysisResult(
                code=obj_name,
                object_type=plsql_type,
                target_database=target_db,
                total_score=total_score,
                normalized_score=normalized_score,
                complexity_level=complexity_level,
                recommendation="",
                base_score=float(base_match.group(1)) if base_match else 1.0,
                code_complexity=float(code_match.group(1)) if code_match else 0.0,
                oracle_features=float(oracle_match.group(1)) if oracle_match else 0.0,
                business_logic=float(business_match.group(1)) if business_match else 0.0,
                conversion_difficulty=float(conversion_match.group(1)) if conversion_match else 0.0,
                detected_oracle_features=features,
                detected_external_dependencies=[],
                line_count=0,
                cursor_count=0,
                exception_blocks=0,
                nesting_depth=0,
                bulk_operations_count=0
            )
            results.append(plsql_result)
        
        return results
    
    def _parse_complexity_level_str(self, level_str: str) -> ComplexityLevel:
        """복잡도 레벨 문자열을 enum으로 변환"""
        mapping = {
            '매우 간단': ComplexityLevel.VERY_SIMPLE,
            '간단': ComplexityLevel.SIMPLE,
            '중간': ComplexityLevel.MODERATE,
            '복잡': ComplexityLevel.COMPLEX,
            '매우 복잡': ComplexityLevel.VERY_COMPLEX,
            '극도로 복잡': ComplexityLevel.EXTREMELY_COMPLEX
        }
        return mapping.get(level_str, ComplexityLevel.SIMPLE)
    
    def _extract_avg_complexity(self, content: str) -> Optional[float]:
        """평균 복잡도 추출
        
        형식: - **평균 복잡도**: 1.74
        """
        # 여러 패턴 시도
        patterns = [
            r'\*\*평균 복잡도\*\*:\s*([\d.]+)',
            r'평균 복잡도[^:]*:\s*([\d.]+)',
            r'Average Complexity[^:]*:\s*([\d.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
    
    def _extract_max_complexity(self, content: str) -> Optional[float]:
        """최대 복잡도 추출
        
        형식: - **최대 복잡도**: 2.85
        """
        patterns = [
            r'\*\*최대 복잡도\*\*:\s*([\d.]+)',
            r'최대 복잡도[^:]*:\s*([\d.]+)',
            r'Max(?:imum)? Complexity[^:]*:\s*([\d.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
    
    def _extract_total_count(self, content: str) -> Optional[int]:
        """전체 객체 수 추출"""
        patterns = [
            r'\*\*전체 객체 수\*\*:\s*(\d+)',
            r'전체 객체 수[^:]*:\s*(\d+)',
            r'Total Objects[^:]*:\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None
    
    def _extract_complexity_distribution(self, content: str) -> Dict[str, int]:
        """복잡도 분포 추출
        
        형식:
        | 복잡도 레벨 | 객체 수 |
        |------------|---------|
        | 매우 간단 (0-1) | 0 |
        | 간단 (1-3) | 50 |
        | 중간 (3-5) | 0 |
        | 복잡 (5-7) | 0 |
        | 매우 복잡 (7-9) | 0 |
        | 극도로 복잡 (9-10) | 0 |
        """
        distribution: Dict[str, int] = {
            'very_simple': 0,  # 0-1
            'simple': 0,       # 1-3
            'moderate': 0,     # 3-5
            'complex': 0,      # 5-7
            'very_complex': 0, # 7-9
            'extremely_complex': 0  # 9-10
        }
        
        # 복잡도 분포 테이블 파싱
        patterns = [
            (r'\|\s*매우 간단\s*\([^)]+\)\s*\|\s*(\d+)\s*\|', 'very_simple'),
            (r'\|\s*간단\s*\([^)]+\)\s*\|\s*(\d+)\s*\|', 'simple'),
            (r'\|\s*중간\s*\([^)]+\)\s*\|\s*(\d+)\s*\|', 'moderate'),
            (r'\|\s*복잡\s*\([^)]+\)\s*\|\s*(\d+)\s*\|', 'complex'),
            (r'\|\s*매우 복잡\s*\([^)]+\)\s*\|\s*(\d+)\s*\|', 'very_complex'),
            (r'\|\s*극도로 복잡\s*\([^)]+\)\s*\|\s*(\d+)\s*\|', 'extremely_complex'),
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, content)
            if match:
                distribution[key] = int(match.group(1))
        
        return distribution
    
    def _extract_type_counts(self, content: str) -> Dict[str, int]:
        """객체 타입별 개수 추출"""
        counts: Dict[str, int] = {}
        
        # | FUNCTION | 1 | 형식
        pattern = r'\|\s*(FUNCTION|PROCEDURE|PACKAGE|TRIGGER|TYPE|TYPE BODY)\s*\|\s*(\d+)\s*\|'
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        for obj_type, count in matches:
            counts[obj_type.upper()] = int(count)
        
        return counts
    
    def _parse_plsql_type(self, type_str: str) -> PLSQLObjectType:
        """PL/SQL 타입 문자열을 enum으로 변환
        
        Note: TYPE, TYPE_BODY는 PLSQLObjectType enum에 없으므로 PROCEDURE로 매핑
        """
        mapping = {
            'function': PLSQLObjectType.FUNCTION,
            'procedure': PLSQLObjectType.PROCEDURE,
            'package': PLSQLObjectType.PACKAGE,
            'trigger': PLSQLObjectType.TRIGGER,
            'type': PLSQLObjectType.PROCEDURE,  # TYPE은 enum에 없음
            'type body': PLSQLObjectType.PROCEDURE,  # TYPE_BODY는 enum에 없음
        }
        return mapping.get(type_str.lower(), PLSQLObjectType.PROCEDURE)


class ReportParser:
    """리포트 파일 파서
    
    MD 및 JSON 형식의 DBCSI 및 SQL 복잡도 분석 리포트를 파싱합니다.
    MD 파일을 우선 파싱하고, 없으면 JSON을 사용합니다.
    """
    
    def __init__(self) -> None:
        self.md_parser = MarkdownReportParser()
    
    def parse_dbcsi_metrics(self, report_path: str) -> Optional[Dict[str, Any]]:
        """
        DBCSI 리포트에서 필요한 메트릭만 추출합니다.
        MD 파일을 우선 파싱하고, JSON은 폴백으로 사용합니다.
        
        Args:
            report_path: DBCSI 리포트 파일 경로 (.md 또는 .json)
            
        Returns:
            메트릭 딕셔너리 또는 None
        """
        # MD 파일인 경우
        if report_path.endswith('.md'):
            return self.md_parser.parse_dbcsi_markdown(report_path)
        
        # JSON 파일인 경우 (폴백)
        return self._parse_dbcsi_json(report_path)
    
    def _parse_dbcsi_json(self, report_path: str) -> Optional[Dict[str, Any]]:
        """JSON 형식 DBCSI 리포트 파싱 (폴백)"""
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            os_info = data.get('os_info', {})
            main_metrics = data.get('main_metrics', [])
            memory_metrics = data.get('memory_metrics', [])
            
            # 평균 CPU 계산
            cpu_values = [m.get('cpu_per_s', 0) for m in main_metrics if m.get('cpu_per_s')]
            avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0
            
            # 평균 I/O 계산
            io_values = []
            for m in main_metrics:
                read_iops = m.get('read_iops', 0) or 0
                write_iops = m.get('write_iops', 0) or 0
                io_values.append(read_iops + write_iops)
            avg_io = sum(io_values) / len(io_values) if io_values else 0.0
            
            # 평균 메모리 계산
            memory_values = [m.get('total_gb', 0) for m in memory_metrics if m.get('total_gb')]
            avg_memory = sum(memory_values) / len(memory_values) if memory_values else 0.0
            
            # RAC 감지
            instances = os_info.get('instances', 1)
            rac_detected = instances is not None and instances > 1
            
            return {
                'avg_cpu_usage': avg_cpu,
                'avg_io_load': avg_io,
                'avg_memory_usage': avg_memory,
                'rac_detected': rac_detected,
                'awr_plsql_lines': os_info.get('count_lines_plsql'),
                'awr_procedure_count': os_info.get('count_procedures'),
                'awr_function_count': os_info.get('count_functions'),
                'awr_package_count': os_info.get('count_packages'),
                'db_name': os_info.get('db_name'),
                'db_version': os_info.get('version'),
                'platform_name': os_info.get('platform_name'),
                'character_set': os_info.get('character_set'),
                'instance_count': instances,
                'is_rac': rac_detected,
                'total_db_size_gb': os_info.get('total_db_size_gb'),
                'physical_memory_gb': os_info.get('physical_memory_gb'),
                'cpu_cores': os_info.get('num_cpu_cores'),
                'num_cpus': os_info.get('num_cpus'),
                'report_type': 'json',
            }
            
        except Exception as e:
            logger.error(f"DBCSI JSON 파싱 실패 ({report_path}): {e}", exc_info=True)
            return None
    
    def parse_sql_complexity_reports(
        self,
        report_paths: List[str],
        target_db: str = "postgresql"
    ) -> Tuple[List[SQLAnalysisResult], List[PLSQLAnalysisResult]]:
        """
        SQL 복잡도 분석 리포트 파일들을 파싱합니다.
        MD 파일을 우선 파싱하고, JSON은 폴백으로 사용합니다.
        
        Args:
            report_paths: SQL 복잡도 리포트 파일 경로 리스트
            target_db: 타겟 데이터베이스 (postgresql 또는 mysql)
            
        Returns:
            (sql_results, plsql_results) 튜플
        """
        sql_results: List[SQLAnalysisResult] = []
        plsql_results: List[PLSQLAnalysisResult] = []
        
        target_db_enum = (
            TargetDatabase.POSTGRESQL 
            if target_db == "postgresql" 
            else TargetDatabase.MYSQL
        )
        
        for report_path in report_paths:
            try:
                # MD 파일인 경우
                if report_path.endswith('.md'):
                    sql, plsql = self.md_parser.parse_plsql_complexity_markdown(
                        report_path, target_db
                    )
                    sql_results.extend(sql)
                    plsql_results.extend(plsql)
                    continue
                
                # JSON 파일인 경우 (폴백)
                if not report_path.endswith('.json'):
                    continue
                
                with open(report_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 배치 리포트인지 확인
                if 'results' in data:
                    logger.info(f"배치 JSON 리포트 파싱: {report_path}")
                    sql, plsql = self._parse_batch_report(data, target_db_enum)
                    sql_results.extend(sql)
                    plsql_results.extend(plsql)
                            
            except Exception as e:
                logger.warning(f"리포트 파싱 실패 ({report_path}): {e}", exc_info=True)
                continue
        
        logger.info(f"복잡도 리포트 파싱 완료: SQL {len(sql_results)}개, PL/SQL {len(plsql_results)}개")
        return sql_results, plsql_results
    
    def _parse_batch_report(
        self,
        data: Dict[str, Any],
        target_db: TargetDatabase
    ) -> Tuple[List[SQLAnalysisResult], List[PLSQLAnalysisResult]]:
        """배치 JSON 리포트 파싱"""
        sql_results: List[SQLAnalysisResult] = []
        plsql_results: List[PLSQLAnalysisResult] = []
        
        for result_data in data.get('results', []):
            try:
                analysis = result_data.get('analysis', {})
                object_type_str = analysis.get('object_type', 'sql')
                
                complexity_level_str = analysis.get('complexity_level', '알 수 없음')
                complexity_level = self._parse_complexity_level(complexity_level_str)
                
                if object_type_str in ['function', 'procedure', 'package', 'trigger', 'type', 'type body']:
                    plsql_type = self._parse_plsql_type(object_type_str)
                    
                    plsql_result = PLSQLAnalysisResult(
                        code=f"{result_data.get('owner', '')}.{result_data.get('object_name', '')}",
                        object_type=plsql_type,
                        target_database=target_db,
                        total_score=analysis.get('total_score', 0.0),
                        normalized_score=analysis.get('normalized_score', 0.0),
                        complexity_level=complexity_level,
                        recommendation=analysis.get('recommendation', ''),
                        base_score=analysis.get('base_score', 0.0),
                        code_complexity=analysis.get('code_complexity', 0.0),
                        oracle_features=analysis.get('oracle_features', 0.0),
                        business_logic=analysis.get('business_logic', 0.0),
                        conversion_difficulty=analysis.get('conversion_difficulty', 0.0),
                        detected_oracle_features=analysis.get('detected_oracle_features', []),
                        detected_external_dependencies=analysis.get('detected_external_dependencies', []),
                        line_count=analysis.get('line_count', 0),
                        cursor_count=analysis.get('cursor_count', 0),
                        exception_blocks=analysis.get('exception_blocks', 0),
                        nesting_depth=analysis.get('nesting_depth', 0),
                        bulk_operations_count=analysis.get('bulk_operations_count', 0)
                    )
                    plsql_results.append(plsql_result)
                else:
                    sql_result = SQLAnalysisResult(
                        query=f"{result_data.get('owner', '')}.{result_data.get('object_name', '')}",
                        target_database=target_db,
                        total_score=analysis.get('total_score', 0.0),
                        normalized_score=analysis.get('normalized_score', 0.0),
                        complexity_level=complexity_level,
                        recommendation=analysis.get('recommendation', ''),
                        structural_complexity=0.0,
                        oracle_specific_features=0.0,
                        functions_expressions=0.0,
                        data_volume=0.0,
                        execution_complexity=0.0,
                        conversion_difficulty=0.0,
                        detected_oracle_features=analysis.get('detected_oracle_features', [])
                    )
                    sql_results.append(sql_result)
                    
            except Exception as e:
                logger.warning(f"개별 결과 파싱 실패: {e}", exc_info=True)
                continue
        
        return sql_results, plsql_results
    
    def _parse_complexity_level(self, level_str: str) -> ComplexityLevel:
        """복잡도 레벨 문자열을 enum으로 변환"""
        mapping = {
            '매우 간단': ComplexityLevel.VERY_SIMPLE,
            '간단': ComplexityLevel.SIMPLE,
            '중간': ComplexityLevel.MODERATE,
            '복잡': ComplexityLevel.COMPLEX,
            '매우 복잡': ComplexityLevel.VERY_COMPLEX,
            '극도로 복잡': ComplexityLevel.EXTREMELY_COMPLEX
        }
        return mapping.get(level_str, ComplexityLevel.MODERATE)
    
    def _parse_plsql_type(self, type_str: str) -> PLSQLObjectType:
        """PL/SQL 타입 문자열을 enum으로 변환
        
        Note: TYPE, TYPE_BODY는 PLSQLObjectType enum에 없으므로 PROCEDURE로 매핑
        """
        mapping = {
            'function': PLSQLObjectType.FUNCTION,
            'procedure': PLSQLObjectType.PROCEDURE,
            'package': PLSQLObjectType.PACKAGE,
            'trigger': PLSQLObjectType.TRIGGER,
            'type': PLSQLObjectType.PROCEDURE,  # TYPE은 enum에 없음
            'type body': PLSQLObjectType.PROCEDURE,  # TYPE_BODY는 enum에 없음
        }
        return mapping.get(type_str.lower(), PLSQLObjectType.PROCEDURE)


def find_reports_in_directory(reports_dir: str) -> Tuple[List[str], List[str]]:
    """
    리포트 디렉토리에서 DBCSI 리포트와 SQL 복잡도 리포트를 찾습니다.
    MD 파일을 우선하고, 없으면 JSON 파일을 사용합니다.
    
    Args:
        reports_dir: 리포트 디렉토리 경로
        
    Returns:
        (dbcsi_reports, sql_complexity_reports) 튜플
    """
    reports_path = Path(reports_dir)
    
    dbcsi_reports: List[str] = []
    sql_complexity_reports: List[str] = []
    
    # MD 파일 우선 검색
    md_files = list(reports_path.glob("**/*.md"))
    json_files = list(reports_path.glob("**/*.json"))
    
    # DBCSI MD 리포트 찾기
    for md_file in md_files:
        filename = md_file.name.lower()
        if any(keyword in filename for keyword in ['dbcsi', 'awr', 'statspack']):
            if 'comparison' not in filename and 'migration' not in filename:
                dbcsi_reports.append(str(md_file))
    
    # DBCSI MD가 없으면 JSON 사용
    if not dbcsi_reports:
        for json_file in json_files:
            filename = json_file.name.lower()
            if any(keyword in filename for keyword in ['dbcsi', 'awr', 'statspack']):
                if 'comparison' not in filename and 'migration' not in filename:
                    dbcsi_reports.append(str(json_file))
    
    # SQL 복잡도 MD 리포트 찾기
    for md_file in md_files:
        filename = md_file.name.lower()
        if 'plsql' in filename and 'complexity' in filename:
            sql_complexity_reports.append(str(md_file))
        elif 'sql_complexity' in filename:
            sql_complexity_reports.append(str(md_file))
    
    # SQL 복잡도 MD가 없으면 JSON 사용
    if not sql_complexity_reports:
        for json_file in json_files:
            filename = json_file.name.lower()
            if 'plsql_f_' in filename or 'sql_complexity' in filename:
                sql_complexity_reports.append(str(json_file))
            elif json_file.parent.name in ['PGSQL', 'MySQL']:
                if 'batch' not in filename and 'migration' not in filename:
                    sql_complexity_reports.append(str(json_file))
    
    logger.info(f"발견된 DBCSI 리포트: {len(dbcsi_reports)}개")
    logger.info(f"발견된 SQL 복잡도 리포트: {len(sql_complexity_reports)}개")
    
    return dbcsi_reports, sql_complexity_reports


def find_reports_by_target(reports_dir: str) -> Dict[str, List[str]]:
    """
    리포트 디렉토리에서 타겟 DB별로 SQL 복잡도 리포트를 찾습니다.
    
    Args:
        reports_dir: 리포트 디렉토리 경로
        
    Returns:
        Dict[str, List[str]]: 타겟 DB별 리포트 경로 딕셔너리
            - 'postgresql': PostgreSQL 타겟 리포트 리스트
            - 'mysql': MySQL 타겟 리포트 리스트
            - 'dbcsi': DBCSI 리포트 리스트
    """
    reports_path = Path(reports_dir)
    
    result: Dict[str, List[str]] = {
        'postgresql': [],
        'mysql': [],
        'dbcsi': []
    }
    
    # MD 파일 우선 검색
    md_files = list(reports_path.glob("**/*.md"))
    json_files = list(reports_path.glob("**/*.json"))
    
    # DBCSI 리포트 찾기
    for md_file in md_files:
        filename = md_file.name.lower()
        if any(keyword in filename for keyword in ['dbcsi', 'awr', 'statspack']):
            if 'comparison' not in filename and 'migration' not in filename:
                result['dbcsi'].append(str(md_file))
    
    if not result['dbcsi']:
        for json_file in json_files:
            filename = json_file.name.lower()
            if any(keyword in filename for keyword in ['dbcsi', 'awr', 'statspack']):
                if 'comparison' not in filename and 'migration' not in filename:
                    result['dbcsi'].append(str(json_file))
    
    # PostgreSQL 복잡도 리포트 찾기
    for md_file in md_files:
        filename = md_file.name.lower()
        filepath = str(md_file).lower()
        
        # 파일명 또는 경로에 postgresql/pgsql 포함
        if ('postgresql' in filename or 'pgsql' in filepath or 
            '_postgresql' in filename or '/pgsql/' in filepath):
            if 'plsql' in filename or 'sql_complexity' in filename:
                result['postgresql'].append(str(md_file))
    
    # MySQL 복잡도 리포트 찾기
    for md_file in md_files:
        filename = md_file.name.lower()
        filepath = str(md_file).lower()
        
        # 파일명 또는 경로에 mysql 포함
        if ('mysql' in filename or '/mysql/' in filepath or '_mysql' in filename):
            if 'plsql' in filename or 'sql_complexity' in filename:
                result['mysql'].append(str(md_file))
    
    # 타겟 구분 없는 일반 리포트 (PostgreSQL로 분류)
    for md_file in md_files:
        filename = md_file.name.lower()
        filepath = str(md_file).lower()
        
        # 이미 분류된 파일 제외
        if str(md_file) in result['postgresql'] or str(md_file) in result['mysql']:
            continue
        
        # 타겟 구분 없는 복잡도 리포트
        if ('plsql' in filename and 'complexity' in filename) or 'sql_complexity' in filename:
            # 기본적으로 PostgreSQL로 분류
            result['postgresql'].append(str(md_file))
    
    logger.info(f"발견된 DBCSI 리포트: {len(result['dbcsi'])}개")
    logger.info(f"발견된 PostgreSQL 복잡도 리포트: {len(result['postgresql'])}개")
    logger.info(f"발견된 MySQL 복잡도 리포트: {len(result['mysql'])}개")
    
    return result
