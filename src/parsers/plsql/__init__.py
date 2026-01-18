"""
PL/SQL Parser Module

PL/SQL 코드를 파싱하여 구문 요소를 추출하는 모듈입니다.
Requirements 8.1을 구현합니다.
"""

from .object_detector import PLSQLObjectDetector
from .code_analyzer import PLSQLCodeAnalyzer
from .feature_analyzer import PLSQLFeatureAnalyzer
from .structure_analyzer import PLSQLStructureAnalyzer


class PLSQLParser(
    PLSQLObjectDetector,
    PLSQLCodeAnalyzer,
    PLSQLFeatureAnalyzer,
    PLSQLStructureAnalyzer
):
    """PL/SQL 코드 파싱 및 구문 요소 추출
    
    Requirements 8.1을 구현합니다:
    - Package (Body/Spec 구분)
    - Procedure
    - Function
    - Trigger
    - View
    - Materialized View
    
    여러 믹스인 클래스를 결합하여 완전한 PL/SQL 파서 기능을 제공합니다:
    - PLSQLObjectDetector: 오브젝트 타입 감지
    - PLSQLCodeAnalyzer: 코드 메트릭 분석
    - PLSQLFeatureAnalyzer: 고급 기능 및 의존성 분석
    - PLSQLStructureAnalyzer: 구조적 요소 분석
    """
    
    def __init__(self, code: str):
        """PLSQLParser 초기화
        
        Args:
            code: 분석할 PL/SQL 코드
        """
        # 모든 부모 클래스는 동일한 PLSQLParserBase를 상속하므로
        # 한 번만 초기화하면 됩니다
        super().__init__(code)


__all__ = ['PLSQLParser']
