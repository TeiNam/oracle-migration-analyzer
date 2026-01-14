"""
ResultFormatter 사용 예제

DBCSI 분석 결과를 JSON 및 Markdown 형식으로 출력하는 예제입니다.
"""

from src.dbcsi.data_models import (
    StatspackData,
    OSInformation,
    MemoryMetric,
    DiskSize,
    MainMetric,
    WaitEvent,
    FeatureUsage,
    MigrationComplexity,
    InstanceRecommendation,
    TargetDatabase
)
from src.dbcsi.result_formatter import StatspackResultFormatter


def main():
    # 샘플 DBCSI 데이터 생성
    statspack_data = StatspackData(
        os_info=OSInformation(
            db_name="PRODDB",
            dbid="1234567890",
            version="19.0.0.0",
            banner="Oracle Database 19c Enterprise Edition Release 19.0.0.0.0",
            platform_name="Linux x86 64-bit",
            num_cpus=16,
            num_cpu_cores=8,
            physical_memory_gb=128.0,
            instances=1,
            is_rds=False,
            character_set="AL32UTF8",
            total_db_size_gb=500.0,
            count_lines_plsql=50000,
            count_packages=100,
            count_procedures=500,
            count_functions=300
        ),
        memory_metrics=[
            MemoryMetric(snap_id=1, instance_number=1, sga_gb=80.0, pga_gb=20.0, total_gb=100.0),
            MemoryMetric(snap_id=2, instance_number=1, sga_gb=82.0, pga_gb=22.0, total_gb=104.0),
        ],
        disk_sizes=[
            DiskSize(snap_id=1, size_gb=500.0),
            DiskSize(snap_id=2, size_gb=505.0),
        ],
        main_metrics=[
            MainMetric(
                snap=1, dur_m=60.0, end="2024-01-14 10:00:00", inst=1,
                cpu_per_s=8.5, read_iops=1500.0, read_mb_s=50.0,
                write_iops=500.0, write_mb_s=20.0, commits_s=100.0
            ),
        ],
        wait_events=[
            WaitEvent(
                snap_id=1, wait_class="User I/O", event_name="db file sequential read",
                pctdbt=25.5, total_time_s=1530.0
            ),
            WaitEvent(
                snap_id=1, wait_class="DB CPU", event_name="DB CPU",
                pctdbt=45.2, total_time_s=2712.0
            ),
        ],
        features=[
            FeatureUsage(
                name="Partitioning", detected_usages=100, total_samples=100,
                currently_used=True, aux_count=50.0
            ),
            FeatureUsage(
                name="Advanced Compression", detected_usages=50, total_samples=100,
                currently_used=True, aux_count=25.0
            ),
        ]
    )
    
    # 마이그레이션 분석 결과 생성
    migration_analysis = {
        TargetDatabase.RDS_ORACLE: MigrationComplexity(
            target=TargetDatabase.RDS_ORACLE,
            score=3.5,
            level="중간",
            factors={
                "기본 점수": 1.0,
                "에디션 변경": 0.0,
                "RAC → Single": 0.0,
                "버전 업그레이드": 0.5,
                "캐릭터셋 변환": 0.0,
                "PL/SQL 코드": 2.0
            },
            recommendations=[
                "RDS for Oracle EE로 마이그레이션 권장",
                "Partitioning 및 Advanced Compression 기능 유지 가능",
                "PL/SQL 코드 검토 및 최적화 필요"
            ],
            warnings=[
                "대용량 PL/SQL 코드 (50,000 라인) 존재",
                "Partitioning 기능 사용 중 (EE 라이선스 필요)"
            ],
            next_steps=[
                "1. RDS for Oracle EE 인스턴스 프로비저닝",
                "2. DMS를 사용한 데이터 마이그레이션 계획 수립",
                "3. PL/SQL 코드 성능 테스트"
            ],
            instance_recommendation=InstanceRecommendation(
                instance_type="db.r6i.4xlarge",
                vcpu=16,
                memory_gib=128,
                current_cpu_usage_pct=53.1,
                current_memory_gb=100.0,
                cpu_headroom_pct=30.0,
                memory_headroom_pct=20.0,
                estimated_monthly_cost_usd=2500.0
            )
        ),
        TargetDatabase.AURORA_POSTGRESQL: MigrationComplexity(
            target=TargetDatabase.AURORA_POSTGRESQL,
            score=6.5,
            level="복잡",
            factors={
                "기본 점수": 3.0,
                "PL/SQL 코드": 2.5,
                "Oracle 특화 기능": 1.0,
                "성능 최적화": 0.0
            },
            recommendations=[
                "PL/SQL을 PL/pgSQL로 변환 필요",
                "Partitioning은 PostgreSQL 네이티브 파티셔닝으로 전환 가능",
                "Advanced Compression은 TOAST 압축으로 대체"
            ],
            warnings=[
                "대규모 PL/SQL 변환 작업 필요 (50,000 라인)",
                "Oracle 특화 기능 변환 필요"
            ],
            next_steps=[
                "1. PL/SQL 코드 분석 및 변환 계획 수립",
                "2. AWS SCT를 사용한 스키마 변환",
                "3. 파일럿 마이그레이션 수행"
            ],
            instance_recommendation=InstanceRecommendation(
                instance_type="db.r6i.4xlarge",
                vcpu=16,
                memory_gib=128,
                current_cpu_usage_pct=53.1,
                current_memory_gb=100.0,
                cpu_headroom_pct=30.0,
                memory_headroom_pct=20.0,
                estimated_monthly_cost_usd=2000.0
            )
        )
    }
    
    print("=" * 80)
    print("1. JSON 직렬화 예제")
    print("=" * 80)
    
    # JSON 직렬화
    json_output = StatspackResultFormatter.to_json(statspack_data)
    print(json_output[:500] + "...\n")
    
    # JSON 역직렬화
    restored_data = StatspackResultFormatter.from_json(json_output)
    print(f"역직렬화 성공: DB 이름 = {restored_data.os_info.db_name}")
    print(f"메모리 메트릭 개수 = {len(restored_data.memory_metrics)}\n")
    
    print("=" * 80)
    print("2. Markdown 보고서 생성 예제")
    print("=" * 80)
    
    # Markdown 생성
    markdown_output = StatspackResultFormatter.to_markdown(
        statspack_data, 
        migration_analysis
    )
    print(markdown_output[:1000] + "...\n")
    
    print("=" * 80)
    print("3. 리포트 파일 저장 예제")
    print("=" * 80)
    
    # JSON 파일 저장 (DB 이름 포함)
    json_filepath = StatspackResultFormatter.save_report(
        content=json_output,
        filename="dbcsi_analysis",
        format="json",
        db_name=statspack_data.os_info.db_name
    )
    print(f"JSON 파일 저장됨: {json_filepath}")
    
    # Markdown 파일 저장 (DB 이름 포함)
    md_filepath = StatspackResultFormatter.save_report(
        content=markdown_output,
        filename="statspack_analysis",
        format="md",
        db_name=statspack_data.os_info.db_name
    )
    print(f"Markdown 파일 저장됨: {md_filepath}")
    
    print("\n" + "=" * 80)
    print("모든 예제 실행 완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()
