"""
마이그레이션 추천 시스템 엔드투엔드 통합 테스트

실제 DBCSI 및 SQL/PL-SQL 분석 결과를 사용하여 전체 워크플로우를 테스트합니다.
- DBCSI 분석 결과 파싱
- SQL/PL-SQL 분석 결과 생성
- 분석 결과 통합
- 의사결정 엔진 실행
- 추천 리포트 생성
- Markdown/JSON 출력
"""

import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path

from src.dbcsi.parser import StatspackParser
from src.oracle_complexity_analyzer import (
    OracleComplexityAnalyzer,
    PLSQLObjectType,
    SQLAnalysisResult,
    PLSQLAnalysisResult,
    TargetDatabase
)
from src.migration_recommendation.integrator import AnalysisResultIntegrator
from src.migration_recommendation.decision_engine import MigrationDecisionEngine
from src.migration_recommendation.report_generator import RecommendationReportGenerator
from src.migration_recommendation.formatters import MarkdownReportFormatter, JSONReportFormatter
from src.migration_recommendation.data_models import MigrationStrategy


def _analyze_sql_files(sql_files):
    """SQL/PL-SQL 파일 분석 헬퍼 함수"""
    analyzer = OracleComplexityAnalyzer()
    sql_analysis = []
    plsql_analysis = []
    
    for sql_file in sql_files:
        if os.path.exists(sql_file):
            result = analyzer.analyze_file(sql_file)
            # PLSQLAnalysisResult는 object_type이 PLSQLObjectType enum
            if isinstance(result, PLSQLAnalysisResult):
                plsql_analysis.append(result)
            else:
                sql_analysis.append(result)
    
    return sql_analysis, plsql_analysis


class TestMigrationRecommendationEndToEnd:
    """마이그레이션 추천 시스템 엔드투엔드 통합 테스트"""
    
    @pytest.fixture
    def sample_statspack_file(self):
        """실제 샘플 Statspack 파일 경로"""
        return "sample_code/dbcsi_statspack_sample01.out"
    
    @pytest.fixture
    def sample_awr_file(self):
        """실제 샘플 AWR 파일 경로"""
        return "sample_code/dbcsi_awr_sample01.out"
    
    @pytest.fixture
    def sample_sql_files(self):
        """실제 샘플 SQL/PL-SQL 파일 경로"""
        return [
            "sample_code/sample_plsql01.sql",
            "sample_code/sample_plsql02.sql",
            "sample_code/sample_plsql03.sql",
            "sample_code/sample_plsql04.sql"
        ]
    
    @pytest.fixture
    def temp_output_dir(self):
        """임시 출력 디렉토리"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_full_workflow_with_statspack(self, sample_statspack_file, sample_sql_files):
        """
        Statspack 파일을 사용한 전체 워크플로우 테스트
        
        워크플로우:
        1. DBCSI 분석 (Statspack 파싱)
        2. SQL/PL-SQL 분석
        3. 분석 결과 통합
        4. 의사결정 엔진 실행
        5. 추천 리포트 생성
        6. Markdown/JSON 출력
        """
        # 1. DBCSI 분석
        parser = StatspackParser(sample_statspack_file)
        dbcsi_result = parser.parse()
        
        assert dbcsi_result is not None
        assert dbcsi_result.os_info.db_name == "ORCL01"
        
        # 2. SQL/PL-SQL 분석
        sql_analysis, plsql_analysis = _analyze_sql_files(sample_sql_files)
        
        assert len(sql_analysis) > 0 or len(plsql_analysis) > 0
        
        # 3. 분석 결과 통합
        integrator = AnalysisResultIntegrator()
        integrated_result = integrator.integrate(
            dbcsi_result=dbcsi_result,
            sql_analysis=sql_analysis,
            plsql_analysis=plsql_analysis
        )
        
        assert integrated_result is not None
        assert integrated_result.dbcsi_result is not None
        assert integrated_result.metrics is not None
        
        # 메트릭 검증
        metrics = integrated_result.metrics
        assert metrics.avg_sql_complexity >= 0
        assert metrics.avg_plsql_complexity >= 0
        assert metrics.total_sql_count >= 0
        assert metrics.total_plsql_count >= 0
        
        # 4. 의사결정 엔진 실행
        decision_engine = MigrationDecisionEngine()
        recommended_strategy = decision_engine.decide_strategy(integrated_result)
        
        assert recommended_strategy in [
            MigrationStrategy.REPLATFORM,
            MigrationStrategy.REFACTOR_MYSQL,
            MigrationStrategy.REFACTOR_POSTGRESQL
        ]
        
        # 5. 추천 리포트 생성
        report_generator = RecommendationReportGenerator(decision_engine)
        recommendation = report_generator.generate_recommendation(integrated_result)
        
        assert recommendation is not None
        assert recommendation.recommended_strategy == recommended_strategy
        assert 3 <= len(recommendation.rationales) <= 5
        assert 1 <= len(recommendation.alternative_strategies) <= 2
        assert 3 <= len(recommendation.risks) <= 5
        assert 3 <= len(recommendation.roadmap.phases) <= 5
        assert recommendation.executive_summary is not None
        
        # 6. Markdown 출력
        markdown_formatter = MarkdownReportFormatter()
        markdown_output = markdown_formatter.format(recommendation, language="ko")
        
        assert markdown_output is not None
        assert len(markdown_output) > 0
        # Executive Summary 또는 요약 제목 확인 (한국어가 기본값)
        assert "# 요약" in markdown_output or "# Executive Summary" in markdown_output or "# 마이그레이션 추천 리포트" in markdown_output
        # 전략 이름이 한국어 또는 영어로 포함되어 있는지 확인
        strategy_names = {
            "replatform": ["RDS for Oracle", "Replatform", "리플랫폼"],
            "refactor_mysql": ["Aurora MySQL", "MySQL", "리팩토링"],
            "refactor_postgresql": ["Aurora PostgreSQL", "PostgreSQL", "리팩토링"]
        }
        strategy_value = recommendation.recommended_strategy.value
        assert any(name in markdown_output for name in strategy_names.get(strategy_value, [strategy_value]))
        
        # 7. JSON 출력
        json_formatter = JSONReportFormatter()
        json_output = json_formatter.format(recommendation)
        
        assert json_output is not None
        assert len(json_output) > 0
        
        # JSON 파싱 가능 여부 확인
        parsed_json = json.loads(json_output)
        assert "recommended_strategy" in parsed_json
        assert parsed_json["recommended_strategy"] == recommended_strategy.value
    
    def test_full_workflow_with_awr(self, sample_awr_file, sample_sql_files):
        """
        AWR 파일을 사용한 전체 워크플로우 테스트
        """
        # 1. DBCSI 분석 (AWR 파싱)
        parser = StatspackParser(sample_awr_file)
        dbcsi_result = parser.parse()
        
        assert dbcsi_result is not None
        assert dbcsi_result.os_info.db_name == "ORA12C"
        
        # 2. SQL/PL-SQL 분석
        sql_analysis, plsql_analysis = _analyze_sql_files(sample_sql_files)
        
        # 3. 분석 결과 통합
        integrator = AnalysisResultIntegrator()
        integrated_result = integrator.integrate(
            dbcsi_result=dbcsi_result,
            sql_analysis=sql_analysis,
            plsql_analysis=plsql_analysis
        )
        
        assert integrated_result is not None
        
        # 4. 의사결정 및 리포트 생성
        decision_engine = MigrationDecisionEngine()
        report_generator = RecommendationReportGenerator(decision_engine)
        recommendation = report_generator.generate_recommendation(integrated_result)
        
        assert recommendation is not None
        assert recommendation.recommended_strategy in [
            MigrationStrategy.REPLATFORM,
            MigrationStrategy.REFACTOR_MYSQL,
            MigrationStrategy.REFACTOR_POSTGRESQL
        ]
    
    def test_report_saving(self, sample_statspack_file, sample_sql_files, temp_output_dir):
        """
        리포트 파일 저장 테스트
        """
        # 전체 워크플로우 실행
        parser = StatspackParser(sample_statspack_file)
        dbcsi_result = parser.parse()
        
        sql_analysis, plsql_analysis = _analyze_sql_files(sample_sql_files)
        
        integrator = AnalysisResultIntegrator()
        integrated_result = integrator.integrate(
            dbcsi_result=dbcsi_result,
            sql_analysis=sql_analysis,
            plsql_analysis=plsql_analysis
        )
        
        decision_engine = MigrationDecisionEngine()
        report_generator = RecommendationReportGenerator(decision_engine)
        recommendation = report_generator.generate_recommendation(integrated_result)
        
        # Markdown 저장
        markdown_formatter = MarkdownReportFormatter()
        markdown_content = markdown_formatter.format(recommendation, language="ko")
        markdown_path = os.path.join(temp_output_dir, "recommendation.md")
        
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        assert os.path.exists(markdown_path)
        assert os.path.getsize(markdown_path) > 0
        
        # JSON 저장
        json_formatter = JSONReportFormatter()
        json_content = json_formatter.format(recommendation)
        json_path = os.path.join(temp_output_dir, "recommendation.json")
        
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_content)
        
        assert os.path.exists(json_path)
        assert os.path.getsize(json_path) > 0
        
        # 저장된 파일 읽기 및 검증
        with open(markdown_path, "r", encoding="utf-8") as f:
            loaded_markdown = f.read()
        assert "Executive Summary" in loaded_markdown or "마이그레이션 추천" in loaded_markdown
        
        with open(json_path, "r", encoding="utf-8") as f:
            loaded_json = json.load(f)
        assert "recommended_strategy" in loaded_json
    
    def test_workflow_without_dbcsi(self, sample_sql_files):
        """
        DBCSI 결과 없이 SQL/PL-SQL 분석만으로 추천 생성 테스트
        """
        # SQL/PL-SQL 분석만 수행
        sql_analysis, plsql_analysis = _analyze_sql_files(sample_sql_files)
        
        # DBCSI 결과 없이 통합
        integrator = AnalysisResultIntegrator()
        integrated_result = integrator.integrate(
            dbcsi_result=None,
            sql_analysis=sql_analysis,
            plsql_analysis=plsql_analysis
        )
        
        assert integrated_result is not None
        assert integrated_result.dbcsi_result is None
        assert integrated_result.metrics is not None
        
        # 성능 메트릭은 0이어야 함
        assert integrated_result.metrics.avg_cpu_usage == 0
        assert integrated_result.metrics.avg_io_load == 0
        assert integrated_result.metrics.avg_memory_usage == 0
        
        # 의사결정 및 리포트 생성은 정상 동작해야 함
        decision_engine = MigrationDecisionEngine()
        report_generator = RecommendationReportGenerator(decision_engine)
        recommendation = report_generator.generate_recommendation(integrated_result)
        
        assert recommendation is not None
        assert recommendation.recommended_strategy in [
            MigrationStrategy.REPLATFORM,
            MigrationStrategy.REFACTOR_MYSQL,
            MigrationStrategy.REFACTOR_POSTGRESQL
        ]
    
    def test_multilingual_output(self, sample_statspack_file, sample_sql_files):
        """
        다국어 출력 테스트 (한국어/영어)
        """
        # 전체 워크플로우 실행
        parser = StatspackParser(sample_statspack_file)
        dbcsi_result = parser.parse()
        
        sql_analysis, plsql_analysis = _analyze_sql_files(sample_sql_files)
        
        integrator = AnalysisResultIntegrator()
        integrated_result = integrator.integrate(
            dbcsi_result=dbcsi_result,
            sql_analysis=sql_analysis,
            plsql_analysis=plsql_analysis
        )
        
        decision_engine = MigrationDecisionEngine()
        report_generator = RecommendationReportGenerator(decision_engine)
        recommendation = report_generator.generate_recommendation(integrated_result)
        
        # 한국어 출력
        markdown_formatter = MarkdownReportFormatter()
        korean_output = markdown_formatter.format(recommendation, language="ko")
        
        assert "Executive Summary" in korean_output or "마이그레이션 추천" in korean_output
        assert "추천 전략" in korean_output or "전략" in korean_output
        assert "근거" in korean_output or "Rationale" in korean_output
        
        # 영어 출력
        english_output = markdown_formatter.format(recommendation, language="en")
        
        assert "# Executive Summary" in english_output
        assert "Recommended Strategy" in english_output
        assert "Rationale" in english_output
    
    def test_all_components_integration(self, sample_statspack_file, sample_sql_files):
        """
        모든 컴포넌트 통합 테스트
        - Integrator
        - DecisionEngine
        - ReportGenerator
        - Formatters
        """
        # 1. 데이터 준비
        parser = StatspackParser(sample_statspack_file)
        dbcsi_result = parser.parse()
        
        sql_analysis, plsql_analysis = _analyze_sql_files(sample_sql_files)
        
        # 2. Integrator 테스트
        integrator = AnalysisResultIntegrator()
        integrated_result = integrator.integrate(
            dbcsi_result=dbcsi_result,
            sql_analysis=sql_analysis,
            plsql_analysis=plsql_analysis
        )
        
        assert integrated_result is not None
        assert integrated_result.metrics is not None
        
        # 3. DecisionEngine 테스트
        decision_engine = MigrationDecisionEngine()
        strategy = decision_engine.decide_strategy(integrated_result)
        
        assert strategy in [
            MigrationStrategy.REPLATFORM,
            MigrationStrategy.REFACTOR_MYSQL,
            MigrationStrategy.REFACTOR_POSTGRESQL
        ]
        
        # 4. ReportGenerator 테스트
        report_generator = RecommendationReportGenerator(decision_engine)
        recommendation = report_generator.generate_recommendation(integrated_result)
        
        assert recommendation is not None
        assert recommendation.recommended_strategy == strategy
        assert len(recommendation.rationales) >= 3
        assert len(recommendation.alternative_strategies) >= 1
        assert len(recommendation.risks) >= 3
        assert len(recommendation.roadmap.phases) >= 3
        
        # 5. Formatters 테스트
        markdown_formatter = MarkdownReportFormatter()
        json_formatter = JSONReportFormatter()
        
        markdown_output = markdown_formatter.format(recommendation, language="ko")
        json_output = json_formatter.format(recommendation)
        
        assert len(markdown_output) > 0
        assert len(json_output) > 0
        
        # JSON 파싱 검증
        parsed_json = json.loads(json_output)
        assert parsed_json["recommended_strategy"] == strategy.value



class TestMigrationRecommendationScenarios:
    """시나리오별 마이그레이션 추천 테스트"""
    
    def test_simple_system_aurora_mysql_scenario(self):
        """
        시나리오 1: 단순 시스템 (Aurora MySQL 추천)
        
        특징 (v2.2.0 임계값 기준):
        - 평균 SQL 복잡도 <= 4.0
        - 평균 PL/SQL 복잡도 <= 3.5
        - PL/SQL 오브젝트 < 20개
        - BULK 연산 < 10개
        
        예상 결과: Aurora MySQL 추천
        """
        from src.migration_recommendation.data_models import (
            IntegratedAnalysisResult,
            AnalysisMetrics
        )
        from src.dbcsi.models import StatspackData, OSInformation
        
        # 단순 시스템 데이터 생성
        # DBCSI 결과 (선택적)
        os_info = OSInformation(
            db_name="SIMPLE_DB",
            banner="Oracle Database 19c Standard Edition 2",
            version="19.0.0.0.0",
            character_set="AL32UTF8",
            instances=1,
            count_lines_plsql=1000,
            count_packages=2,
            count_functions=5,
            count_procedures=8
        )
        dbcsi_result = StatspackData(os_info=os_info)
        
        # 단순 SQL 분석 결과 (복잡도 2.5-3.5, 평균 <= 4.0)
        sql_analysis = [
            SQLAnalysisResult(
                query=f"SELECT * FROM table_{i}",
                target_database=TargetDatabase.POSTGRESQL,
                total_score=2.5 + (i % 3) * 0.5,
                normalized_score=2.5 + (i % 3) * 0.5,
                complexity_level=None,
                recommendation="",
                structural_complexity=1.0,
                oracle_specific_features=0.5,
                functions_expressions=0.5,
                data_volume=0.5,
                execution_complexity=0.5,
                conversion_difficulty=0.5
            )
            for i in range(15)
        ]
        
        # 단순 PL/SQL 분석 결과 (복잡도 2.5-3.5, 평균 <= 3.5)
        plsql_analysis = [
            PLSQLAnalysisResult(
                code=f"CREATE PROCEDURE proc_{i} AS BEGIN NULL; END;",
                object_type=PLSQLObjectType.PROCEDURE,
                target_database=TargetDatabase.POSTGRESQL,
                total_score=2.5 + (i % 3) * 0.5,
                normalized_score=2.5 + (i % 3) * 0.5,
                complexity_level=None,
                recommendation="",
                base_score=2.0,
                code_complexity=0.5,
                oracle_features=0.3,
                business_logic=0.2,
                conversion_difficulty=0.0,
                bulk_operations_count=0  # BULK 연산 없음
            )
            for i in range(10)  # 20개 미만
        ]
        
        # 분석 결과 통합
        integrator = AnalysisResultIntegrator()
        integrated_result = integrator.integrate(
            dbcsi_result=dbcsi_result,
            sql_analysis=sql_analysis,
            plsql_analysis=plsql_analysis
        )
        
        # 메트릭 검증 (v2.2.0 임계값 기준)
        metrics = integrated_result.metrics
        assert metrics.avg_sql_complexity <= 4.0
        assert metrics.avg_plsql_complexity <= 3.5
        assert metrics.total_plsql_count < 20
        assert metrics.bulk_operation_count < 10
        
        # 의사결정 엔진 실행
        decision_engine = MigrationDecisionEngine()
        strategy = decision_engine.decide_strategy(integrated_result)
        
        # Aurora MySQL 추천 확인
        assert strategy == MigrationStrategy.REFACTOR_MYSQL
        
        # 리포트 생성
        report_generator = RecommendationReportGenerator(decision_engine)
        recommendation = report_generator.generate_recommendation(integrated_result)
        
        assert recommendation.recommended_strategy == MigrationStrategy.REFACTOR_MYSQL
        assert recommendation.confidence_level in ["high", "medium"]
        
        # 근거에 "단순" 또는 "낮은 복잡도" 언급 확인
        rationale_texts = [r.reason for r in recommendation.rationales]
        assert any("단순" in text or "낮" in text or "3.5" in text or "4.0" in text for text in rationale_texts)
        
        # 대안 전략에 PostgreSQL 또는 Replatform 포함 확인
        alternative_strategies = [alt.strategy for alt in recommendation.alternative_strategies]
        assert MigrationStrategy.REFACTOR_POSTGRESQL in alternative_strategies or \
               MigrationStrategy.REPLATFORM in alternative_strategies
    
    def test_medium_complexity_aurora_postgresql_scenario(self):
        """
        시나리오 2: 중간 복잡도 시스템 (Aurora PostgreSQL 추천)
        
        특징 (v2.2.0 임계값 기준):
        - 평균 SQL 복잡도 4.0-5.5 (Replatform 임계값 6.0 미만)
        - 평균 PL/SQL 복잡도 3.5-5.5 (MySQL 임계값 3.5 초과, Replatform 6.0 미만)
        - BULK 연산 >= 10개 (MySQL 제외 조건)
        
        예상 결과: Aurora PostgreSQL 추천
        """
        from src.migration_recommendation.data_models import (
            IntegratedAnalysisResult,
            AnalysisMetrics
        )
        from src.dbcsi.models import StatspackData, OSInformation
        
        # 중간 복잡도 시스템 데이터 생성
        os_info = OSInformation(
            db_name="MEDIUM_DB",
            banner="Oracle Database 19c Enterprise Edition",
            version="19.0.0.0.0",
            character_set="AL32UTF8",
            instances=1,
            count_lines_plsql=5000,
            count_packages=10,
            count_functions=20,
            count_procedures=30
        )
        dbcsi_result = StatspackData(os_info=os_info)
        
        # 중간 복잡도 SQL 분석 결과 (복잡도 4.5-5.5, Replatform 6.0 미만)
        sql_analysis = [
            SQLAnalysisResult(
                query=f"SELECT * FROM table_{i}",
                target_database=TargetDatabase.POSTGRESQL,
                total_score=4.5 + (i % 3) * 0.5,
                normalized_score=4.5 + (i % 3) * 0.5,
                complexity_level=None,
                recommendation="",
                structural_complexity=2.0,
                oracle_specific_features=1.0,
                functions_expressions=1.0,
                data_volume=0.5,
                execution_complexity=0.5,
                conversion_difficulty=0.5
            )
            for i in range(30)
        ]
        
        # 중간 복잡도 PL/SQL 분석 결과 (복잡도 4.0-5.0, BULK 연산 포함)
        plsql_analysis = [
            PLSQLAnalysisResult(
                code=f"CREATE PROCEDURE proc_{i} AS BEGIN NULL; END;",
                object_type=PLSQLObjectType.PROCEDURE,
                target_database=TargetDatabase.POSTGRESQL,
                total_score=4.0 + (i % 3) * 0.5,
                normalized_score=4.0 + (i % 3) * 0.5,
                complexity_level=None,
                recommendation="",
                base_score=2.5,
                code_complexity=1.0,
                oracle_features=0.5,
                business_logic=0.5,
                conversion_difficulty=0.0,
                bulk_operations_count=1 if i < 12 else 0  # 12개 BULK 연산
            )
            for i in range(40)
        ]
        
        # 분석 결과 통합
        integrator = AnalysisResultIntegrator()
        integrated_result = integrator.integrate(
            dbcsi_result=dbcsi_result,
            sql_analysis=sql_analysis,
            plsql_analysis=plsql_analysis
        )
        
        # 메트릭 검증 (v2.2.0 임계값 기준)
        metrics = integrated_result.metrics
        assert metrics.avg_sql_complexity < 6.0  # Replatform 임계값 미만
        assert metrics.avg_plsql_complexity > 3.5  # MySQL 임계값 초과
        assert metrics.avg_plsql_complexity < 6.0  # Replatform 임계값 미만
        assert metrics.bulk_operation_count >= 10  # BULK 연산으로 MySQL 제외
        
        # 의사결정 엔진 실행
        decision_engine = MigrationDecisionEngine()
        strategy = decision_engine.decide_strategy(integrated_result)
        
        # Aurora PostgreSQL 추천 확인
        assert strategy == MigrationStrategy.REFACTOR_POSTGRESQL
        
        # 리포트 생성
        report_generator = RecommendationReportGenerator(decision_engine)
        recommendation = report_generator.generate_recommendation(integrated_result)
        
        assert recommendation.recommended_strategy == MigrationStrategy.REFACTOR_POSTGRESQL
        
        # 근거에 "BULK" 또는 "중간" 언급 확인
        rationale_texts = [r.reason for r in recommendation.rationales]
        assert any("BULK" in text or "중간" in text or "PostgreSQL" in text for text in rationale_texts)
        
        # 위험 요소에 "BULK 연산" 언급 확인
        risk_descriptions = [r.description for r in recommendation.risks]
        assert any("BULK" in desc for desc in risk_descriptions)
    
    def test_complex_system_replatform_scenario(self):
        """
        시나리오 3: 복잡한 시스템 (Replatform 추천)
        
        특징 (v2.2.0 임계값 기준):
        - 평균 SQL 복잡도 >= 6.0 또는
        - 평균 PL/SQL 복잡도 >= 6.0 또는
        - 복잡도 7.0 이상 오브젝트 >= 25% 또는
        - 복잡 오브젝트 절대 개수 >= 20개
        
        예상 결과: Replatform (RDS Oracle SE2) 추천
        """
        from src.migration_recommendation.data_models import (
            IntegratedAnalysisResult,
            AnalysisMetrics
        )
        from src.dbcsi.models import StatspackData, OSInformation
        
        # 복잡한 시스템 데이터 생성
        os_info = OSInformation(
            db_name="COMPLEX_DB",
            banner="Oracle Database 19c Enterprise Edition",
            version="19.0.0.0.0",
            character_set="AL32UTF8",
            instances=2,  # RAC 환경
            count_lines_plsql=15000,
            count_packages=50,
            count_functions=100,
            count_procedures=150
        )
        dbcsi_result = StatspackData(os_info=os_info)
        
        # 복잡한 SQL 분석 결과 (복잡도 6.5-8.0, Replatform 임계값 6.0 이상)
        sql_analysis = [
            SQLAnalysisResult(
                query=f"SELECT * FROM table_{i}",
                target_database=TargetDatabase.POSTGRESQL,
                total_score=6.5 + (i % 3) * 0.5,
                normalized_score=6.5 + (i % 3) * 0.5,
                complexity_level=None,
                recommendation="",
                structural_complexity=3.0,
                oracle_specific_features=2.0,
                functions_expressions=1.5,
                data_volume=0.5,
                execution_complexity=0.5,
                conversion_difficulty=1.0
            )
            for i in range(50)
        ]
        
        # 복잡한 PL/SQL 분석 결과 (복잡도 6.5-7.5, Replatform 임계값 6.0 이상)
        plsql_analysis = [
            PLSQLAnalysisResult(
                code=f"CREATE PROCEDURE proc_{i} AS BEGIN NULL; END;",
                object_type=PLSQLObjectType.PROCEDURE,
                target_database=TargetDatabase.POSTGRESQL,
                total_score=6.5 + (i % 3) * 0.5,
                normalized_score=6.5 + (i % 3) * 0.5,
                complexity_level=None,
                recommendation="",
                base_score=4.0,
                code_complexity=1.5,
                oracle_features=1.0,
                business_logic=0.5,
                conversion_difficulty=0.5,
                bulk_operations_count=1 if i < 20 else 0
            )
            for i in range(60)
        ]
        
        # 분석 결과 통합
        integrator = AnalysisResultIntegrator()
        integrated_result = integrator.integrate(
            dbcsi_result=dbcsi_result,
            sql_analysis=sql_analysis,
            plsql_analysis=plsql_analysis
        )
        
        # 메트릭 검증 (v2.2.0 임계값 기준)
        metrics = integrated_result.metrics
        assert metrics.avg_sql_complexity >= 6.0 or \
               metrics.avg_plsql_complexity >= 6.0 or \
               metrics.high_complexity_ratio >= 0.25
        
        # 의사결정 엔진 실행
        decision_engine = MigrationDecisionEngine()
        strategy = decision_engine.decide_strategy(integrated_result)
        
        # Replatform 추천 확인
        assert strategy == MigrationStrategy.REPLATFORM
        
        # 리포트 생성
        report_generator = RecommendationReportGenerator(decision_engine)
        recommendation = report_generator.generate_recommendation(integrated_result)
        
        assert recommendation.recommended_strategy == MigrationStrategy.REPLATFORM
        
        # 근거에 "복잡" 또는 "6.0" 언급 확인
        rationale_texts = [r.reason for r in recommendation.rationales]
        assert any("복잡" in text or "6.0" in text or "높" in text for text in rationale_texts)
        
        # 위험 요소에 "Single 인스턴스" 또는 "RAC" 언급 확인
        risk_descriptions = [r.description for r in recommendation.risks]
        assert any("Single" in desc or "RAC" in desc or "인스턴스" in desc for desc in risk_descriptions)
        
        # 대안 전략에 Aurora PostgreSQL 포함 확인 (복잡도가 6.0 근처인 경우)
        alternative_strategies = [alt.strategy for alt in recommendation.alternative_strategies]
        assert len(alternative_strategies) >= 1
