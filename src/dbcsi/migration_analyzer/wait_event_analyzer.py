"""
대기 이벤트 분석 모듈

대기 이벤트를 카테고리별로 분류하고 분석합니다.
"""

from typing import Dict, Any, List


def analyze_wait_events(statspack_data) -> Dict[str, Any]:
    """
    대기 이벤트 분석
    
    대기 이벤트를 카테고리별로 분류하고 분석합니다.
    
    Args:
        statspack_data: StatspackData 또는 AWRData 객체
    
    Returns:
        Dict[str, Any]: 대기 이벤트 분석 결과
            - db_cpu_pct: DB CPU 비율
            - user_io_pct: User I/O 대기 비율
            - system_io_pct: System I/O 대기 비율
            - commit_pct: Commit 대기 비율
            - network_pct: Network 대기 비율
            - other_pct: 기타 대기 비율
            - top_events: 상위 대기 이벤트 목록
            - recommendations: 최적화 권장사항
    """
    result: Dict[str, Any] = {
        "db_cpu_pct": 0.0,
        "user_io_pct": 0.0,
        "system_io_pct": 0.0,
        "commit_pct": 0.0,
        "network_pct": 0.0,
        "other_pct": 0.0,
        "top_events": [],
        "recommendations": []
    }
    
    if not statspack_data.wait_events:
        return result
    
    # 대기 이벤트 카테고리별 분류
    category_totals: Dict[str, float] = {
        "DB CPU": 0.0,
        "User I/O": 0.0,
        "System I/O": 0.0,
        "Commit": 0.0,
        "Network": 0.0,
        "Other": 0.0
    }
    
    total_time = 0.0
    
    for event in statspack_data.wait_events:
        wait_class = event.wait_class
        time_s = event.total_time_s if event.total_time_s else 0.0
        
        total_time += time_s
        
        # 카테고리별 분류
        if "CPU" in wait_class:
            category_totals["DB CPU"] += time_s
        elif "User I/O" in wait_class:
            category_totals["User I/O"] += time_s
        elif "System I/O" in wait_class:
            category_totals["System I/O"] += time_s
        elif "Commit" in wait_class:
            category_totals["Commit"] += time_s
        elif "Network" in wait_class:
            category_totals["Network"] += time_s
        else:
            category_totals["Other"] += time_s
    
    # 비율 계산
    if total_time > 0:
        result["db_cpu_pct"] = (category_totals["DB CPU"] / total_time) * 100
        result["user_io_pct"] = (category_totals["User I/O"] / total_time) * 100
        result["system_io_pct"] = (category_totals["System I/O"] / total_time) * 100
        result["commit_pct"] = (category_totals["Commit"] / total_time) * 100
        result["network_pct"] = (category_totals["Network"] / total_time) * 100
        result["other_pct"] = (category_totals["Other"] / total_time) * 100
    
    # 상위 이벤트 추출 (시간 기준 상위 10개)
    sorted_events = sorted(
        statspack_data.wait_events,
        key=lambda e: e.total_time_s if e.total_time_s else 0.0,
        reverse=True
    )
    result["top_events"] = [
        {
            "event_name": e.event_name,
            "wait_class": e.wait_class,
            "total_time_s": e.total_time_s,
            "pctdbt": e.pctdbt
        }
        for e in sorted_events[:10]
    ]
    
    # 최적화 권장사항 생성
    recommendations = []
    
    if result["db_cpu_pct"] > 70:
        recommendations.append("DB CPU 사용률이 매우 높습니다. 쿼리 튜닝 및 인스턴스 크기 증가를 고려하세요.")
    elif result["db_cpu_pct"] > 50:
        recommendations.append("DB CPU 사용률이 높습니다. 쿼리 최적화를 권장합니다.")
    
    if result["user_io_pct"] > 40:
        recommendations.append("User I/O 대기가 높습니다. 인덱스 최적화, 파티셔닝, 스토리지 타입 업그레이드를 고려하세요.")
    
    if result["commit_pct"] > 20:
        recommendations.append("Commit 대기가 높습니다. 배치 커밋 또는 비동기 커밋을 고려하세요.")
    
    # control file 관련 대기 이벤트 확인
    control_file_events = [
        e for e in statspack_data.wait_events
        if "control file" in e.event_name.lower()
    ]
    if control_file_events:
        recommendations.append("Control file 관련 대기가 감지되었습니다. Aurora/RDS 환경에서는 자동으로 개선됩니다.")
    
    result["recommendations"] = recommendations
    
    return result
