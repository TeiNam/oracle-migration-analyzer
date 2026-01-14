#!/usr/bin/env python3
"""
AWR 파일 비교 예제

이 스크립트는 두 개의 AWR 파일을 비교하여 성능 변화를 분석하고
비교 리포트를 생성하는 방법을 보여줍니다.

사용법:
    python example_awr_comparison.py
"""

import os
from datetime import datetime

from src.dbcsi.parser import StatspackParser
from src.dbcsi.migration_analyzer import MigrationAnalyzer
from src.dbcsi.result_formatter import StatspackResultFormatter
from src.dbcsi.data_models import TargetDatabase


def compare_metrics(label, before_value, after_value, unit="", lower_is_better=False):
    """메트릭 비교 및 출력"""
    if before_value is None or after_value is None:
        return
    
    change = after_value - before_value
    change_pct = (change / before_value * 100) if before_value != 0 else 0
    
    # 개선 여부 판단
    if lower_is_better:
        improved = change < 0
    else:
        improved = change > 0
    
    status = "✅" if improved else "⚠️" if abs(change_pct) > 10 else "➡️"
    
    print(f"  {label}:")
    print(f"    Before: {before_value:.2f}{unit}")
    print(f"    After:  {after_value:.2f}{unit}")
    print(f"    Change: {change:+.2f}{unit} ({change_pct:+.1f}%) {status}")


def main():
    """AWR 파일 비교 예제"""
    
    # 1. 비교할 AWR 파일 설정
    # 실제 사용 시에는 서로 다른 시점의 AWR 파일을 지정하세요
    awr_file_before = "sample_code/dbcsi_awr_sample01.out"
    awr_file_after = "sample_code/dbcsi_awr_sample01.out"  # 예제에서는 동일 파일 사용
    
    if not os.path.exists(awr_file_before):
        print(f"❌ Before AWR 파일을 찾을 수 없습니다: {awr_file_before}")
        return
    
    if not os.path.exists(awr_file_after):
        print(f"❌ After AWR 파일을 찾을 수 없습니다: {awr_file_after}")
        return
    
    print("=" * 80)
    print("📊 AWR 파일 비교 분석 예제")
    print("=" * 80)
    print(f"\nBefore: {awr_file_before}")
    print(f"After:  {awr_file_after}\n")
    
    # 2. AWR 파일 파싱
    print("🔍 AWR 파일 파싱 중...")
    
    parser_before = StatspackParser(awr_file_before)
    awr_data_before = parser_before.parse()
    
    parser_after = StatspackParser(awr_file_after)
    awr_data_after = parser_after.parse()
    
    print("✅ 파싱 완료\n")
    
    # 3. 시스템 정보 비교
    print("=" * 80)
    print("📋 시스템 정보 비교")
    print("=" * 80)
    print()
    
    print(f"데이터베이스:")
    print(f"  Before: {awr_data_before.os_info.db_name} ({awr_data_before.os_info.version})")
    print(f"  After:  {awr_data_after.os_info.db_name} ({awr_data_after.os_info.version})")
    
    print(f"\nCPU 코어:")
    print(f"  Before: {awr_data_before.os_info.num_cpu_cores}")
    print(f"  After:  {awr_data_after.os_info.num_cpu_cores}")
    
    print(f"\n물리 메모리:")
    compare_metrics(
        "Memory",
        awr_data_before.os_info.physical_memory_gb,
        awr_data_after.os_info.physical_memory_gb,
        " GB"
    )
    
    print(f"\n데이터베이스 크기:")
    compare_metrics(
        "DB Size",
        awr_data_before.os_info.total_db_size_gb,
        awr_data_after.os_info.total_db_size_gb,
        " GB"
    )
    
    print()
    
    # 4. 성능 메트릭 비교
    print("=" * 80)
    print("📈 성능 메트릭 비교")
    print("=" * 80)
    print()
    
    # 메모리 메트릭 비교
    if awr_data_before.memory_metrics and awr_data_after.memory_metrics:
        avg_memory_before = sum(m.total_gb for m in awr_data_before.memory_metrics) / len(awr_data_before.memory_metrics)
        avg_memory_after = sum(m.total_gb for m in awr_data_after.memory_metrics) / len(awr_data_after.memory_metrics)
        
        compare_metrics(
            "Average Memory Usage",
            avg_memory_before,
            avg_memory_after,
            " GB"
        )
        print()
    
    # 백분위수 CPU 비교 (AWR 특화)
    if (hasattr(awr_data_before, 'percentile_cpu') and awr_data_before.percentile_cpu and
        hasattr(awr_data_after, 'percentile_cpu') and awr_data_after.percentile_cpu):
        
        print("CPU 백분위수 비교:")
        for percentile in ["99th_percentile", "95th_percentile", "Average"]:
            if percentile in awr_data_before.percentile_cpu and percentile in awr_data_after.percentile_cpu:
                before_cpu = awr_data_before.percentile_cpu[percentile].on_cpu
                after_cpu = awr_data_after.percentile_cpu[percentile].on_cpu
                compare_metrics(
                    f"  {percentile}",
                    before_cpu,
                    after_cpu,
                    " cores",
                    lower_is_better=True
                )
        print()
    
    # 백분위수 I/O 비교 (AWR 특화)
    if (hasattr(awr_data_before, 'percentile_io') and awr_data_before.percentile_io and
        hasattr(awr_data_after, 'percentile_io') and awr_data_after.percentile_io):
        
        print("I/O 백분위수 비교:")
        for percentile in ["99th_percentile", "95th_percentile", "Average"]:
            if percentile in awr_data_before.percentile_io and percentile in awr_data_after.percentile_io:
                before_iops = awr_data_before.percentile_io[percentile].rw_iops
                after_iops = awr_data_after.percentile_io[percentile].rw_iops
                compare_metrics(
                    f"  {percentile} IOPS",
                    before_iops,
                    after_iops,
                    "",
                    lower_is_better=True
                )
        print()
    
    # 5. 마이그레이션 난이도 비교
    print("=" * 80)
    print("🎯 마이그레이션 난이도 비교")
    print("=" * 80)
    print()
    
    analyzer_before = MigrationAnalyzer(awr_data_before)
    analysis_before = analyzer_before.analyze()
    
    analyzer_after = MigrationAnalyzer(awr_data_after)
    analysis_after = analyzer_after.analyze()
    
    for target in [TargetDatabase.RDS_ORACLE, TargetDatabase.AURORA_POSTGRESQL, TargetDatabase.AURORA_MYSQL]:
        complexity_before = analysis_before[target]
        complexity_after = analysis_after[target]
        
        print(f"\n### {target.value}")
        compare_metrics(
            "Complexity Score",
            complexity_before.score,
            complexity_after.score,
            "",
            lower_is_better=True
        )
        
        print(f"  Level Before: {complexity_before.level}")
        print(f"  Level After:  {complexity_after.level}")
    
    print()
    
    # 6. 버퍼 캐시 효율성 비교 (AWR 특화)
    if (hasattr(awr_data_before, 'buffer_cache_stats') and awr_data_before.buffer_cache_stats and
        hasattr(awr_data_after, 'buffer_cache_stats') and awr_data_after.buffer_cache_stats):
        
        print("=" * 80)
        print("💾 버퍼 캐시 효율성 비교")
        print("=" * 80)
        print()
        
        avg_hit_ratio_before = sum(s.hit_ratio for s in awr_data_before.buffer_cache_stats) / len(awr_data_before.buffer_cache_stats)
        avg_hit_ratio_after = sum(s.hit_ratio for s in awr_data_after.buffer_cache_stats) / len(awr_data_after.buffer_cache_stats)
        
        compare_metrics(
            "Average Hit Ratio",
            avg_hit_ratio_before,
            avg_hit_ratio_after,
            "%"
        )
        
        print()
    
    # 7. 워크로드 패턴 비교 (AWR 특화)
    if (hasattr(awr_data_before, 'workload_profiles') and awr_data_before.workload_profiles and
        hasattr(awr_data_after, 'workload_profiles') and awr_data_after.workload_profiles):
        
        print("=" * 80)
        print("🔄 워크로드 패턴 비교")
        print("=" * 80)
        print()
        
        # CPU vs I/O 비율 계산
        def calculate_workload_ratio(workload_profiles):
            cpu_time = sum(p.total_dbtime_sum for p in workload_profiles if "CPU" in p.event)
            io_time = sum(p.total_dbtime_sum for p in workload_profiles if "I/O" in p.wait_class)
            total_time = sum(p.total_dbtime_sum for p in workload_profiles)
            
            if total_time > 0:
                cpu_pct = (cpu_time / total_time) * 100
                io_pct = (io_time / total_time) * 100
            else:
                cpu_pct = io_pct = 0
            
            return cpu_pct, io_pct
        
        cpu_pct_before, io_pct_before = calculate_workload_ratio(awr_data_before.workload_profiles)
        cpu_pct_after, io_pct_after = calculate_workload_ratio(awr_data_after.workload_profiles)
        
        print("워크로드 타입:")
        compare_metrics(
            "  CPU Intensive",
            cpu_pct_before,
            cpu_pct_after,
            "%"
        )
        compare_metrics(
            "  I/O Intensive",
            io_pct_before,
            io_pct_after,
            "%"
        )
        
        print()
    
    # 8. 비교 리포트 저장
    print("=" * 80)
    print("💾 비교 리포트 저장")
    print("=" * 80)
    
    # 출력 디렉토리 생성
    output_dir = "reports"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Markdown 비교 리포트 저장
    comparison_path = os.path.join(output_dir, f"awr_comparison_{timestamp}.md")
    with open(comparison_path, "w", encoding="utf-8") as f:
        f.write(f"# AWR 비교 분석 리포트\n\n")
        f.write(f"분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 파일 정보\n\n")
        f.write(f"- Before: {awr_file_before}\n")
        f.write(f"- After: {awr_file_after}\n\n")
        
        f.write(f"## 마이그레이션 난이도 비교\n\n")
        for target in [TargetDatabase.RDS_ORACLE, TargetDatabase.AURORA_POSTGRESQL, TargetDatabase.AURORA_MYSQL]:
            complexity_before = analysis_before[target]
            complexity_after = analysis_after[target]
            
            f.write(f"### {target.value}\n\n")
            f.write(f"- Before: {complexity_before.score:.2f} ({complexity_before.level})\n")
            f.write(f"- After: {complexity_after.score:.2f} ({complexity_after.level})\n")
            
            change = complexity_after.score - complexity_before.score
            f.write(f"- Change: {change:+.2f}\n\n")
    
    print(f"✅ 비교 리포트 저장: {comparison_path}")
    
    print()
    print("=" * 80)
    print("✅ 비교 분석 완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()
