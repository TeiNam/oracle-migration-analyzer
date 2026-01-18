"""
추세 분석 모듈

시계열 데이터의 추세를 분석하는 기능을 제공합니다.
"""

import statistics
from typing import List, Optional

from ..models import AWRData
from .data_models import BatchFileResult, TrendMetrics


class TrendAnalyzer:
    """추세 분석기"""
    
    @staticmethod
    def analyze_cpu_trend(results: List[BatchFileResult]) -> Optional[TrendMetrics]:
        """
        CPU 사용률 추세 분석
        
        Args:
            results: 파일 분석 결과 리스트
            
        Returns:
            CPU 추세 메트릭 (데이터 부족 시 None)
        """
        values = []
        timestamps = []
        
        for result in results:
            if result.statspack_data and result.statspack_data.main_metrics:
                # 평균 CPU 사용률 계산
                avg_cpu = statistics.mean([
                    m.cpu_per_s 
                    for m in result.statspack_data.main_metrics 
                    if m.cpu_per_s > 0
                ])
                if avg_cpu > 0:
                    values.append(avg_cpu)
                    timestamps.append(result.timestamp or "")
        
        if len(values) < 2:
            return None
        
        return TrendAnalyzer._calculate_trend_metrics("CPU Usage (per second)", values, timestamps)
    
    @staticmethod
    def analyze_io_trend(results: List[BatchFileResult]) -> Optional[TrendMetrics]:
        """
        I/O 부하 추세 분석
        
        Args:
            results: 파일 분석 결과 리스트
            
        Returns:
            I/O 추세 메트릭 (데이터 부족 시 None)
        """
        values = []
        timestamps = []
        
        for result in results:
            if result.statspack_data and result.statspack_data.main_metrics:
                # 평균 I/O (읽기 + 쓰기 IOPS) 계산
                avg_io = statistics.mean([
                    m.read_iops + m.write_iops 
                    for m in result.statspack_data.main_metrics 
                    if (m.read_iops + m.write_iops) > 0
                ])
                if avg_io > 0:
                    values.append(avg_io)
                    timestamps.append(result.timestamp or "")
        
        if len(values) < 2:
            return None
        
        return TrendAnalyzer._calculate_trend_metrics("I/O IOPS", values, timestamps)
    
    @staticmethod
    def analyze_memory_trend(results: List[BatchFileResult]) -> Optional[TrendMetrics]:
        """
        메모리 사용량 추세 분석
        
        Args:
            results: 파일 분석 결과 리스트
            
        Returns:
            메모리 추세 메트릭 (데이터 부족 시 None)
        """
        values = []
        timestamps = []
        
        for result in results:
            if result.statspack_data and result.statspack_data.memory_metrics:
                # 평균 메모리 사용량 계산
                avg_memory = statistics.mean([m.total_gb for m in result.statspack_data.memory_metrics])
                if avg_memory > 0:
                    values.append(avg_memory)
                    timestamps.append(result.timestamp or "")
        
        if len(values) < 2:
            return None
        
        return TrendAnalyzer._calculate_trend_metrics("Memory Usage (GB)", values, timestamps)
    
    @staticmethod
    def analyze_buffer_cache_trend(results: List[BatchFileResult]) -> Optional[TrendMetrics]:
        """
        버퍼 캐시 히트율 추세 분석 (AWR 전용)
        
        Args:
            results: 파일 분석 결과 리스트
            
        Returns:
            버퍼 캐시 추세 메트릭 (데이터 부족 시 None)
        """
        values = []
        timestamps = []
        
        for result in results:
            # AWR 데이터인지 확인
            if isinstance(result.statspack_data, AWRData) and result.statspack_data.buffer_cache_stats:
                # 평균 히트율 계산
                avg_hit_ratio = statistics.mean([b.hit_ratio for b in result.statspack_data.buffer_cache_stats])
                if avg_hit_ratio > 0:
                    values.append(avg_hit_ratio)
                    timestamps.append(result.timestamp or "")
        
        if len(values) < 2:
            return None
        
        return TrendAnalyzer._calculate_trend_metrics("Buffer Cache Hit Ratio (%)", values, timestamps)
    
    @staticmethod
    def _calculate_trend_metrics(metric_name: str, values: List[float], timestamps: List[str]) -> TrendMetrics:
        """
        추세 메트릭 계산
        
        Args:
            metric_name: 메트릭 이름
            values: 값 리스트
            timestamps: 타임스탬프 리스트
            
        Returns:
            TrendMetrics: 추세 메트릭
        """
        avg = statistics.mean(values)
        min_val = min(values)
        max_val = max(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        
        # 추세 판단 (첫 값과 마지막 값 비교)
        change_pct = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0.0
        
        if abs(change_pct) < 5:
            trend = "stable"
        elif change_pct > 0:
            trend = "increasing"
        else:
            trend = "decreasing"
        
        return TrendMetrics(
            metric_name=metric_name,
            values=values,
            timestamps=timestamps,
            avg=avg,
            min_val=min_val,
            max_val=max_val,
            std_dev=std_dev,
            trend=trend,
            change_pct=change_pct
        )
