"""
인스턴스 추천 모듈

리소스 사용량 기반으로 RDS 인스턴스 사이즈를 추천합니다.
"""

from typing import Optional, Dict, Tuple
from ..models import TargetDatabase, InstanceRecommendation


# r6i 인스턴스 패밀리 스펙 (vCPU, Memory GiB)
R6I_INSTANCES = {
    "db.r6i.large": (2, 16),
    "db.r6i.xlarge": (4, 32),
    "db.r6i.2xlarge": (8, 64),
    "db.r6i.4xlarge": (16, 128),
    "db.r6i.8xlarge": (32, 256),
    "db.r6i.12xlarge": (48, 384),
    "db.r6i.16xlarge": (64, 512),
    "db.r6i.24xlarge": (96, 768),
    "db.r6i.32xlarge": (128, 1024),
}


def select_instance_type(required_vcpu: int, required_memory_gb: int) -> Optional[str]:
    """
    CPU와 메모리 요구사항을 만족하는 최소 r6i 인스턴스 선택
    
    Args:
        required_vcpu: 필요한 vCPU 수
        required_memory_gb: 필요한 메모리 (GB)
    
    Returns:
        Optional[str]: 선택된 인스턴스 타입 (예: "db.r6i.4xlarge") 또는 None
    """
    # 요구사항을 만족하는 인스턴스 필터링
    suitable_instances = []
    
    for instance_type, (vcpu, memory_gib) in R6I_INSTANCES.items():
        if vcpu >= required_vcpu and memory_gib >= required_memory_gb:
            suitable_instances.append((instance_type, vcpu, memory_gib))
    
    if not suitable_instances:
        # 요구사항을 만족하는 인스턴스가 없음
        return None
    
    # vCPU 기준으로 정렬하여 최소 인스턴스 선택
    suitable_instances.sort(key=lambda x: (x[1], x[2]))
    
    return suitable_instances[0][0]


def recommend_instance_size(
    target: TargetDatabase,
    complexity_score: float,
    cpu_p99_pct: float,
    num_cpus: int,
    memory_avg_gb: float,
    physical_memory_gb: float
) -> Optional[InstanceRecommendation]:
    """
    리소스 사용량 기반 RDS 인스턴스 사이즈 추천
    
    - CPU: P99 CPU 사용률 + 30% 여유분
    - 메모리: 현재 SGA+PGA + 20% 여유분
    - 난이도 > 7: RDS for Oracle만 추천
    - 난이도 <= 7: Aurora MySQL/PostgreSQL도 추천
    
    Args:
        target: 타겟 데이터베이스
        complexity_score: 마이그레이션 난이도 점수
        cpu_p99_pct: P99 CPU 사용률
        num_cpus: 현재 CPU 수
        memory_avg_gb: 평균 메모리 사용량 (GB)
        physical_memory_gb: 물리 메모리 크기 (GB)
    
    Returns:
        Optional[InstanceRecommendation]: 인스턴스 추천 정보 또는 None
    """
    # 난이도 기반 타겟 필터링
    if complexity_score > 7.0:
        # 난이도가 높으면 RDS for Oracle만 추천
        if target != TargetDatabase.RDS_ORACLE:
            return None
    
    # CPU 요구사항 계산 (P99 + 30% 여유분)
    # 필요한 vCPU 계산
    # P99 사용률 기준으로 필요한 CPU 수 계산 후 30% 여유분 추가
    if cpu_p99_pct > 0:
        required_vcpu = int((num_cpus * (cpu_p99_pct / 100.0) * 1.3) + 0.5)
    else:
        required_vcpu = num_cpus
    
    # 최소 2 vCPU
    required_vcpu = max(required_vcpu, 2)
    
    # 메모리 요구사항 계산 (현재 + 20% 여유분)
    if memory_avg_gb > 0:
        required_memory_gb = int(memory_avg_gb * 1.2 + 0.5)
    else:
        # 메모리 정보가 없으면 물리 메모리 기준
        required_memory_gb = int(physical_memory_gb * 1.2 + 0.5)
    
    # 최소 16 GB
    required_memory_gb = max(required_memory_gb, 16)
    
    # 인스턴스 타입 선택
    instance_type = select_instance_type(required_vcpu, required_memory_gb)
    
    if not instance_type:
        # 요구사항을 만족하는 인스턴스가 없음
        return None
    
    # 선택된 인스턴스 스펙
    selected_vcpu, selected_memory_gib = R6I_INSTANCES[instance_type]
    
    # CPU 여유분 계산
    if cpu_p99_pct > 0:
        cpu_headroom_pct = ((selected_vcpu / num_cpus) - (cpu_p99_pct / 100.0)) * 100
    else:
        cpu_headroom_pct = 30.0  # 기본 여유분
    
    # 메모리 여유분 계산
    if memory_avg_gb > 0:
        memory_headroom_pct = ((selected_memory_gib - memory_avg_gb) / memory_avg_gb) * 100
    else:
        memory_headroom_pct = 20.0  # 기본 여유분
    
    return InstanceRecommendation(
        instance_type=instance_type,
        vcpu=selected_vcpu,
        memory_gib=selected_memory_gib,
        current_cpu_usage_pct=cpu_p99_pct,
        current_memory_gb=memory_avg_gb,
        cpu_headroom_pct=cpu_headroom_pct,
        memory_headroom_pct=memory_headroom_pct,
        estimated_monthly_cost_usd=None  # 비용 계산은 선택적
    )
