"""
신뢰도 계산기

분석 데이터 가용성에 따른 신뢰도를 계산하고 근거를 생성합니다.
ANALYSIS_MODES_AND_DATA_REQUIREMENTS.md 기반
"""

from typing import List, Optional
from .data_models import (
    AnalysisMode,
    AnalysisMetrics,
    DataAvailability,
    ConfidenceAssessment,
    MigrationStrategy,
)


class ConfidenceCalculator:
    """신뢰도 계산기
    
    데이터 가용성과 분석 결과를 기반으로 신뢰도를 계산합니다.
    """
    
    # 분석 모드별 기본 신뢰도
    MODE_BASE_CONFIDENCE = {
        AnalysisMode.FULL: 95,
        AnalysisMode.DB_ONLY: 80,
        AnalysisMode.QUICK: 60,
        AnalysisMode.SQL_ONLY: 50,
        AnalysisMode.PLSQL_ONLY: 55,
        AnalysisMode.MINIMAL: 40,
    }
    
    @classmethod
    def calculate(
        cls,
        data_availability: DataAvailability,
        metrics: AnalysisMetrics,
        strategy: MigrationStrategy
    ) -> ConfidenceAssessment:
        """신뢰도 계산
        
        Args:
            data_availability: 데이터 가용성 정보
            metrics: 분석 메트릭
            strategy: 추천 전략
            
        Returns:
            ConfidenceAssessment: 신뢰도 평가 결과
        """
        mode = data_availability.get_analysis_mode()
        base_confidence = cls.MODE_BASE_CONFIDENCE[mode]
        
        # 개별 항목 신뢰도 계산
        sql_conf = cls._calc_sql_confidence(data_availability, metrics)
        plsql_conf = cls._calc_plsql_confidence(data_availability, metrics)
        perf_conf = cls._calc_performance_confidence(data_availability, metrics)
        strategy_conf = cls._calc_strategy_confidence(mode, strategy, metrics)
        
        # 종합 신뢰도 (가중 평균)
        overall = int(
            sql_conf * 0.25 +
            plsql_conf * 0.30 +
            perf_conf * 0.20 +
            strategy_conf * 0.25
        )
        
        # 신뢰도 근거 생성
        factors = cls._generate_confidence_factors(
            data_availability, metrics, mode, sql_conf, plsql_conf, perf_conf
        )
        
        # 신뢰도 향상 방법 생성
        suggestions = cls._generate_improvement_suggestions(data_availability, mode)
        
        return ConfidenceAssessment(
            overall_confidence=overall,
            sql_complexity_confidence=sql_conf,
            plsql_complexity_confidence=plsql_conf,
            performance_metrics_confidence=perf_conf,
            strategy_confidence=strategy_conf,
            analysis_mode=mode,
            confidence_factors=factors,
            improvement_suggestions=suggestions,
            data_availability=data_availability,
        )
    
    @classmethod
    def _calc_sql_confidence(
        cls, data: DataAvailability, metrics: AnalysisMetrics
    ) -> int:
        """SQL 복잡도 신뢰도 계산"""
        if data.has_sql and data.sql_file_count > 0:
            # 실측값 사용
            if data.sql_file_count >= 50:
                return 95
            elif data.sql_file_count >= 20:
                return 90
            elif data.sql_file_count >= 10:
                return 85
            else:
                return 75
        elif data.has_dbcsi:
            # AWR 기반 추정값 사용
            return 60
        else:
            # 추정값 사용 (ORM 가정)
            return 40
    
    @classmethod
    def _calc_plsql_confidence(
        cls, data: DataAvailability, metrics: AnalysisMetrics
    ) -> int:
        """PL/SQL 복잡도 신뢰도 계산"""
        if data.has_plsql and data.plsql_file_count > 0:
            # 실측값 사용
            if data.plsql_file_count >= 50:
                return 95
            elif data.plsql_file_count >= 20:
                return 90
            elif data.plsql_file_count >= 10:
                return 85
            else:
                return 75
        elif data.has_dbcsi and metrics.awr_plsql_lines:
            # AWR 통계 기반 추정
            return 70
        else:
            # 추정값 사용
            return 35
    
    @classmethod
    def _calc_performance_confidence(
        cls, data: DataAvailability, metrics: AnalysisMetrics
    ) -> int:
        """성능 메트릭 신뢰도 계산"""
        if not data.has_dbcsi:
            return 30
        
        # AWR이 Statspack보다 더 상세한 정보 제공
        base = 85 if data.dbcsi_type == "awr" else 75
        
        # 메트릭 완성도에 따른 보정
        if metrics.avg_cpu_usage > 0 and metrics.avg_io_load > 0:
            base += 5
        if metrics.top_wait_events:
            base += 5
        
        return min(base, 95)
    
    @classmethod
    def _calc_strategy_confidence(
        cls, mode: AnalysisMode, strategy: MigrationStrategy, metrics: AnalysisMetrics
    ) -> int:
        """전략 추천 신뢰도 계산"""
        base = cls.MODE_BASE_CONFIDENCE[mode]
        
        # 전략별 보정
        if strategy == MigrationStrategy.REPLATFORM:
            # Replatform은 보수적 선택이므로 신뢰도 높음
            if metrics.avg_plsql_complexity >= 8.0:
                return min(base + 10, 95)
            return base
        elif strategy == MigrationStrategy.REFACTOR_MYSQL:
            # MySQL은 PL/SQL 지원 안 함 → PL/SQL 데이터 중요
            if mode in [AnalysisMode.QUICK, AnalysisMode.SQL_ONLY]:
                return max(base - 15, 40)
            return base
        else:  # PostgreSQL
            # PostgreSQL은 PL/pgSQL로 변환 가능 → 중간 신뢰도
            return base
    
    @classmethod
    def _generate_confidence_factors(
        cls,
        data: DataAvailability,
        metrics: AnalysisMetrics,
        mode: AnalysisMode,
        sql_conf: int,
        plsql_conf: int,
        perf_conf: int,
    ) -> List[str]:
        """신뢰도 근거 생성 (사람이 읽을 수 있는 설명)"""
        factors = []
        
        # 분석 모드 설명
        mode_desc = {
            AnalysisMode.FULL: "모든 데이터 소스(SQL, PL/SQL, DBCSI)가 포함되어 가장 정확한 분석이 가능합니다.",
            AnalysisMode.DB_ONLY: "서비스 SQL 데이터가 없어 SQL 복잡도는 추정값을 사용합니다. ORM 기반 애플리케이션에서는 유효한 분석입니다.",
            AnalysisMode.QUICK: "DBCSI 데이터만으로 분석하여 빠른 사전 평가가 가능하나, 코드 복잡도는 추정값입니다.",
            AnalysisMode.SQL_ONLY: "SQL 데이터만 분석되어 PL/SQL 복잡도와 성능 메트릭이 누락되었습니다.",
            AnalysisMode.PLSQL_ONLY: "PL/SQL 데이터만 분석되어 서비스 SQL과 성능 메트릭이 누락되었습니다.",
            AnalysisMode.MINIMAL: "최소한의 데이터로 분석되어 신뢰도가 낮습니다. 추가 데이터 수집을 권장합니다.",
        }
        factors.append(f"📊 **분석 모드**: {mode.value.upper()} - {mode_desc[mode]}")
        
        # SQL 데이터 상태
        if data.has_sql:
            factors.append(f"✅ **SQL 분석**: {data.sql_file_count}개 파일 분석 완료 (신뢰도 {sql_conf}%)")
        else:
            factors.append(f"⚠️ **SQL 분석**: 데이터 없음 - ORM 기반 단순 CRUD로 가정 (신뢰도 {sql_conf}%)")
        
        # PL/SQL 데이터 상태
        if data.has_plsql:
            factors.append(f"✅ **PL/SQL 분석**: {data.plsql_file_count}개 파일 분석 완료 (신뢰도 {plsql_conf}%)")
        elif metrics.awr_plsql_lines:
            factors.append(f"🔶 **PL/SQL 분석**: AWR 통계 기반 추정 ({metrics.awr_plsql_lines:,}줄) (신뢰도 {plsql_conf}%)")
        else:
            factors.append(f"⚠️ **PL/SQL 분석**: 데이터 없음 (신뢰도 {plsql_conf}%)")
        
        # DBCSI 데이터 상태
        if data.has_dbcsi:
            dbcsi_type = "AWR" if data.dbcsi_type == "awr" else "Statspack"
            factors.append(f"✅ **성능 메트릭**: {dbcsi_type} 데이터 분석 완료 (신뢰도 {perf_conf}%)")
        else:
            factors.append(f"⚠️ **성능 메트릭**: 데이터 없음 - 인스턴스 사이징 정확도 낮음 (신뢰도 {perf_conf}%)")
        
        return factors
    
    @classmethod
    def _generate_improvement_suggestions(
        cls, data: DataAvailability, mode: AnalysisMode
    ) -> List[str]:
        """신뢰도 향상 방법 생성"""
        suggestions = []
        
        if not data.has_sql:
            suggestions.append(
                "📁 **서비스 SQL 추가**: 소스 코드에서 .sql 파일을 수집하거나, "
                "ORM 매핑 파일에서 SQL을 추출하면 신뢰도가 15-20% 향상됩니다."
            )
        
        if not data.has_plsql:
            suggestions.append(
                "📁 **PL/SQL 추가**: `ora_plsql_full.sql` 스크립트를 실행하여 "
                "데이터베이스의 모든 PL/SQL 코드를 추출하면 신뢰도가 20-25% 향상됩니다."
            )
        
        if not data.has_dbcsi:
            suggestions.append(
                "📁 **DBCSI 추가**: AWR 또는 Statspack 리포트를 생성하면 "
                "성능 메트릭과 인스턴스 사이징 정확도가 크게 향상됩니다."
            )
        elif data.dbcsi_type == "statspack":
            suggestions.append(
                "📈 **AWR 사용 권장**: Statspack 대신 AWR 리포트를 사용하면 "
                "더 상세한 성능 분석이 가능합니다 (Enterprise Edition 필요)."
            )
        
        if mode == AnalysisMode.FULL:
            suggestions.append(
                "✅ **최적 상태**: 모든 데이터가 포함되어 있습니다. "
                "추가 개선이 필요하지 않습니다."
            )
        
        return suggestions


def determine_data_availability(
    sql_count: int,
    plsql_count: int,
    has_dbcsi: bool,
    dbcsi_type: str = "",
    sql_source: str = "file",
    plsql_source: str = "file",
    dbcsi_source: str = "file",
) -> DataAvailability:
    """데이터 가용성 결정 헬퍼 함수"""
    return DataAvailability(
        has_sql=sql_count > 0,
        sql_file_count=sql_count,
        sql_source=sql_source if sql_count > 0 else "none",
        has_plsql=plsql_count > 0,
        plsql_file_count=plsql_count,
        plsql_source=plsql_source if plsql_count > 0 else "none",
        has_dbcsi=has_dbcsi,
        dbcsi_type=dbcsi_type if has_dbcsi else "none",
        dbcsi_source=dbcsi_source if has_dbcsi else "none",
    )
