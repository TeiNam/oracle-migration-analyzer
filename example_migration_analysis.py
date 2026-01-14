#!/usr/bin/env python3
"""
DBCSI 마이그레이션 분석 예제

이 스크립트는 DBCSI 데이터를 기반으로 상세한 마이그레이션 분석을 수행하는 방법을 보여줍니다.
"""

from src.dbcsi.parser import StatspackParser
from src.dbcsi.migration_analyzer import MigrationAnalyzer
from src.dbcsi.data_models import TargetDatabase, OracleEdition


def print_section(title):
    """섹션 제목 출력"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section("DBCSI 마이그레이션 분석 예제")
    
    # 1. DBCSI 파일 파싱
    print("\n1. DBCSI 파일 파싱 중...")
    parser = StatspackParser("sample_code/dbcsi_statspack_sample01.out")
    statspack_data = parser.parse()
    print(f"   ✓ 파싱 완료: {statspack_data.os_info.db_name}")
    
    # 2. 마이그레이션 분석기 생성
    print("\n2. 마이그레이션 분석기 초기화 중...")
    analyzer = MigrationAnalyzer(statspack_data)
    print("   ✓ 분석기 준비 완료")
    
    # 3. Oracle 환경 감지
    print_section("Oracle 환경 감지")
    
    edition = analyzer._detect_oracle_edition()
    is_rac = analyzer._detect_rac()
    charset = analyzer._detect_character_set()
    requires_conversion = analyzer._requires_charset_conversion()
    
    print(f"\nOracle 에디션: {edition.value}")
    print(f"RAC 환경: {'예' if is_rac else '아니오'}")
    print(f"캐릭터셋: {charset}")
    print(f"캐릭터셋 변환 필요: {'예' if requires_conversion else '아니오'}")
    
    if requires_conversion:
        charset_complexity = analyzer._calculate_charset_complexity()
        print(f"캐릭터셋 변환 복잡도: +{charset_complexity:.2f}점")
    
    # 4. 리소스 사용량 분석
    print_section("리소스 사용량 분석")
    
    resource_usage = analyzer._analyze_resource_usage()
    
    print(f"\nCPU 사용률:")
    print(f"  - 평균: {resource_usage['cpu_avg_pct']:.4f}%")
    print(f"  - P99: {resource_usage['cpu_p99_pct']:.4f}%")
    
    print(f"\n메모리 사용량:")
    print(f"  - 평균: {resource_usage['memory_avg_gb']:.2f} GB")
    print(f"  - 최대: {resource_usage['memory_max_gb']:.2f} GB")
    
    print(f"\n디스크:")
    print(f"  - 크기: {resource_usage['disk_size_gb']:.2f} GB")
    
    print(f"\nIOPS:")
    print(f"  - Read 평균: {resource_usage['read_iops_avg']:.2f}")
    print(f"  - Write 평균: {resource_usage['write_iops_avg']:.2f}")
    print(f"  - Total P99: {resource_usage['total_iops_p99']:.2f}")
    
    # 5. 대기 이벤트 분석
    print_section("대기 이벤트 분석")
    
    wait_analysis = analyzer._analyze_wait_events()
    
    print(f"\nDB CPU 비율: {wait_analysis['db_cpu_pct']:.2f}%")
    print(f"User I/O 비율: {wait_analysis['user_io_pct']:.2f}%")
    
    print(f"\nTop 5 대기 이벤트:")
    for i, event in enumerate(wait_analysis['top_events'][:5], 1):
        print(f"  {i}. {event['event_name']}")
        print(f"     Wait Class: {event['wait_class']}")
        print(f"     % DBT: {event['pctdbt']:.2f}%")
    
    # 6. 타겟별 마이그레이션 분석
    print_section("타겟별 마이그레이션 난이도 분석")
    
    # 각 타겟별로 개별 분석
    targets = [
        TargetDatabase.RDS_ORACLE,
        TargetDatabase.AURORA_POSTGRESQL,
        TargetDatabase.AURORA_MYSQL
    ]
    
    for target in targets:
        print(f"\n### {target.value}")
        print("-" * 80)
        
        result = analyzer.analyze(target=target)
        complexity = result[target]
        
        print(f"\n난이도 점수: {complexity.score:.2f} / 10.0")
        print(f"난이도 레벨: {complexity.level}")
        
        print(f"\n점수 구성 요소:")
        for factor, score in complexity.factors.items():
            print(f"  - {factor}: {score:.2f}")
        
        if complexity.instance_recommendation:
            rec = complexity.instance_recommendation
            print(f"\nRDS 인스턴스 추천:")
            print(f"  - 인스턴스 타입: {rec.instance_type}")
            print(f"  - vCPU: {rec.vcpu}")
            print(f"  - 메모리: {rec.memory_gib} GiB")
            print(f"  - CPU 여유분: {rec.cpu_headroom_pct:.2f}%")
            print(f"  - 메모리 여유분: {rec.memory_headroom_pct:.2f}%")
        
        print(f"\n주요 권장사항:")
        for i, recommendation in enumerate(complexity.recommendations[:5], 1):
            print(f"  {i}. {recommendation}")
        
        if complexity.warnings:
            print(f"\n경고:")
            for warning in complexity.warnings:
                print(f"  ⚠️  {warning}")
        
        print(f"\n다음 단계:")
        for i, step in enumerate(complexity.next_steps[:3], 1):
            print(f"  {i}. {step}")
    
    # 7. 권장 타겟 선택
    print_section("권장 타겟 데이터베이스")
    
    all_results = analyzer.analyze()
    
    # 난이도 순으로 정렬
    sorted_targets = sorted(
        all_results.items(),
        key=lambda x: x[1].score
    )
    
    print("\n난이도 순위:")
    for i, (target, complexity) in enumerate(sorted_targets, 1):
        print(f"  {i}. {target.value}")
        print(f"     점수: {complexity.score:.2f} / 10.0")
        print(f"     레벨: {complexity.level}")
        if complexity.instance_recommendation:
            print(f"     추천 인스턴스: {complexity.instance_recommendation.instance_type}")
    
    # 가장 낮은 난이도의 타겟 추천
    recommended_target, recommended_complexity = sorted_targets[0]
    print(f"\n✅ 권장 타겟: {recommended_target.value}")
    print(f"   이유: 가장 낮은 마이그레이션 난이도 ({recommended_complexity.score:.2f}점)")
    
    print_section("분석 완료!")


if __name__ == "__main__":
    main()
