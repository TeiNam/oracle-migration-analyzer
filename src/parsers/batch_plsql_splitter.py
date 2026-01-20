"""
Batch PL/SQL Splitter

배치 PL/SQL 파일을 계정별, 타입별로 개별 SQL 파일로 분리하는 모듈입니다.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from .batch_plsql_parser import BatchPLSQLParser, PLSQLObject

logger = logging.getLogger(__name__)


class BatchPLSQLSplitter:
    """배치 PL/SQL 파일 분리기
    
    배치 PL/SQL 파일(.out)을 파싱하여 계정별, 타입별로 개별 SQL 파일로 분리합니다.
    
    출력 구조:
    output_dir/
    ├── OWNER1/
    │   ├── FUNCTION/
    │   │   ├── func1.sql
    │   │   └── func2.sql
    │   ├── PROCEDURE/
    │   │   └── proc1.sql
    │   └── TYPE/
    │       └── type1.sql
    └── OWNER2/
        └── ...
    """
    
    def __init__(self, input_file: str, output_dir: Optional[str] = None):
        """BatchPLSQLSplitter 초기화
        
        Args:
            input_file: 입력 배치 PL/SQL 파일 경로
            output_dir: 출력 디렉토리 (기본값: 입력 파일명_split)
        """
        self.input_file = Path(input_file)
        
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            # 기본 출력 디렉토리: 입력파일명_split
            self.output_dir = self.input_file.parent / f"{self.input_file.stem}_split"
        
        self.parser: Optional[BatchPLSQLParser] = None
        self.objects: List[PLSQLObject] = []
    
    def parse(self) -> List[PLSQLObject]:
        """배치 PL/SQL 파일 파싱
        
        Returns:
            파싱된 PL/SQL 객체 리스트
            
        Raises:
            FileNotFoundError: 입력 파일이 존재하지 않는 경우
            IOError: 파일 읽기 실패
        """
        if not self.input_file.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {self.input_file}")
        
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"파일 읽기 실패: {self.input_file}", exc_info=True)
            raise IOError(f"파일 읽기 실패: {e}")
        
        self.parser = BatchPLSQLParser(content)
        self.objects = self.parser.parse()
        
        logger.info(f"파싱 완료: {len(self.objects)}개 객체 발견")
        return self.objects
    
    def split(self) -> Dict[str, int]:
        """객체를 계정별, 타입별로 개별 파일로 분리
        
        Returns:
            Dict[str, int]: 통계 정보 (owner별 파일 수)
            
        Raises:
            ValueError: 파싱이 먼저 수행되지 않은 경우
        """
        if not self.objects:
            raise ValueError("먼저 parse()를 호출하여 파일을 파싱해야 합니다.")
        
        # 출력 디렉토리 생성
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        stats: Dict[str, int] = {}
        
        for obj in self.objects:
            # 계정별 디렉토리 생성
            owner_dir = self.output_dir / obj.owner
            owner_dir.mkdir(exist_ok=True)
            
            # 타입별 디렉토리 생성
            type_dir = owner_dir / obj.object_type
            type_dir.mkdir(exist_ok=True)
            
            # 파일명 생성 (객체명.sql)
            # 특수문자 제거 및 소문자 변환
            safe_name = self._sanitize_filename(obj.object_name)
            output_file = type_dir / f"{safe_name}.sql"
            
            # 중복 파일명 처리
            counter = 1
            while output_file.exists():
                output_file = type_dir / f"{safe_name}_{counter}.sql"
                counter += 1
            
            # 파일 작성
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    # 헤더 주석 추가
                    f.write(f"-- Owner: {obj.owner}\n")
                    f.write(f"-- Type: {obj.object_type}\n")
                    f.write(f"-- Name: {obj.object_name}\n")
                    f.write(f"-- Source: {self.input_file.name} (Lines {obj.line_start}-{obj.line_end})\n")
                    f.write("-- " + "=" * 60 + "\n\n")
                    
                    # DDL 코드 작성
                    f.write(obj.ddl_code)
                    f.write("\n/\n")
                
                # 통계 업데이트
                stats[obj.owner] = stats.get(obj.owner, 0) + 1
                
                logger.debug(f"파일 생성: {output_file}")
                
            except Exception as e:
                logger.error(f"파일 작성 실패: {output_file}", exc_info=True)
                continue
        
        logger.info(f"분리 완료: {sum(stats.values())}개 파일 생성")
        return stats
    
    def _sanitize_filename(self, name: str) -> str:
        """파일명으로 사용 가능하도록 문자열 정리
        
        Args:
            name: 원본 객체명
            
        Returns:
            정리된 파일명
        """
        # 특수문자를 언더스코어로 변환
        safe_name = name.replace('$', '_')
        safe_name = safe_name.replace(' ', '_')
        safe_name = safe_name.replace('/', '_')
        safe_name = safe_name.replace('\\', '_')
        
        # 소문자 변환
        safe_name = safe_name.lower()
        
        return safe_name
    
    def get_statistics(self) -> Dict[str, Dict[str, int]]:
        """계정별, 타입별 통계 정보 반환
        
        Returns:
            Dict[owner, Dict[type, count]]: 계정별 타입별 객체 수
            
        Raises:
            ValueError: 파싱이 먼저 수행되지 않은 경우
        """
        if not self.objects:
            raise ValueError("먼저 parse()를 호출하여 파일을 파싱해야 합니다.")
        
        stats: Dict[str, Dict[str, int]] = {}
        
        for obj in self.objects:
            if obj.owner not in stats:
                stats[obj.owner] = {}
            
            obj_type = obj.object_type
            stats[obj.owner][obj_type] = stats[obj.owner].get(obj_type, 0) + 1
        
        return stats
    
    def print_statistics(self) -> None:
        """통계 정보 출력"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 60)
        print("배치 PL/SQL 파일 분리 통계")
        print("=" * 60)
        print(f"입력 파일: {self.input_file}")
        print(f"출력 디렉토리: {self.output_dir}")
        print(f"전체 객체 수: {len(self.objects)}")
        print()
        
        for owner, types in sorted(stats.items()):
            print(f"📁 {owner}/")
            for obj_type, count in sorted(types.items()):
                print(f"   └─ {obj_type}: {count}개")
            print()
        
        print("=" * 60)


def split_batch_plsql_file(input_file: str, output_dir: Optional[str] = None) -> Dict[str, int]:
    """배치 PL/SQL 파일을 개별 파일로 분리 (편의 함수)
    
    Args:
        input_file: 입력 배치 PL/SQL 파일 경로
        output_dir: 출력 디렉토리 (선택사항)
        
    Returns:
        Dict[str, int]: 계정별 파일 수
    """
    splitter = BatchPLSQLSplitter(input_file, output_dir)
    splitter.parse()
    stats = splitter.split()
    splitter.print_statistics()
    
    return stats
