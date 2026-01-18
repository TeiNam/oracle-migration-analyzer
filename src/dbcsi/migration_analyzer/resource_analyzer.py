"""
리소스 사용량 분석 모듈

CPU, 메모리, 디스크, IOPS 사용량을 분석합니다.
"""

from typing import Dict, Any
import statistics
from ..logging_config import get_logger

# 로거 초기화
logger = get_logger("resource_analyzer")


def analyze_resource_usage(statspack_data) -> Dict[str, Any]:
    """
    리소스 사용량 분석
    
    CPU, 메모리, 디스크, IOPS 사용량을 분석합니다.
    
    Args:
        statspack_data: StatspackData 또는 AWRData 객체
    
    Returns:
        Dict[str, Any]: 리소스 사용량 분석 결과
            - cpu_avg_pct: 평균 CPU 사용률
            - cpu_p99_pct: P99 CPU 사용률
            - memory_avg_gb: 평균 메모리 사용량 (SGA+PGA)
            - memory_max_gb: 최대 메모리 사용량
            - disk_size_gb: 디스크 크기
            - read_iops_avg: 평균 읽기 IOPS
            - write_iops_avg: 평균 쓰기 IOPS
            - total_iops_avg: 평균 총 IOPS
            - total_iops_p99: P99 총 IOPS
    """
    logger.debug("리소스 사용량 분석 시작")
    result: Dict[str, Any] = {}
    
    # CPU 사용률 분석
    if statspack_data.main_metrics:
        logger.debug(f"메인 메트릭 개수: {len(statspack_data.main_metrics)}")
        cpu_values = [m.cpu_per_s for m in statspack_data.main_metrics if m.cpu_per_s is not None]
        if cpu_values:
            logger.debug(f"CPU 값 개수: {len(cpu_values)}")
            result["cpu_avg_pct"] = statistics.mean(cpu_values)
            # P99 계산 (99번째 백분위수)
            sorted_cpu = sorted(cpu_values)
            p99_index = int(len(sorted_cpu) * 0.99)
            result["cpu_p99_pct"] = sorted_cpu[min(p99_index, len(sorted_cpu) - 1)]
            logger.debug(f"CPU 평균: {result['cpu_avg_pct']:.2f}%, P99: {result['cpu_p99_pct']:.2f}%")
        else:
            result["cpu_avg_pct"] = 0.0
            result["cpu_p99_pct"] = 0.0
    else:
        result["cpu_avg_pct"] = 0.0
        result["cpu_p99_pct"] = 0.0
    
    # 메모리 사용량 분석
    if statspack_data.memory_metrics:
        logger.debug(f"메모리 메트릭 개수: {len(statspack_data.memory_metrics)}")
        memory_totals = [m.total_gb for m in statspack_data.memory_metrics if m.total_gb is not None]
        if memory_totals:
            result["memory_avg_gb"] = statistics.mean(memory_totals)
            result["memory_max_gb"] = max(memory_totals)
            logger.debug(f"메모리 평균: {result['memory_avg_gb']:.2f} GB, 최대: {result['memory_max_gb']:.2f} GB")
        else:
            result["memory_avg_gb"] = 0.0
            result["memory_max_gb"] = 0.0
    else:
        result["memory_avg_gb"] = 0.0
        result["memory_max_gb"] = 0.0
    
    # 디스크 크기 분석
    if statspack_data.disk_sizes:
        disk_sizes = [d.size_gb for d in statspack_data.disk_sizes if d.size_gb is not None]
        if disk_sizes:
            result["disk_size_gb"] = max(disk_sizes)
            logger.debug(f"최대 디스크 크기: {result['disk_size_gb']:.2f} GB")
        else:
            result["disk_size_gb"] = 0.0
    else:
        result["disk_size_gb"] = 0.0
    
    # IOPS 분석
    if statspack_data.main_metrics:
        read_iops = [m.read_iops for m in statspack_data.main_metrics if m.read_iops is not None]
        write_iops = [m.write_iops for m in statspack_data.main_metrics if m.write_iops is not None]
        
        if read_iops:
            result["read_iops_avg"] = statistics.mean(read_iops)
        else:
            result["read_iops_avg"] = 0.0
        
        if write_iops:
            result["write_iops_avg"] = statistics.mean(write_iops)
        else:
            result["write_iops_avg"] = 0.0
        
        # 총 IOPS 계산
        if read_iops and write_iops:
            total_iops = [r + w for r, w in zip(read_iops, write_iops)]
            result["total_iops_avg"] = statistics.mean(total_iops)
            # P99 IOPS
            sorted_iops = sorted(total_iops)
            p99_index = int(len(sorted_iops) * 0.99)
            result["total_iops_p99"] = sorted_iops[min(p99_index, len(sorted_iops) - 1)]
            logger.debug(f"IOPS 평균: {result['total_iops_avg']:.2f}, P99: {result['total_iops_p99']:.2f}")
        else:
            result["total_iops_avg"] = 0.0
            result["total_iops_p99"] = 0.0
    else:
        result["read_iops_avg"] = 0.0
        result["write_iops_avg"] = 0.0
        result["total_iops_avg"] = 0.0
        result["total_iops_p99"] = 0.0
    
    logger.debug("리소스 사용량 분석 완료")
    return result
