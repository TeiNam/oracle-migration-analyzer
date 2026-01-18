"""
CLI 헬퍼 함수 모듈

CLI 도구에서 공통으로 사용되는 유틸리티 함수들을 제공합니다.
"""

from pathlib import Path
from typing import Optional


def detect_file_type(filepath: str) -> str:
    """
    파일 타입을 자동으로 감지합니다 (AWR vs Statspack).
    
    감지 알고리즘:
    1. 먼저 파일명에서 AWR 또는 STATSPACK 키워드 확인
    2. 파일명에 없으면 파일 내용에서 AWR 특화 마커 확인
    
    AWR 특화 섹션 마커:
    - ~~BEGIN-IOSTAT-FUNCTION~~
    - ~~BEGIN-PERCENT-CPU~~
    - ~~BEGIN-PERCENT-IO~~
    - ~~BEGIN-WORKLOAD~~
    - ~~BEGIN-BUFFER-CACHE~~
    
    Args:
        filepath: 분석할 파일 경로
        
    Returns:
        "awr" 또는 "statspack"
        
    Example:
        >>> detect_file_type("sample_awr.out")
        'awr'
        >>> detect_file_type("statspack_report.out")
        'statspack'
    """
    # 1. 파일명 확인 (대소문자 무시)
    filename_lower = Path(filepath).name.lower()
    
    if 'awr' in filename_lower:
        return "awr"
    elif 'statspack' in filename_lower:
        return "statspack"
    
    # 2. 파일명에 타입 정보가 없으면 파일 내용 확인
    awr_markers = [
        "~~BEGIN-IOSTAT-FUNCTION~~",
        "~~BEGIN-PERCENT-CPU~~",
        "~~BEGIN-PERCENT-IO~~",
        "~~BEGIN-WORKLOAD~~",
        "~~BEGIN-BUFFER-CACHE~~"
    ]
    
    try:
        # UTF-8로 시도
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read(50000)  # 처음 50KB만 읽기 (성능 최적화)
        except UnicodeDecodeError:
            # Latin-1로 폴백
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read(50000)
        
        # AWR 마커가 하나라도 있으면 AWR 파일
        for marker in awr_markers:
            if marker in content:
                return "awr"
        
        # AWR 마커가 없으면 Statspack 파일
        return "statspack"
        
    except Exception:
        # 파일 읽기 실패 시 기본값으로 Statspack 반환
        return "statspack"


def generate_output_path(
    source_path: Path,
    output_dir: Path,
    target_db: Optional[str] = None
) -> Path:
    """
    출력 경로를 자동으로 생성합니다.
    
    Args:
        source_path: 원본 파일 경로
        output_dir: 출력 디렉토리
        target_db: 타겟 데이터베이스 (선택)
        
    Returns:
        생성된 출력 경로
        
    Example:
        >>> generate_output_path(Path("sample.out"), Path("reports"))
        Path('reports/sample.md')
    """
    # 파일명 생성 (원본 파일명에서 확장자를 .md로 변경)
    output_filename = source_path.stem
    
    # 타겟 DB가 지정된 경우 파일명에 추가
    if target_db:
        output_filename = f"{output_filename}_{target_db}"
    
    output_filename = f"{output_filename}.md"
    
    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir / output_filename


def print_progress(step: int, total: int, message: str) -> None:
    """
    진행 상황을 출력합니다.
    
    Args:
        step: 현재 단계
        total: 전체 단계
        message: 메시지
        
    Example:
        >>> print_progress(1, 4, "파일 파싱 중")
        [1/4] 파일 파싱 중
    """
    import sys
    print(f"[{step}/{total}] {message}", file=sys.stderr)
