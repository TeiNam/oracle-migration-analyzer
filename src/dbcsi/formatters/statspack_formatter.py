"""
Statspack 포맷터 모듈

Statspack 분석 결과를 Markdown 형식으로 출력합니다.
"""

from datetime import datetime
from typing import Dict

from .base_formatter import BaseFormatter
from ..data_models import (
    StatspackData,
    MigrationComplexity,
    TargetDatabase,
)


class StatspackResultFormatter(BaseFormatter):
    """Statspack 분석 결과 포맷터"""
    
    @staticmethod
    def to_markdown(statspack_data: StatspackData, 
                    migration_analysis: Dict[TargetDatabase, MigrationComplexity] = None) -> str:
        """분석 결과를 Markdown 형식으로 변환
        
        Args:
            statspack_data: Statspack 파싱 데이터
            migration_analysis: 마이그레이션 난이도 분석 결과 (선택적)
            
        Returns:
            Markdown 형식의 문자열
        """
        md = []
        
        # 제목 - AWR 데이터인지 확인
        is_awr = hasattr(statspack_data, 'is_awr') and statspack_data.is_awr()
        report_title = "AWR 분석 보고서" if is_awr else "Statspack 분석 보고서"
        md.append(f"# {report_title}\n")
        md.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 1. 시스템 정보 요약
        md.append("## 1. 시스템 정보 요약\n")
        os_info = statspack_data.os_info
        if os_info:
            md.append(f"- **데이터베이스 이름**: {os_info.db_name or 'N/A'}")
            md.append(f"- **DBID**: {os_info.dbid or 'N/A'}")
            md.append(f"- **버전**: {os_info.version or 'N/A'}")
            md.append(f"- **배너**: {os_info.banner or 'N/A'}")
            md.append(f"- **플랫폼**: {os_info.platform_name or 'N/A'}")
            md.append(f"- **CPU 개수**: {os_info.num_cpus or 'N/A'}")
            md.append(f"- **CPU 코어 수**: {os_info.num_cpu_cores or 'N/A'}")
            md.append(f"- **물리 메모리**: {os_info.physical_memory_gb or 'N/A'} GB")
            md.append(f"- **인스턴스 수**: {os_info.instances or 'N/A'}")
            md.append(f"- **RDS 환경**: {'예' if os_info.is_rds else '아니오'}")
            md.append(f"- **캐릭터셋**: {os_info.character_set or 'N/A'}")
            md.append(f"- **총 DB 크기**: {os_info.total_db_size_gb or 'N/A'} GB")
            
            # PL/SQL 코드 통계
            if os_info.count_lines_plsql or os_info.count_packages or os_info.count_procedures or os_info.count_functions:
                md.append("\n**PL/SQL 코드 통계:**")
                if os_info.count_lines_plsql:
                    md.append(f"- **PL/SQL 코드 라인 수**: {os_info.count_lines_plsql:,}")
                if os_info.count_packages:
                    md.append(f"- **패키지 수**: {os_info.count_packages}")
                if os_info.count_procedures:
                    md.append(f"- **프로시저 수**: {os_info.count_procedures}")
                if os_info.count_functions:
                    md.append(f"- **함수 수**: {os_info.count_functions}")
            
            # 스키마 및 테이블 통계
            if os_info.count_schemas or os_info.count_tables:
                md.append("\n**데이터베이스 오브젝트 통계:**")
                if os_info.count_schemas and isinstance(os_info.count_schemas, int):
                    md.append(f"- **스키마 수**: {os_info.count_schemas}")
                if os_info.count_tables and isinstance(os_info.count_tables, int):
                    md.append(f"- **테이블 수**: {os_info.count_tables}")
            
            md.append("")
        
        # 2. 메모리 사용량 통계
        if statspack_data.memory_metrics:
            md.append("## 2. 메모리 사용량 통계\n")
            
            total_gbs = [m.total_gb for m in statspack_data.memory_metrics]
            sga_gbs = [m.sga_gb for m in statspack_data.memory_metrics]
            pga_gbs = [m.pga_gb for m in statspack_data.memory_metrics]
            
            md.append("**요약:**")
            md.append(f"- **총 스냅샷 수**: {len(statspack_data.memory_metrics)}개")
            md.append(f"- **평균 메모리 사용량**: {sum(total_gbs)/len(total_gbs):.2f} GB (SGA: {sum(sga_gbs)/len(sga_gbs):.2f} GB, PGA: {sum(pga_gbs)/len(pga_gbs):.2f} GB)")
            md.append(f"- **최소 메모리 사용량**: {min(total_gbs):.2f} GB")
            md.append(f"- **최대 메모리 사용량**: {max(total_gbs):.2f} GB")
            md.append("")
            
            md.append("**상세 데이터 (최근 10개):**\n")
            md.append("| Snap ID | Instance | SGA (GB) | PGA (GB) | Total (GB) |")
            md.append("|---------|----------|----------|----------|------------|")
            for metric in statspack_data.memory_metrics[:10]:
                md.append(f"| {metric.snap_id} | {metric.instance_number} | "
                         f"{metric.sga_gb:.2f} | {metric.pga_gb:.2f} | {metric.total_gb:.2f} |")
            if len(statspack_data.memory_metrics) > 10:
                md.append(f"\n*전체 {len(statspack_data.memory_metrics)}개 중 10개만 표시*")
            md.append("")
        
        # 3. 디스크 사용량 통계
        if statspack_data.disk_sizes:
            md.append("## 3. 디스크 사용량 통계\n")
            
            sizes = [d.size_gb for d in statspack_data.disk_sizes]
            
            md.append("**요약:**")
            md.append(f"- **총 스냅샷 수**: {len(statspack_data.disk_sizes)}개")
            md.append(f"- **평균 디스크 사용량**: {sum(sizes)/len(sizes):.2f} GB")
            md.append(f"- **최소 디스크 사용량**: {min(sizes):.2f} GB")
            md.append(f"- **최대 디스크 사용량**: {max(sizes):.2f} GB")
            md.append("")
            
            md.append("**상세 데이터 (최근 10개):**\n")
            md.append("| Snap ID | Size (GB) |")
            md.append("|---------|-----------|")
            for disk in statspack_data.disk_sizes[:10]:
                md.append(f"| {disk.snap_id} | {disk.size_gb:.2f} |")
            if len(statspack_data.disk_sizes) > 10:
                md.append(f"\n*전체 {len(statspack_data.disk_sizes)}개 중 10개만 표시*")
            md.append("")
        
        # 4. 주요 성능 메트릭 요약
        if statspack_data.main_metrics:
            md.append("## 4. 주요 성능 메트릭 요약\n")
            
            cpu_values = [m.cpu_per_s for m in statspack_data.main_metrics]
            read_iops_values = [m.read_iops for m in statspack_data.main_metrics]
            write_iops_values = [m.write_iops for m in statspack_data.main_metrics]
            commits_values = [m.commits_s for m in statspack_data.main_metrics]
            
            if statspack_data.main_metrics:
                first_time = statspack_data.main_metrics[0].end
                last_time = statspack_data.main_metrics[-1].end
                md.append(f"**분석 기간**: {first_time} ~ {last_time}")
                md.append("")
            
            md.append("**요약:**")
            md.append(f"- **총 스냅샷 수**: {len(statspack_data.main_metrics)}개")
            md.append(f"- **평균 CPU/s**: {sum(cpu_values)/len(cpu_values):.2f} (최소: {min(cpu_values):.2f}, 최대: {max(cpu_values):.2f})")
            md.append(f"- **평균 Read IOPS**: {sum(read_iops_values)/len(read_iops_values):.2f} (최소: {min(read_iops_values):.2f}, 최대: {max(read_iops_values):.2f})")
            md.append(f"- **평균 Write IOPS**: {sum(write_iops_values)/len(write_iops_values):.2f} (최소: {min(write_iops_values):.2f}, 최대: {max(write_iops_values):.2f})")
            md.append(f"- **평균 Commits/s**: {sum(commits_values)/len(commits_values):.2f} (최소: {min(commits_values):.2f}, 최대: {max(commits_values):.2f})")
            md.append("")
            
            display_count = min(24, len(statspack_data.main_metrics))
            md.append(f"**상세 데이터 (최근 {display_count}개 - 하루 패턴):**\n")
            md.append("| 시간 | Duration (m) | CPU/s | Read IOPS | Write IOPS | Commits/s |")
            md.append("|------|--------------|-------|-----------|------------|-----------|")
            for metric in statspack_data.main_metrics[:display_count]:
                md.append(f"| {metric.end} | {metric.dur_m:.1f} | {metric.cpu_per_s:.2f} | "
                         f"{metric.read_iops:.2f} | {metric.write_iops:.2f} | {metric.commits_s:.2f} |")
            if len(statspack_data.main_metrics) > display_count:
                md.append(f"\n*전체 {len(statspack_data.main_metrics)}개 중 {display_count}개만 표시*")
            md.append("")
        
        # 5. Top 대기 이벤트
        if statspack_data.wait_events:
            md.append("## 5. Top 대기 이벤트\n")
            
            md.append("**요약:**")
            md.append(f"- **총 대기 이벤트 수**: {len(statspack_data.wait_events)}개")
            
            wait_class_times = {}
            for event in statspack_data.wait_events:
                if event.wait_class not in wait_class_times:
                    wait_class_times[event.wait_class] = 0
                wait_class_times[event.wait_class] += event.total_time_s
            
            md.append(f"- **주요 대기 클래스**: {', '.join([f'{k} ({v:.0f}s)' for k, v in sorted(wait_class_times.items(), key=lambda x: x[1], reverse=True)[:3]])}")
            md.append("")
            
            md.append("**상세 데이터 (상위 20개):**\n")
            md.append("| Snap ID | Wait Class | Event Name | % DBT | Total Time (s) |")
            md.append("|---------|------------|------------|-------|----------------|")
            for event in statspack_data.wait_events[:20]:
                md.append(f"| {event.snap_id} | {event.wait_class} | {event.event_name} | "
                         f"{event.pctdbt:.2f} | {event.total_time_s:.2f} |")
            if len(statspack_data.wait_events) > 20:
                md.append(f"\n*전체 {len(statspack_data.wait_events)}개 중 20개만 표시*")
            md.append("")
        
        # 6. 사용된 Oracle 기능 목록
        if statspack_data.features:
            md.append("## 6. 사용된 Oracle 기능 목록\n")
            md.append("| Feature Name | Detected Usages | Currently Used |")
            md.append("|--------------|-----------------|----------------|")
            for feature in statspack_data.features:
                used_str = "예" if feature.currently_used else "아니오"
                md.append(f"| {feature.name} | {feature.detected_usages} | {used_str} |")
            md.append("")
        
        # 7. SGA 조정 권장사항
        if statspack_data.sga_advice:
            md.append("## 7. SGA 조정 권장사항\n")
            
            md.append("**요약:**")
            md.append(f"- **총 권장사항 수**: {len(statspack_data.sga_advice)}개")
            
            current_sga = next((a for a in statspack_data.sga_advice if abs(a.sga_size_factor - 1.0) < 0.01), None)
            if current_sga:
                md.append(f"- **현재 SGA 크기**: {current_sga.sga_size} MB (예상 DB Time: {current_sga.estd_db_time}, 예상 Physical Reads: {current_sga.estd_physical_reads})")
            
            optimal_sga = min(statspack_data.sga_advice, key=lambda x: x.estd_db_time)
            if optimal_sga and optimal_sga != current_sga:
                md.append(f"- **권장 SGA 크기**: {optimal_sga.sga_size} MB (예상 DB Time: {optimal_sga.estd_db_time}, 예상 Physical Reads: {optimal_sga.estd_physical_reads})")
            md.append("")
            
            md.append("**상세 데이터 (10개 샘플):**\n")
            md.append("| SGA Size (MB) | Size Factor | Est. DB Time | Est. Physical Reads |")
            md.append("|---------------|-------------|--------------|---------------------|")
            for advice in statspack_data.sga_advice[:10]:
                md.append(f"| {advice.sga_size} | {advice.sga_size_factor:.2f} | "
                         f"{advice.estd_db_time} | {advice.estd_physical_reads} |")
            if len(statspack_data.sga_advice) > 10:
                md.append(f"\n*전체 {len(statspack_data.sga_advice)}개 중 10개만 표시*")
            md.append("")
        
        # 8. 마이그레이션 분석 결과
        if migration_analysis:
            md.append("## 8. 마이그레이션 분석 결과\n")
            for target, complexity in migration_analysis.items():
                md.append(f"### {target.value}\n")
                md.append(f"- **난이도 점수**: {complexity.score:.2f} / 10.0")
                md.append(f"- **난이도 레벨**: {complexity.level}")
                md.append("")
                
                if complexity.factors:
                    md.append("**점수 구성 요소:**\n")
                    for factor, score in complexity.factors.items():
                        md.append(f"- {factor}: {score:.2f}")
                    md.append("")
                
                if complexity.instance_recommendation:
                    rec = complexity.instance_recommendation
                    md.append("**RDS 인스턴스 추천:**\n")
                    md.append(f"- **인스턴스 타입**: {rec.instance_type}")
                    md.append(f"- **vCPU**: {rec.vcpu}")
                    md.append(f"- **메모리**: {rec.memory_gib} GiB")
                    md.append(f"- **현재 CPU 사용률**: {rec.current_cpu_usage_pct:.2f}%")
                    md.append(f"- **현재 메모리 사용량**: {rec.current_memory_gb:.2f} GB")
                    md.append(f"- **CPU 여유분**: {rec.cpu_headroom_pct:.2f}%")
                    md.append(f"- **메모리 여유분**: {rec.memory_headroom_pct:.2f}%")
                    if rec.estimated_monthly_cost_usd:
                        md.append(f"- **예상 월간 비용**: ${rec.estimated_monthly_cost_usd:.2f}")
                    md.append("")
                
                if complexity.recommendations:
                    md.append("**권장사항:**\n")
                    for rec in complexity.recommendations:
                        md.append(f"- {rec}")
                    md.append("")
                
                if complexity.warnings:
                    md.append("**경고:**\n")
                    for warning in complexity.warnings:
                        md.append(f"- ⚠️ {warning}")
                    md.append("")
                
                if complexity.next_steps:
                    md.append("**다음 단계:**\n")
                    for step in complexity.next_steps:
                        md.append(f"- {step}")
                    md.append("")
        
        return "\n".join(md)
    
    @staticmethod
    def batch_to_markdown(batch_result) -> str:
        """배치 분석 결과를 Markdown 형식으로 변환
        
        Args:
            batch_result: BatchAnalysisResult 객체
            
        Returns:
            Markdown 형식의 문자열
        """
        md = []
        
        md.append("# Statspack 배치 분석 보고서\n")
        md.append(f"분석 시간: {batch_result.analysis_timestamp}\n")
        
        # 전체 요약
        md.append("## 전체 요약\n")
        md.append(f"- **총 파일 수**: {batch_result.total_files}")
        md.append(f"- **성공**: {batch_result.successful_files}")
        md.append(f"- **실패**: {batch_result.failed_files}")
        success_rate = (batch_result.successful_files / batch_result.total_files * 100) if batch_result.total_files > 0 else 0
        md.append(f"- **성공률**: {success_rate:.1f}%")
        md.append("")
        
        # 성공한 파일 목록
        successful_files = [r for r in batch_result.file_results if r.success]
        if successful_files:
            md.append("## 성공한 파일\n")
            md.append("| 파일명 | DB 이름 | 버전 | 총 크기 (GB) |")
            md.append("|--------|---------|------|--------------|")
            for result in successful_files:
                db_name = result.statspack_data.os_info.db_name or "N/A"
                version = result.statspack_data.os_info.version or "N/A"
                size = result.statspack_data.os_info.total_db_size_gb or 0
                md.append(f"| {result.filename} | {db_name} | {version} | {size:.2f} |")
            md.append("")
        
        # 실패한 파일 목록
        failed_files = [r for r in batch_result.file_results if not r.success]
        if failed_files:
            md.append("## 실패한 파일\n")
            md.append("| 파일명 | 오류 메시지 |")
            md.append("|--------|-------------|")
            for result in failed_files:
                error_msg = result.error_message or "알 수 없는 오류"
                if len(error_msg) > 100:
                    error_msg = error_msg[:97] + "..."
                md.append(f"| {result.filename} | {error_msg} |")
            md.append("")
        
        # 마이그레이션 분석 요약
        if successful_files and successful_files[0].migration_analysis:
            md.append("## 마이그레이션 난이도 요약\n")
            
            targets = list(successful_files[0].migration_analysis.keys())
            
            for target in targets:
                md.append(f"### {target.value}\n")
                md.append("| 파일명 | DB 이름 | 난이도 점수 | 난이도 레벨 | 추천 인스턴스 |")
                md.append("|--------|---------|-------------|-------------|---------------|")
                
                for result in successful_files:
                    if result.migration_analysis and target in result.migration_analysis:
                        complexity = result.migration_analysis[target]
                        db_name = result.statspack_data.os_info.db_name or "N/A"
                        instance = complexity.instance_recommendation.instance_type if complexity.instance_recommendation else "N/A"
                        md.append(f"| {result.filename} | {db_name} | {complexity.score:.2f} | "
                                 f"{complexity.level} | {instance} |")
                md.append("")
        
        # 개별 파일 상세 정보
        if successful_files:
            md.append("## 개별 파일 상세 정보\n")
            for result in successful_files:
                md.append(f"### {result.filename}\n")
                
                os_info = result.statspack_data.os_info
                md.append(f"- **DB 이름**: {os_info.db_name or 'N/A'}")
                md.append(f"- **버전**: {os_info.version or 'N/A'}")
                md.append(f"- **총 크기**: {os_info.total_db_size_gb or 'N/A'} GB")
                md.append(f"- **CPU 개수**: {os_info.num_cpus or 'N/A'}")
                md.append(f"- **메모리**: {os_info.physical_memory_gb or 'N/A'} GB")
                
                if result.statspack_data.memory_metrics:
                    avg_total = sum(m.total_gb for m in result.statspack_data.memory_metrics) / len(result.statspack_data.memory_metrics)
                    md.append(f"- **평균 메모리 사용량**: {avg_total:.2f} GB")
                
                if result.migration_analysis:
                    md.append("\n**마이그레이션 난이도:**")
                    for target, complexity in result.migration_analysis.items():
                        md.append(f"- {target.value}: {complexity.score:.2f} ({complexity.level})")
                
                md.append("")
        
        return "\n".join(md)
