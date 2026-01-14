#!/usr/bin/env python3
"""
Statspack 단일 파일 분석 예제

이 스크립트는 단일 Statspack 파일을 파싱하고 분석하는 방법을 보여줍니다.
"""

from src.statspack.parser import StatspackParser
from src.statspack.migration_analyzer import MigrationAnalyzer
from src.statspack.result_formatter import StatspackResultFormatter
from src.statspack.data_models import TargetDatabase


def main():
    # 1. Statspack 파일 파싱
    print("=" * 80)
    print("Statspack 파일 파싱 중...")
    print("=" * 80)
    
    parser = StatspackParser("sample_code/dbcsi_statspack_sample01.out")
    statspack_data = parser.parse()
    
    # 2. 파싱 결과 요약 출력
    print(f"\n데이터베이스 이름: {statspack_data.os_info.db_name}")
    print(f"버전: {statspack_data.os_info.version}")
    print(f"배너: {statspack_data.os_info.banner}")
    print(f"CPU 개수: {statspack_data.os_info.num_cpus}")
    print(f"물리 메모리: {statspack_data.os_info.physical_memory_gb} GB")
    print(f"총 DB 크기: {statspack_data.os_info.total_db_size_gb} GB")
    print(f"캐릭터셋: {statspack_data.os_info.character_set}")
    print(f"\n메모리 메트릭 수: {len(statspack_data.memory_metrics)}")
    print(f"주요 메트릭 수: {len(statspack_data.main_metrics)}")
    print(f"대기 이벤트 수: {len(statspack_data.wait_events)}")
    print(f"사용된 기능 수: {len(statspack_data.features)}")
    
    # 3. 마이그레이션 분석
    print("\n" + "=" * 80)
    print("마이그레이션 난이도 분석 중...")
    print("=" * 80)
    
    analyzer = MigrationAnalyzer(statspack_data)
    analysis_results = analyzer.analyze()
    
    # 4. 분석 결과 출력
    for target, complexity in analysis_results.items():
        print(f"\n### {target.value}")
        print(f"난이도 점수: {complexity.score:.2f} / 10.0")
        print(f"난이도 레벨: {complexity.level}")
        
        print("\n점수 구성 요소:")
        for factor, score in complexity.factors.items():
            print(f"  - {factor}: {score:.2f}")
        
        if complexity.instance_recommendation:
            rec = complexity.instance_recommendation
            print(f"\nRDS 인스턴스 추천:")
            print(f"  - 인스턴스 타입: {rec.instance_type}")
            print(f"  - vCPU: {rec.vcpu}")
            print(f"  - 메모리: {rec.memory_gib} GiB")
            print(f"  - 현재 CPU 사용률: {rec.current_cpu_usage_pct:.2f}%")
            print(f"  - 현재 메모리 사용량: {rec.current_memory_gb:.2f} GB")
        
        print(f"\n권장사항 ({len(complexity.recommendations)}개):")
        for i, rec in enumerate(complexity.recommendations[:3], 1):
            print(f"  {i}. {rec}")
        if len(complexity.recommendations) > 3:
            print(f"  ... 외 {len(complexity.recommendations) - 3}개")
    
    # 5. JSON 출력
    print("\n" + "=" * 80)
    print("JSON 형식으로 변환 중...")
    print("=" * 80)
    
    json_output = StatspackResultFormatter.to_json(statspack_data)
    print(f"\nJSON 길이: {len(json_output)} 바이트")
    
    # JSON 파일로 저장
    with open("reports/example_single_file.json", "w", encoding="utf-8") as f:
        f.write(json_output)
    print("JSON 파일 저장: reports/example_single_file.json")
    
    # 6. Markdown 출력
    print("\n" + "=" * 80)
    print("Markdown 리포트 생성 중...")
    print("=" * 80)
    
    markdown_output = StatspackResultFormatter.to_markdown(
        statspack_data,
        analysis_results
    )
    print(f"\nMarkdown 길이: {len(markdown_output)} 바이트")
    
    # Markdown 파일로 저장
    with open("reports/example_single_file.md", "w", encoding="utf-8") as f:
        f.write(markdown_output)
    print("Markdown 파일 저장: reports/example_single_file.md")
    
    print("\n" + "=" * 80)
    print("분석 완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()
