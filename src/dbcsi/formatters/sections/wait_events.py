"""
Top Wait Events 섹션 포맷터

Oracle 데이터베이스의 주요 대기 이벤트를 표시합니다.
"""

from typing import List, Dict, Any
from collections import defaultdict
from ...models import StatspackData


class WaitEventsFormatter:
    """대기 이벤트 포맷터"""
    
    # Wait Class별 마이그레이션 영향 설명
    WAIT_CLASS_IMPACT = {
        "User I/O": {
            "desc_ko": "데이터 파일 읽기/쓰기 대기",
            "desc_en": "Data file read/write wait",
            "impact_ko": "스토리지 성능 중요, Aurora I/O 최적화 검토",
            "impact_en": "Storage performance critical, review Aurora I/O optimization"
        },
        "User": {
            "desc_ko": "사용자 I/O 대기 (데이터 파일 읽기/쓰기)",
            "desc_en": "User I/O wait (data file read/write)",
            "impact_ko": "스토리지 성능 중요, Aurora I/O 최적화 검토",
            "impact_en": "Storage performance critical, review Aurora I/O optimization"
        },
        "Concurrency": {
            "desc_ko": "락, 래치 등 동시성 제어 대기",
            "desc_en": "Lock, latch concurrency control wait",
            "impact_ko": "락 경합 패턴이 타겟 DB에서도 유사하게 발생 가능",
            "impact_en": "Lock contention patterns may occur similarly in target DB"
        },
        "Network": {
            "desc_ko": "네트워크 통신 대기",
            "desc_en": "Network communication wait",
            "impact_ko": "애플리케이션-DB 간 거리, 연결 풀 설정 검토",
            "impact_en": "Review app-DB distance, connection pool settings"
        },
        "Commit": {
            "desc_ko": "트랜잭션 커밋 대기",
            "desc_en": "Transaction commit wait",
            "impact_ko": "Aurora는 분산 로그로 커밋 성능 개선 가능",
            "impact_en": "Aurora can improve commit performance with distributed log"
        },
        "Configuration": {
            "desc_ko": "설정 관련 대기",
            "desc_en": "Configuration related wait",
            "impact_ko": "타겟 DB 파라미터 튜닝 필요",
            "impact_en": "Target DB parameter tuning required"
        },
        "System I/O": {
            "desc_ko": "시스템 I/O 대기",
            "desc_en": "System I/O wait",
            "impact_ko": "로그 파일, 컨트롤 파일 I/O - Aurora에서 자동 관리",
            "impact_en": "Log/control file I/O - auto-managed in Aurora"
        },
        "System": {
            "desc_ko": "시스템 I/O 대기 (로그/컨트롤 파일)",
            "desc_en": "System I/O wait (log/control files)",
            "impact_ko": "로그 파일, 컨트롤 파일 I/O - Aurora에서 자동 관리",
            "impact_en": "Log/control file I/O - auto-managed in Aurora"
        },
        "Scheduler": {
            "desc_ko": "스케줄러 대기",
            "desc_en": "Scheduler wait",
            "impact_ko": "CPU 리소스 경합 - 인스턴스 사이징 검토",
            "impact_en": "CPU resource contention - review instance sizing"
        },
        "Idle": {
            "desc_ko": "유휴 대기",
            "desc_en": "Idle wait",
            "impact_ko": "정상적인 유휴 상태 - 무시 가능",
            "impact_en": "Normal idle state - can be ignored"
        },
        "DB": {
            "desc_ko": "데이터베이스 CPU 사용",
            "desc_en": "Database CPU usage",
            "impact_ko": "CPU 사용량 - 인스턴스 vCPU 사이징 기준",
            "impact_en": "CPU usage - basis for instance vCPU sizing"
        },
        "Other": {
            "desc_ko": "기타 대기 이벤트",
            "desc_en": "Other wait events",
            "impact_ko": "개별 이벤트 분석 필요",
            "impact_en": "Individual event analysis required"
        },
        "Application": {
            "desc_ko": "애플리케이션 레벨 대기",
            "desc_en": "Application level wait",
            "impact_ko": "애플리케이션 코드 최적화 검토",
            "impact_en": "Review application code optimization"
        },
        "Cluster": {
            "desc_ko": "RAC 클러스터 통신 대기",
            "desc_en": "RAC cluster communication wait",
            "impact_ko": "Aurora는 단일 Writer - RAC 관련 대기 제거됨",
            "impact_en": "Aurora single Writer - RAC waits eliminated"
        },
        "Administrative": {
            "desc_ko": "관리 작업 대기",
            "desc_en": "Administrative task wait",
            "impact_ko": "DBA 작업 관련 - 마이그레이션 영향 낮음",
            "impact_en": "DBA task related - low migration impact"
        }
    }
    
    @staticmethod
    def format(data: StatspackData, language: str = "ko") -> str:
        """Top Wait Events 섹션 포맷
        
        Args:
            data: Statspack/AWR 데이터
            language: 출력 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식의 문자열
        """
        if not data.wait_events:
            return ""
        
        if language == "ko":
            return WaitEventsFormatter._format_ko(data)
        return WaitEventsFormatter._format_en(data)
    
    @staticmethod
    def _aggregate_wait_events(data: StatspackData) -> List[Dict[str, Any]]:
        """대기 이벤트를 집계하여 상위 이벤트 반환"""
        event_totals: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"wait_class": "", "total_time": 0, "total_pctdbt": 0, "count": 0}
        )
        
        for event in data.wait_events:
            key = event.event_name
            event_totals[key]["wait_class"] = event.wait_class
            event_totals[key]["total_time"] += event.total_time_s
            event_totals[key]["total_pctdbt"] += event.pctdbt
            event_totals[key]["count"] += 1
        
        # 평균 pctdbt 계산 및 정렬
        result = []
        for event_name, data_dict in event_totals.items():
            avg_pctdbt = data_dict["total_pctdbt"] / data_dict["count"] if data_dict["count"] > 0 else 0
            result.append({
                "event_name": event_name,
                "wait_class": data_dict["wait_class"],
                "total_time": data_dict["total_time"],
                "avg_pctdbt": avg_pctdbt
            })
        
        # DB Time % 기준 정렬
        result.sort(key=lambda x: x["avg_pctdbt"], reverse=True)
        return result[:10]  # 상위 10개
    
    @staticmethod
    def _format_ko(data: StatspackData) -> str:
        """한국어 대기 이벤트"""
        lines = []
        
        lines.append("## ⏱️ Top Wait Events\n")
        lines.append("### 이 섹션의 목적\n")
        lines.append("Oracle 데이터베이스가 **어디서 시간을 소비하는지** 보여줍니다.")
        lines.append("대기 이벤트 분석을 통해 성능 병목 지점을 파악하고,")
        lines.append("마이그레이션 후 주의해야 할 영역을 식별합니다.\n")
        lines.append("> **💡 IT 관계자를 위한 설명**")
        lines.append("> - **Wait Event**: 데이터베이스가 특정 작업을 기다리는 동안 발생하는 이벤트")
        lines.append("> - **DB Time %**: 전체 데이터베이스 시간 중 해당 이벤트가 차지하는 비율")
        lines.append("> - 비율이 높은 이벤트일수록 성능에 큰 영향을 미칩니다")
        lines.append("> - 마이그레이션 후에도 유사한 패턴이 나타날 수 있어 사전 대비가 필요합니다\n")
        
        # Wait Class 설명
        lines.append("### Wait Class 설명\n")
        lines.append("> **Wait Class**는 대기 이벤트를 유형별로 분류한 것입니다.")
        lines.append("> 각 클래스별로 마이그레이션 시 고려해야 할 사항이 다릅니다.\n")
        lines.append("| Wait Class | 설명 | 마이그레이션 고려사항 |")
        lines.append("|------------|------|---------------------|")
        
        # 실제 사용된 Wait Class만 표시
        used_classes = set(e.wait_class for e in data.wait_events)
        for wc in used_classes:
            if wc in WaitEventsFormatter.WAIT_CLASS_IMPACT:
                info = WaitEventsFormatter.WAIT_CLASS_IMPACT[wc]
                lines.append(f"| **{wc}** | {info['desc_ko']} | {info['impact_ko']} |")
            else:
                lines.append(f"| **{wc}** | - | - |")
        
        lines.append("")
        
        # Top Wait Events 테이블
        top_events = WaitEventsFormatter._aggregate_wait_events(data)
        
        lines.append("### Top 10 Wait Events\n")
        lines.append("> 가장 많은 시간을 소비한 상위 10개 대기 이벤트입니다.")
        lines.append("> DB Time %가 높은 이벤트일수록 성능 개선 효과가 큽니다.\n")
        lines.append("| 순위 | Wait Class | Event Name | DB Time % | 총 대기 시간 |")
        lines.append("|------|------------|------------|-----------|-------------|")
        
        for i, event in enumerate(top_events, 1):
            time_str = f"{event['total_time']:,.0f}초" if event['total_time'] > 0 else "-"
            lines.append(
                f"| {i} | {event['wait_class']} | {event['event_name']} | "
                f"{event['avg_pctdbt']:.1f}% | {time_str} |"
            )
        
        lines.append("")
        
        # 마이그레이션 영향 분석
        lines.append("### 마이그레이션 영향 분석\n")
        lines.append("> 위 대기 이벤트 패턴을 바탕으로 분석한 마이그레이션 관련 주요 사항입니다.\n")
        
        # Wait Class별 비중 계산
        class_totals: Dict[str, float] = defaultdict(float)
        for event in top_events:
            class_totals[event["wait_class"]] += event["avg_pctdbt"]
        
        analysis_points = []
        
        # User I/O 분석
        user_io_pct = class_totals.get("User I/O", 0) + class_totals.get("User", 0)
        if user_io_pct > 30:
            analysis_points.append(f"- ⚠️ **User I/O 비중 높음 ({user_io_pct:.1f}%)**: "
                                 "디스크 읽기/쓰기 대기가 많습니다. "
                                 "Aurora I/O-Optimized 옵션을 검토하세요.")
        
        # Concurrency 분석
        concurrency_pct = class_totals.get("Concurrency", 0)
        if concurrency_pct > 10:
            analysis_points.append(f"- ⚠️ **Concurrency 이슈 존재 ({concurrency_pct:.1f}%)**: "
                                 "여러 사용자가 동시에 같은 데이터에 접근할 때 발생합니다. "
                                 "애플리케이션 락 패턴 분석이 필요합니다.")
        
        # Network 분석
        network_pct = class_totals.get("Network", 0)
        if network_pct > 5:
            analysis_points.append(f"- ℹ️ **Network 대기 존재 ({network_pct:.1f}%)**: "
                                 "애플리케이션과 DB 간 통신 지연입니다. "
                                 "AWS 내 동일 VPC 배치로 개선 가능합니다.")
        
        # Commit 분석
        commit_pct = class_totals.get("Commit", 0)
        if commit_pct > 5:
            analysis_points.append(f"- ✅ **Commit 대기 ({commit_pct:.1f}%)**: "
                                 "트랜잭션 완료 대기입니다. "
                                 "Aurora의 분산 로그 아키텍처로 개선될 수 있습니다.")
        
        if analysis_points:
            lines.extend(analysis_points)
        else:
            lines.append("- ✅ **특별한 성능 이슈 없음**: 대기 이벤트가 정상 범위 내에 있습니다.")
        
        lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_en(data: StatspackData) -> str:
        """영어 대기 이벤트"""
        lines = []
        
        lines.append("## ⏱️ Top Wait Events\n")
        lines.append("> Wait events indicate where the database spends time waiting.")
        lines.append("> Analyze to identify performance bottlenecks.\n")
        
        top_events = WaitEventsFormatter._aggregate_wait_events(data)
        
        lines.append("### Top 10 Wait Events\n")
        lines.append("| Rank | Wait Class | Event Name | DB Time % | Total Time |")
        lines.append("|------|------------|------------|-----------|------------|")
        
        for i, event in enumerate(top_events, 1):
            time_str = f"{event['total_time']:,.0f}s" if event['total_time'] > 0 else "-"
            lines.append(
                f"| {i} | {event['wait_class']} | {event['event_name']} | "
                f"{event['avg_pctdbt']:.1f}% | {time_str} |"
            )
        
        lines.append("")
        
        return "\n".join(lines)
