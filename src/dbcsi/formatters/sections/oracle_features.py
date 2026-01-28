"""
Oracle 기능 사용 현황 섹션 포맷터

Oracle 데이터베이스에서 사용 중인 기능을 파악하여 마이그레이션 호환성을 평가합니다.
"""

from typing import List, Dict, Any, Tuple
from ...models import StatspackData


class OracleFeaturesFormatter:
    """Oracle 기능 사용 현황 포맷터"""
    
    # Oracle 내부 관리 기능 (마이그레이션에 영향 없음)
    # 이 기능들은 Oracle EE 설치 시 기본 활성화되며, 타겟 DB에서 자동 관리됨
    INTERNAL_FEATURES = {
        # 자동 유지보수 기능 - 타겟 DB에서 자체 관리
        "Adaptive Plans",
        "Automatic Maintenance - Optimizer Statistics Gathering",
        "Automatic Maintenance - SQL Tuning Advisor",
        "Automatic Maintenance - Space Advisor",
        "Automatic Reoptimization",
        "Automatic SGA Tuning",
        "Automatic SQL Execution Memory",
        "Automatic Undo Management",
        "DBMS_STATS Incremental Maintenance",
        "SQL Plan Directive",
        # 스토리지/세그먼트 관리 - 타겟 DB에서 자동 관리
        "Deferred Segment Creation",
        "Automatic Segment Space Management",
        "Locally Managed Tablespaces",
        "Bigfile Tablespace",
        "SecureFiles",
        # 설정/감사 기능 - 타겟 DB에서 별도 설정
        "Server Parameter File",
        "Traditional Audit",
        "Unified Audit",
        "Character Set",
        # 기타 내부 기능
        "Oracle Managed Files",
        "Services",
        "Resource Manager",
    }
    
    # 기능별 마이그레이션 영향도 및 대응 방안
    FEATURE_IMPACT: Dict[str, Dict[str, Any]] = {
        # 높은 영향도 (비호환) - 실제 검토 필요
        "Real Application Clusters": {
            "impact": "🔴", "level": "high",
            "response_ko": "Aurora Multi-AZ 또는 Global Database로 대체",
            "response_en": "Replace with Aurora Multi-AZ or Global Database"
        },
        "Advanced Compression": {
            "impact": "🔴", "level": "high",
            "response_ko": "Aurora 스토리지 비용 비교 필요",
            "response_en": "Compare Aurora storage costs"
        },
        "OLAP": {
            "impact": "🔴", "level": "high",
            "response_ko": "Amazon Redshift 또는 Athena 검토",
            "response_en": "Consider Amazon Redshift or Athena"
        },
        "Data Mining": {
            "impact": "🔴", "level": "high",
            "response_ko": "Amazon SageMaker 연동",
            "response_en": "Integrate with Amazon SageMaker"
        },
        "Oracle Database Vault": {
            "impact": "🔴", "level": "high",
            "response_ko": "IAM 및 애플리케이션 레벨 보안으로 대체",
            "response_en": "Replace with IAM and application-level security"
        },
        "Label Security": {
            "impact": "🔴", "level": "high",
            "response_ko": "애플리케이션 레벨 구현 필요",
            "response_en": "Application-level implementation required"
        },
        "Oracle Streams": {
            "impact": "🔴", "level": "high",
            "response_ko": "DMS 또는 Kinesis로 대체",
            "response_en": "Replace with DMS or Kinesis"
        },
        "Advanced Queuing": {
            "impact": "🔴", "level": "high",
            "response_ko": "Amazon SQS 또는 SNS로 대체",
            "response_en": "Replace with Amazon SQS or SNS"
        },
        "GoldenGate": {
            "impact": "🔴", "level": "high",
            "response_ko": "DMS CDC 또는 Debezium으로 대체",
            "response_en": "Replace with DMS CDC or Debezium"
        },
        "In-Memory Column Store": {
            "impact": "🔴", "level": "high",
            "response_ko": "Aurora 또는 Redshift 검토",
            "response_en": "Consider Aurora or Redshift"
        },
        
        # 중간 영향도 (부분 호환) - 검토 필요
        "Partitioning": {
            "impact": "🟠", "level": "medium",
            "response_ko": "PostgreSQL: 네이티브 지원, MySQL: 제한적 지원",
            "response_en": "PostgreSQL: native support, MySQL: limited"
        },
        "Spatial": {
            "impact": "🟠", "level": "medium",
            "response_ko": "PostGIS 또는 MySQL Spatial로 대체",
            "response_en": "Replace with PostGIS or MySQL Spatial"
        },
        "XML DB": {
            "impact": "🟠", "level": "medium",
            "response_ko": "PostgreSQL XML 타입 또는 JSON 변환",
            "response_en": "PostgreSQL XML type or JSON conversion"
        },
        "Oracle Text": {
            "impact": "🟠", "level": "medium",
            "response_ko": "PostgreSQL Full Text Search 또는 OpenSearch",
            "response_en": "PostgreSQL Full Text Search or OpenSearch"
        },
        "Materialized Views": {
            "impact": "🟠", "level": "medium",
            "response_ko": "PostgreSQL: 지원, MySQL: 뷰로 대체",
            "response_en": "PostgreSQL: supported, MySQL: use views"
        },
        "Real Application Security": {
            "impact": "🟠", "level": "medium",
            "response_ko": "애플리케이션 레벨 보안으로 구현",
            "response_en": "Implement at application level"
        },
        "Oracle Java Virtual Machine": {
            "impact": "🟠", "level": "medium",
            "response_ko": "Java 로직을 애플리케이션 레이어로 이관",
            "response_en": "Move Java logic to application layer"
        },
        "LOB": {
            "impact": "🟠", "level": "medium",
            "response_ko": "PostgreSQL: BYTEA/TEXT, MySQL: BLOB/TEXT",
            "response_en": "PostgreSQL: BYTEA/TEXT, MySQL: BLOB/TEXT"
        },
        "Object": {
            "impact": "🟠", "level": "medium",
            "response_ko": "객체 타입을 테이블/JSON으로 변환",
            "response_en": "Convert object types to tables/JSON"
        },
        "Extensibility": {
            "impact": "🟠", "level": "medium",
            "response_ko": "확장 기능 검토 필요",
            "response_en": "Review extensibility features"
        },
        "Oracle Call Interface (OCI)": {
            "impact": "🟠", "level": "medium",
            "response_ko": "타겟 DB 드라이버로 변경",
            "response_en": "Change to target DB driver"
        },
        "Oracle Utility External Table (ORACLE_LOADER)": {
            "impact": "🟠", "level": "medium",
            "response_ko": "COPY 명령 또는 데이터 파이프라인 사용",
            "response_en": "Use COPY command or data pipeline"
        },
        "SQL*Plus": {
            "impact": "🟢", "level": "low",
            "response_ko": "psql/mysql CLI로 대체",
            "response_en": "Replace with psql/mysql CLI"
        },
        
        # 낮은 영향도 (호환) - 무시 가능
        "Locally Managed Tablespaces": {
            "impact": "🟢", "level": "low",
            "response_ko": "호환 가능",
            "response_en": "Compatible"
        },
        "SecureFiles": {
            "impact": "🟢", "level": "low",
            "response_ko": "호환 가능",
            "response_en": "Compatible"
        },
        "Automatic Segment Space Management": {
            "impact": "🟢", "level": "low",
            "response_ko": "자동 관리 (무시 가능)",
            "response_en": "Auto-managed (can ignore)"
        }
    }
    
    @staticmethod
    def format(data: StatspackData, language: str = "ko") -> str:
        """Oracle 기능 사용 현황 섹션 포맷
        
        Args:
            data: Statspack/AWR 데이터
            language: 출력 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식의 문자열
        """
        if not data.features:
            return ""
        
        if language == "ko":
            return OracleFeaturesFormatter._format_ko(data)
        return OracleFeaturesFormatter._format_en(data)
    
    @staticmethod
    def _categorize_features(
        data: StatspackData
    ) -> Tuple[List[Any], List[Any], List[Any], List[Any]]:
        """기능을 user/system/내부관리/기타로 분류
        
        Returns:
            (user_features, system_features, internal_features, other_features)
        """
        user_features = []
        system_features = []
        internal_features = []
        other_features = []
        
        for feature in data.features:
            name = feature.name
            clean_name = name.replace(" (user)", "").replace(" (system)", "").strip()
            
            if "(system)" in name.lower():
                system_features.append(feature)
            elif "(user)" in name.lower():
                user_features.append(feature)
            elif clean_name in OracleFeaturesFormatter.INTERNAL_FEATURES:
                internal_features.append(feature)
            else:
                other_features.append(feature)
        
        return user_features, system_features, internal_features, other_features
    
    @staticmethod
    def _get_feature_impact(feature_name: str, language: str) -> Tuple[str, str]:
        """기능의 영향도와 대응 방안 반환"""
        # 기능 이름에서 (user), (system) 제거하여 매칭
        clean_name = feature_name.replace(" (user)", "").replace(" (system)", "").strip()
        
        if clean_name in OracleFeaturesFormatter.FEATURE_IMPACT:
            info = OracleFeaturesFormatter.FEATURE_IMPACT[clean_name]
            response_key = "response_ko" if language == "ko" else "response_en"
            return info["impact"], info[response_key]
        
        # 부분 매칭 시도
        for key, info in OracleFeaturesFormatter.FEATURE_IMPACT.items():
            if key.lower() in clean_name.lower() or clean_name.lower() in key.lower():
                response_key = "response_ko" if language == "ko" else "response_en"
                return info["impact"], info[response_key]
        
        # 기본값
        default_response = "검토 필요" if language == "ko" else "Review required"
        return "🟠", default_response
    
    @staticmethod
    def _format_ko(data: StatspackData) -> str:
        """한국어 Oracle 기능 사용 현황"""
        lines = []
        
        lines.append("## 🔧 Oracle 기능 사용 현황\n")
        lines.append("### 이 섹션의 목적\n")
        lines.append("Oracle 데이터베이스에서 사용 중인 **기능(Feature)**을 파악하여")
        lines.append("마이그레이션 호환성을 평가합니다.\n")
        lines.append("> **💡 IT 관계자를 위한 설명**")
        lines.append("> - **Feature**: Oracle이 제공하는 특수 기능 (압축, 파티셔닝, 보안 등)")
        lines.append("> - **호환성**: 타겟 DB(Aurora 등)에서 동일 기능을 지원하는지 여부")
        lines.append("> - 비호환 기능이 많을수록 마이그레이션 복잡도와 비용이 증가합니다")
        lines.append("> - 일부 기능은 AWS의 다른 서비스로 대체할 수 있습니다\n")
        
        # 영향도 범례
        lines.append("### 영향도 범례\n")
        lines.append("> 각 기능이 마이그레이션에 미치는 영향을 아이콘으로 표시합니다.\n")
        lines.append("| 아이콘 | 의미 | 설명 | 예상 추가 작업 |")
        lines.append("|--------|------|------|---------------|")
        lines.append("| 🟢 | 호환 | 타겟 DB에서 동일/유사 기능 지원 | 없음 또는 최소 |")
        lines.append("| 🟠 | 부분 호환 | 일부 기능 제한 또는 다른 방식 필요 | 코드 수정 필요 |")
        lines.append("| 🔴 | 비호환 | 대체 방안 필요 또는 아키텍처 변경 | 설계 변경 필요 |")
        lines.append("")
        
        # 기능 분류
        user_features, system_features, internal_features, other_features = \
            OracleFeaturesFormatter._categorize_features(data)
        
        # 사용자 기능 (마이그레이션 시 검토 필요)
        if user_features:
            lines.append("### 사용자 기능 (마이그레이션 시 검토 필요)\n")
            lines.append("> 애플리케이션에서 직접 사용하는 기능입니다. 마이그레이션 시 대체 방안이 필요합니다.\n")
            lines.append("| 기능 | 사용 횟수 | 영향도 | 대응 방안 |")
            lines.append("|------|----------|--------|----------|")
            
            for feature in user_features:
                impact, response = OracleFeaturesFormatter._get_feature_impact(
                    feature.name, "ko"
                )
                lines.append(
                    f"| {feature.name} | {feature.detected_usages} | "
                    f"{impact} | {response} |"
                )
            lines.append("")
        
        # 기타 주요 기능 (내부 관리 기능 제외)
        if other_features:
            lines.append("### 마이그레이션 검토 필요 기능\n")
            lines.append("> 아래 기능들은 마이그레이션 시 호환성 검토가 필요합니다.\n")
            lines.append("| 기능 | 사용 횟수 | 영향도 | 대응 방안 |")
            lines.append("|------|----------|--------|----------|")
            
            for feature in other_features:
                impact, response = OracleFeaturesFormatter._get_feature_impact(
                    feature.name, "ko"
                )
                lines.append(
                    f"| {feature.name} | {feature.detected_usages} | "
                    f"{impact} | {response} |"
                )
            lines.append("")
        
        # Oracle 내부 관리 기능 (접힌 상태로 표시)
        if internal_features:
            lines.append("### Oracle 내부 관리 기능 (마이그레이션 영향 없음)\n")
            lines.append("> 아래 기능들은 Oracle EE 설치 시 기본 활성화되는 내부 관리 기능입니다.")
            lines.append("> 타겟 DB에서 자동으로 관리되므로 마이그레이션 시 별도 조치가 필요 없습니다.\n")
            lines.append("<details>")
            lines.append("<summary>내부 관리 기능 목록 보기 (무시 가능)</summary>\n")
            lines.append("| 기능 | 설명 |")
            lines.append("|------|------|")
            
            # 내부 기능 설명 매핑
            internal_desc = {
                "Adaptive Plans": "쿼리 실행 계획 자동 조정",
                "Automatic Maintenance - Optimizer Statistics Gathering": "통계 자동 수집",
                "Automatic Maintenance - SQL Tuning Advisor": "SQL 튜닝 자동 권장",
                "Automatic Maintenance - Space Advisor": "공간 관리 자동 권장",
                "Automatic Reoptimization": "쿼리 자동 재최적화",
                "Automatic SGA Tuning": "SGA 메모리 자동 조정",
                "Automatic SQL Execution Memory": "SQL 실행 메모리 자동 관리",
                "Automatic Undo Management": "Undo 세그먼트 자동 관리",
                "DBMS_STATS Incremental Maintenance": "증분 통계 유지",
                "SQL Plan Directive": "SQL 실행 계획 지시자",
                "Deferred Segment Creation": "세그먼트 지연 생성",
                "Automatic Segment Space Management": "세그먼트 공간 자동 관리",
                "Locally Managed Tablespaces": "로컬 관리 테이블스페이스",
                "Bigfile Tablespace": "대용량 테이블스페이스",
                "SecureFiles": "LOB 스토리지 최적화",
                "Server Parameter File": "서버 파라미터 파일",
                "Traditional Audit": "기존 감사 기능",
                "Unified Audit": "통합 감사 기능",
                "Character Set": "문자셋 설정",
                "Oracle Managed Files": "Oracle 관리 파일",
                "Services": "서비스 관리",
                "Resource Manager": "리소스 관리자",
            }
            
            for feature in internal_features:
                clean_name = feature.name.replace(" (user)", "").replace(" (system)", "").strip()
                desc = internal_desc.get(clean_name, "Oracle 내부 관리 기능")
                lines.append(f"| {feature.name} | {desc} |")
            
            lines.append("\n</details>")
            lines.append("")
        
        # 시스템 기능 (접힌 상태로 표시)
        if system_features:
            lines.append("### 시스템 기능 (참고용)\n")
            lines.append("<details>")
            lines.append("<summary>시스템 기능 목록 보기</summary>\n")
            lines.append("| 기능 | 사용 횟수 |")
            lines.append("|------|----------|")
            
            for feature in system_features:
                lines.append(f"| {feature.name} | {feature.detected_usages} |")
            
            lines.append("\n</details>")
            lines.append("")
        
        # 마이그레이션 영향 요약
        lines.append("### 마이그레이션 영향 요약\n")
        lines.append("> 위 기능 분석을 바탕으로 한 전체 요약입니다.\n")
        
        # 영향도별 카운트 (내부 관리 기능 제외)
        high_impact = 0
        medium_impact = 0
        
        for feature in user_features + other_features:
            impact, _ = OracleFeaturesFormatter._get_feature_impact(feature.name, "ko")
            if impact == "🔴":
                high_impact += 1
            elif impact == "🟠":
                medium_impact += 1
        
        if high_impact > 0:
            lines.append(f"- ⚠️ **비호환 기능 {high_impact}개**: 대체 방안 수립이 필요합니다. "
                        "AWS 서비스(SQS, Kinesis 등)로 대체하거나 아키텍처 변경이 필요할 수 있습니다.")
        if medium_impact > 0:
            lines.append(f"- ℹ️ **부분 호환 기능 {medium_impact}개**: 일부 코드 수정이 필요합니다. "
                        "대부분 SCT 도구로 자동 변환 후 수동 검토로 해결 가능합니다.")
        if high_impact == 0 and medium_impact == 0:
            lines.append("- ✅ **모든 사용자 기능이 타겟 DB와 호환됩니다.** "
                        "마이그레이션 복잡도가 낮습니다.")
        
        if internal_features:
            lines.append(f"- 📋 **Oracle 내부 관리 기능 {len(internal_features)}개**는 마이그레이션 영향 없음 "
                        "(타겟 DB에서 자동 관리)")
        
        lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_en(data: StatspackData) -> str:
        """영어 Oracle 기능 사용 현황"""
        lines = []
        
        lines.append("## 🔧 Oracle Feature Usage\n")
        lines.append("> Identify Oracle features in use to evaluate migration compatibility.\n")
        
        lines.append("### Impact Legend\n")
        lines.append("| Icon | Meaning | Description |")
        lines.append("|------|---------|-------------|")
        lines.append("| 🟢 | Compatible | Target DB supports same/similar feature |")
        lines.append("| 🟠 | Partial | Some limitations or different approach needed |")
        lines.append("| 🔴 | Incompatible | Alternative solution or architecture change needed |")
        lines.append("")
        
        user_features, system_features, internal_features, other_features = \
            OracleFeaturesFormatter._categorize_features(data)
        
        if user_features or other_features:
            lines.append("### Features Requiring Review\n")
            lines.append("| Feature | Usage Count | Impact | Response |")
            lines.append("|---------|-------------|--------|----------|")
            
            for feature in user_features + other_features:
                impact, response = OracleFeaturesFormatter._get_feature_impact(
                    feature.name, "en"
                )
                lines.append(
                    f"| {feature.name} | {feature.detected_usages} | "
                    f"{impact} | {response} |"
                )
            lines.append("")
        
        if internal_features:
            lines.append("### Internal Management Features (No Migration Impact)\n")
            lines.append("<details>")
            lines.append("<summary>View internal features (can ignore)</summary>\n")
            lines.append("| Feature | Usage Count |")
            lines.append("|---------|-------------|")
            
            for feature in internal_features:
                lines.append(f"| {feature.name} | {feature.detected_usages} |")
            
            lines.append("\n</details>")
            lines.append("")
        
        return "\n".join(lines)
