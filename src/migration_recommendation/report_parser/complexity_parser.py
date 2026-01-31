"""
복잡도 리포트 파서

SQL/PL-SQL 복잡도 분석 MD 리포트를 파싱합니다.
"""

import re
import logging
from typing import List, Optional, Dict, Any, Tuple

from ...oracle_complexity_analyzer.data_models import SQLAnalysisResult, PLSQLAnalysisResult
from ...oracle_complexity_analyzer.enums import TargetDatabase, ComplexityLevel, PLSQLObjectType

logger = logging.getLogger(__name__)


class ComplexityReportParser:
    """복잡도 리포트 파서
    
    SQL/PL-SQL 복잡도 분석 MD 리포트를 파싱합니다.
    """
    
    def parse_plsql_complexity_markdown_with_summary(
        self,
        report_path: str,
        target_db: str = "postgresql"
    ) -> Tuple[List[SQLAnalysisResult], List[PLSQLAnalysisResult], Dict[str, Any]]:
        """PL/SQL 복잡도 MD 리포트를 파싱하고 요약 정보도 반환합니다."""
        sql_results, plsql_results = self.parse_plsql_complexity_markdown(
            report_path, target_db
        )
        
        summary: Dict[str, Any] = {
            'oracle_features': [],
            'external_dependencies': [],
            'conversion_guide': {},
            'object_type_counts': {},
            'total_objects': 0,
            'avg_complexity': None,
            'max_complexity': None
        }
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            summary['oracle_features'] = self._extract_oracle_features_summary(content)
            summary['external_dependencies'] = self._extract_external_dependencies_summary(content)
            summary['conversion_guide'] = self._extract_conversion_guide(content)
            summary['object_type_counts'] = self._extract_type_counts(content)
            summary['total_objects'] = self._extract_total_count(content)
            summary['avg_complexity'] = self._extract_avg_complexity(content)
            summary['max_complexity'] = self._extract_max_complexity(content)
            
        except Exception as e:
            logger.warning(f"요약 정보 추출 실패 ({report_path}): {e}")
        
        return sql_results, plsql_results, summary

    def parse_plsql_complexity_markdown(
        self,
        report_path: str,
        target_db: str = "postgresql"
    ) -> Tuple[List[SQLAnalysisResult], List[PLSQLAnalysisResult]]:
        """PL/SQL 복잡도 MD 리포트를 파싱합니다."""
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
            
            avg_complexity = self._extract_avg_complexity(content)
            
            # 개별 객체 분석 결과 파싱
            individual_results = self._extract_individual_results(content, target_db_enum)
            
            if individual_results:
                plsql_results = individual_results
            else:
                type_counts = self._extract_type_counts(content)
                
                if not type_counts:
                    single_result = self._extract_single_file_result(
                        content, target_db_enum, report_path
                    )
                    if single_result:
                        plsql_results.append(single_result)
                else:
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
            
            logger.info(f"PL/SQL MD 파싱 완료: {len(plsql_results)}개 객체")
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
        
        object_pattern = r'###\s*\d+\.\s*([^\n]+)\n(.*?)(?=###\s*\d+\.|$)'
        matches = re.findall(object_pattern, content, re.DOTALL)
        
        for obj_name, obj_content in matches:
            obj_name = obj_name.strip()
            
            type_match = re.search(r'\*\*타입\*\*:\s*(\w+(?:\s+\w+)?)', obj_content)
            obj_type_str = type_match.group(1) if type_match else "PROCEDURE"
            plsql_type = self._parse_plsql_type(obj_type_str.lower())
            
            score_match = re.search(r'\*\*정규화 점수\*\*:\s*([\d.]+)', obj_content)
            normalized_score = float(score_match.group(1)) if score_match else 1.0
            
            raw_match = re.search(r'\*\*원점수.*?\*\*:\s*([\d.]+)', obj_content)
            total_score = float(raw_match.group(1)) if raw_match else normalized_score * 2
            
            level_match = re.search(r'\*\*복잡도 레벨\*\*:\s*(\S+)', obj_content)
            level_str = level_match.group(1) if level_match else "간단"
            complexity_level = self._parse_complexity_level_str(level_str)
            
            base_match = re.search(r'\|\s*기본 점수\s*\|\s*([\d.]+)\s*\|', obj_content)
            code_match = re.search(r'\|\s*코드 복잡도\s*\|\s*([\d.]+)\s*\|', obj_content)
            oracle_match = re.search(r'\|\s*Oracle 특화 기능\s*\|\s*([\d.]+)\s*\|', obj_content)
            business_match = re.search(r'\|\s*비즈니스 로직\s*\|\s*([\d.]+)\s*\|', obj_content)
            conversion_match = re.search(r'\|\s*변환 난이도\s*\|\s*([\d.]+)\s*\|', obj_content)
            
            features: List[str] = []
            features_match = re.search(
                r'\*\*감지된 Oracle 특화 기능\*\*:\s*\n((?:- [^\n]+\n?)+)', 
                obj_content
            )
            if features_match:
                for f in features_match.group(1).strip().split('\n'):
                    feature = f.strip('- \n')
                    if feature and not feature.startswith('...') and '외' not in feature:
                        features.append(feature)
            
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
    
    def _extract_single_file_result(
        self,
        content: str,
        target_db: TargetDatabase,
        report_path: str
    ) -> Optional[PLSQLAnalysisResult]:
        """단일 파일 복잡도 리포트에서 결과 추출"""
        type_match = re.search(r'\*\*오브젝트 타입\*\*:\s*(\w+)', content)
        if not type_match:
            return None
        
        obj_type_str = type_match.group(1)
        plsql_type = self._parse_plsql_type(obj_type_str.lower())
        
        score_match = re.search(r'\*\*정규화 점수\*\*:\s*([\d.]+)', content)
        normalized_score = float(score_match.group(1)) if score_match else 1.0
        
        raw_match = re.search(r'\*\*원점수.*?\*\*:\s*([\d.]+)', content)
        total_score = float(raw_match.group(1)) if raw_match else normalized_score * 2
        
        level_match = re.search(r'\*\*복잡도 레벨\*\*:\s*([^\n]+)', content)
        level_str = level_match.group(1).strip() if level_match else "간단"
        complexity_level = self._parse_complexity_level_str(level_str)
        
        base_match = re.search(r'\|\s*기본 점수\s*\|\s*([\d.]+)\s*\|', content)
        code_match = re.search(r'\|\s*코드 복잡도\s*\|\s*([\d.]+)\s*\|', content)
        oracle_match = re.search(r'\|\s*Oracle 특화 기능\s*\|\s*([\d.]+)\s*\|', content)
        business_match = re.search(r'\|\s*비즈니스 로직\s*\|\s*([\d.]+)\s*\|', content)
        conversion_match = re.search(r'\|\s*변환 난이도\s*\|\s*([\d.]+)\s*\|', content)
        
        features: List[str] = []
        features_section = re.search(
            r'## 감지된 Oracle 특화 기능\s*\n((?:- [^\n]+\n?)+)',
            content
        )
        if features_section:
            for line in features_section.group(1).strip().split('\n'):
                feature = line.strip('- \n')
                if feature:
                    features.append(feature)
        
        dependencies: List[str] = []
        deps_section = re.search(
            r'## 감지된 외부 의존성\s*\n((?:- [^\n]+\n?)+)',
            content
        )
        if deps_section:
            for line in deps_section.group(1).strip().split('\n'):
                dep = line.strip('- \n')
                if dep:
                    dependencies.append(dep)
        
        line_count_match = re.search(r'\*\*코드 라인 수\*\*:\s*(\d+)', content)
        cursor_match = re.search(r'\*\*커서 개수\*\*:\s*(\d+)', content)
        exception_match = re.search(r'\*\*예외 블록 개수\*\*:\s*(\d+)', content)
        nesting_match = re.search(r'\*\*중첩 깊이\*\*:\s*(\d+)', content)
        bulk_match = re.search(r'\*\*BULK 연산 개수\*\*:\s*(\d+)', content)
        
        import os
        code_name = os.path.splitext(os.path.basename(report_path))[0]
        
        return PLSQLAnalysisResult(
            code=code_name,
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
            detected_external_dependencies=dependencies,
            line_count=int(line_count_match.group(1)) if line_count_match else 0,
            cursor_count=int(cursor_match.group(1)) if cursor_match else 0,
            exception_blocks=int(exception_match.group(1)) if exception_match else 0,
            nesting_depth=int(nesting_match.group(1)) if nesting_match else 0,
            bulk_operations_count=int(bulk_match.group(1)) if bulk_match else 0
        )
    
    def _extract_avg_complexity(self, content: str) -> Optional[float]:
        """평균 복잡도 추출"""
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
        """최대 복잡도 추출"""
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
    
    def _extract_type_counts(self, content: str) -> Dict[str, int]:
        """객체 타입별 개수 추출"""
        counts: Dict[str, int] = {}
        
        pattern = r'\|\s*(FUNCTION|PROCEDURE|PACKAGE|PACKAGE BODY|TRIGGER|TYPE|TYPE BODY)\s*\|\s*(\d+)\s*\|'
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        for obj_type, count in matches:
            normalized_type = obj_type.upper()
            counts[normalized_type] = int(count)
        
        return counts
    
    def _parse_plsql_type(self, type_str: str) -> PLSQLObjectType:
        """PL/SQL 타입 문자열을 enum으로 변환"""
        mapping = {
            'function': PLSQLObjectType.FUNCTION,
            'procedure': PLSQLObjectType.PROCEDURE,
            'package': PLSQLObjectType.PACKAGE,
            'trigger': PLSQLObjectType.TRIGGER,
            'type': PLSQLObjectType.PROCEDURE,
            'type body': PLSQLObjectType.PROCEDURE,
        }
        return mapping.get(type_str.lower(), PLSQLObjectType.PROCEDURE)
    
    def _extract_oracle_features_summary(self, content: str) -> List[str]:
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
    
    def _extract_external_dependencies_summary(self, content: str) -> List[str]:
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
    
    def _extract_conversion_guide(self, content: str) -> Dict[str, str]:
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
