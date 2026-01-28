"""
Quick Assessment 테스트

DBCSI 데이터 기반 빠른 마이그레이션 방향성 판단 기능 테스트
"""

import pytest
from src.dbcsi.models import (
    StatspackData,
    OSInformation,
    MemoryMetric,
    MainMetric,
    FeatureUsage,
)
from src.dbcsi.formatters.sections.quick_assessment import (
    QuickAssessor,
    QuickAssessmentFormatter,
    AssessmentResult,
)


class TestQuickAssessor:
    """QuickAssessor 단위 테스트"""

    def test_oracle_required_rac_high_write_iops(self):
        """RAC + 높은 쓰기 IOPS → Oracle 필수"""
        data = StatspackData(
            os_info=OSInformation(
                instances=2,  # RAC
                count_lines_plsql=5000,
            ),
            main_metrics=[
                MainMetric(
                    snap=1, dur_m=60, end="2024-01-01", inst=1,
                    cpu_per_s=50, read_iops=5000, read_mb_s=100,
                    write_iops=2000,  # 높은 쓰기 IOPS
                    write_mb_s=50, commits_s=100
                )
            ]
        )
        
        result = QuickAssessor.assess(data)
        
        assert result.result == AssessmentResult.ORACLE_REQUIRED
        assert result.rac_mitigatable is False
        assert "RAC" in result.reasons[0]

    def test_rac_mitigatable_low_write_iops(self):
        """RAC + 낮은 쓰기 IOPS → RAC 대체 가능"""
        data = StatspackData(
            os_info=OSInformation(
                instances=2,  # RAC
                count_lines_plsql=5000,
            ),
            main_metrics=[
                MainMetric(
                    snap=1, dur_m=60, end="2024-01-01", inst=1,
                    cpu_per_s=50, read_iops=5000, read_mb_s=100,
                    write_iops=500,  # 낮은 쓰기 IOPS (< 1000)
                    write_mb_s=10, commits_s=50
                )
            ]
        )
        
        result = QuickAssessor.assess(data)
        
        # RAC지만 쓰기 IOPS가 낮아서 대체 가능
        assert result.rac_mitigatable is True
        assert "쓰기 IOPS가 낮음" in result.reasons[0]
        assert "Multi-AZ" in result.recommendations[0]

    def test_oracle_required_large_plsql(self):
        """대규모 PL/SQL (≥100,000줄) → Oracle 필수"""
        data = StatspackData(
            os_info=OSInformation(
                instances=1,
                count_lines_plsql=150000,  # 대규모
            )
        )
        
        result = QuickAssessor.assess(data)
        
        assert result.result == AssessmentResult.ORACLE_REQUIRED
        assert "대규모 PL/SQL" in result.reasons[0]
        assert "Replatform" in result.recommendations[0]

    def test_oracle_required_ee_hard_features(self):
        """대체 어려운 EE 기능 사용 → Oracle 필수"""
        data = StatspackData(
            os_info=OSInformation(
                instances=1,
                count_lines_plsql=5000,
            ),
            features=[
                FeatureUsage(
                    name="OLAP (user)",
                    detected_usages=10,
                    total_samples=100,
                    currently_used=True
                )
            ]
        )
        
        result = QuickAssessor.assess(data)
        
        assert result.result == AssessmentResult.ORACLE_REQUIRED
        assert "대체 어려운 EE 기능" in result.reasons[0]
        assert "OLAP" in result.reasons[0]

    def test_needs_analysis_medium_plsql(self):
        """중간 규모 PL/SQL (20,000~100,000줄) → 상세 분석 필요"""
        data = StatspackData(
            os_info=OSInformation(
                instances=1,
                count_lines_plsql=50000,  # 중간 규모
            )
        )
        
        result = QuickAssessor.assess(data)
        
        assert result.result == AssessmentResult.NEEDS_DETAILED_ANALYSIS
        assert "중간 규모 PL/SQL" in result.reasons[0]

    def test_needs_analysis_ee_soft_features(self):
        """대체 가능한 EE 기능 사용 → 상세 분석 필요"""
        data = StatspackData(
            os_info=OSInformation(
                instances=1,
                count_lines_plsql=5000,
                count_procedures=10,
                count_functions=5,
                count_packages=3,
                total_db_size_gb=100,
            ),
            features=[
                FeatureUsage(
                    name="Partitioning (user)",
                    detected_usages=5,
                    total_samples=100,
                    currently_used=True
                ),
                FeatureUsage(
                    name="Advanced Compression (user)",
                    detected_usages=3,
                    total_samples=100,
                    currently_used=True
                )
            ]
        )
        
        result = QuickAssessor.assess(data)
        
        # 대체 가능 기능 2개 이상 → 상세 분석 필요
        assert result.result == AssessmentResult.NEEDS_DETAILED_ANALYSIS
        assert "대체 가능한 EE 기능" in result.reasons[0]

    def test_open_source_possible_small_db(self):
        """소규모 DB, 단일 인스턴스, EE 미사용 → 오픈소스 가능"""
        data = StatspackData(
            os_info=OSInformation(
                instances=1,
                count_lines_plsql=8000,
                count_procedures=20,
                count_functions=10,
                count_packages=5,
                total_db_size_gb=100,
            ),
            features=[
                # system 레벨만 사용 (무시됨)
                FeatureUsage(
                    name="Partitioning (system)",
                    detected_usages=5,
                    total_samples=100,
                    currently_used=True
                )
            ]
        )
        
        result = QuickAssessor.assess(data)
        
        assert result.result == AssessmentResult.OPEN_SOURCE_POSSIBLE
        assert result.confidence >= 0.7
        assert "PostgreSQL" in " ".join(result.recommendations)

    def test_open_source_possible_with_one_soft_feature(self):
        """대체 가능 EE 기능 1개만 사용 → 오픈소스 가능 (낮은 신뢰도)"""
        data = StatspackData(
            os_info=OSInformation(
                instances=1,
                count_lines_plsql=5000,
                count_procedures=10,
                count_functions=5,
                count_packages=3,
                total_db_size_gb=50,
            ),
            features=[
                FeatureUsage(
                    name="Partitioning (user)",
                    detected_usages=5,
                    total_samples=100,
                    currently_used=True
                )
            ]
        )
        
        result = QuickAssessor.assess(data)
        
        assert result.result == AssessmentResult.OPEN_SOURCE_POSSIBLE
        assert result.confidence < 0.75  # 낮은 신뢰도

    def test_oracle_required_many_db_links(self):
        """다수의 DB Link (≥10) → Oracle 필수"""
        data = StatspackData(
            os_info=OSInformation(
                instances=1,
                count_lines_plsql=5000,
                count_db_links=15,  # 다수
            )
        )
        
        result = QuickAssessor.assess(data)
        
        assert result.result == AssessmentResult.ORACLE_REQUIRED
        assert "DB Link" in result.reasons[0]

    def test_system_features_ignored(self):
        """system 레벨 EE 기능은 무시"""
        data = StatspackData(
            os_info=OSInformation(
                instances=1,
                count_lines_plsql=5000,
                count_procedures=10,
                count_functions=5,
                count_packages=3,
                total_db_size_gb=50,
            ),
            features=[
                # system 레벨 - 무시되어야 함
                FeatureUsage(
                    name="OLAP (system)",
                    detected_usages=100,
                    total_samples=100,
                    currently_used=True
                ),
                FeatureUsage(
                    name="Data Mining (system)",
                    detected_usages=50,
                    total_samples=100,
                    currently_used=True
                )
            ]
        )
        
        result = QuickAssessor.assess(data)
        
        # system 레벨은 무시되므로 오픈소스 가능
        assert result.result == AssessmentResult.OPEN_SOURCE_POSSIBLE


class TestQuickAssessmentFormatter:
    """QuickAssessmentFormatter 단위 테스트"""

    def test_format_korean(self):
        """한국어 포맷 테스트"""
        data = StatspackData(
            os_info=OSInformation(
                db_name="TESTDB",
                instances=1,
                count_lines_plsql=5000,
                count_procedures=20,
                count_functions=10,
                count_packages=5,
                total_db_size_gb=100,
            )
        )
        
        markdown = QuickAssessmentFormatter.format(data, language="ko")
        
        assert "## ⚡ Quick Assessment" in markdown
        assert "판단 결과" in markdown
        assert "신뢰도" in markdown
        assert "분석 데이터 요약" in markdown
        assert "PL/SQL 라인 수" in markdown
        assert "다음 단계" in markdown

    def test_format_english(self):
        """영어 포맷 테스트"""
        data = StatspackData(
            os_info=OSInformation(
                db_name="TESTDB",
                instances=1,
                count_lines_plsql=5000,
            )
        )
        
        markdown = QuickAssessmentFormatter.format(data, language="en")
        
        assert "## ⚡ Quick Assessment" in markdown
        assert "Result:" in markdown
        assert "Confidence" in markdown

    def test_format_oracle_required(self):
        """Oracle 필수 결과 포맷"""
        data = StatspackData(
            os_info=OSInformation(
                instances=2,  # RAC
                count_lines_plsql=5000,
            ),
            main_metrics=[
                MainMetric(
                    snap=1, dur_m=60, end="2024-01-01", inst=1,
                    cpu_per_s=50, read_iops=5000, read_mb_s=100,
                    write_iops=5000, write_mb_s=100, commits_s=100
                )
            ]
        )
        
        markdown = QuickAssessmentFormatter.format(data, language="ko")
        
        assert "🔴" in markdown
        assert "Oracle 유지 권장" in markdown

    def test_format_open_source_possible(self):
        """오픈소스 가능 결과 포맷"""
        data = StatspackData(
            os_info=OSInformation(
                instances=1,
                count_lines_plsql=5000,
                count_procedures=10,
                count_functions=5,
                count_packages=3,
                total_db_size_gb=50,
            )
        )
        
        markdown = QuickAssessmentFormatter.format(data, language="ko")
        
        assert "🟢" in markdown
        assert "오픈소스 전환 가능" in markdown

    def test_format_rac_mitigatable(self):
        """RAC 대체 가능 안내 포맷"""
        data = StatspackData(
            os_info=OSInformation(
                instances=2,  # RAC
                count_lines_plsql=5000,
            ),
            main_metrics=[
                MainMetric(
                    snap=1, dur_m=60, end="2024-01-01", inst=1,
                    cpu_per_s=50, read_iops=5000, read_mb_s=100,
                    write_iops=500,  # 낮은 쓰기 IOPS
                    write_mb_s=10, commits_s=50
                )
            ]
        )
        
        markdown = QuickAssessmentFormatter.format(data, language="ko")
        
        assert "RAC 대체 가능성" in markdown
        assert "Multi-AZ" in markdown
        assert "Read Replica" in markdown

    def test_format_with_write_iops(self):
        """쓰기 IOPS 표시 테스트"""
        data = StatspackData(
            os_info=OSInformation(
                instances=1,
                count_lines_plsql=5000,
            ),
            main_metrics=[
                MainMetric(
                    snap=1, dur_m=60, end="2024-01-01", inst=1,
                    cpu_per_s=50, read_iops=5000, read_mb_s=100,
                    write_iops=1500, write_mb_s=30, commits_s=100
                ),
                MainMetric(
                    snap=2, dur_m=60, end="2024-01-01", inst=1,
                    cpu_per_s=60, read_iops=6000, read_mb_s=120,
                    write_iops=2000, write_mb_s=40, commits_s=120
                )
            ]
        )
        
        markdown = QuickAssessmentFormatter.format(data, language="ko")
        
        assert "쓰기 IOPS" in markdown
        assert "2,000" in markdown  # 최대값


class TestQuickAssessmentIntegration:
    """Quick Assessment 통합 테스트"""

    def test_statspack_formatter_includes_quick_assessment(self):
        """StatspackResultFormatter에 Quick Assessment 포함 확인"""
        from src.dbcsi.formatters.statspack_formatter import StatspackResultFormatter
        
        data = StatspackData(
            os_info=OSInformation(
                db_name="TESTDB",
                instances=1,
                count_lines_plsql=5000,
            )
        )
        
        markdown = StatspackResultFormatter.to_markdown(data)
        
        assert "## ⚡ Quick Assessment" in markdown
        assert "판단 결과" in markdown

    def test_real_sample_awr(self):
        """실제 AWR 샘플 데이터로 테스트"""
        from src.dbcsi.parsers import AWRParser
        import os
        
        sample_path = "sample_code/dbcsi_awr_sample01.out"
        if not os.path.exists(sample_path):
            pytest.skip("샘플 파일 없음")
        
        parser = AWRParser(sample_path)
        data = parser.parse()
        
        result = QuickAssessor.assess(data)
        
        # 결과가 유효한 AssessmentResult인지 확인
        assert result.result in AssessmentResult
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.reasons) > 0

    def test_real_sample_statspack(self):
        """실제 Statspack 샘플 데이터로 테스트"""
        from src.dbcsi.parsers import StatspackParser
        import os
        
        sample_path = "sample_code/dbcsi_statspack_sample01.out"
        if not os.path.exists(sample_path):
            pytest.skip("샘플 파일 없음")
        
        parser = StatspackParser(sample_path)
        data = parser.parse()
        
        result = QuickAssessor.assess(data)
        
        # 결과가 유효한 AssessmentResult인지 확인
        assert result.result in AssessmentResult
        assert 0.0 <= result.confidence <= 1.0
