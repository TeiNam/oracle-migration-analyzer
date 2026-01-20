"""
분석 결과 통합기

DBCSI 분석기와 SQL/PL-SQL 분석기의 결과를 통합하고 메트릭을 추출합니다.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from src.oracle_complexity_analyzer.data_models import SQLAnalysisResult, PLSQLAnalysisResult
from src.migration_recommendation.data_models import (
    IntegratedAnalysisResult,
    AnalysisMetrics
)


class AnalysisResultIntegrator:
    """분석 결과 통합기
    
    DBCSI 분석 결과와 SQL/PL-SQL 분석 결과를 통합하여
    마이그레이션 의사결정에 필요한 메트릭을 추출합니다.
    
    Requirements:
    - 1.1: DBCSI와 SQL 분석 결과 통합
    - 1.4: 평균 SQL 복잡도 계산
    - 1.5: 평균 PL/SQL 복잡도 계산
    - 1.6: BULK 연산 개수 집계
    - 11.1: 평균 CPU 사용률 추출
    - 11.2: 평균 I/O 부하 추출
    - 11.3: 평균 메모리 사용량 추출
    - 12.1: 복잡도 7.0 이상 SQL 개수 집계
    - 12.2: 복잡도 7.0 이상 PL/SQL 개수 집계
    """
    
    def integrate(
        self,
        dbcsi_metrics: Optional[Dict[str, Any]],
        sql_analysis: List[SQLAnalysisResult],
        plsql_analysis: List[PLSQLAnalysisResult]
    ) -> IntegratedAnalysisResult:
        """
        분석 결과를 통합합니다.
        
        Args:
            dbcsi_metrics: DBCSI 메트릭 딕셔너리 (간소화된 형태)
            sql_analysis: SQL 복잡도 분석 결과 리스트
            plsql_analysis: PL/SQL 복잡도 분석 결과 리스트
            
        Returns:
            IntegratedAnalysisResult: 통합된 분석 결과
            
        Raises:
            ValueError: 필수 분석 결과가 누락된 경우
        """
        # 입력 검증
        if not sql_analysis and not plsql_analysis:
            raise ValueError("SQL 또는 PL/SQL 분석 결과가 필요합니다")
        
        # 메트릭 추출
        metrics = self.extract_metrics(dbcsi_metrics, sql_analysis, plsql_analysis)
        
        # 통합 결과 생성
        return IntegratedAnalysisResult(
            dbcsi_result=None,  # 간소화된 버전에서는 None
            sql_analysis=sql_analysis,
            plsql_analysis=plsql_analysis,
            metrics=metrics,
            analysis_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def extract_metrics(
        self,
        dbcsi_metrics: Optional[Dict[str, Any]],
        sql_analysis: List[SQLAnalysisResult],
        plsql_analysis: List[PLSQLAnalysisResult]
    ) -> AnalysisMetrics:
        """
        분석 결과에서 메트릭을 추출합니다.
        
        Args:
            dbcsi_metrics: DBCSI 메트릭 딕셔너리
            sql_analysis: SQL 복잡도 분석 결과 리스트
            plsql_analysis: PL/SQL 복잡도 분석 결과 리스트
            
        Returns:
            AnalysisMetrics: 추출된 메트릭
        """
        # 성능 메트릭 추출
        if dbcsi_metrics:
            avg_cpu = dbcsi_metrics.get('avg_cpu_usage', 0.0)
            avg_io = dbcsi_metrics.get('avg_io_load', 0.0)
            avg_memory = dbcsi_metrics.get('avg_memory_usage', 0.0)
            rac_detected = dbcsi_metrics.get('rac_detected', False)
            awr_plsql_lines = dbcsi_metrics.get('awr_plsql_lines')
            awr_procedure_count = dbcsi_metrics.get('awr_procedure_count')
            awr_function_count = dbcsi_metrics.get('awr_function_count')
            awr_package_count = dbcsi_metrics.get('awr_package_count')
        else:
            avg_cpu, avg_io, avg_memory = 0.0, 0.0, 0.0
            rac_detected = False
            awr_plsql_lines = None
            awr_procedure_count = None
            awr_function_count = None
            awr_package_count = None
        
        # BULK 연산 개수 집계
        bulk_operation_count = self._count_bulk_operations(plsql_analysis)
        avg_sql_complexity = self._calculate_avg_complexity(sql_analysis)
        avg_plsql_complexity = self._calculate_avg_complexity(plsql_analysis)
        
        # 복잡도 분포 계산
        high_complexity_sql_count = self._count_high_complexity(sql_analysis, threshold=7.0)
        high_complexity_plsql_count = self._count_high_complexity(plsql_analysis, threshold=7.0)
        total_sql_count = len(sql_analysis)
        total_plsql_count = len(plsql_analysis)
        
        # 복잡 오브젝트 비율 계산
        total_count = total_sql_count + total_plsql_count
        high_count = high_complexity_sql_count + high_complexity_plsql_count
        high_complexity_ratio = high_count / total_count if total_count > 0 else 0.0
        
        # BULK 연산 개수 집계
        bulk_operation_count = self._count_bulk_operations(plsql_analysis)
        
        return AnalysisMetrics(
            avg_cpu_usage=avg_cpu,
            avg_io_load=avg_io,
            avg_memory_usage=avg_memory,
            avg_sql_complexity=avg_sql_complexity,
            avg_plsql_complexity=avg_plsql_complexity,
            high_complexity_sql_count=high_complexity_sql_count,
            high_complexity_plsql_count=high_complexity_plsql_count,
            total_sql_count=total_sql_count,
            total_plsql_count=total_plsql_count,
            high_complexity_ratio=high_complexity_ratio,
            bulk_operation_count=bulk_operation_count,
            rac_detected=rac_detected,
            awr_plsql_lines=awr_plsql_lines,
            awr_procedure_count=awr_procedure_count,
            awr_function_count=awr_function_count,
            awr_package_count=awr_package_count
        )
    
    def _calculate_avg_complexity(
        self,
        analysis_results: List[Union[SQLAnalysisResult, PLSQLAnalysisResult]]
    ) -> float:
        """
        평균 복잡도 계산
        
        Args:
            analysis_results: 분석 결과 리스트
            
        Returns:
            float: 평균 복잡도 점수
        """
        if not analysis_results:
            return 0.0
        
        complexity_scores = [result.normalized_score for result in analysis_results]
        return sum(complexity_scores) / len(complexity_scores)
    
    def _count_high_complexity(
        self,
        analysis_results: List[Union[SQLAnalysisResult, PLSQLAnalysisResult]],
        threshold: float = 7.0
    ) -> int:
        """
        복잡도 임계값 이상 오브젝트 개수 집계
        
        Args:
            analysis_results: 분석 결과 리스트
            threshold: 복잡도 임계값 (기본값: 7.0)
            
        Returns:
            int: 임계값 이상 오브젝트 개수
        """
        return sum(1 for result in analysis_results if result.normalized_score >= threshold)
    
    def _count_bulk_operations(
        self,
        plsql_analysis: List[PLSQLAnalysisResult]
    ) -> int:
        """
        BULK 연산 개수 집계
        
        Args:
            plsql_analysis: PL/SQL 분석 결과 리스트
            
        Returns:
            int: BULK 연산 총 개수
        """
        return sum(result.bulk_operations_count for result in plsql_analysis)
