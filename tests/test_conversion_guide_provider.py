"""
ConversionGuideProvider 테스트

Requirements 15.1, 15.2, 15.3을 검증합니다.
"""

import pytest
import sys
import os

# 상위 디렉토리의 모듈을 import하기 위한 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from oracle_complexity_analyzer import TargetDatabase
from formatters.conversion_guide_provider import ConversionGuideProvider


class TestConversionGuideProvider:
    """ConversionGuideProvider 클래스 테스트"""
    
    def test_postgresql_initialization(self):
        """PostgreSQL 타겟으로 초기화 테스트"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        assert provider.target == TargetDatabase.POSTGRESQL
        assert provider.mappings == ConversionGuideProvider.POSTGRESQL_MAPPINGS
    
    def test_mysql_initialization(self):
        """MySQL 타겟으로 초기화 테스트"""
        provider = ConversionGuideProvider(TargetDatabase.MYSQL)
        assert provider.target == TargetDatabase.MYSQL
        assert provider.mappings == ConversionGuideProvider.MYSQL_MAPPINGS
    
    def test_postgresql_rownum_mapping(self):
        """PostgreSQL ROWNUM 변환 가이드 테스트 (Requirement 15.1)"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        guides = provider.get_conversion_guide(['ROWNUM'])
        
        assert 'ROWNUM' in guides
        assert 'LIMIT/OFFSET' in guides['ROWNUM']
    
    def test_postgresql_decode_mapping(self):
        """PostgreSQL DECODE 변환 가이드 테스트 (Requirement 15.1)"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        guides = provider.get_conversion_guide(['DECODE'])
        
        assert 'DECODE' in guides
        assert 'CASE' in guides['DECODE']
    
    def test_postgresql_nvl_mapping(self):
        """PostgreSQL NVL 변환 가이드 테스트 (Requirement 15.1)"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        guides = provider.get_conversion_guide(['NVL'])
        
        assert 'NVL' in guides
        assert 'COALESCE' in guides['NVL']
    
    def test_postgresql_merge_mapping(self):
        """PostgreSQL MERGE 변환 가이드 테스트 (Requirement 15.1)"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        guides = provider.get_conversion_guide(['MERGE'])
        
        assert 'MERGE' in guides
        assert 'ON CONFLICT' in guides['MERGE']
    
    def test_postgresql_listagg_mapping(self):
        """PostgreSQL LISTAGG 변환 가이드 테스트 (Requirement 15.1)"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        guides = provider.get_conversion_guide(['LISTAGG'])
        
        assert 'LISTAGG' in guides
        assert 'STRING_AGG' in guides['LISTAGG']
    
    def test_postgresql_connect_by_mapping(self):
        """PostgreSQL CONNECT BY 변환 가이드 테스트 (Requirement 15.1)"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        guides = provider.get_conversion_guide(['CONNECT BY'])
        
        assert 'CONNECT BY' in guides
        assert 'WITH RECURSIVE' in guides['CONNECT BY']
    
    def test_mysql_rownum_mapping(self):
        """MySQL ROWNUM 변환 가이드 테스트 (Requirement 15.2)"""
        provider = ConversionGuideProvider(TargetDatabase.MYSQL)
        guides = provider.get_conversion_guide(['ROWNUM'])
        
        assert 'ROWNUM' in guides
        assert 'LIMIT' in guides['ROWNUM']
    
    def test_mysql_decode_mapping(self):
        """MySQL DECODE 변환 가이드 테스트 (Requirement 15.2)"""
        provider = ConversionGuideProvider(TargetDatabase.MYSQL)
        guides = provider.get_conversion_guide(['DECODE'])
        
        assert 'DECODE' in guides
        assert 'CASE' in guides['DECODE']
    
    def test_mysql_nvl_mapping(self):
        """MySQL NVL 변환 가이드 테스트 (Requirement 15.2)"""
        provider = ConversionGuideProvider(TargetDatabase.MYSQL)
        guides = provider.get_conversion_guide(['NVL'])
        
        assert 'NVL' in guides
        assert 'IFNULL' in guides['NVL']
    
    def test_mysql_sysdate_mapping(self):
        """MySQL SYSDATE 변환 가이드 테스트 (Requirement 15.2)"""
        provider = ConversionGuideProvider(TargetDatabase.MYSQL)
        guides = provider.get_conversion_guide(['SYSDATE'])
        
        assert 'SYSDATE' in guides
        assert 'NOW()' in guides['SYSDATE']
    
    def test_mysql_merge_mapping(self):
        """MySQL MERGE 변환 가이드 테스트 (Requirement 15.2)"""
        provider = ConversionGuideProvider(TargetDatabase.MYSQL)
        guides = provider.get_conversion_guide(['MERGE'])
        
        assert 'MERGE' in guides
        assert 'ON DUPLICATE KEY' in guides['MERGE']
    
    def test_mysql_listagg_mapping(self):
        """MySQL LISTAGG 변환 가이드 테스트 (Requirement 15.2)"""
        provider = ConversionGuideProvider(TargetDatabase.MYSQL)
        guides = provider.get_conversion_guide(['LISTAGG'])
        
        assert 'LISTAGG' in guides
        assert 'GROUP_CONCAT' in guides['LISTAGG']
    
    def test_mysql_app_migration_message(self):
        """MySQL 애플리케이션 이관 메시지 테스트 (Requirement 15.3)"""
        provider = ConversionGuideProvider(TargetDatabase.MYSQL)
        message = provider.get_mysql_app_migration_message()
        
        assert message != ""
        assert "애플리케이션" in message
        assert "이관" in message
    
    def test_postgresql_no_app_migration_message(self):
        """PostgreSQL은 애플리케이션 이관 메시지 없음 테스트"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        message = provider.get_mysql_app_migration_message()
        
        assert message == ""
    
    def test_multiple_features_conversion(self):
        """여러 기능 동시 변환 가이드 테스트"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        features = ['ROWNUM', 'DECODE', 'NVL', 'LISTAGG']
        guides = provider.get_conversion_guide(features)
        
        assert len(guides) == 4
        assert all(feature in guides for feature in features)
    
    def test_case_insensitive_matching(self):
        """대소문자 구분 없는 매칭 테스트"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        
        # 소문자로 입력
        guides_lower = provider.get_conversion_guide(['rownum', 'decode'])
        assert len(guides_lower) == 2
        
        # 대문자로 입력
        guides_upper = provider.get_conversion_guide(['ROWNUM', 'DECODE'])
        assert len(guides_upper) == 2
        
        # 혼합
        guides_mixed = provider.get_conversion_guide(['RoWnUm', 'DeCoDe'])
        assert len(guides_mixed) == 2
    
    def test_unknown_feature(self):
        """알 수 없는 기능 처리 테스트"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        guides = provider.get_conversion_guide(['UNKNOWN_FEATURE_XYZ'])
        
        # 알 수 없는 기능은 가이드에 포함되지 않음
        assert 'UNKNOWN_FEATURE_XYZ' not in guides
    
    def test_has_mapping(self):
        """변환 가이드 존재 여부 확인 테스트"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        
        assert provider.has_mapping('ROWNUM') is True
        assert provider.has_mapping('DECODE') is True
        assert provider.has_mapping('UNKNOWN_FEATURE') is False
    
    def test_get_all_mappings(self):
        """전체 매핑 반환 테스트"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        all_mappings = provider.get_all_mappings()
        
        assert isinstance(all_mappings, dict)
        assert len(all_mappings) > 0
        assert 'ROWNUM' in all_mappings
        assert 'DECODE' in all_mappings
    
    def test_postgresql_package_mapping(self):
        """PostgreSQL Package 변환 가이드 테스트"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        guides = provider.get_conversion_guide(['Package'])
        
        assert 'Package' in guides
        assert 'SCHEMA' in guides['Package'] or '함수' in guides['Package']
    
    def test_mysql_package_mapping(self):
        """MySQL Package 변환 가이드 테스트 (Requirement 15.3)"""
        provider = ConversionGuideProvider(TargetDatabase.MYSQL)
        guides = provider.get_conversion_guide(['Package'])
        
        assert 'Package' in guides
        assert '애플리케이션' in guides['Package']
        assert '이관' in guides['Package']
    
    def test_mysql_procedure_mapping(self):
        """MySQL Procedure 변환 가이드 테스트 (Requirement 15.3)"""
        provider = ConversionGuideProvider(TargetDatabase.MYSQL)
        guides = provider.get_conversion_guide(['Procedure'])
        
        assert 'Procedure' in guides
        # MySQL은 Procedure를 제한적으로 지원하며 애플리케이션 이관 권장
        assert 'PROCEDURE' in guides['Procedure'] or '애플리케이션' in guides['Procedure']
    
    def test_empty_features_list(self):
        """빈 기능 목록 처리 테스트"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        guides = provider.get_conversion_guide([])
        
        assert guides == {}
    
    def test_postgresql_bulk_collect_mapping(self):
        """PostgreSQL BULK COLLECT 변환 가이드 테스트"""
        provider = ConversionGuideProvider(TargetDatabase.POSTGRESQL)
        guides = provider.get_conversion_guide(['BULK COLLECT'])
        
        assert 'BULK COLLECT' in guides
        assert 'SQL' in guides['BULK COLLECT'] or '배치' in guides['BULK COLLECT']
    
    def test_mysql_bulk_collect_mapping(self):
        """MySQL BULK COLLECT 변환 가이드 테스트 (Requirement 15.3)"""
        provider = ConversionGuideProvider(TargetDatabase.MYSQL)
        guides = provider.get_conversion_guide(['BULK COLLECT'])
        
        assert 'BULK COLLECT' in guides
        assert '미지원' in guides['BULK COLLECT'] or '애플리케이션' in guides['BULK COLLECT']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
