"""
메트릭 계산기

SQL/PL-SQL 분석 결과에서 복잡도 메트릭을 계산합니다.
"""

from typing import Dict, List, Optional, Sequence, Union

from src.oracle_complexity_analyzer.data_models import SQLAnalysisResult, PLSQLAnalysisResult


class MetricsCalculator:
    """복잡도 메트릭 계산 클래스"""
    
    def calculate_avg_complexity(
        self,
        analysis_results: Sequence[Union[SQLAnalysisResult, PLSQLAnalysisResult]]
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
    
    def calculate_max_complexity(
        self,
        analysis_results: Sequence[Union[SQLAnalysisResult, PLSQLAnalysisResult]]
    ) -> Optional[float]:
        """
        최대 복잡도 계산
        
        Args:
            analysis_results: 분석 결과 리스트
            
        Returns:
            Optional[float]: 최대 복잡도 점수 (결과가 없으면 None)
        """
        if not analysis_results:
            return None
        
        complexity_scores = [result.normalized_score for result in analysis_results]
        return max(complexity_scores)
    
    def count_high_complexity(
        self,
        analysis_results: Sequence[Union[SQLAnalysisResult, PLSQLAnalysisResult]],
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
    
    def count_bulk_operations(
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
    
    def aggregate_oracle_features(
        self,
        plsql_analysis: List[PLSQLAnalysisResult]
    ) -> Dict[str, int]:
        """
        PL/SQL 분석 결과에서 Oracle 특화 기능 집계
        
        Args:
            plsql_analysis: PL/SQL 분석 결과 리스트
            
        Returns:
            Dict[str, int]: 기능명 -> 사용 횟수
        """
        features: Dict[str, int] = {}
        for result in plsql_analysis:
            for feature in result.detected_oracle_features:
                features[feature] = features.get(feature, 0) + 1
        return features
    
    def aggregate_external_dependencies(
        self,
        plsql_analysis: List[PLSQLAnalysisResult]
    ) -> Dict[str, int]:
        """
        PL/SQL 분석 결과에서 외부 의존성 집계
        
        Args:
            plsql_analysis: PL/SQL 분석 결과 리스트
            
        Returns:
            Dict[str, int]: 의존성명 -> 사용 횟수
        """
        dependencies: Dict[str, int] = {}
        for result in plsql_analysis:
            for dep in result.detected_external_dependencies:
                dependencies[dep] = dependencies.get(dep, 0) + 1
        return dependencies
    
    def merge_external_dependencies(
        self,
        from_analysis: Dict[str, int],
        from_report: List[str]
    ) -> Dict[str, int]:
        """
        분석 결과와 리포트에서 추출한 외부 의존성 병합
        
        Args:
            from_analysis: 개별 분석 결과에서 집계한 의존성
            from_report: 리포트 요약에서 추출한 의존성 목록
            
        Returns:
            Dict[str, int]: 병합된 의존성 (의존성명 -> 사용 횟수)
        """
        result = dict(from_analysis)
        
        # 리포트에서 추출한 의존성 추가 (분석 결과에 없는 경우)
        for dep in from_report:
            if dep not in result:
                result[dep] = 1  # 리포트에서만 발견된 경우 1회로 설정
        
        return result
