"""
Markdown 대기 이벤트 포맷터

Top Wait Events 섹션을 Markdown 형식으로 변환합니다.
"""

from typing import List, Dict, Any
from ...data_models import AnalysisMetrics


class WaitEventsFormatterMixin:
    """대기 이벤트 포맷터 믹스인"""
    
    # Wait Class별 마이그레이션 고려사항
    WAIT_CLASS_INFO = {
        'DB CPU': {
            'ko': 'CPU 사용량. 인스턴스 vCPU 산정 기준',
            'en': 'CPU usage. Basis for instance vCPU sizing'
        },
        'User I/O': {
            'ko': '데이터 파일 읽기/쓰기 대기. 스토리지 성능 중요',
            'en': 'Data file read/write wait. Storage performance critical'
        },
        'System I/O': {
            'ko': '시스템 I/O 대기. 로그 파일 동기화 등',
            'en': 'System I/O wait. Log file sync etc.'
        },
        'Concurrency': {
            'ko': '락, 래치 등 동시성 제어 대기',
            'en': 'Lock, latch concurrency control wait'
        },
        'Network': {
            'ko': '네트워크 통신 대기. 연결 풀 설정 검토',
            'en': 'Network communication wait. Review connection pool'
        },
        'Commit': {
            'ko': '트랜잭션 커밋 대기. Aurora 분산 로그 이점',
            'en': 'Transaction commit wait. Aurora distributed log benefit'
        },
        'Other': {
            'ko': '기타 대기 이벤트',
            'en': 'Other wait events'
        }
    }
    
    @staticmethod
    def _format_wait_events(metrics: AnalysisMetrics, language: str) -> str:
        """대기 이벤트 섹션 포맷"""
        if not metrics.top_wait_events:
            return ""
        
        if language == "ko":
            return WaitEventsFormatterMixin._format_ko(metrics.top_wait_events)
        return WaitEventsFormatterMixin._format_en(metrics.top_wait_events)
    
    @staticmethod
    def _format_ko(wait_events: List[Dict[str, Any]]) -> str:
        """한국어 대기 이벤트"""
        sections = []
        
        sections.append("# ⏱️ Top Wait Events\n")
        sections.append("> Oracle 데이터베이스의 주요 대기 이벤트입니다.")
        sections.append("> 성능 병목 지점 파악 및 마이그레이션 후 주의 영역 식별에 활용됩니다.\n")
        
        # 테이블 헤더
        sections.append("| 순위 | Wait Class | Event Name | DB Time % | 설명 |")
        sections.append("|------|------------|------------|-----------|------|")
        
        for i, event in enumerate(wait_events, 1):
            wait_class = event.get('wait_class', 'Unknown')
            event_name = event.get('event_name', 'Unknown')
            pctdbt = event.get('avg_pctdbt', 0.0)
            
            # Wait Class 설명
            info = WaitEventsFormatterMixin.WAIT_CLASS_INFO.get(wait_class, {})
            desc = info.get('ko', '-')
            
            sections.append(f"| {i} | {wait_class} | {event_name} | {pctdbt:.1f}% | {desc} |")
        
        # 마이그레이션 영향 분석
        sections.append("\n## 마이그레이션 영향 분석\n")
        
        # Wait Class별 비중 계산
        class_totals: Dict[str, float] = {}
        for event in wait_events:
            wc = event.get('wait_class', 'Other')
            class_totals[wc] = class_totals.get(wc, 0) + event.get('avg_pctdbt', 0)
        
        implications = []
        if class_totals.get('User I/O', 0) > 20:
            implications.append(f"- **User I/O 비중 높음 ({class_totals['User I/O']:.1f}%)**: "
                              "스토리지 성능이 중요, Aurora I/O 최적화 필요")
        if class_totals.get('DB CPU', 0) > 50:
            implications.append(f"- **CPU 집약적 워크로드 ({class_totals['DB CPU']:.1f}%)**: "
                              "적절한 vCPU 수 확보 필요")
        if class_totals.get('Concurrency', 0) > 10:
            implications.append(f"- **동시성 이슈 존재 ({class_totals['Concurrency']:.1f}%)**: "
                              "락 경합 패턴 분석 필요")
        if class_totals.get('Commit', 0) > 5:
            implications.append(f"- **커밋 대기 존재 ({class_totals['Commit']:.1f}%)**: "
                              "Aurora 분산 스토리지로 개선 가능")
        
        if implications:
            sections.extend(implications)
        else:
            sections.append("- 특별한 성능 이슈 없음")
        
        return "\n".join(sections)
    
    @staticmethod
    def _format_en(wait_events: List[Dict[str, Any]]) -> str:
        """영어 대기 이벤트"""
        sections = []
        
        sections.append("# ⏱️ Top Wait Events\n")
        sections.append("> Key wait events from the Oracle database.")
        sections.append("> Used to identify performance bottlenecks and areas of concern.\n")
        
        sections.append("| Rank | Wait Class | Event Name | DB Time % | Description |")
        sections.append("|------|------------|------------|-----------|-------------|")
        
        for i, event in enumerate(wait_events, 1):
            wait_class = event.get('wait_class', 'Unknown')
            event_name = event.get('event_name', 'Unknown')
            pctdbt = event.get('avg_pctdbt', 0.0)
            
            info = WaitEventsFormatterMixin.WAIT_CLASS_INFO.get(wait_class, {})
            desc = info.get('en', '-')
            
            sections.append(f"| {i} | {wait_class} | {event_name} | {pctdbt:.1f}% | {desc} |")
        
        return "\n".join(sections)
