"""
Batch PL/SQL Parser

여러 PL/SQL 객체가 포함된 파일을 파싱하는 모듈입니다.
ora_plsql_full.sql 스크립트의 출력 형식을 지원합니다.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class PLSQLObject:
    """개별 PL/SQL 객체 정보"""
    owner: str
    object_type: str
    object_name: str
    ddl_code: str
    line_start: int
    line_end: int


class BatchPLSQLParser:
    """배치 PL/SQL 파일 파서
    
    여러 PL/SQL 객체가 연속으로 나열된 파일을 개별 객체로 분리합니다.
    
    지원 형식:
    -- ============================================================
    -- Owner: SCHEMA_NAME
    -- Type: OBJECT_TYPE
    -- Name: OBJECT_NAME
    -- ============================================================
    
    CREATE OR REPLACE ...
    /
    """
    
    def __init__(self, content: str):
        """BatchPLSQLParser 초기화
        
        Args:
            content: 배치 PL/SQL 파일 내용
        """
        self.content = content
        self.lines = content.split('\n')
        self.objects: List[PLSQLObject] = []
    
    def parse(self) -> List[PLSQLObject]:
        """파일을 파싱하여 개별 PL/SQL 객체 추출
        
        Returns:
            추출된 PL/SQL 객체 리스트
        """
        self.objects = []
        current_object = None
        ddl_lines: List[str] = []
        in_ddl = False
        line_start = 0
        
        for i, line in enumerate(self.lines, 1):
            # 객체 헤더 감지
            if line.strip().startswith('-- Owner:'):
                # 이전 객체 저장
                if current_object and ddl_lines:
                    current_object.ddl_code = '\n'.join(ddl_lines).strip()
                    current_object.line_end = i - 1
                    if current_object.ddl_code:
                        self.objects.append(current_object)
                
                # 새 객체 시작
                owner = self._extract_value(line, 'Owner:')
                current_object = PLSQLObject(
                    owner=owner,
                    object_type='',
                    object_name='',
                    ddl_code='',
                    line_start=i,
                    line_end=0
                )
                ddl_lines = []
                in_ddl = False
                line_start = i
                
            elif line.strip().startswith('-- Type:') and current_object:
                current_object.object_type = self._extract_value(line, 'Type:')
                
            elif line.strip().startswith('-- Name:') and current_object:
                current_object.object_name = self._extract_value(line, 'Name:')
                
            elif current_object and not line.strip().startswith('--'):
                # DDL 코드 수집
                if line.strip():
                    in_ddl = True
                    ddl_lines.append(line)
                elif in_ddl:
                    # 빈 줄도 DDL 내부에서는 유지
                    ddl_lines.append(line)
        
        # 마지막 객체 저장
        if current_object and ddl_lines:
            current_object.ddl_code = '\n'.join(ddl_lines).strip()
            current_object.line_end = len(self.lines)
            if current_object.ddl_code:
                self.objects.append(current_object)
        
        return self.objects
    
    def _extract_value(self, line: str, prefix: str) -> str:
        """헤더 라인에서 값 추출
        
        Args:
            line: 헤더 라인
            prefix: 추출할 값의 접두사 (예: 'Owner:', 'Type:')
            
        Returns:
            추출된 값
        """
        match = re.search(rf'{re.escape(prefix)}\s*(.+)', line)
        if match:
            return match.group(1).strip()
        return ''
    
    def get_statistics(self) -> Dict[str, int]:
        """객체 통계 정보 반환
        
        Returns:
            객체 타입별 개수
        """
        stats: Dict[str, int] = {}
        for obj in self.objects:
            obj_type = obj.object_type
            stats[obj_type] = stats.get(obj_type, 0) + 1
        return stats
    
    def get_objects_by_type(self, object_type: str) -> List[PLSQLObject]:
        """특정 타입의 객체만 필터링
        
        Args:
            object_type: 필터링할 객체 타입
            
        Returns:
            해당 타입의 객체 리스트
        """
        return [obj for obj in self.objects if obj.object_type.upper() == object_type.upper()]
    
    def get_objects_by_owner(self, owner: str) -> List[PLSQLObject]:
        """특정 소유자의 객체만 필터링
        
        Args:
            owner: 필터링할 소유자
            
        Returns:
            해당 소유자의 객체 리스트
        """
        return [obj for obj in self.objects if obj.owner.upper() == owner.upper()]
