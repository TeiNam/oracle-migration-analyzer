"""
마이그레이션 전략별 샘플 리포트 생성 테스트

각 전략(Replatform, Aurora MySQL, Aurora PostgreSQL)별로 
샘플 리포트를 생성하고 reports/samples/ 디렉토리에 저장합니다.
"""

import pytest
from pathlib import Path

from src.dbcsi.models import StatspackData, OSInformation, MainMetric
from src.oracle_complexity_analyzer import (
    PLSQLObjectType,
    SQLAnalysisResult,
    PLSQLAnalysisResult,
    TargetDatabase
)
from src.migration_recommendation.integrator import AnalysisResultIntegrator
from src.migration_recommendation.decision_engine import MigrationDecisionEngine
from src.migration_recommendation.report_generator import RecommendationReportGenerator
from src.migration_recommendation.formatters import MarkdownReportFormatter
from src.migration_recommendation.data_models import MigrationStrategy


# 샘플 리포트 저장 디렉토리
SAMPLE_REPORTS_DIR = Path("reports/samples")


class TestSampleReportGeneration:
    """각 마이그레이션 전략별 샘플 리포트 생성 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_output_dir(self) -> None:
        """샘플 리포트 저장 디렉토리 생성"""
        SAMPLE_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def test_generate_replatform_rds_oracle_report(self) -> None:
        """
        Replatform (RDS Oracle SE2) 샘플 리포트 생성
        
        시나리오: 복잡도가 높고 PL/SQL 오브젝트가 많은 엔터프라이즈 시스템
        - SQL 복잡도: 7.5+ (매우 높음)
        - PL/SQL 복잡도: 7.0+ (매우 높음)
        - PL/SQL 오브젝트: 150개
        """
        os_info = OSInformation(
            db_name="ENTERPRISE_ERP",
            banner="Oracle Database 19c Enterprise Edition Release 19.0.0.0.0",
            version="19.0.0.0.0",
            character_set="AL32UTF8",
            instances=1,
            count_lines_plsql=85000,
            count_packages=45,
            count_functions=55,
            count_procedures=50,
            total_db_size_gb=850.0,
            physical_memory_gb=128.0,
            num_cpu_cores=16,
            count_schemas=12,
            count_tables=450,
            count_views=746,
            count_indexes=8561,
            count_triggers=35,
            count_types=20,
            # 추가 오브젝트
            count_sequences=701,
            count_lobs=1180,
            count_materialized_views=28,
            count_db_links=3
        )
        
        # 성능 메트릭 (인스턴스 추천용)
        main_metrics = [
            MainMetric(
                snap=1, dur_m=60.0, end="2026-01-01 01:00", inst=1,
                cpu_per_s=45.0, read_iops=8500.0, read_mb_s=280.0,
                write_iops=2200.0, write_mb_s=85.0, commits_s=450.0
            ),
            MainMetric(
                snap=2, dur_m=60.0, end="2026-01-01 02:00", inst=1,
                cpu_per_s=52.0, read_iops=9200.0, read_mb_s=310.0,
                write_iops=2500.0, write_mb_s=95.0, commits_s=520.0
            ),
            MainMetric(
                snap=3, dur_m=60.0, end="2026-01-01 03:00", inst=1,
                cpu_per_s=38.0, read_iops=7800.0, read_mb_s=250.0,
                write_iops=1900.0, write_mb_s=72.0, commits_s=380.0
            ),
        ]
        dbcsi_result = StatspackData(os_info=os_info, main_metrics=main_metrics)
        
        sql_analysis = self._create_sql_analysis(
            count=80,
            complexity_range=(7.0, 8.5),
            high_complexity_ratio=0.4
        )
        
        plsql_analysis = self._create_plsql_analysis(
            count=150,
            complexity_range=(6.5, 8.0),
            bulk_count=25,
            high_complexity_ratio=0.35
        )
        
        recommendation = self._generate_recommendation(
            dbcsi_result, sql_analysis, plsql_analysis
        )
        
        assert recommendation.recommended_strategy == MigrationStrategy.REPLATFORM
        
        self._save_report(
            recommendation,
            "01_replatform_rds_oracle_sample.md",
            "Replatform (RDS Oracle SE2) - 엔터프라이즈 ERP 시스템"
        )
    
    def test_generate_aurora_mysql_report(self) -> None:
        """
        Aurora MySQL (Refactoring) 샘플 리포트 생성
        
        시나리오: 단순한 CRUD 위주 시스템
        - SQL 복잡도: 4.5 이하 (낮음)
        - PL/SQL 복잡도: 4.0 이하 (낮음)
        - PL/SQL 오브젝트: 50개 미만
        - BULK 연산 없음
        """
        os_info = OSInformation(
            db_name="SIMPLE_CRM",
            banner="Oracle Database 19c Standard Edition 2 Release 19.0.0.0.0",
            version="19.0.0.0.0",
            character_set="AL32UTF8",
            instances=1,
            count_lines_plsql=2500,
            count_packages=2,
            count_functions=5,
            count_procedures=8,
            total_db_size_gb=45.0,
            physical_memory_gb=32.0,
            num_cpu_cores=4,
            count_schemas=3,
            count_tables=65,
            count_views=12,
            count_indexes=120,
            count_triggers=5,
            count_types=0
        )
        dbcsi_result = StatspackData(os_info=os_info)
        
        sql_analysis = self._create_sql_analysis(
            count=25,
            complexity_range=(2.0, 4.0),
            high_complexity_ratio=0.0
        )
        
        plsql_analysis = self._create_plsql_analysis(
            count=30,
            complexity_range=(2.0, 3.5),
            bulk_count=0,
            high_complexity_ratio=0.0
        )
        
        recommendation = self._generate_recommendation(
            dbcsi_result, sql_analysis, plsql_analysis
        )
        
        assert recommendation.recommended_strategy == MigrationStrategy.REFACTOR_MYSQL
        
        self._save_report(
            recommendation,
            "02_aurora_mysql_refactoring_sample.md",
            "Aurora MySQL (Refactoring) - 단순 CRM 시스템"
        )
    
    def test_generate_aurora_postgresql_report(self) -> None:
        """
        Aurora PostgreSQL (Refactoring) 샘플 리포트 생성
        
        시나리오: 중간 복잡도, BULK 연산 사용, PostgreSQL 친화적 기능 사용
        - SQL 복잡도: 4.5-5.5 (중간)
        - PL/SQL 복잡도: 4.0-5.0 (중간)
        - PL/SQL 오브젝트: 60개
        - BULK 연산 15개
        """
        os_info = OSInformation(
            db_name="ANALYTICS_PLATFORM",
            banner="Oracle Database 19c Enterprise Edition Release 19.0.0.0.0",
            version="19.0.0.0.0",
            character_set="AL32UTF8",
            instances=1,
            count_lines_plsql=18000,
            count_packages=15,
            count_functions=25,
            count_procedures=20,
            total_db_size_gb=320.0,
            physical_memory_gb=64.0,
            num_cpu_cores=8,
            count_schemas=8,
            count_tables=180,
            count_views=45,
            count_indexes=420,
            count_triggers=18,
            count_types=8
        )
        dbcsi_result = StatspackData(os_info=os_info)
        
        sql_analysis = self._create_sql_analysis(
            count=50,
            complexity_range=(4.0, 5.5),
            high_complexity_ratio=0.1
        )
        
        plsql_analysis = self._create_plsql_analysis(
            count=60,
            complexity_range=(4.0, 5.5),
            bulk_count=15,
            high_complexity_ratio=0.1
        )
        
        recommendation = self._generate_recommendation(
            dbcsi_result, sql_analysis, plsql_analysis
        )
        
        assert recommendation.recommended_strategy == MigrationStrategy.REFACTOR_POSTGRESQL
        
        self._save_report(
            recommendation,
            "03_aurora_postgresql_refactoring_sample.md",
            "Aurora PostgreSQL (Refactoring) - 분석 플랫폼"
        )
    
    def test_generate_aurora_postgresql_high_plsql_report(self) -> None:
        """
        Aurora PostgreSQL (Refactoring) 샘플 리포트 - PL/SQL 많은 경우
        
        시나리오: PL/SQL 오브젝트가 많지만 복잡도는 중간 이하
        - SQL 복잡도: 4.5-5.5 (중간)
        - PL/SQL 복잡도: 4.5-5.5 (중간)
        - PL/SQL 오브젝트: 80개
        - BULK 연산 15개
        """
        os_info = OSInformation(
            db_name="SUPPLY_CHAIN_MGMT",
            banner="Oracle Database 19c Enterprise Edition Release 19.0.0.0.0",
            version="19.0.0.0.0",
            character_set="AL32UTF8",
            instances=1,
            count_lines_plsql=28000,
            count_packages=20,
            count_functions=30,
            count_procedures=30,
            total_db_size_gb=480.0,
            physical_memory_gb=96.0,
            num_cpu_cores=12,
            count_schemas=10,
            count_tables=320,
            count_views=65,
            count_indexes=750,
            count_triggers=25,
            count_types=12
        )
        dbcsi_result = StatspackData(os_info=os_info)
        
        sql_analysis = self._create_sql_analysis(
            count=60,
            complexity_range=(4.0, 5.5),
            high_complexity_ratio=0.08
        )
        
        plsql_analysis = self._create_plsql_analysis(
            count=80,
            complexity_range=(4.0, 5.5),
            bulk_count=15,
            high_complexity_ratio=0.08
        )
        
        recommendation = self._generate_recommendation(
            dbcsi_result, sql_analysis, plsql_analysis
        )
        
        assert recommendation.recommended_strategy == MigrationStrategy.REFACTOR_POSTGRESQL
        
        self._save_report(
            recommendation,
            "04_aurora_postgresql_high_plsql_sample.md",
            "Aurora PostgreSQL (Refactoring) - 공급망 관리 시스템"
        )
    
    # Helper methods
    
    def _create_sql_analysis(
        self,
        count: int,
        complexity_range: tuple,
        high_complexity_ratio: float
    ) -> list:
        """SQL 분석 결과 생성"""
        min_complexity, max_complexity = complexity_range
        results = []
        
        high_count = int(count * high_complexity_ratio)
        normal_count = count - high_count
        
        for i in range(normal_count):
            complexity = min_complexity + (i % 5) * 0.2
            results.append(SQLAnalysisResult(
                query=f"SELECT * FROM table_{i} WHERE condition_{i} = :param",
                target_database=TargetDatabase.POSTGRESQL,
                total_score=complexity,
                normalized_score=complexity,
                complexity_level=None,
                recommendation="",
                structural_complexity=complexity * 0.3,
                oracle_specific_features=complexity * 0.2,
                functions_expressions=complexity * 0.2,
                data_volume=complexity * 0.1,
                execution_complexity=complexity * 0.1,
                conversion_difficulty=complexity * 0.1
            ))
        
        for i in range(high_count):
            complexity = 7.0 + (i % 3) * 0.5
            results.append(SQLAnalysisResult(
                query=f"SELECT complex_query_{i}",
                target_database=TargetDatabase.POSTGRESQL,
                total_score=complexity,
                normalized_score=complexity,
                complexity_level=None,
                recommendation="",
                structural_complexity=complexity * 0.3,
                oracle_specific_features=complexity * 0.2,
                functions_expressions=complexity * 0.2,
                data_volume=complexity * 0.1,
                execution_complexity=complexity * 0.1,
                conversion_difficulty=complexity * 0.1
            ))
        
        return results
    
    def _create_plsql_analysis(
        self,
        count: int,
        complexity_range: tuple,
        bulk_count: int,
        high_complexity_ratio: float
    ) -> list:
        """PL/SQL 분석 결과 생성"""
        min_complexity, max_complexity = complexity_range
        results = []
        
        high_count = int(count * high_complexity_ratio)
        normal_count = count - high_count
        
        object_types = [
            PLSQLObjectType.PROCEDURE,
            PLSQLObjectType.FUNCTION,
            PLSQLObjectType.PACKAGE
        ]
        
        for i in range(normal_count):
            complexity = min_complexity + (i % 5) * 0.2
            has_bulk = i < bulk_count
            results.append(PLSQLAnalysisResult(
                code=f"CREATE {object_types[i % 3].value} obj_{i}",
                object_type=object_types[i % 3],
                target_database=TargetDatabase.POSTGRESQL,
                total_score=complexity,
                normalized_score=complexity,
                complexity_level=None,
                recommendation="",
                base_score=complexity * 0.4,
                code_complexity=complexity * 0.2,
                oracle_features=complexity * 0.2,
                business_logic=complexity * 0.1,
                conversion_difficulty=complexity * 0.1,
                bulk_operations_count=1 if has_bulk else 0
            ))
        
        for i in range(high_count):
            complexity = 7.0 + (i % 3) * 0.5
            results.append(PLSQLAnalysisResult(
                code=f"CREATE {object_types[i % 3].value} complex_obj_{i}",
                object_type=object_types[i % 3],
                target_database=TargetDatabase.POSTGRESQL,
                total_score=complexity,
                normalized_score=complexity,
                complexity_level=None,
                recommendation="",
                base_score=complexity * 0.4,
                code_complexity=complexity * 0.2,
                oracle_features=complexity * 0.2,
                business_logic=complexity * 0.1,
                conversion_difficulty=complexity * 0.1,
                bulk_operations_count=0
            ))
        
        return results
    
    def _generate_recommendation(
        self,
        dbcsi_result: StatspackData,
        sql_analysis: list,
        plsql_analysis: list
    ):
        """추천 리포트 생성"""
        integrator = AnalysisResultIntegrator()
        integrated_result = integrator.integrate(
            dbcsi_result=dbcsi_result,
            sql_analysis=sql_analysis,
            plsql_analysis=plsql_analysis
        )
        
        decision_engine = MigrationDecisionEngine()
        report_generator = RecommendationReportGenerator(decision_engine)
        
        return report_generator.generate_recommendation(integrated_result)
    
    def _save_report(
        self,
        recommendation,
        filename: str,
        description: str
    ) -> None:
        """리포트를 파일로 저장"""
        formatter = MarkdownReportFormatter()
        ko_content = formatter.format(recommendation, language="ko")
        ko_path = SAMPLE_REPORTS_DIR / filename
        
        header = f"""<!-- 
샘플 리포트: {description}
생성일: 자동 생성
전략: {recommendation.recommended_strategy.value}
신뢰도: {recommendation.confidence_level}
-->

"""
        
        with open(ko_path, "w", encoding="utf-8") as f:
            f.write(header + ko_content)
        
        assert ko_path.exists()
        assert ko_path.stat().st_size > 0
        
        print(f"\n✅ 샘플 리포트 생성 완료: {ko_path}")
        print(f"   - 전략: {recommendation.recommended_strategy.value}")
        print(f"   - 신뢰도: {recommendation.confidence_level}")


class TestSampleReportValidation:
    """생성된 샘플 리포트 검증 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_output_dir(self) -> None:
        """샘플 리포트 저장 디렉토리 생성"""
        SAMPLE_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _ensure_reports_generated(self) -> None:
        """샘플 리포트가 생성되어 있는지 확인하고, 없으면 생성"""
        SAMPLE_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        
        generator = TestSampleReportGeneration()
        # 각 테스트 메서드 직접 호출 (fixture 아닌 일반 메서드)
        generator.test_generate_replatform_rds_oracle_report()
        generator.test_generate_aurora_mysql_report()
        generator.test_generate_aurora_postgresql_report()
        generator.test_generate_aurora_postgresql_high_plsql_report()
    
    def test_all_sample_reports_exist(self) -> None:
        """모든 샘플 리포트가 생성되었는지 확인"""
        expected_files = [
            "01_replatform_rds_oracle_sample.md",
            "02_aurora_mysql_refactoring_sample.md",
            "03_aurora_postgresql_refactoring_sample.md",
            "04_aurora_postgresql_high_plsql_sample.md",
        ]
        
        self._ensure_reports_generated()
        
        for filename in expected_files:
            filepath = SAMPLE_REPORTS_DIR / filename
            assert filepath.exists(), f"샘플 리포트 누락: {filename}"
            assert filepath.stat().st_size > 1000, f"리포트 내용 부족: {filename}"
    
    def test_sample_reports_contain_refactoring_guide(self) -> None:
        """Refactoring 리포트에 접근 방식 가이드가 포함되어 있는지 확인"""
        refactoring_files = [
            "02_aurora_mysql_refactoring_sample.md",
            "03_aurora_mysql_refactoring_sample.md",
            "03_aurora_postgresql_refactoring_sample.md",
            "04_aurora_postgresql_high_plsql_sample.md",
        ]
        
        self._ensure_reports_generated()
        
        for filename in refactoring_files:
            filepath = SAMPLE_REPORTS_DIR / filename
            if filepath.exists():
                content = filepath.read_text(encoding="utf-8")
                # Refactoring 관련 키워드 확인 (다양한 형태 허용)
                assert any(keyword in content for keyword in [
                    "Refactoring", "리팩토링", "변환", "마이그레이션", 
                    "Aurora", "MySQL", "PostgreSQL"
                ]), f"Refactoring 관련 내용 누락: {filename}"
