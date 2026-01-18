"""
기본 포맷터 모듈

JSON 직렬화, 파일 저장 등 공통 기능을 제공합니다.
"""

import json
import os
from datetime import datetime
from typing import Union, Dict, Any
from pathlib import Path

from ..models import (
    StatspackData,
    MigrationComplexity,
    TargetDatabase,
    statspack_to_dict,
    dict_to_statspack,
    migration_complexity_to_dict,
    dict_to_migration_complexity
)


class BaseFormatter:
    """기본 포맷터 클래스
    
    JSON 직렬화/역직렬화, 파일 저장 등 공통 기능을 제공합니다.
    """
    
    @staticmethod
    def to_json(data: Union[StatspackData, Dict[TargetDatabase, MigrationComplexity]]) -> str:
        """분석 결과를 JSON 형식으로 변환
        
        Args:
            data: StatspackData 또는 MigrationComplexity 딕셔너리
            
        Returns:
            JSON 형식의 문자열
        """
        if isinstance(data, StatspackData):
            data_dict = statspack_to_dict(data)
            data_dict["_type"] = "StatspackData"
        elif isinstance(data, dict):
            data_dict = {}
            for target, complexity in data.items():
                key = target.value if isinstance(target, TargetDatabase) else str(target)
                data_dict[key] = migration_complexity_to_dict(complexity)
            data_dict["_type"] = "MigrationComplexityDict"
        else:
            raise ValueError(f"지원하지 않는 데이터 타입: {type(data)}")
        
        return json.dumps(data_dict, indent=2, ensure_ascii=False)
    
    @staticmethod
    def from_json(json_str: str) -> Union[StatspackData, Dict[TargetDatabase, MigrationComplexity]]:
        """JSON 문자열을 분석 결과 객체로 변환
        
        Args:
            json_str: JSON 형식의 문자열
            
        Returns:
            StatspackData 또는 MigrationComplexity 딕셔너리
            
        Raises:
            ValueError: JSON 파싱 실패 시
        """
        try:
            data_dict = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 실패: {e}")
        
        data_type = data_dict.pop("_type", None)
        
        if data_type == "StatspackData":
            return dict_to_statspack(data_dict)
        elif data_type == "MigrationComplexityDict":
            result = {}
            for key, value in data_dict.items():
                target = None
                for t in TargetDatabase:
                    if t.value == key:
                        target = t
                        break
                if target:
                    result[target] = dict_to_migration_complexity(value)
            return result
        else:
            raise ValueError(f"알 수 없는 데이터 타입: {data_type}")
    
    @staticmethod
    def save_report(content: str, 
                   filename: str, 
                   format: str = "md",
                   base_dir: str = "reports",
                   db_name: str = None) -> str:
        """리포트를 날짜별/DB별 폴더에 저장
        
        Args:
            content: 저장할 내용
            filename: 기본 파일명 (확장자 제외)
            format: 파일 형식 ("md" 또는 "json")
            base_dir: 기본 디렉토리 (기본값: "reports")
            db_name: 데이터베이스 이름 (선택적)
            
        Returns:
            저장된 파일의 전체 경로
            
        Raises:
            PermissionError: 파일 쓰기 권한이 없을 때
            OSError: 기타 파일 시스템 오류
        """
        today = datetime.now().strftime("%Y%m%d")
        
        if db_name:
            safe_db_name = "".join(c for c in db_name if c.isalnum() or c in ('-', '_')).lower()
            report_dir = Path(base_dir) / today / safe_db_name
        else:
            report_dir = Path(base_dir) / today
        
        try:
            report_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(f"폴더 생성 권한이 없습니다: {report_dir}") from e
        except OSError as e:
            raise OSError(f"폴더 생성 중 오류 발생: {report_dir}") from e
        
        timestamp = datetime.now().strftime("%H%M%S")
        full_filename = f"{filename}_{timestamp}.{format}"
        filepath = report_dir / full_filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except PermissionError as e:
            raise PermissionError(f"파일 쓰기 권한이 없습니다: {filepath}") from e
        except OSError as e:
            raise OSError(f"파일 저장 중 오류 발생: {filepath}") from e
        
        return str(filepath)
    
    @staticmethod
    def batch_to_json(batch_result) -> str:
        """배치 분석 결과를 JSON 형식으로 변환
        
        Args:
            batch_result: BatchAnalysisResult 객체
            
        Returns:
            JSON 형식의 문자열
        """
        result_dict = {
            "_type": "BatchAnalysisResult",
            "total_files": batch_result.total_files,
            "successful_files": batch_result.successful_files,
            "failed_files": batch_result.failed_files,
            "analysis_timestamp": batch_result.analysis_timestamp,
            "file_results": []
        }
        
        for file_result in batch_result.file_results:
            file_dict = {
                "filepath": file_result.filepath,
                "filename": file_result.filename,
                "success": file_result.success,
                "error_message": file_result.error_message
            }
            
            if file_result.success and file_result.statspack_data:
                file_dict["statspack_data"] = statspack_to_dict(file_result.statspack_data)
                
                if file_result.migration_analysis:
                    migration_dict = {}
                    for target, complexity in file_result.migration_analysis.items():
                        migration_dict[target.value] = migration_complexity_to_dict(complexity)
                    file_dict["migration_analysis"] = migration_dict
            
            result_dict["file_results"].append(file_dict)
        
        return json.dumps(result_dict, indent=2, ensure_ascii=False)
