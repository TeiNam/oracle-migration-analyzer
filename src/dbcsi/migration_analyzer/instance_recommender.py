"""
인스턴스 추천 모듈

리소스 사용량 기반으로 RDS 인스턴스 사이즈를 추천합니다.
"""

from typing import Optional, Dict, Tuple, List
from ..models import TargetDatabase, InstanceRecommendation
from ..models.base_models import SGAAdvice


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


def get_recommended_sga_from_advice(sga_advice: List[SGAAdvice]) -> float:
    """
    SGA 권장사항에서 최대 권장 SGA 크기 추출 (GB 단위)
    
    RAC 환경에서는 모든 인스턴스의 권장 SGA 중 최대값을 반환합니다.
    권장 SGA는 size_factor가 1.0보다 큰 값 중 Physical Reads가 
    더 이상 감소하지 않는 지점의 SGA 크기입니다.
    
    Args:
        sga_advice: SGAAdvice 객체 리스트
        
    Returns:
        float: 권장 SGA 크기 (GB), 권장사항이 없으면 0.0
    """
    if not sga_advice:
        return 0.0
    
    # 인스턴스별로 그룹화
    instances: Dict[int, List[SGAAdvice]] = {}
    for advice in sga_advice:
        inst_id = advice.inst_id
        if inst_id not in instances:
            instances[inst_id] = []
        instances[inst_id].append(advice)
    
    max_recommended_sga_mb = 0.0
    
    for inst_id, advice_list in instances.items():
        # size_factor 기준으로 정렬
        sorted_list = sorted(advice_list, key=lambda x: x.sga_size_factor)
        
        # 현재 SGA 찾기 (size_factor가 1.0인 것)
        current_sga = next(
            (a for a in sorted_list if abs(a.sga_size_factor - 1.0) < 0.01), None
        )
        
        if not current_sga:
            continue
        
        # size_factor > 1.0인 항목들 확인
        larger_factors = [a for a in sorted_list if a.sga_size_factor > 1.0]
        
        if not larger_factors:
            # 확장 권장사항이 없으면 현재 SGA 사용
            if current_sga.sga_size > max_recommended_sga_mb:
                max_recommended_sga_mb = current_sga.sga_size
            continue
        
        # Physical Reads가 더 이상 감소하지 않는 지점 찾기
        # (가장 많이 반복되는 Physical Reads 값의 가장 작은 Size Factor)
        factors_from_current = [a for a in sorted_list if a.sga_size_factor >= 1.0]
        
        # Physical Reads 값별 빈도수 계산
        reads_count: Dict[int, int] = {}
        for a in factors_from_current:
            reads = a.estd_physical_reads
            reads_count[reads] = reads_count.get(reads, 0) + 1
        
        # 가장 많이 반복되는 Physical Reads 값 찾기
        max_count = max(reads_count.values())
        most_common_reads = [r for r, c in reads_count.items() if c == max_count]
        
        # 가장 많이 반복되는 값 중 가장 작은 Physical Reads 선택
        target_reads = min(most_common_reads)
        
        # 해당 Physical Reads를 가진 항목들 중 가장 작은 Size Factor의 SGA
        candidates = [a for a in factors_from_current if a.estd_physical_reads == target_reads]
        optimal_sga = min(candidates, key=lambda x: x.sga_size_factor)
        
        if optimal_sga.sga_size > max_recommended_sga_mb:
            max_recommended_sga_mb = optimal_sga.sga_size
    
    # MB를 GB로 변환
    return max_recommended_sga_mb / 1024.0


def recommend_instance_size(
    target: TargetDatabase,
    complexity_score: float,
    cpu_p99_pct: float,
    num_cpus: int,
    memory_avg_gb: float,
    physical_memory_gb: float,
    sga_advice: Optional[List[SGAAdvice]] = None
) -> Optional[InstanceRecommendation]:
    """
    리소스 사용량 기반 RDS 인스턴스 사이즈 추천
    
    - CPU: P99 CPU 사용률 + 30% 여유분
    - 메모리: max(현재 SGA+PGA, 권장 SGA+PGA) + 20% 여유분
    - 난이도 > 7: RDS for Oracle만 추천
    - 난이도 <= 7: Aurora MySQL/PostgreSQL도 추천
    
    Args:
        target: 타겟 데이터베이스
        complexity_score: 마이그레이션 난이도 점수
        cpu_p99_pct: P99 CPU 사용률
        num_cpus: 현재 CPU 수
        memory_avg_gb: 평균 메모리 사용량 (GB)
        physical_memory_gb: 물리 메모리 크기 (GB)
        sga_advice: SGA 권장사항 리스트 (Optional)
    
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
    
    # SGA 권장사항에서 권장 SGA 크기 추출
    recommended_sga_gb = 0.0
    if sga_advice:
        recommended_sga_gb = get_recommended_sga_from_advice(sga_advice)
    
    # 메모리 요구사항 계산
    # 권장 SGA가 있으면 PGA 추정치(현재 메모리의 약 10%)를 더해서 비교
    if memory_avg_gb > 0:
        # PGA 추정: 현재 메모리 사용량의 약 10% (SGA가 대부분이므로)
        estimated_pga_gb = memory_avg_gb * 0.1
        
        # 권장 SGA + PGA vs 현재 메모리 중 큰 값 선택
        if recommended_sga_gb > 0:
            recommended_total_gb = recommended_sga_gb + estimated_pga_gb
            base_memory_gb = max(memory_avg_gb, recommended_total_gb)
        else:
            base_memory_gb = memory_avg_gb
        
        required_memory_gb = int(base_memory_gb * 1.2 + 0.5)
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
