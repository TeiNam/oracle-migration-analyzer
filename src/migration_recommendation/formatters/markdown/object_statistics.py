"""
Markdown 오브젝트 통계 포맷터

데이터베이스 오브젝트 통계 섹션을 Markdown 형식으로 변환합니다.
"""

from ...data_models import AnalysisMetrics


class ObjectStatisticsFormatterMixin:
    """오브젝트 통계 포맷터 믹스인"""
    
    @staticmethod
    def _format_object_statistics(metrics: AnalysisMetrics, language: str) -> str:
        """오브젝트 통계 섹션 포맷"""
        # 데이터가 없으면 빈 문자열 반환
        has_plsql = any([
            metrics.awr_package_count, metrics.awr_procedure_count,
            metrics.awr_function_count, metrics.awr_plsql_lines
        ])
        has_schema = any([
            metrics.count_schemas, metrics.count_tables, metrics.count_views,
            metrics.count_indexes, metrics.count_triggers
        ])
        
        if not has_plsql and not has_schema:
            return ""
        
        if language == "ko":
            return ObjectStatisticsFormatterMixin._format_ko(metrics, has_plsql, has_schema)
        return ObjectStatisticsFormatterMixin._format_en(metrics, has_plsql, has_schema)
    
    @staticmethod
    def _extract_number(value) -> int:
        """문자열이나 숫자에서 숫자 값 추출"""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            import re
            numbers = re.findall(r'\d+', value)
            if numbers:
                return int(numbers[-1])
        return 0
    
    @staticmethod
    def _format_ko(metrics: AnalysisMetrics, has_plsql: bool, has_schema: bool) -> str:
        """한국어 오브젝트 통계"""
        sections = []
        
        sections.append("# 📦 데이터베이스 오브젝트 통계\n")
        sections.append("> 마이그레이션 대상 오브젝트의 전체 현황입니다.\n")
        
        # PL/SQL 오브젝트
        if has_plsql:
            sections.append("## PL/SQL 오브젝트\n")
            sections.append("| 오브젝트 유형 | 개수 | 변환 난이도 |")
            sections.append("|-------------|------|------------|")
            
            if metrics.awr_package_count:
                pkg = ObjectStatisticsFormatterMixin._extract_number(metrics.awr_package_count)
                sections.append(f"| 패키지 | {pkg:,} | 🔴 높음 |")
            if metrics.awr_procedure_count:
                proc = ObjectStatisticsFormatterMixin._extract_number(metrics.awr_procedure_count)
                sections.append(f"| 프로시저 | {proc:,} | 🟠 중간 |")
            if metrics.awr_function_count:
                func = ObjectStatisticsFormatterMixin._extract_number(metrics.awr_function_count)
                sections.append(f"| 함수 | {func:,} | 🟠 중간 |")
            if metrics.count_triggers:
                sections.append(f"| 트리거 | {metrics.count_triggers:,} | 🟠 중간 |")
            if metrics.count_types:
                sections.append(f"| 타입 | {metrics.count_types:,} | 🔴 높음 |")
            if metrics.awr_plsql_lines:
                lines = ObjectStatisticsFormatterMixin._extract_number(metrics.awr_plsql_lines)
                sections.append(f"| **총 PL/SQL 라인 수** | **{lines:,}** | - |")
        
        # 스키마 오브젝트
        if has_schema:
            sections.append("\n## 스키마 오브젝트\n")
            sections.append("| 오브젝트 유형 | 개수 | 변환 방법 |")
            sections.append("|-------------|------|----------|")
            
            if metrics.count_schemas:
                sections.append(f"| 스키마 | {metrics.count_schemas:,} | SCT 자동 변환 |")
            if metrics.count_tables:
                sections.append(f"| 테이블 | {metrics.count_tables:,} | SCT 자동 변환 |")
            if metrics.count_views:
                sections.append(f"| 뷰 | {metrics.count_views:,} | 일부 수동 검토 |")
            if metrics.count_indexes:
                sections.append(f"| 인덱스 | {metrics.count_indexes:,} | SCT 자동 변환 |")
            if metrics.count_sequences:
                sections.append(f"| 시퀀스 | {metrics.count_sequences:,} | SCT 자동 변환 |")
            if metrics.count_materialized_views:
                sections.append(f"| 구체화 뷰 | {metrics.count_materialized_views:,} | 수동 검토 필요 |")
            if metrics.count_db_links:
                sections.append(f"| DB Link | {metrics.count_db_links:,} | 아키텍처 검토 |")
            if metrics.count_lobs:
                sections.append(f"| LOB | {metrics.count_lobs:,} | SCT 자동 변환 |")
        
        return "\n".join(sections)
    
    @staticmethod
    def _format_en(metrics: AnalysisMetrics, has_plsql: bool, has_schema: bool) -> str:
        """영어 오브젝트 통계"""
        sections = []
        
        sections.append("# 📦 Database Object Statistics\n")
        sections.append("> Overview of all objects for migration.\n")
        
        if has_plsql:
            sections.append("## PL/SQL Objects\n")
            sections.append("| Object Type | Count | Conversion Difficulty |")
            sections.append("|-------------|-------|----------------------|")
            
            if metrics.awr_package_count:
                pkg = ObjectStatisticsFormatterMixin._extract_number(metrics.awr_package_count)
                sections.append(f"| Package | {pkg:,} | 🔴 High |")
            if metrics.awr_procedure_count:
                proc = ObjectStatisticsFormatterMixin._extract_number(metrics.awr_procedure_count)
                sections.append(f"| Procedure | {proc:,} | 🟠 Medium |")
            if metrics.awr_function_count:
                func = ObjectStatisticsFormatterMixin._extract_number(metrics.awr_function_count)
                sections.append(f"| Function | {func:,} | 🟠 Medium |")
            if metrics.count_triggers:
                sections.append(f"| Trigger | {metrics.count_triggers:,} | 🟠 Medium |")
            if metrics.count_types:
                sections.append(f"| Type | {metrics.count_types:,} | 🔴 High |")
            if metrics.awr_plsql_lines:
                lines = ObjectStatisticsFormatterMixin._extract_number(metrics.awr_plsql_lines)
                sections.append(f"| **Total PL/SQL Lines** | **{lines:,}** | - |")
        
        if has_schema:
            sections.append("\n## Schema Objects\n")
            sections.append("| Object Type | Count | Conversion Method |")
            sections.append("|-------------|-------|-------------------|")
            
            if metrics.count_schemas:
                sections.append(f"| Schema | {metrics.count_schemas:,} | SCT Auto |")
            if metrics.count_tables:
                sections.append(f"| Table | {metrics.count_tables:,} | SCT Auto |")
            if metrics.count_views:
                sections.append(f"| View | {metrics.count_views:,} | Manual Review |")
            if metrics.count_indexes:
                sections.append(f"| Index | {metrics.count_indexes:,} | SCT Auto |")
            if metrics.count_sequences:
                sections.append(f"| Sequence | {metrics.count_sequences:,} | SCT Auto |")
            if metrics.count_materialized_views:
                sections.append(f"| Materialized View | {metrics.count_materialized_views:,} | Manual |")
            if metrics.count_db_links:
                sections.append(f"| DB Link | {metrics.count_db_links:,} | Architecture Review |")
            if metrics.count_lobs:
                sections.append(f"| LOB | {metrics.count_lobs:,} | SCT Auto |")
        
        return "\n".join(sections)
