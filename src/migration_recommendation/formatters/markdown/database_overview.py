"""
Markdown 데이터베이스 개요 포맷터

데이터베이스 기본 정보 및 오브젝트 통계 섹션을 Markdown 형식으로 변환합니다.
"""

from typing import Optional, List, Dict, Any
from ...data_models import AnalysisMetrics


class DatabaseOverviewFormatterMixin:
    """데이터베이스 개요 포맷터 믹스인"""
    
    @staticmethod
    def _format_database_overview(metrics: AnalysisMetrics, language: str) -> str:
        """데이터베이스 개요 섹션 포맷 (간소화 버전)
        
        Args:
            metrics: 분석 메트릭 데이터
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식 문자열
        """
        if not any([metrics.db_name, metrics.db_version, metrics.total_db_size_gb]):
            return ""
        
        if language == "ko":
            return DatabaseOverviewFormatterMixin._format_ko(metrics)
        return DatabaseOverviewFormatterMixin._format_en(metrics)
    
    @staticmethod
    def _format_ko(metrics: AnalysisMetrics) -> str:
        """한국어 데이터베이스 개요 - AWR 리포트 양식"""
        sections = []
        
        # 헤더
        sections.append("## 데이터베이스 개요\n")
        
        # 기본 정보 테이블 (3컬럼: 항목 | 값 | 설명)
        sections.append("### 기본 정보\n")
        sections.append("| 항목 | 값 | 설명 |")
        sections.append("|------|-----|------|")
        
        if metrics.db_name:
            sections.append(
                f"| 데이터베이스 이름 | {metrics.db_name} | "
                "마이그레이션 대상 DB를 식별하는 이름입니다 |"
            )
        if metrics.db_version:
            sections.append(
                f"| Oracle 버전 | {metrics.db_version} | "
                "현재 사용 중인 Oracle 버전입니다 |"
            )
        if metrics.character_set:
            charset_desc = "데이터베이스 문자 인코딩 방식입니다"
            if "UTF" in metrics.character_set.upper():
                charset_desc = "UTF8 계열로 Aurora와 호환됩니다"
            sections.append(f"| 문자셋 | {metrics.character_set} | {charset_desc} |")
        
        # 인스턴스 정보
        if metrics.instance_count and metrics.instance_count > 1:
            sections.append(
                f"| 인스턴스 수 | {metrics.instance_count} (RAC) | "
                "RAC 구성으로 마이그레이션 시 추가 검토가 필요합니다 |"
            )
        else:
            sections.append(
                "| 인스턴스 수 | 1 (단일 인스턴스) | "
                "단일 서버로 마이그레이션이 상대적으로 단순합니다 |"
            )
        
        # 크기 및 리소스 정보
        sections.append("")
        sections.append("### 크기 및 리소스 정보\n")
        sections.append("| 항목 | 값 | 설명 |")
        sections.append("|------|-----|------|")
        
        if metrics.total_db_size_gb:
            size_desc = "실제 데이터가 차지하는 디스크 공간입니다"
            if metrics.total_db_size_gb < 100:
                size_desc = "소규모 DB로 빠른 마이그레이션이 가능합니다"
            elif metrics.total_db_size_gb < 500:
                size_desc = "중소 규모로 일반적인 마이그레이션 절차를 적용합니다"
            elif metrics.total_db_size_gb < 1000:
                size_desc = "중간 규모로 일반적인 마이그레이션 절차를 적용합니다"
            else:
                size_desc = "대규모 DB로 단계적 마이그레이션을 권장합니다"
            sections.append(f"| 전체 DB 크기 | {metrics.total_db_size_gb:,.1f} GB | {size_desc} |")
        
        if metrics.physical_memory_gb:
            sections.append(
                f"| 물리 메모리 | {metrics.physical_memory_gb:,.1f} GB | "
                "현재 서버의 총 메모리입니다. Aurora 인스턴스 선택 시 참고합니다 |"
            )
        if metrics.cpu_cores:
            sections.append(
                f"| CPU 코어 수 | {metrics.cpu_cores} | "
                "현재 서버의 CPU 코어 수입니다. AWS vCPU 산정 기준이 됩니다 |"
            )
        
        # PL/SQL 오브젝트 통계
        plsql_section = DatabaseOverviewFormatterMixin._format_plsql_objects_ko(metrics)
        if plsql_section:
            sections.append("")
            sections.append(plsql_section)
        
        # 스키마 오브젝트 통계
        schema_section = DatabaseOverviewFormatterMixin._format_schema_objects_ko(metrics)
        if schema_section:
            sections.append("")
            sections.append(schema_section)
        
        return "\n".join(sections)
    
    @staticmethod
    def _format_plsql_objects_ko(metrics: AnalysisMetrics) -> str:
        """PL/SQL 오브젝트 통계 (한국어) - AWR 리포트 양식"""
        # AWR에서 가져온 PL/SQL 통계가 있는지 확인
        has_plsql_stats = any([
            metrics.awr_package_count,
            metrics.awr_procedure_count,
            metrics.awr_function_count,
            metrics.awr_plsql_lines
        ])
        
        if not has_plsql_stats:
            return ""
        
        lines = []
        lines.append("### PL/SQL 오브젝트\n")
        lines.append("| 오브젝트 유형 | 개수 | 변환 난이도 | 설명 |")
        lines.append("|-------------|------|------------|------|")
        
        if metrics.awr_package_count:
            lines.append(
                f"| 패키지 | {metrics.awr_package_count:,} | 🔴 높음 | "
                "여러 프로시저/함수를 묶은 모듈. 가장 복잡한 변환 대상 |"
            )
        if metrics.awr_procedure_count:
            lines.append(
                f"| 프로시저 | {metrics.awr_procedure_count:,} | 🟠 중간 | "
                "특정 작업을 수행하는 프로그램 단위 |"
            )
        if metrics.awr_function_count:
            lines.append(
                f"| 함수 | {metrics.awr_function_count:,} | 🟠 중간 | "
                "값을 계산하여 반환하는 프로그램 단위 |"
            )
        if metrics.count_triggers:
            lines.append(
                f"| 트리거 | {metrics.count_triggers:,} | 🟠 중간 | "
                "데이터 변경 시 자동 실행되는 프로그램 |"
            )
        if metrics.count_types:
            lines.append(
                f"| 타입 | {metrics.count_types:,} | 🔴 높음 | "
                "사용자 정의 데이터 타입. 타겟 DB에서 재설계 필요 |"
            )
        
        # 총계
        total_objects = sum(filter(None, [
            metrics.awr_package_count,
            metrics.awr_procedure_count,
            metrics.awr_function_count,
            metrics.count_triggers,
            metrics.count_types
        ]))
        if total_objects > 0:
            lines.append(
                f"| **총 PL/SQL 오브젝트 수** | **{total_objects:,}** | - | "
                "변환 대상 프로그램 오브젝트 총합 |"
            )
        
        if metrics.awr_plsql_lines:
            lines.append(
                f"| **총 PL/SQL 라인 수** | **{metrics.awr_plsql_lines:,}** | - | "
                "변환 작업량 산정의 기준 |"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_schema_objects_ko(metrics: AnalysisMetrics) -> str:
        """스키마 오브젝트 통계 (한국어) - AWR 리포트 양식"""
        has_schema_stats = any([
            metrics.count_schemas,
            metrics.count_tables,
            metrics.count_views,
            metrics.count_indexes
        ])
        
        if not has_schema_stats:
            return ""
        
        lines = []
        lines.append("### 스키마 오브젝트\n")
        lines.append("| 오브젝트 유형 | 개수 | 변환 방법 | 설명 |")
        lines.append("|-------------|------|----------|------|")
        
        if metrics.count_schemas:
            lines.append(
                f"| 스키마 | {metrics.count_schemas:,} | SCT 자동 변환 | "
                "데이터베이스 내 논리적 구분 단위 |"
            )
        if metrics.count_tables:
            lines.append(
                f"| 테이블 | {metrics.count_tables:,} | SCT 자동 변환 | "
                "실제 데이터가 저장되는 기본 단위 |"
            )
        if metrics.count_views:
            lines.append(
                f"| 뷰 | {metrics.count_views:,} | 일부 수동 검토 | "
                "가상 테이블. 복잡한 뷰는 검토 필요 |"
            )
        if metrics.count_indexes:
            lines.append(
                f"| 인덱스 | {metrics.count_indexes:,} | SCT 자동 변환 | "
                "검색 속도 향상을 위한 구조 |"
            )
        if metrics.count_sequences:
            lines.append(
                f"| 시퀀스 | {metrics.count_sequences:,} | SCT 자동 변환 | "
                "자동 증가 번호 생성기 |"
            )
        if metrics.count_lobs:
            lines.append(
                f"| LOB | {metrics.count_lobs:,} | SCT 자동 변환 | "
                "대용량 데이터 (이미지, 문서 등) |"
            )
        if metrics.count_materialized_views:
            lines.append(
                f"| Materialized View | {metrics.count_materialized_views:,} | 수동 검토 | "
                "미리 계산된 결과 저장. 갱신 로직 검토 필요 |"
            )
        if metrics.count_db_links:
            lines.append(
                f"| DB Link | {metrics.count_db_links:,} | 아키텍처 검토 | "
                "다른 DB 연결. 네트워크 구성 재설계 필요 |"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_en(metrics: AnalysisMetrics) -> str:
        """영어 데이터베이스 개요 - AWR 리포트 양식"""
        sections = []
        
        sections.append("## Database Overview\n")
        
        # 기본 정보 (3컬럼)
        sections.append("### Basic Information\n")
        sections.append("| Item | Value | Description |")
        sections.append("|------|-------|-------------|")
        
        if metrics.db_name:
            sections.append(
                f"| Database Name | {metrics.db_name} | "
                "Identifies the migration target database |"
            )
        if metrics.db_version:
            sections.append(
                f"| Oracle Version | {metrics.db_version} | "
                "Current Oracle version in use |"
            )
        if metrics.character_set:
            charset_desc = "Database character encoding"
            if "UTF" in metrics.character_set.upper():
                charset_desc = "UTF8 family, compatible with Aurora"
            sections.append(f"| Character Set | {metrics.character_set} | {charset_desc} |")
        
        if metrics.instance_count and metrics.instance_count > 1:
            sections.append(
                f"| Instance Count | {metrics.instance_count} (RAC) | "
                "RAC configuration requires additional review |"
            )
        else:
            sections.append(
                "| Instance Count | 1 (Single Instance) | "
                "Single server, relatively simple migration |"
            )
        
        # 크기 및 리소스
        sections.append("")
        sections.append("### Size and Resource Information\n")
        sections.append("| Item | Value | Description |")
        sections.append("|------|-------|-------------|")
        
        if metrics.total_db_size_gb:
            size_desc = "Actual disk space used by data"
            if metrics.total_db_size_gb < 100:
                size_desc = "Small DB, fast migration possible"
            elif metrics.total_db_size_gb < 500:
                size_desc = "Small-medium size, standard migration procedure"
            elif metrics.total_db_size_gb < 1000:
                size_desc = "Medium size, standard migration procedure"
            else:
                size_desc = "Large DB, phased migration recommended"
            sections.append(f"| Total DB Size | {metrics.total_db_size_gb:,.1f} GB | {size_desc} |")
        
        if metrics.physical_memory_gb:
            sections.append(
                f"| Physical Memory | {metrics.physical_memory_gb:,.1f} GB | "
                "Current server memory. Reference for Aurora instance selection |"
            )
        if metrics.cpu_cores:
            sections.append(
                f"| CPU Cores | {metrics.cpu_cores} | "
                "Current server CPU cores. Basis for AWS vCPU calculation |"
            )
        
        # PL/SQL Objects
        plsql_section = DatabaseOverviewFormatterMixin._format_plsql_objects_en(metrics)
        if plsql_section:
            sections.append("")
            sections.append(plsql_section)
        
        # Schema Objects
        schema_section = DatabaseOverviewFormatterMixin._format_schema_objects_en(metrics)
        if schema_section:
            sections.append("")
            sections.append(schema_section)
        
        return "\n".join(sections)
    
    @staticmethod
    def _format_plsql_objects_en(metrics: AnalysisMetrics) -> str:
        """PL/SQL Objects (English) - AWR report format"""
        has_plsql_stats = any([
            metrics.awr_package_count,
            metrics.awr_procedure_count,
            metrics.awr_function_count,
            metrics.awr_plsql_lines
        ])
        
        if not has_plsql_stats:
            return ""
        
        lines = []
        lines.append("### PL/SQL Objects\n")
        lines.append("| Object Type | Count | Conversion Difficulty | Description |")
        lines.append("|-------------|-------|----------------------|-------------|")
        
        if metrics.awr_package_count:
            lines.append(
                f"| Package | {metrics.awr_package_count:,} | 🔴 High | "
                "Module bundling procedures/functions. Most complex to convert |"
            )
        if metrics.awr_procedure_count:
            lines.append(
                f"| Procedure | {metrics.awr_procedure_count:,} | 🟠 Medium | "
                "Program unit performing specific tasks |"
            )
        if metrics.awr_function_count:
            lines.append(
                f"| Function | {metrics.awr_function_count:,} | 🟠 Medium | "
                "Program unit that calculates and returns values |"
            )
        if metrics.count_triggers:
            lines.append(
                f"| Trigger | {metrics.count_triggers:,} | 🟠 Medium | "
                "Auto-executed program on data changes |"
            )
        if metrics.count_types:
            lines.append(
                f"| Type | {metrics.count_types:,} | 🔴 High | "
                "User-defined data type. Requires redesign in target DB |"
            )
        
        total_objects = sum(filter(None, [
            metrics.awr_package_count,
            metrics.awr_procedure_count,
            metrics.awr_function_count,
            metrics.count_triggers,
            metrics.count_types
        ]))
        if total_objects > 0:
            lines.append(
                f"| **Total PL/SQL Objects** | **{total_objects:,}** | - | "
                "Total program objects to convert |"
            )
        
        if metrics.awr_plsql_lines:
            lines.append(
                f"| **Total PL/SQL Lines** | **{metrics.awr_plsql_lines:,}** | - | "
                "Basis for conversion effort estimation |"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_schema_objects_en(metrics: AnalysisMetrics) -> str:
        """Schema Objects (English) - AWR report format"""
        has_schema_stats = any([
            metrics.count_schemas,
            metrics.count_tables,
            metrics.count_views,
            metrics.count_indexes
        ])
        
        if not has_schema_stats:
            return ""
        
        lines = []
        lines.append("### Schema Objects\n")
        lines.append("| Object Type | Count | Conversion Method | Description |")
        lines.append("|-------------|-------|-------------------|-------------|")
        
        if metrics.count_schemas:
            lines.append(
                f"| Schema | {metrics.count_schemas:,} | SCT Auto | "
                "Logical grouping unit in database |"
            )
        if metrics.count_tables:
            lines.append(
                f"| Table | {metrics.count_tables:,} | SCT Auto | "
                "Basic unit where data is stored |"
            )
        if metrics.count_views:
            lines.append(
                f"| View | {metrics.count_views:,} | Partial Manual | "
                "Virtual table. Complex views need review |"
            )
        if metrics.count_indexes:
            lines.append(
                f"| Index | {metrics.count_indexes:,} | SCT Auto | "
                "Structure for search performance |"
            )
        if metrics.count_sequences:
            lines.append(
                f"| Sequence | {metrics.count_sequences:,} | SCT Auto | "
                "Auto-increment number generator |"
            )
        if metrics.count_lobs:
            lines.append(
                f"| LOB | {metrics.count_lobs:,} | SCT Auto | "
                "Large objects (images, documents) |"
            )
        if metrics.count_materialized_views:
            lines.append(
                f"| Materialized View | {metrics.count_materialized_views:,} | Manual Review | "
                "Pre-computed results. Refresh logic review needed |"
            )
        if metrics.count_db_links:
            lines.append(
                f"| DB Link | {metrics.count_db_links:,} | Architecture Review | "
                "Cross-DB connection. Network redesign needed |"
            )
        
        return "\n".join(lines)
