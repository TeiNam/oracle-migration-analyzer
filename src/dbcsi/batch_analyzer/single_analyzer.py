"""
단일 파일 분석 모듈

개별 Statspack/AWR 파일을 분석하는 기능을 제공합니다.
"""

from pathlib import Path
from typing import Optional

from ..parsers import StatspackParser, AWRParser
from ..exceptions import StatspackParseError, StatspackFileError
from ..migration_analyzer import MigrationAnalyzer, TargetDatabase
from ..logging_config import get_logger
from .data_models import BatchFileResult
from .file_processor import FileProcessor

# 로거 초기화
logger = get_logger("single_analyzer")


class SingleFileAnalyzer:
    """단일 파일 분석기"""
    
    @staticmethod
    def analyze_file(
        filepath: Path,
        analyze_migration: bool = False,
        target: Optional[TargetDatabase] = None
    ) -> BatchFileResult:
        """
        단일 파일 분석
        
        Args:
            filepath: 파일 경로
            analyze_migration: 마이그레이션 난이도 분석 포함 여부
            target: 특정 타겟 데이터베이스
            
        Returns:
            BatchFileResult: 파일 분석 결과
        """
        try:
            # 파일 타입 자동 감지 (AWR vs Statspack)
            file_type = FileProcessor.detect_file_type(filepath)
            
            # 적절한 파서 선택
            if file_type == "awr":
                parser = AWRParser(str(filepath))
            else:
                parser = StatspackParser(str(filepath))
            
            # 파일 파싱
            statspack_data = parser.parse()
            
            # 타임스탬프 추출 (파일명 또는 데이터에서)
            timestamp = FileProcessor.extract_timestamp(filepath, statspack_data)
            
            # 마이그레이션 분석 (선택적)
            migration_analysis = None
            if analyze_migration:
                analyzer = MigrationAnalyzer(statspack_data)
                migration_analysis = analyzer.analyze(target=target)
            
            return BatchFileResult(
                filepath=str(filepath),
                filename=filepath.name,
                success=True,
                statspack_data=statspack_data,
                migration_analysis=migration_analysis,
                timestamp=timestamp
            )
            
        except (StatspackParseError, StatspackFileError) as e:
            # 파싱 오류 - 건너뛰고 계속 진행
            logger.error(f"파싱 오류: {filepath}", exc_info=True)
            return BatchFileResult(
                filepath=str(filepath),
                filename=filepath.name,
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            # 기타 예외 - 건너뛰고 계속 진행
            logger.error(f"예상치 못한 오류: {filepath}", exc_info=True)
            return BatchFileResult(
                filepath=str(filepath),
                filename=filepath.name,
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
