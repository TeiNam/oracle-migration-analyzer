#!/usr/bin/env python3
"""
AWR 파일 분석 예제

이 스크립트는 단일 AWR 파일을 분석하여 마이그레이션 난이도를 평가하고
상세 리포트를 생성하는 방법을 보여줍니다.

사용법:
    python example_awr_analysis.py
"""

import os
from datetime import datetime

from src.dbcsi.parser import StatspackParser
from src.dbcsi.migration_analyzer import MigrationAnalyzer
from src.dbcsi.result_formatter import StatspackResultFormatter
from src.dbcsi.data_models import TargetDatabase


def main():
    """AWR 파일 분석 예제"""
    
    # 1. AWR 파일 경로 설정
    awr_file = "sample_code/dbcsi_awr_sample01.out"
    
    if not os.path.exists(awr_file):
        print(f"❌ AWR 파일을 찾을 수 없습니다: {awr_file}")
        return
    
    print("=" * 80)
    print("📊 AWR 파일 분석 예제")
    print("=" * 80)
    print(f"\n분석 파일: {awr_file}\n")
    
    # 2. AWR 파일 파싱
    print("🔍 AWR 파일 파싱 중...")
    parser = StatspackParser(awr_file)
    awr_data = parser.parse()
    print("✅ 파싱 완료\n")
    
    # 3. 기본 정보 출력
    print("=" * 80)
    print("📋 시스템 정보")
    print("=" * 80)
    print(f"데이터베이스 이름: {awr_data.os_info.db_name}")
    print(f"Oracle 버전: {awr_data.os_info.version}")
    print(f"Oracle 에디션: {awr_data.os_info.banner}")
    print(f"플랫폼: {awr_data.os_info.platform_name}")
    print(f"CPU 코어 수: {awr_data.os_info.num_cpu_cores}")
    print(f"물리 메모리: {awr_data.os_info.physical_memory_gb:.2f} GB")
    print(f"데이터베이스 크기: {awr_data.os_info.total_db_size_gb:.2f} GB")
    print(f"인스턴스 수: {awr_data.os_info.instances}")
    print(f"캐릭터셋: {awr_data.os_info.character_set}")
    print()
    
    # 4. AWR 특화 데이터 확인
    print("=" * 80)
    print("🔬 AWR 특화 데이터")
    print("=" * 80)
    
    # 백분위수 CPU 메트릭
    if hasattr(awr_data, 'percentile_cpu') and awr_data.percentile_cpu:
        print("\n📊 CPU 백분위수 메트릭:")
        for metric_name, metric_data in awr_data.percentile_cpu.items():
            print(f"  - {metric_name}: {metric_data.on_cpu} cores")
    else:
        print("\n⚠️  CPU 백분위수 데이터 없음 (AWR 파서 미구현)")
    
    # 백분위수 I/O 메트릭
    if hasattr(awr_data, 'percentile_io') and awr_data.percentile_io:
        print("\n📊 I/O 백분위수 메트릭:")
        for metric_name, metric_data in awr_data.percentile_io.items():
            print(f"  - {metric_name}: {metric_data.rw_iops} IOPS, {metric_data.rw_mbps} MB/s")
    else:
        print("\n⚠️  I/O 백분위수 데이터 없음 (AWR 파서 미구현)")
    
    # 워크로드 프로파일
    if hasattr(awr_data, 'workload_profiles') and awr_data.workload_profiles:
        print(f"\n📊 워크로드 프로파일: {len(awr_data.workload_profiles)}개 레코드")
        print("  상위 5개 이벤트:")
        for profile in awr_data.workload_profiles[:5]:
            print(f"    - {profile.event} ({profile.module}): {profile.aas_contribution_pct:.2f}%")
    else:
        print("\n⚠️  워크로드 프로파일 데이터 없음 (AWR 파서 미구현)")
    
    # 버퍼 캐시 통계
    if hasattr(awr_data, 'buffer_cache_stats') and awr_data.buffer_cache_stats:
        print(f"\n📊 버퍼 캐시 통계: {len(awr_data.buffer_cache_stats)}개 스냅샷")
        avg_hit_ratio = sum(s.hit_ratio for s in awr_data.buffer_cache_stats) / len(awr_data.buffer_cache_stats)
        print(f"  평균 히트율: {avg_hit_ratio:.2f}%")
    else:
        print("\n⚠️  버퍼 캐시 데이터 없음 (AWR 파서 미구현)")
    
    # I/O 함수별 통계
    if hasattr(awr_data, 'iostat_functions') and awr_data.iostat_functions:
        print(f"\n📊 I/O 함수별 통계: {len(awr_data.iostat_functions)}개 레코드")
        io_by_function = {}
        for iostat in awr_data.iostat_functions:
            if iostat.function_name not in io_by_function:
                io_by_function[iostat.function_name] = []
            io_by_function[iostat.function_name].append(iostat.megabytes_per_s)
        
        for func, values in io_by_function.items():
            avg_io = sum(values) / len(values)
            print(f"  - {func}: {avg_io:.2f} MB/s (평균)")
    else:
        print("\n⚠️  I/O 함수별 데이터 없음 (AWR 파서 미구현)")
    
    print()
    
    # 5. 마이그레이션 분석
    print("=" * 80)
    print("🎯 마이그레이션 난이도 분석")
    print("=" * 80)
    print("\n분석 중...\n")
    
    analyzer = MigrationAnalyzer(awr_data)
    analysis_results = analyzer.analyze()
    
    # 각 타겟별 결과 출력
    for target, complexity in analysis_results.items():
        print(f"\n### {target.value}")
        print(f"난이도 점수: {complexity.score:.2f} / 10.0")
        print(f"난이도 레벨: {complexity.level}")
        
        # 인스턴스 추천 (RDS Oracle만)
        if complexity.instance_recommendation:
            rec = complexity.instance_recommendation
            print(f"\n추천 인스턴스:")
            print(f"  - 타입: {rec.instance_type}")
            print(f"  - vCPU: {rec.vcpu}")
            print(f"  - 메모리: {rec.memory_gib} GiB")
            print(f"  - CPU 여유분: {rec.cpu_headroom_pct:.1f}%")
            print(f"  - 메모리 여유분: {rec.memory_headroom_pct:.1f}%")
        
        print(f"\n주요 권장사항:")
        for i, rec in enumerate(complexity.recommendations[:3], 1):
            print(f"  {i}. {rec}")
    
    print()
    
    # 6. 리포트 저장
    print("=" * 80)
    print("💾 리포트 저장")
    print("=" * 80)
    
    # 출력 디렉토리 생성
    output_dir = "reports"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON 저장
    json_output = StatspackResultFormatter.to_json(awr_data)
    json_path = os.path.join(output_dir, f"awr_analysis_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_output)
    print(f"✅ JSON 리포트 저장: {json_path}")
    
    # Markdown 저장
    markdown_output = StatspackResultFormatter.to_markdown(awr_data, analysis_results)
    markdown_path = os.path.join(output_dir, f"awr_analysis_{timestamp}.md")
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(markdown_output)
    print(f"✅ Markdown 리포트 저장: {markdown_path}")
    
    print()
    print("=" * 80)
    print("✅ 분석 완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()
