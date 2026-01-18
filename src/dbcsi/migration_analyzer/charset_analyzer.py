"""
캐릭터셋 분석 모듈

Oracle 캐릭터셋 감지 및 변환 필요성을 분석합니다.
"""

from typing import Tuple


def detect_character_set(character_set: str) -> str:
    """
    캐릭터셋 감지
    
    Args:
        character_set: OS-INFORMATION에서 추출한 Character Set 정보
        
    Returns:
        str: 캐릭터셋 이름 (없으면 빈 문자열)
    """
    return character_set if character_set else ""


def requires_charset_conversion(charset: str) -> bool:
    """
    캐릭터셋 변환 필요 여부
    
    현재 캐릭터셋이 AL32UTF8이 아니면 변환이 필요합니다.
    
    Args:
        charset: 캐릭터셋 이름
        
    Returns:
        bool: 캐릭터셋 변환 필요 여부
    """
    if not charset:
        # 캐릭터셋 정보가 없으면 변환 불필요로 간주
        return False
    
    return charset.upper() != "AL32UTF8"


def analyze_charset(character_set: str) -> Tuple[str, bool]:
    """
    캐릭터셋 종합 분석
    
    캐릭터셋을 감지하고 변환 필요성을 판단합니다.
    
    Args:
        character_set: OS-INFORMATION에서 추출한 Character Set 정보
        
    Returns:
        Tuple[str, bool]: (캐릭터셋 이름, 변환 필요 여부)
    """
    charset = detect_character_set(character_set)
    needs_conversion = requires_charset_conversion(charset)
    
    return charset, needs_conversion
