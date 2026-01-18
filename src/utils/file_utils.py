"""
파일 처리 유틸리티 모듈

이 모듈은 파일 검색, 읽기 등 파일 처리와 관련된 유틸리티 함수들을 제공합니다.
"""

from pathlib import Path
from typing import List


def find_files_by_extension(
    directory: Path,
    extensions: List[str]
) -> List[Path]:
    """확장자로 파일 찾기
    
    지정된 디렉토리에서 특정 확장자를 가진 모든 파일을 재귀적으로 검색합니다.
    
    Args:
        directory: 검색할 디렉토리 경로
        extensions: 확장자 리스트 (예: ['.sql', '.pls', '.out'])
                   확장자는 점(.)을 포함해야 합니다.
        
    Returns:
        찾은 파일 경로 리스트 (Path 객체)
        
    Raises:
        ValueError: directory가 존재하지 않거나 디렉토리가 아닌 경우
        ValueError: extensions가 비어있는 경우
        
    Example:
        >>> from pathlib import Path
        >>> directory = Path("sample_code")
        >>> extensions = [".sql", ".pls"]
        >>> files = find_files_by_extension(directory, extensions)
        >>> print(f"Found {len(files)} files")
        Found 8 files
    """
    # 입력 검증
    if not directory.exists():
        raise ValueError(f"디렉토리가 존재하지 않습니다: {directory}")
    
    if not directory.is_dir():
        raise ValueError(f"디렉토리가 아닙니다: {directory}")
    
    if not extensions:
        raise ValueError("확장자 리스트가 비어있습니다")
    
    # 확장자 정규화 (소문자로 변환)
    normalized_extensions = [ext.lower() for ext in extensions]
    
    # 파일 검색
    found_files: List[Path] = []
    
    # 재귀적으로 모든 파일 검색
    for item in directory.rglob("*"):
        if item.is_file():
            # 파일 확장자 확인 (대소문자 구분 없이)
            file_extension = item.suffix.lower()
            if file_extension in normalized_extensions:
                found_files.append(item)
    
    # 파일명으로 정렬하여 반환
    return sorted(found_files)


def read_file_with_encoding(
    filepath: Path,
    encodings: List[str] = None
) -> str:
    """여러 인코딩으로 파일 읽기 시도
    
    지정된 인코딩 리스트를 순서대로 시도하여 파일을 읽습니다.
    첫 번째로 성공한 인코딩으로 파일 내용을 반환합니다.
    
    Args:
        filepath: 읽을 파일 경로
        encodings: 시도할 인코딩 리스트 (기본값: ['utf-8', 'latin-1', 'cp949'])
        
    Returns:
        파일 내용 (문자열)
        
    Raises:
        FileNotFoundError: 파일이 존재하지 않는 경우
        IOError: 모든 인코딩으로 읽기 실패한 경우
        
    Example:
        >>> from pathlib import Path
        >>> filepath = Path("sample.txt")
        >>> content = read_file_with_encoding(filepath)
        >>> print(len(content))
        1234
    """
    if encodings is None:
        encodings = ['utf-8', 'latin-1', 'cp949']
    
    # 파일 존재 확인
    if not filepath.exists():
        raise FileNotFoundError(f"파일이 존재하지 않습니다: {filepath}")
    
    if not filepath.is_file():
        raise ValueError(f"파일이 아닙니다: {filepath}")
    
    # 각 인코딩으로 시도
    last_error = None
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError) as e:
            last_error = e
            continue
    
    # 모든 인코딩 실패
    raise IOError(
        f"모든 인코딩으로 파일 읽기 실패: {filepath}\n"
        f"시도한 인코딩: {encodings}\n"
        f"마지막 오류: {last_error}"
    )
