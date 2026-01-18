"""
이상 징후 감지 모듈

성능 메트릭의 이상 징후를 감지하는 기능을 제공합니다.
"""

from typing import List, Optional

from .data_models import BatchFileResult, TrendMetrics, Anomaly


class AnomalyDetector:
    """이상 징후 감지기"""
    
    @staticmethod
    def detect_anomalies(
        results: List[BatchFileResult],
        cpu_trend: Optional[TrendMetrics],
        io_trend: Optional[TrendMetrics],
        memory_trend: Optional[TrendMetrics],
        buffer_cache_trend: Optional[TrendMetrics]
    ) -> List[Anomaly]:
        """
        이상 징후 감지
        
        급격한 성능 변화를 감지합니다:
        - CPU 사용률 급증 (평균 대비 2 표준편차 이상)
        - I/O 부하 급증 (평균 대비 2 표준편차 이상)
        - 메모리 사용량 급증 (평균 대비 2 표준편차 이상)
        - 버퍼 캐시 히트율 급락 (평균 대비 2 표준편차 이하)
        
        Args:
            results: 파일 분석 결과 리스트
            cpu_trend: CPU 추세
            io_trend: I/O 추세
            memory_trend: 메모리 추세
            buffer_cache_trend: 버퍼 캐시 추세
            
        Returns:
            이상 징후 리스트
        """
        anomalies = []
        
        # CPU 이상 징후 감지
        if cpu_trend and cpu_trend.std_dev > 0:
            anomalies.extend(AnomalyDetector._detect_cpu_anomalies(results, cpu_trend))
        
        # I/O 이상 징후 감지
        if io_trend and io_trend.std_dev > 0:
            anomalies.extend(AnomalyDetector._detect_io_anomalies(results, io_trend))
        
        # 메모리 이상 징후 감지
        if memory_trend and memory_trend.std_dev > 0:
            anomalies.extend(AnomalyDetector._detect_memory_anomalies(results, memory_trend))
        
        # 버퍼 캐시 히트율 이상 징후 감지 (하락)
        if buffer_cache_trend and buffer_cache_trend.std_dev > 0:
            anomalies.extend(AnomalyDetector._detect_buffer_cache_anomalies(results, buffer_cache_trend))
        
        # 심각도 순으로 정렬 (high > medium > low)
        severity_order = {"high": 0, "medium": 1, "low": 2}
        anomalies.sort(key=lambda a: severity_order.get(a.severity, 3))
        
        return anomalies
    
    @staticmethod
    def _detect_cpu_anomalies(results: List[BatchFileResult], cpu_trend: TrendMetrics) -> List[Anomaly]:
        """CPU 이상 징후 감지"""
        anomalies = []
        threshold_high = cpu_trend.avg + (2 * cpu_trend.std_dev)
        threshold_low = cpu_trend.avg - (2 * cpu_trend.std_dev)
        
        for i, (value, timestamp) in enumerate(zip(cpu_trend.values, cpu_trend.timestamps)):
            if value > threshold_high:
                severity = "high" if value > threshold_high * 1.5 else "medium"
                anomalies.append(Anomaly(
                    timestamp=timestamp,
                    filename=results[i].filename if i < len(results) else "",
                    metric_name="CPU Usage",
                    value=value,
                    expected_range=(threshold_low, threshold_high),
                    severity=severity,
                    description=f"CPU 사용률이 평균({cpu_trend.avg:.2f}) 대비 {((value - cpu_trend.avg) / cpu_trend.avg * 100):.1f}% 증가했습니다."
                ))
        
        return anomalies
    
    @staticmethod
    def _detect_io_anomalies(results: List[BatchFileResult], io_trend: TrendMetrics) -> List[Anomaly]:
        """I/O 이상 징후 감지"""
        anomalies = []
        threshold_high = io_trend.avg + (2 * io_trend.std_dev)
        threshold_low = io_trend.avg - (2 * io_trend.std_dev)
        
        for i, (value, timestamp) in enumerate(zip(io_trend.values, io_trend.timestamps)):
            if value > threshold_high:
                severity = "high" if value > threshold_high * 1.5 else "medium"
                anomalies.append(Anomaly(
                    timestamp=timestamp,
                    filename=results[i].filename if i < len(results) else "",
                    metric_name="I/O IOPS",
                    value=value,
                    expected_range=(threshold_low, threshold_high),
                    severity=severity,
                    description=f"I/O 부하가 평균({io_trend.avg:.2f}) 대비 {((value - io_trend.avg) / io_trend.avg * 100):.1f}% 증가했습니다."
                ))
        
        return anomalies
    
    @staticmethod
    def _detect_memory_anomalies(results: List[BatchFileResult], memory_trend: TrendMetrics) -> List[Anomaly]:
        """메모리 이상 징후 감지"""
        anomalies = []
        threshold_high = memory_trend.avg + (2 * memory_trend.std_dev)
        threshold_low = memory_trend.avg - (2 * memory_trend.std_dev)
        
        for i, (value, timestamp) in enumerate(zip(memory_trend.values, memory_trend.timestamps)):
            if value > threshold_high:
                severity = "medium"
                anomalies.append(Anomaly(
                    timestamp=timestamp,
                    filename=results[i].filename if i < len(results) else "",
                    metric_name="Memory Usage",
                    value=value,
                    expected_range=(threshold_low, threshold_high),
                    severity=severity,
                    description=f"메모리 사용량이 평균({memory_trend.avg:.2f} GB) 대비 {((value - memory_trend.avg) / memory_trend.avg * 100):.1f}% 증가했습니다."
                ))
        
        return anomalies
    
    @staticmethod
    def _detect_buffer_cache_anomalies(results: List[BatchFileResult], buffer_cache_trend: TrendMetrics) -> List[Anomaly]:
        """버퍼 캐시 히트율 이상 징후 감지 (하락)"""
        anomalies = []
        threshold_high = buffer_cache_trend.avg + (2 * buffer_cache_trend.std_dev)
        threshold_low = buffer_cache_trend.avg - (2 * buffer_cache_trend.std_dev)
        
        for i, (value, timestamp) in enumerate(zip(buffer_cache_trend.values, buffer_cache_trend.timestamps)):
            if value < threshold_low:
                severity = "high" if value < threshold_low * 0.9 else "medium"
                anomalies.append(Anomaly(
                    timestamp=timestamp,
                    filename=results[i].filename if i < len(results) else "",
                    metric_name="Buffer Cache Hit Ratio",
                    value=value,
                    expected_range=(threshold_low, threshold_high),
                    severity=severity,
                    description=f"버퍼 캐시 히트율이 평균({buffer_cache_trend.avg:.2f}%) 대비 {((buffer_cache_trend.avg - value) / buffer_cache_trend.avg * 100):.1f}% 하락했습니다."
                ))
        
        return anomalies
