"""
성능 메트릭 상세 섹션 포맷터

AWR/Statspack에서 수집된 실제 운영 환경의 성능 데이터를 표시합니다.
"""

from typing import List, Optional
from ...models import StatspackData


class PerformanceMetricsFormatter:
    """성능 메트릭 포맷터"""
    
    @staticmethod
    def format(data: StatspackData, language: str = "ko") -> str:
        """성능 메트릭 상세 섹션 포맷
        
        Args:
            data: Statspack/AWR 데이터
            language: 출력 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식의 문자열
        """
        if not data.main_metrics:
            return ""
        
        if language == "ko":
            return PerformanceMetricsFormatter._format_ko(data)
        return PerformanceMetricsFormatter._format_en(data)
    
    @staticmethod
    def _format_ko(data: StatspackData) -> str:
        """한국어 성능 메트릭 상세"""
        lines = []
        metrics = data.main_metrics
        
        lines.append("## ⚡ 성능 메트릭 상세\n")
        lines.append("### 이 섹션의 목적\n")
        lines.append("AWR/Statspack에서 수집된 **실제 운영 환경의 성능 데이터**입니다.")
        lines.append("이 데이터를 바탕으로 AWS 타겟 인스턴스의 크기(CPU, 메모리, 스토리지)를 결정합니다.\n")
        lines.append("> **💡 IT 관계자를 위한 설명**")
        lines.append("> - **AWR/Statspack**: Oracle이 자동으로 수집하는 성능 통계 리포트")
        lines.append("> - **인스턴스 사이징**: AWS에서 적절한 서버 크기를 선택하는 것")
        lines.append("> - 과소 산정 → 성능 문제 발생, 과대 산정 → 비용 낭비\n")
        
        # 분석 기간
        if metrics:
            first_time = metrics[0].end
            last_time = metrics[-1].end
            lines.append(f"**분석 기간**: {first_time} ~ {last_time}\n")
        
        # CPU 사용량
        cpu_values = [m.cpu_per_s for m in metrics]
        avg_cpu = sum(cpu_values) / len(cpu_values)
        max_cpu = max(cpu_values)
        min_cpu = min(cpu_values)
        
        lines.append("### CPU 사용량\n")
        lines.append("> **CPU/s란?** 초당 CPU 사용량입니다. 이 값이 높을수록 더 많은 vCPU가 필요합니다.\n")
        lines.append("| 메트릭 | 값 | 의미 |")
        lines.append("|--------|-----|------|")
        lines.append(f"| 평균 CPU/s | {avg_cpu:.2f} | 일반적인 부하 상태 |")
        lines.append(f"| 최소 CPU/s | {min_cpu:.2f} | 가장 한가한 시점 |")
        lines.append(f"| 최대 CPU/s | {max_cpu:.2f} | 가장 바쁜 시점 (피크) |")
        lines.append("")
        
        # I/O 성능
        read_iops = [m.read_iops for m in metrics]
        write_iops = [m.write_iops for m in metrics]
        
        # read_mb_s, write_mb_s가 있는 경우
        read_mbps = [getattr(m, 'read_mb_s', 0) or 0 for m in metrics]
        write_mbps = [getattr(m, 'write_mb_s', 0) or 0 for m in metrics]
        
        avg_read_iops = sum(read_iops) / len(read_iops)
        avg_write_iops = sum(write_iops) / len(write_iops)
        total_iops = avg_read_iops + avg_write_iops
        
        lines.append("### I/O 성능\n")
        lines.append("> **💡 용어 설명**")
        lines.append("> - **IOPS**: 초당 I/O 작업 수. 디스크가 얼마나 자주 읽기/쓰기하는지 나타냄")
        lines.append("> - **처리량(MB/s)**: 초당 전송 데이터량. 대용량 데이터 처리 능력")
        lines.append("> - **읽기**: 데이터 조회 작업, **쓰기**: 데이터 저장/수정 작업\n")
        
        lines.append("| 메트릭 | 읽기 | 쓰기 | 합계 | 의미 |")
        lines.append("|--------|------|------|------|------|")
        lines.append(f"| 평균 IOPS | {avg_read_iops:.0f} | {avg_write_iops:.0f} | {total_iops:.0f} | "
                    "일반적인 디스크 사용량 |")
        lines.append(f"| 최대 IOPS | {max(read_iops):.0f} | {max(write_iops):.0f} | "
                    f"{max(read_iops) + max(write_iops):.0f} | 피크 시 디스크 사용량 |")
        
        # MB/s 데이터가 있는 경우
        if any(read_mbps) or any(write_mbps):
            avg_read_mbps = sum(read_mbps) / len(read_mbps) if read_mbps else 0
            avg_write_mbps = sum(write_mbps) / len(write_mbps) if write_mbps else 0
            lines.append(f"| 평균 처리량 (MB/s) | {avg_read_mbps:.1f} | {avg_write_mbps:.1f} | "
                        f"{avg_read_mbps + avg_write_mbps:.1f} | 데이터 전송 속도 |")
        
        lines.append("")
        
        # 트랜잭션
        commits = [m.commits_s for m in metrics]
        avg_commits = sum(commits) / len(commits)
        max_commits = max(commits)
        
        lines.append("### 트랜잭션\n")
        lines.append("> **💡 트랜잭션이란?**")
        lines.append("> 데이터베이스에서 하나의 작업 단위입니다. 예: 주문 처리, 결제 완료 등")
        lines.append("> 커밋/초가 높을수록 시스템이 더 많은 업무를 처리하고 있다는 의미입니다.\n")
        lines.append("| 메트릭 | 값 | 의미 |")
        lines.append("|--------|-----|------|")
        lines.append(f"| 평균 커밋/초 | {avg_commits:.2f} | 초당 완료되는 트랜잭션 수 |")
        lines.append(f"| 최대 커밋/초 | {max_commits:.2f} | 피크 시 트랜잭션 처리량 |")
        lines.append("")
        
        # 마이그레이션 시사점
        lines.append("### 마이그레이션 시사점\n")
        lines.append("> 위 성능 데이터를 바탕으로 분석한 AWS 인스턴스 선택 가이드입니다.\n")
        
        # 읽기/쓰기 비율 분석
        read_ratio = avg_read_iops / total_iops * 100 if total_iops > 0 else 50
        if read_ratio > 70:
            lines.append(f"- 📖 **읽기 비중이 높음 ({read_ratio:.0f}%)**: 조회 작업이 많은 시스템입니다. "
                        "Aurora Read Replica를 활용하면 읽기 성능을 분산시킬 수 있습니다.")
        elif read_ratio < 30:
            lines.append(f"- ✏️ **쓰기 비중이 높음 ({100-read_ratio:.0f}%)**: 데이터 입력/수정이 많은 시스템입니다. "
                        "쓰기 최적화된 인스턴스(r6g 계열)를 권장합니다.")
        else:
            lines.append(f"- ⚖️ **읽기/쓰기 균형 ({read_ratio:.0f}%/{100-read_ratio:.0f}%)**: "
                        "범용 인스턴스가 적합합니다.")
        
        # IOPS 분석
        if total_iops > 10000:
            lines.append(f"- ⚠️ **높은 IOPS ({total_iops:.0f})**: 디스크 사용량이 많습니다. "
                        "Aurora I/O-Optimized 또는 Provisioned IOPS 스토리지를 검토하세요.")
        else:
            lines.append("- ✅ **IOPS 적정**: Aurora는 스토리지 I/O가 자동 확장되므로 "
                        "별도 IOPS 설정이 필요 없습니다.")
        
        # 커밋 분석
        if avg_commits > 100:
            lines.append(f"- 🔄 **높은 트랜잭션 처리량 ({avg_commits:.0f}/s)**: "
                        "Aurora의 분산 스토리지 아키텍처가 이런 워크로드에 유리합니다.")
        
        lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_en(data: StatspackData) -> str:
        """영어 성능 메트릭 상세"""
        lines = []
        metrics = data.main_metrics
        
        lines.append("## ⚡ Performance Metrics Details\n")
        lines.append("> Performance data from AWR/Statspack.")
        lines.append("> Used for target instance sizing.\n")
        
        cpu_values = [m.cpu_per_s for m in metrics]
        avg_cpu = sum(cpu_values) / len(cpu_values)
        
        lines.append("### CPU Usage\n")
        lines.append("| Metric | Value | Description |")
        lines.append("|--------|-------|-------------|")
        lines.append(f"| Average CPU/s | {avg_cpu:.2f} | Analysis period average |")
        lines.append(f"| Max CPU/s | {max(cpu_values):.2f} | Peak load |")
        lines.append("")
        
        read_iops = [m.read_iops for m in metrics]
        write_iops = [m.write_iops for m in metrics]
        
        lines.append("### I/O Performance\n")
        lines.append("| Metric | Read | Write | Total |")
        lines.append("|--------|------|-------|-------|")
        avg_read = sum(read_iops) / len(read_iops)
        avg_write = sum(write_iops) / len(write_iops)
        lines.append(f"| Average IOPS | {avg_read:.0f} | {avg_write:.0f} | {avg_read + avg_write:.0f} |")
        lines.append("")
        
        return "\n".join(lines)
