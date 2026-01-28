"""
신뢰도 섹션 포맷터

분석 신뢰도와 데이터 가용성을 Markdown으로 포맷팅합니다.
"""

from typing import Optional
from ...data_models import ConfidenceAssessment, DataAvailability, AnalysisMode


class ConfidenceFormatterMixin:
    """신뢰도 섹션 포맷터 믹스인"""
    
    def _format_confidence_section(
        self,
        confidence: Optional[ConfidenceAssessment],
        language: str = "ko"
    ) -> str:
        """신뢰도 섹션 포맷팅
        
        Args:
            confidence: 신뢰도 평가 결과
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            str: Markdown 형식 문자열
        """
        if not confidence:
            return ""
        
        if language == "ko":
            return self._format_confidence_ko(confidence)
        return self._format_confidence_en(confidence)
    
    def _format_confidence_ko(self, conf: ConfidenceAssessment) -> str:
        """한국어 신뢰도 섹션"""
        lines = []
        
        lines.append("## 📊 분석 신뢰도 및 데이터 가용성\n")
        lines.append("> 이 섹션은 분석 결과의 신뢰도와 그 근거를 설명합니다.\n")
        
        # 종합 신뢰도 표시 (시각적 게이지)
        overall = conf.overall_confidence
        gauge = self._create_confidence_gauge(overall)
        level_text, level_color = self._get_confidence_level(overall)
        
        lines.append(f"### 종합 신뢰도: {level_color} **{overall}%** ({level_text})\n")
        lines.append(f"```")
        lines.append(f"{gauge}")
        lines.append(f"```\n")
        
        # 분석 모드 설명
        mode_info = self._get_mode_info_ko(conf.analysis_mode)
        lines.append(f"### 분석 모드: **{conf.analysis_mode.value.upper()}**\n")
        lines.append(f"{mode_info}\n")
        
        # 데이터 가용성 테이블
        lines.append("### 데이터 가용성\n")
        lines.append("| 데이터 소스 | 상태 | 파일 수 | 신뢰도 기여 |")
        lines.append("|------------|------|--------|------------|")
        
        data = conf.data_availability
        if data:
            # SQL
            sql_status = "✅ 포함" if data.has_sql else "❌ 미포함"
            sql_count = f"{data.sql_file_count}개" if data.has_sql else "-"
            sql_contrib = f"{conf.sql_complexity_confidence}%" if data.has_sql else "추정값 사용"
            lines.append(f"| 서비스 SQL | {sql_status} | {sql_count} | {sql_contrib} |")
            
            # PL/SQL
            plsql_status = "✅ 포함" if data.has_plsql else "❌ 미포함"
            plsql_count = f"{data.plsql_file_count}개" if data.has_plsql else "-"
            plsql_contrib = f"{conf.plsql_complexity_confidence}%" if data.has_plsql else "AWR 추정" if data.has_dbcsi else "추정값 사용"
            lines.append(f"| PL/SQL | {plsql_status} | {plsql_count} | {plsql_contrib} |")
            
            # DBCSI
            dbcsi_status = "✅ 포함" if data.has_dbcsi else "❌ 미포함"
            dbcsi_type = data.dbcsi_type.upper() if data.has_dbcsi else "-"
            dbcsi_contrib = f"{conf.performance_metrics_confidence}%" if data.has_dbcsi else "기본값 사용"
            lines.append(f"| DBCSI ({dbcsi_type}) | {dbcsi_status} | - | {dbcsi_contrib} |")
        
        lines.append("")
        
        # 개별 신뢰도 상세
        lines.append("### 항목별 신뢰도 상세\n")
        lines.append("| 분석 항목 | 신뢰도 | 데이터 출처 | 설명 |")
        lines.append("|----------|--------|------------|------|")
        
        # SQL 복잡도
        sql_source = self._get_source_desc_ko(data.sql_source if data else "none", "sql")
        sql_desc = "실측값 기반 분석" if data and data.has_sql else "ORM 기반 단순 CRUD 가정"
        lines.append(f"| SQL 복잡도 | {conf.sql_complexity_confidence}% | {sql_source} | {sql_desc} |")
        
        # PL/SQL 복잡도
        plsql_source = self._get_source_desc_ko(data.plsql_source if data else "none", "plsql")
        plsql_desc = "실측값 기반 분석" if data and data.has_plsql else "AWR 통계 기반 추정" if data and data.has_dbcsi else "기본값 사용"
        lines.append(f"| PL/SQL 복잡도 | {conf.plsql_complexity_confidence}% | {plsql_source} | {plsql_desc} |")
        
        # 성능 메트릭
        perf_source = self._get_source_desc_ko(data.dbcsi_source if data else "none", "dbcsi")
        perf_desc = "실측값 기반 분석" if data and data.has_dbcsi else "기본값 사용"
        lines.append(f"| 성능 메트릭 | {conf.performance_metrics_confidence}% | {perf_source} | {perf_desc} |")
        
        # 전략 추천
        lines.append(f"| 전략 추천 | {conf.strategy_confidence}% | 종합 분석 | 위 항목 종합 |")
        lines.append("")
        
        # 신뢰도 근거
        if conf.confidence_factors:
            lines.append("### 신뢰도 판단 근거\n")
            for factor in conf.confidence_factors:
                lines.append(f"{factor}\n")
            lines.append("")
        
        # 신뢰도 향상 방법
        if conf.improvement_suggestions:
            lines.append("### 💡 신뢰도 향상 방법\n")
            for suggestion in conf.improvement_suggestions:
                lines.append(f"- {suggestion}")
            lines.append("")
        
        # 주의사항
        if conf.overall_confidence < 70:
            lines.append("### ⚠️ 주의사항\n")
            lines.append("> 현재 분석 신뢰도가 70% 미만입니다. ")
            lines.append("> 최종 의사결정 전에 추가 데이터 수집을 강력히 권장합니다.")
            lines.append("> 특히 대규모 마이그레이션 프로젝트에서는 Full 모드 분석이 필수입니다.\n")
        
        return "\n".join(lines)
    
    def _format_confidence_en(self, conf: ConfidenceAssessment) -> str:
        """영어 신뢰도 섹션"""
        lines = []
        
        lines.append("## 📊 Analysis Confidence & Data Availability\n")
        lines.append("> This section explains the confidence level and its basis.\n")
        
        overall = conf.overall_confidence
        gauge = self._create_confidence_gauge(overall)
        level_text, level_color = self._get_confidence_level_en(overall)
        
        lines.append(f"### Overall Confidence: {level_color} **{overall}%** ({level_text})\n")
        lines.append(f"```")
        lines.append(f"{gauge}")
        lines.append(f"```\n")
        
        lines.append(f"### Analysis Mode: **{conf.analysis_mode.value.upper()}**\n")
        
        # Data availability table
        lines.append("### Data Availability\n")
        lines.append("| Data Source | Status | Files | Confidence |")
        lines.append("|-------------|--------|-------|------------|")
        
        data = conf.data_availability
        if data:
            sql_status = "✅ Included" if data.has_sql else "❌ Missing"
            lines.append(f"| Service SQL | {sql_status} | {data.sql_file_count} | {conf.sql_complexity_confidence}% |")
            
            plsql_status = "✅ Included" if data.has_plsql else "❌ Missing"
            lines.append(f"| PL/SQL | {plsql_status} | {data.plsql_file_count} | {conf.plsql_complexity_confidence}% |")
            
            dbcsi_status = "✅ Included" if data.has_dbcsi else "❌ Missing"
            lines.append(f"| DBCSI | {dbcsi_status} | - | {conf.performance_metrics_confidence}% |")
        
        lines.append("")
        
        return "\n".join(lines)
    
    def _create_confidence_gauge(self, confidence: int) -> str:
        """신뢰도 게이지 생성"""
        filled = confidence // 5
        empty = 20 - filled
        bar = "█" * filled + "░" * empty
        return f"[{bar}] {confidence}%"
    
    def _get_confidence_level(self, confidence: int) -> tuple:
        """신뢰도 레벨 텍스트 (한국어)"""
        if confidence >= 90:
            return "매우 높음", "🟢"
        elif confidence >= 75:
            return "높음", "🟢"
        elif confidence >= 60:
            return "보통", "🟡"
        elif confidence >= 45:
            return "낮음", "🟠"
        else:
            return "매우 낮음", "🔴"
    
    def _get_confidence_level_en(self, confidence: int) -> tuple:
        """신뢰도 레벨 텍스트 (영어)"""
        if confidence >= 90:
            return "Very High", "🟢"
        elif confidence >= 75:
            return "High", "🟢"
        elif confidence >= 60:
            return "Medium", "🟡"
        elif confidence >= 45:
            return "Low", "🟠"
        else:
            return "Very Low", "🔴"
    
    def _get_mode_info_ko(self, mode: AnalysisMode) -> str:
        """분석 모드 설명 (한국어)"""
        info = {
            AnalysisMode.FULL: (
                "**Full 모드**는 서비스 SQL, PL/SQL, DBCSI 데이터를 모두 활용하여 "
                "가장 정확한 분석을 제공합니다. 모든 데이터 소스가 실측값이므로 "
                "추천 결과의 신뢰도가 가장 높습니다."
            ),
            AnalysisMode.DB_ONLY: (
                "**DB-Only 모드**는 서비스 SQL 없이 PL/SQL과 DBCSI 데이터만으로 분석합니다. "
                "서비스 SQL은 ORM 기반 단순 CRUD로 가정합니다. "
                "JPA, Hibernate, MyBatis 등 ORM을 사용하는 환경에서 유효한 분석입니다."
            ),
            AnalysisMode.QUICK: (
                "**Quick 모드**는 DBCSI 데이터만으로 빠른 사전 평가를 제공합니다. "
                "코드 복잡도는 AWR/Statspack 통계 기반 추정값을 사용합니다. "
                "마이그레이션 검토 초기 단계에서 Go/No-Go 결정에 활용할 수 있습니다."
            ),
            AnalysisMode.SQL_ONLY: (
                "**SQL-Only 모드**는 서비스 SQL만 분석합니다. "
                "PL/SQL 복잡도와 성능 메트릭이 누락되어 신뢰도가 낮습니다. "
                "PL/SQL과 DBCSI 데이터 추가를 강력히 권장합니다."
            ),
            AnalysisMode.PLSQL_ONLY: (
                "**PL/SQL-Only 모드**는 PL/SQL만 분석합니다. "
                "서비스 SQL과 성능 메트릭이 누락되어 신뢰도가 낮습니다. "
                "DBCSI 데이터 추가를 권장합니다."
            ),
            AnalysisMode.MINIMAL: (
                "**Minimal 모드**는 최소한의 데이터로 분석합니다. "
                "신뢰도가 매우 낮아 참고용으로만 활용하시기 바랍니다. "
                "추가 데이터 수집이 필수입니다."
            ),
        }
        return info.get(mode, "")
    
    def _get_source_desc_ko(self, source: str, data_type: str) -> str:
        """데이터 출처 설명 (한국어)"""
        if source == "file":
            return "파일 분석"
        elif source == "report":
            return "리포트 파싱"
        elif source == "awr_estimate":
            return "AWR 추정"
        else:
            return "없음 (추정값)"
