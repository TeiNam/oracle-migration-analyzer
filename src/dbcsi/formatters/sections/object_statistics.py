"""
데이터베이스 오브젝트 통계 섹션 포맷터

PL/SQL 오브젝트와 스키마 오브젝트의 전체 현황을 표시합니다.
"""

import re
from typing import Optional
from ...models import StatspackData


class ObjectStatisticsFormatter:
    """오브젝트 통계 포맷터"""
    
    @staticmethod
    def _extract_number(value) -> int:
        """문자열이나 숫자에서 숫자 값만 추출"""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            numbers = re.findall(r'\d+', value)
            if numbers:
                return int(numbers[-1])
        return 0
    
    @staticmethod
    def format(data: StatspackData, language: str = "ko") -> str:
        """오브젝트 통계 섹션 포맷
        
        Args:
            data: Statspack/AWR 데이터
            language: 출력 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식의 문자열
        """
        if language == "ko":
            return ObjectStatisticsFormatter._format_ko(data)
        return ObjectStatisticsFormatter._format_en(data)
    
    @staticmethod
    def _format_ko(data: StatspackData) -> str:
        """한국어 오브젝트 통계"""
        lines = []
        os_info = data.os_info
        
        if not os_info:
            return ""
        
        # PL/SQL 관련 데이터가 있는지 확인
        has_plsql = any([
            os_info.count_packages,
            os_info.count_procedures,
            os_info.count_functions,
            os_info.count_lines_plsql
        ])
        
        # 스키마 오브젝트 데이터가 있는지 확인
        has_schema = any([
            os_info.count_schemas,
            os_info.count_tables
        ])
        
        if not has_plsql and not has_schema:
            return ""
        
        lines.append("## 📦 데이터베이스 오브젝트 통계\n")
        lines.append("### 이 섹션의 목적\n")
        lines.append("마이그레이션 대상 오브젝트(테이블, 프로시저 등)의 전체 현황을 보여줍니다.")
        lines.append("오브젝트 유형별 개수를 파악하여 **변환 작업량과 소요 시간을 추정**하는 데 사용됩니다.\n")
        lines.append("> **💡 IT 관계자를 위한 설명**")
        lines.append("> - **오브젝트**: 데이터베이스에 저장된 구성 요소 (테이블, 프로시저, 함수 등)")
        lines.append("> - **변환**: Oracle 문법을 타겟 DB(Aurora 등) 문법으로 바꾸는 작업")
        lines.append("> - 오브젝트 수가 많을수록 마이그레이션 기간과 비용이 증가합니다\n")
        
        # PL/SQL 오브젝트 섹션
        if has_plsql:
            lines.append("### PL/SQL 오브젝트\n")
            lines.append("> **PL/SQL 오브젝트란?**")
            lines.append("> Oracle 데이터베이스에 저장된 **프로그램 코드**입니다.")
            lines.append("> 비즈니스 로직, 데이터 처리 규칙 등이 포함되어 있습니다.")
            lines.append("> 마이그레이션 시 타겟 DB 문법으로 **수동 변환이 필요**합니다.\n")
            lines.append("> **💡 변환 난이도 설명**")
            lines.append("> - 🔴 **높음**: 복잡한 로직, 수동 변환 필수, 전문가 검토 필요")
            lines.append("> - 🟠 **중간**: 일부 자동 변환 가능, 검토 필요")
            lines.append("> - 🟢 **낮음**: 대부분 자동 변환 가능\n")
            
            lines.append("| 오브젝트 유형 | 개수 | 변환 난이도 | 설명 |")
            lines.append("|-------------|------|------------|------|")
            
            pkg_count = ObjectStatisticsFormatter._extract_number(os_info.count_packages)
            proc_count = ObjectStatisticsFormatter._extract_number(os_info.count_procedures)
            func_count = ObjectStatisticsFormatter._extract_number(os_info.count_functions)
            trigger_count = ObjectStatisticsFormatter._extract_number(os_info.count_triggers)
            type_count = ObjectStatisticsFormatter._extract_number(os_info.count_types)
            type_body_count = ObjectStatisticsFormatter._extract_number(os_info.count_type_bodies)
            
            if pkg_count > 0:
                lines.append(f"| 패키지 | {pkg_count:,} | 🔴 높음 | "
                           "여러 프로시저/함수를 묶은 모듈. 가장 복잡한 변환 대상 |")
            if proc_count > 0:
                lines.append(f"| 프로시저 | {proc_count:,} | 🟠 중간 | "
                           "특정 작업을 수행하는 프로그램 단위 |")
            if func_count > 0:
                lines.append(f"| 함수 | {func_count:,} | 🟠 중간 | "
                           "값을 계산하여 반환하는 프로그램 단위 |")
            if trigger_count > 0:
                lines.append(f"| 트리거 | {trigger_count:,} | 🟠 중간 | "
                           "데이터 변경 시 자동 실행되는 프로그램 |")
            if type_count > 0:
                lines.append(f"| 타입 | {type_count:,} | 🔴 높음 | "
                           "사용자 정의 데이터 타입. 타겟 DB에서 재설계 필요 |")
            if type_body_count > 0:
                lines.append(f"| 타입 바디 | {type_body_count:,} | 🔴 높음 | "
                           "타입의 메서드 구현부. 타입과 함께 변환 필요 |")
            
            # PL/SQL 오브젝트 총합 계산
            total_plsql_objects = (pkg_count + proc_count + func_count + 
                                   trigger_count + type_count + type_body_count)
            if total_plsql_objects > 0:
                lines.append(f"| **총 PL/SQL 오브젝트 수** | **{total_plsql_objects:,}** | - | "
                           "변환 대상 프로그램 오브젝트 총합 |")
            
            # PL/SQL 라인 수
            if os_info.count_lines_plsql:
                lines.append(f"| **총 PL/SQL 라인 수** | **{os_info.count_lines_plsql:,}** | - | "
                           "변환 작업량 산정의 기준 |")
            
            lines.append("")
            
            # 변환 작업량 추정
            if os_info.count_lines_plsql:
                estimated_hours = os_info.count_lines_plsql * 20 / 100 / 60  # 100줄당 20분
                lines.append("#### 변환 작업량 추정\n")
                lines.append("> **💡 이 수치의 의미**")
                lines.append("> 아래는 업계 평균 기준의 추정치입니다. 실제 소요 시간은 코드 복잡도,")
                lines.append("> 개발자 숙련도, 사용 도구에 따라 달라질 수 있습니다.\n")
                lines.append(f"- **예상 변환 시간**: 약 **{estimated_hours:.0f}시간** (100줄당 20분 기준)")
                lines.append(f"- **AI 도구 활용 시**: 약 **{estimated_hours * 0.6:.0f}시간** (40% 단축 가능)")
                lines.append(f"- **예상 인력**: {estimated_hours / 8:.1f}인일 (1일 8시간 기준)")
                lines.append("")
        
        # 스키마 오브젝트 섹션
        if has_schema:
            lines.append("### 스키마 오브젝트\n")
            lines.append("> **스키마 오브젝트란?**")
            lines.append("> 테이블, 뷰, 인덱스 등 **데이터 구조를 정의**하는 오브젝트입니다.")
            lines.append("> 실제 비즈니스 데이터가 저장되는 곳입니다.\n")
            
            lines.append("> **💡 AWS SCT(Schema Conversion Tool)란?**")
            lines.append("> AWS에서 제공하는 무료 도구로, Oracle 스키마를 Aurora/PostgreSQL/MySQL")
            lines.append("> 스키마로 자동 변환해줍니다. 수동 작업 대비 90% 이상 시간 절약 가능.\n")
            
            lines.append("> **⚠️ SCT 변환의 한계**")
            lines.append("> SCT가 모든 오브젝트를 자동 변환하는 것은 아닙니다:")
            lines.append("> - **자동 변환 가능**: 테이블, 인덱스, 시퀀스, 기본 뷰 등")
            lines.append("> - **수동 검토 필요**: 복잡한 뷰, Materialized View, 파티션 테이블, 사용자 정의 타입")
            lines.append("> - **타겟 DB에 따라 불가**: Oracle 전용 기능(DB Link, Advanced Queue 등)은")
            lines.append(">   타겟 DB에서 지원하지 않아 아키텍처 재설계가 필요할 수 있습니다.\n")
            
            lines.append("| 오브젝트 유형 | 개수 | 변환 방법 | 설명 |")
            lines.append("|-------------|------|----------|------|")
            
            # 스키마
            if os_info.count_schemas and isinstance(os_info.count_schemas, int):
                lines.append(f"| 스키마 | {os_info.count_schemas:,} | SCT 자동 변환 | "
                           "데이터베이스 내 논리적 구분 단위 |")
            
            # 테이블
            if os_info.count_tables and isinstance(os_info.count_tables, int):
                lines.append(f"| 테이블 | {os_info.count_tables:,} | SCT 자동 변환 | "
                           "실제 데이터가 저장되는 기본 단위 |")
            
            # 뷰
            view_count = ObjectStatisticsFormatter._extract_number(os_info.count_views)
            if view_count > 0:
                lines.append(f"| 뷰 | {view_count:,} | 일부 수동 검토 | "
                           "가상 테이블. 복잡한 뷰는 검토 필요 |")
            
            # 인덱스
            idx_count = ObjectStatisticsFormatter._extract_number(os_info.count_indexes)
            if idx_count > 0:
                lines.append(f"| 인덱스 | {idx_count:,} | SCT 자동 변환 | "
                           "검색 속도 향상을 위한 구조 |")
            
            # 시퀀스
            seq_count = ObjectStatisticsFormatter._extract_number(os_info.count_sequences)
            if seq_count > 0:
                lines.append(f"| 시퀀스 | {seq_count:,} | SCT 자동 변환 | "
                           "자동 증가 번호 생성기 |")
            
            # LOB
            lob_count = ObjectStatisticsFormatter._extract_number(os_info.count_lobs)
            if lob_count > 0:
                lines.append(f"| LOB | {lob_count:,} | SCT 자동 변환 | "
                           "대용량 데이터 (이미지, 문서 등) |")
            
            # Materialized View
            mv_count = ObjectStatisticsFormatter._extract_number(os_info.count_materialized_views)
            if mv_count > 0:
                lines.append(f"| Materialized View | {mv_count:,} | 수동 검토 | "
                           "미리 계산된 결과 저장. 갱신 로직 검토 필요 |")
            
            # DB Link
            dblink_count = ObjectStatisticsFormatter._extract_number(os_info.count_db_links)
            if dblink_count > 0:
                lines.append(f"| DB Link | {dblink_count:,} | 아키텍처 검토 | "
                           "다른 DB 연결. 네트워크 구성 재설계 필요 |")
            
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_en(data: StatspackData) -> str:
        """영어 오브젝트 통계"""
        lines = []
        os_info = data.os_info
        
        if not os_info:
            return ""
        
        has_plsql = any([
            os_info.count_packages,
            os_info.count_procedures,
            os_info.count_functions,
            os_info.count_lines_plsql
        ])
        
        has_schema = any([
            os_info.count_schemas,
            os_info.count_tables
        ])
        
        if not has_plsql and not has_schema:
            return ""
        
        lines.append("## 📦 Database Object Statistics\n")
        lines.append("> Overview of migration target objects.")
        lines.append("> Used to estimate conversion workload.\n")
        
        if has_plsql:
            lines.append("### PL/SQL Objects\n")
            lines.append("| Object Type | Count | Conversion Difficulty |")
            lines.append("|-------------|-------|----------------------|")
            
            pkg_count = ObjectStatisticsFormatter._extract_number(os_info.count_packages)
            proc_count = ObjectStatisticsFormatter._extract_number(os_info.count_procedures)
            func_count = ObjectStatisticsFormatter._extract_number(os_info.count_functions)
            
            if pkg_count > 0:
                lines.append(f"| Packages | {pkg_count:,} | 🔴 High |")
            if proc_count > 0:
                lines.append(f"| Procedures | {proc_count:,} | 🟠 Medium |")
            if func_count > 0:
                lines.append(f"| Functions | {func_count:,} | 🟠 Medium |")
            
            if os_info.count_lines_plsql:
                lines.append(f"| **Total PL/SQL Lines** | **{os_info.count_lines_plsql:,}** | - |")
            
            lines.append("")
        
        if has_schema:
            lines.append("### Schema Objects\n")
            lines.append("| Object Type | Count | Conversion Method |")
            lines.append("|-------------|-------|-------------------|")
            
            if os_info.count_schemas and isinstance(os_info.count_schemas, int):
                lines.append(f"| Schemas | {os_info.count_schemas:,} | SCT Auto |")
            
            if os_info.count_tables and isinstance(os_info.count_tables, int):
                lines.append(f"| Tables | {os_info.count_tables:,} | SCT Auto |")
            
            lines.append("")
        
        return "\n".join(lines)
