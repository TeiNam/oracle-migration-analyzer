"""
Markdown Oracle 기능 사용 현황 포맷터

Oracle 기능 사용 현황 섹션을 Markdown 형식으로 변환합니다.
"""

from typing import List, Dict, Any
from ...data_models import AnalysisMetrics


class OracleFeaturesFormatterMixin:
    """Oracle 기능 사용 현황 포맷터 믹스인"""
    
    # EE 전용 기능 및 마이그레이션 영향도
    EE_FEATURES = {
        'Advanced Compression': {'impact': '🔴', 'alt_ko': 'Aurora 스토리지 비용 비교', 'alt_en': 'Compare Aurora storage cost'},
        'OLAP': {'impact': '🔴', 'alt_ko': 'Redshift/Athena 검토', 'alt_en': 'Consider Redshift/Athena'},
        'Data Mining': {'impact': '🔴', 'alt_ko': 'SageMaker 연동', 'alt_en': 'SageMaker integration'},
        'Spatial': {'impact': '🟠', 'alt_ko': 'PostGIS 사용', 'alt_en': 'Use PostGIS'},
        'Label Security': {'impact': '🔴', 'alt_ko': '대체 어려움', 'alt_en': 'Difficult to replace'},
        'Database Vault': {'impact': '🔴', 'alt_ko': '대체 어려움', 'alt_en': 'Difficult to replace'},
        'Real Application Security': {'impact': '🟠', 'alt_ko': '애플리케이션 레벨 구현', 'alt_en': 'App-level implementation'},
        'Partitioning': {'impact': '🟠', 'alt_ko': 'PostgreSQL 네이티브 지원', 'alt_en': 'PostgreSQL native support'},
        'Real Application Clusters': {'impact': '🔴', 'alt_ko': 'Aurora Multi-AZ/Global DB', 'alt_en': 'Aurora Multi-AZ/Global DB'},
        'Real Application Testing': {'impact': '🟠', 'alt_ko': '대체 방안 검토', 'alt_en': 'Review alternatives'},
    }
    
    @staticmethod
    def _format_oracle_features(metrics: AnalysisMetrics, language: str) -> str:
        """Oracle 기능 사용 현황 섹션 포맷"""
        if not metrics.oracle_features_used:
            return ""
        
        if language == "ko":
            return OracleFeaturesFormatterMixin._format_ko(metrics.oracle_features_used)
        return OracleFeaturesFormatterMixin._format_en(metrics.oracle_features_used)
    
    @staticmethod
    def _is_user_feature(name: str) -> bool:
        """사용자 레벨 기능인지 확인"""
        return '(user)' in name.lower()
    
    @staticmethod
    def _is_system_feature(name: str) -> bool:
        """시스템 레벨 기능인지 확인"""
        return '(system)' in name.lower()
    
    @staticmethod
    def _get_feature_impact(name: str) -> Dict[str, str]:
        """기능의 마이그레이션 영향도 반환"""
        for key, info in OracleFeaturesFormatterMixin.EE_FEATURES.items():
            if key.lower() in name.lower():
                return info
        return {'impact': '🟢', 'alt_ko': '호환 가능', 'alt_en': 'Compatible'}
    
    @staticmethod
    def _format_ko(features: List[Dict[str, Any]]) -> str:
        """한국어 Oracle 기능 사용 현황"""
        sections = []
        
        sections.append("# 🔧 Oracle 기능 사용 현황\n")
        sections.append("> Oracle 데이터베이스에서 사용 중인 기능을 파악하여 마이그레이션 호환성을 평가합니다.\n")
        
        # 영향도 범례
        sections.append("## 영향도 범례\n")
        sections.append("| 아이콘 | 의미 | 설명 |")
        sections.append("|--------|------|------|")
        sections.append("| 🟢 | 호환 | 타겟 DB에서 동일/유사 기능 지원 |")
        sections.append("| 🟠 | 부분 호환 | 일부 기능 제한 또는 다른 방식 필요 |")
        sections.append("| 🔴 | 비호환 | 대체 방안 필요 또는 아키텍처 변경 |")
        
        # 사용자 기능 (중요)
        user_features = [f for f in features if OracleFeaturesFormatterMixin._is_user_feature(f['name'])]
        system_features = [f for f in features if OracleFeaturesFormatterMixin._is_system_feature(f['name'])]
        other_features = [f for f in features if not OracleFeaturesFormatterMixin._is_user_feature(f['name']) 
                        and not OracleFeaturesFormatterMixin._is_system_feature(f['name'])]
        
        # 사용자 기능 (마이그레이션 시 중요)
        if user_features:
            sections.append("\n## 사용자 기능 (마이그레이션 시 검토 필요)\n")
            sections.append("| 기능 | 사용 횟수 | 영향도 | 대응 방안 |")
            sections.append("|------|----------|--------|----------|")
            
            for f in user_features:
                name = f['name']
                usages = f.get('detected_usages', 0)
                impact_info = OracleFeaturesFormatterMixin._get_feature_impact(name)
                sections.append(f"| {name} | {usages:,} | {impact_info['impact']} | {impact_info['alt_ko']} |")
        
        # 기타 주요 기능
        important_others = [f for f in other_features 
                          if any(key.lower() in f['name'].lower() for key in OracleFeaturesFormatterMixin.EE_FEATURES)]
        if important_others:
            sections.append("\n## 기타 주요 기능\n")
            sections.append("| 기능 | 사용 횟수 | 영향도 | 대응 방안 |")
            sections.append("|------|----------|--------|----------|")
            
            for f in important_others:
                name = f['name']
                usages = f.get('detected_usages', 0)
                impact_info = OracleFeaturesFormatterMixin._get_feature_impact(name)
                sections.append(f"| {name} | {usages:,} | {impact_info['impact']} | {impact_info['alt_ko']} |")
        
        # 시스템 기능 (참고용)
        if system_features:
            sections.append("\n## 시스템 기능 (참고용, 대부분 무시 가능)\n")
            sections.append("<details>")
            sections.append("<summary>시스템 기능 목록 보기</summary>\n")
            sections.append("| 기능 | 사용 횟수 |")
            sections.append("|------|----------|")
            for f in system_features[:10]:  # 최대 10개
                sections.append(f"| {f['name']} | {f.get('detected_usages', 0):,} |")
            sections.append("\n</details>")
        
        # 마이그레이션 영향 요약
        sections.append("\n## 마이그레이션 영향 요약\n")
        
        high_impact = [f for f in user_features 
                      if OracleFeaturesFormatterMixin._get_feature_impact(f['name'])['impact'] == '🔴']
        medium_impact = [f for f in user_features 
                        if OracleFeaturesFormatterMixin._get_feature_impact(f['name'])['impact'] == '🟠']
        
        if high_impact:
            sections.append(f"- **비호환 기능**: {len(high_impact)}개 - 대체 방안 또는 아키텍처 변경 필요")
        if medium_impact:
            sections.append(f"- **부분 호환 기능**: {len(medium_impact)}개 - 일부 수정 필요")
        if not high_impact and not medium_impact:
            sections.append("- 모든 사용자 기능이 타겟 DB와 호환됩니다.")
        
        return "\n".join(sections)
    
    @staticmethod
    def _format_en(features: List[Dict[str, Any]]) -> str:
        """영어 Oracle 기능 사용 현황"""
        sections = []
        
        sections.append("# 🔧 Oracle Feature Usage\n")
        sections.append("> Identifies Oracle features in use to assess migration compatibility.\n")
        
        sections.append("## Impact Legend\n")
        sections.append("| Icon | Meaning | Description |")
        sections.append("|------|---------|-------------|")
        sections.append("| 🟢 | Compatible | Target DB supports same/similar feature |")
        sections.append("| 🟠 | Partial | Some limitations or different approach needed |")
        sections.append("| 🔴 | Incompatible | Alternative needed or architecture change |")
        
        user_features = [f for f in features if OracleFeaturesFormatterMixin._is_user_feature(f['name'])]
        
        if user_features:
            sections.append("\n## User Features (Review Required)\n")
            sections.append("| Feature | Usage Count | Impact | Alternative |")
            sections.append("|---------|-------------|--------|-------------|")
            
            for f in user_features:
                name = f['name']
                usages = f.get('detected_usages', 0)
                impact_info = OracleFeaturesFormatterMixin._get_feature_impact(name)
                sections.append(f"| {name} | {usages:,} | {impact_info['impact']} | {impact_info['alt_en']} |")
        
        return "\n".join(sections)
