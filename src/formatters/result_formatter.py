"""
Result Formatter

분석 결과를 JSON 및 Markdown 형식으로 출력하는 모듈입니다.
Requirements 14.1, 14.2, 14.3, 14.4, 14.5를 구현합니다.
"""

import json
from typing import Union
from dataclasses import asdict

from src.oracle_complexity_analyzer import (
    SQLAnalysisResult,
    PLSQLAnalysisResult,
    TargetDatabase,
    ComplexityLevel,
    PLSQLObjectType
)


class ResultFormatter:
    """분석 결과 포맷터
    
    Requirements:
    - 14.1: JSON 형식 출력
    - 14.2: Markdown 형식 출력
    - 14.3: JSON 역직렬화
    - 14.4: Round-trip 직렬화 지원
    - 14.5: Markdown 보고서 완전성
    """
    
    @staticmethod
    def to_json(result: Union[SQLAnalysisResult, PLSQLAnalysisResult]) -> str:
        """분석 결과를 JSON 형식으로 변환
        
        Requirements 14.1을 구현합니다.
        - 유효한 JSON 형식으로 출력
        - Enum 타입을 문자열로 변환
        - 모든 필드 포함
        
        Args:
            result: SQL 또는 PL/SQL 분석 결과 객체
            
        Returns:
            JSON 형식의 문자열
        """
        # dataclass를 dict로 변환
        result_dict = asdict(result)
        
        # Enum 타입을 문자열로 변환
        if isinstance(result, SQLAnalysisResult):
            result_dict['target_database'] = result.target_database.value
            result_dict['complexity_level'] = result.complexity_level.value
            result_dict['result_type'] = 'sql'
        elif isinstance(result, PLSQLAnalysisResult):
            result_dict['target_database'] = result.target_database.value
            result_dict['complexity_level'] = result.complexity_level.value
            result_dict['object_type'] = result.object_type.value
            result_dict['result_type'] = 'plsql'
        
        # JSON 문자열로 변환 (들여쓰기 포함, 한글 유니코드 이스케이프 방지)
        return json.dumps(result_dict, indent=2, ensure_ascii=False)
    
    @staticmethod
    def from_json(json_str: str, result_type: str) -> Union[SQLAnalysisResult, PLSQLAnalysisResult]:
        """JSON 문자열을 분석 결과 객체로 변환
        
        Requirements 14.3을 구현합니다.
        - JSON 문자열을 파싱하여 원본 객체 생성
        - Enum 타입 복원
        
        Args:
            json_str: JSON 형식의 문자열
            result_type: 결과 타입 ('sql' 또는 'plsql')
            
        Returns:
            SQLAnalysisResult 또는 PLSQLAnalysisResult 객체
            
        Raises:
            ValueError: 잘못된 result_type이거나 JSON 파싱 실패 시
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 실패: {e}")
        
        # result_type 필드가 있으면 사용, 없으면 인자 사용
        actual_type = data.pop('result_type', result_type)
        
        # result_type 유효성 검증
        if actual_type not in ('sql', 'plsql'):
            raise ValueError(f"지원하지 않는 result_type: {actual_type}")
        
        # 필수 필드 확인
        if 'target_database' not in data:
            raise ValueError("필수 필드 'target_database'가 없습니다")
        if 'complexity_level' not in data:
            raise ValueError("필수 필드 'complexity_level'가 없습니다")
        
        # Enum 타입 복원
        try:
            data['target_database'] = TargetDatabase(data['target_database'])
            data['complexity_level'] = ComplexityLevel(data['complexity_level'])
        except ValueError as e:
            raise ValueError(f"Enum 변환 실패: {e}")
        
        if actual_type == 'sql':
            return SQLAnalysisResult(**data)
        elif actual_type == 'plsql':
            if 'object_type' not in data:
                raise ValueError("PL/SQL 결과에 필수 필드 'object_type'이 없습니다")
            try:
                data['object_type'] = PLSQLObjectType(data['object_type'])
            except ValueError as e:
                raise ValueError(f"object_type Enum 변환 실패: {e}")
            return PLSQLAnalysisResult(**data)
    
    @staticmethod
    def to_markdown(result: Union[SQLAnalysisResult, PLSQLAnalysisResult]) -> str:
        """분석 결과를 Markdown 형식으로 변환
        
        Requirements 14.2, 14.5를 구현합니다.
        - 가독성 좋은 Markdown 보고서 생성
        - 모든 필수 섹션 포함
        
        Args:
            result: SQL 또는 PL/SQL 분석 결과 객체
            
        Returns:
            Markdown 형식의 문자열
        """
        if isinstance(result, SQLAnalysisResult):
            return ResultFormatter._format_sql_markdown(result)
        elif isinstance(result, PLSQLAnalysisResult):
            return ResultFormatter._format_plsql_markdown(result)
        else:
            raise ValueError(f"지원하지 않는 결과 타입: {type(result)}")
    
    @staticmethod
    def _format_sql_markdown(result: SQLAnalysisResult) -> str:
        """SQL 분석 결과 Markdown 포맷
        
        Requirements 14.5를 구현합니다.
        다음 섹션을 포함합니다:
        - 복잡도 점수 요약
        - 복잡도 레벨 및 권장사항
        - 세부 점수 테이블
        - 감지된 Oracle 특화 기능 목록
        - 감지된 Oracle 특화 함수 목록
        - 원본 쿼리
        
        Args:
            result: SQL 분석 결과 객체
            
        Returns:
            Markdown 형식의 문자열
        """
        md = []
        
        # 제목
        md.append("# Oracle SQL 복잡도 분석 결과\n")
        
        # 복잡도 점수 요약
        md.append("## 복잡도 점수 요약\n")
        md.append(f"- **타겟 데이터베이스**: {result.target_database.value.upper()}")
        md.append(f"- **원점수 (Raw Score)**: {result.total_score:.2f}")
        md.append(f"- **정규화 점수**: {result.normalized_score:.2f} / 10.0")
        md.append(f"- **복잡도 레벨**: {result.complexity_level.value}")
        md.append(f"- **권장사항**: {result.recommendation}\n")
        
        # 세부 점수 테이블
        md.append("## 세부 점수\n")
        md.append("| 카테고리 | 점수 |")
        md.append("|---------|------|")
        md.append(f"| 구조적 복잡성 | {result.structural_complexity:.2f} |")
        md.append(f"| Oracle 특화 기능 | {result.oracle_specific_features:.2f} |")
        md.append(f"| 함수/표현식 | {result.functions_expressions:.2f} |")
        md.append(f"| 데이터 볼륨 | {result.data_volume:.2f} |")
        md.append(f"| 실행 복잡성 | {result.execution_complexity:.2f} |")
        md.append(f"| 변환 난이도 | {result.conversion_difficulty:.2f} |")
        md.append("")
        
        # 분석 메타데이터
        md.append("## 분석 메타데이터\n")
        md.append(f"- **JOIN 개수**: {result.join_count}")
        md.append(f"- **서브쿼리 중첩 깊이**: {result.subquery_depth}")
        md.append(f"- **CTE 개수**: {result.cte_count}")
        md.append(f"- **집합 연산자 개수**: {result.set_operators_count}\n")
        
        # 감지된 Oracle 특화 기능
        if result.detected_oracle_features:
            md.append("## 감지된 Oracle 특화 기능\n")
            for feature in result.detected_oracle_features:
                md.append(f"- {feature}")
            md.append("")
        
        # 감지된 Oracle 특화 함수
        if result.detected_oracle_functions:
            md.append("## 감지된 Oracle 특화 함수\n")
            for func in result.detected_oracle_functions:
                md.append(f"- {func}")
            md.append("")
        
        # 감지된 힌트
        if result.detected_hints:
            md.append("## 감지된 힌트\n")
            for hint in result.detected_hints:
                md.append(f"- {hint}")
            md.append("")
        
        # 변환 가이드
        if result.conversion_guides:
            md.append("## 변환 가이드\n")
            md.append("| Oracle 기능 | 대체 방법 |")
            md.append("|------------|----------|")
            for feature, guide in result.conversion_guides.items():
                md.append(f"| {feature} | {guide} |")
            md.append("")
        
        # 원본 쿼리
        md.append("## 원본 쿼리\n")
        md.append("```sql")
        md.append(result.query)
        md.append("```\n")
        
        return "\n".join(md)
    
    @staticmethod
    def _format_plsql_markdown(result: PLSQLAnalysisResult) -> str:
        """PL/SQL 분석 결과 Markdown 포맷
        
        Requirements 14.5를 구현합니다.
        다음 섹션을 포함합니다:
        - 복잡도 점수 요약
        - 복잡도 레벨 및 권장사항
        - 세부 점수 테이블
        - 감지된 Oracle 특화 기능 목록
        - 감지된 외부 의존성 목록
        - 원본 코드
        
        Args:
            result: PL/SQL 분석 결과 객체
            
        Returns:
            Markdown 형식의 문자열
        """
        md = []
        
        # 제목
        md.append("# Oracle PL/SQL 복잡도 분석 결과\n")
        
        # 복잡도 점수 요약
        md.append("## 복잡도 점수 요약\n")
        md.append(f"- **오브젝트 타입**: {result.object_type.value.upper()}")
        md.append(f"- **타겟 데이터베이스**: {result.target_database.value.upper()}")
        md.append(f"- **원점수 (Raw Score)**: {result.total_score:.2f}")
        md.append(f"- **정규화 점수**: {result.normalized_score:.2f} / 10.0")
        md.append(f"- **복잡도 레벨**: {result.complexity_level.value}")
        md.append(f"- **권장사항**: {result.recommendation}\n")
        
        # 세부 점수 테이블
        md.append("## 세부 점수\n")
        md.append("| 카테고리 | 점수 |")
        md.append("|---------|------|")
        md.append(f"| 기본 점수 | {result.base_score:.2f} |")
        md.append(f"| 코드 복잡도 | {result.code_complexity:.2f} |")
        md.append(f"| Oracle 특화 기능 | {result.oracle_features:.2f} |")
        md.append(f"| 비즈니스 로직 | {result.business_logic:.2f} |")
        md.append(f"| 변환 난이도 | {result.conversion_difficulty:.2f} |")
        
        # MySQL 타겟인 경우 추가 점수 표시
        if result.target_database == TargetDatabase.MYSQL:
            md.append(f"| MySQL 제약 | {result.mysql_constraints:.2f} |")
            md.append(f"| 애플리케이션 이관 페널티 | {result.app_migration_penalty:.2f} |")
        
        md.append("")
        
        # 분석 메타데이터
        md.append("## 분석 메타데이터\n")
        md.append(f"- **코드 라인 수**: {result.line_count}")
        md.append(f"- **커서 개수**: {result.cursor_count}")
        md.append(f"- **예외 블록 개수**: {result.exception_blocks}")
        md.append(f"- **중첩 깊이**: {result.nesting_depth}")
        md.append(f"- **BULK 연산 개수**: {result.bulk_operations_count}")
        md.append(f"- **동적 SQL 개수**: {result.dynamic_sql_count}\n")
        
        # 감지된 Oracle 특화 기능
        if result.detected_oracle_features:
            md.append("## 감지된 Oracle 특화 기능\n")
            for feature in result.detected_oracle_features:
                md.append(f"- {feature}")
            md.append("")
        
        # 감지된 외부 의존성
        if result.detected_external_dependencies:
            md.append("## 감지된 외부 의존성\n")
            for dep in result.detected_external_dependencies:
                md.append(f"- {dep}")
            md.append("")
        
        # 변환 가이드
        if result.conversion_guides:
            md.append("## 변환 가이드\n")
            md.append("| Oracle 기능 | 대체 방법 |")
            md.append("|------------|----------|")
            for feature, guide in result.conversion_guides.items():
                md.append(f"| {feature} | {guide} |")
            md.append("")
        
        # 원본 코드
        md.append("## 원본 코드\n")
        md.append("```sql")
        md.append(result.code)
        md.append("```\n")
        
        return "\n".join(md)

    @staticmethod
    def batch_to_markdown(batch_result: dict, target_db: str = "PostgreSQL") -> str:
        """배치 PL/SQL 분석 결과를 Markdown 형식으로 변환
        
        Args:
            batch_result: 배치 분석 결과 딕셔너리
            target_db: 타겟 데이터베이스 이름
            
        Returns:
            Markdown 형식의 문자열
        """
        md = []
        
        # 제목
        md.append(f"# 배치 PL/SQL 분석 리포트\n")
        md.append(f"**타겟 데이터베이스**: {target_db}\n")
        
        # 전체 요약
        md.append("## 전체 요약\n")
        md.append(f"- **전체 객체 수**: {batch_result['total_objects']}")
        md.append(f"- **분석 성공**: {batch_result['analyzed_objects']}")
        md.append(f"- **분석 실패**: {batch_result['failed_objects']}\n")
        
        # 객체 타입별 통계
        if batch_result.get('statistics'):
            md.append("## 객체 타입별 통계\n")
            md.append("| 객체 타입 | 개수 |")
            md.append("|----------|------|")
            for obj_type, count in sorted(batch_result['statistics'].items()):
                md.append(f"| {obj_type} | {count} |")
            md.append("")
        
        # 복잡도 요약
        if batch_result.get('summary'):
            summary = batch_result['summary']
            md.append("## 복잡도 요약\n")
            md.append(f"- **평균 복잡도**: {summary.get('average_score', 0):.2f}")
            md.append(f"- **최대 복잡도**: {summary.get('max_score', 0):.2f}")
            md.append(f"- **최소 복잡도**: {summary.get('min_score', 0):.2f}\n")
            
            # 복잡도 분포
            if summary.get('complexity_distribution'):
                dist = summary['complexity_distribution']
                md.append("### 복잡도 분포\n")
                md.append("| 복잡도 레벨 | 객체 수 |")
                md.append("|------------|---------|")
                md.append(f"| 매우 간단 (0-1) | {dist.get('very_simple', 0)} |")
                md.append(f"| 간단 (1-3) | {dist.get('simple', 0)} |")
                md.append(f"| 중간 (3-5) | {dist.get('moderate', 0)} |")
                md.append(f"| 복잡 (5-7) | {dist.get('complex', 0)} |")
                md.append(f"| 매우 복잡 (7-9) | {dist.get('very_complex', 0)} |")
                md.append(f"| 극도로 복잡 (9-10) | {dist.get('extremely_complex', 0)} |")
                md.append("")
        
        # 전체 감지된 Oracle 특화 기능 집계
        all_oracle_features = set()
        all_external_deps = set()
        for obj_result in batch_result.get('results', []):
            analysis = obj_result['analysis']
            if analysis.detected_oracle_features:
                all_oracle_features.update(analysis.detected_oracle_features)
            if analysis.detected_external_dependencies:
                all_external_deps.update(analysis.detected_external_dependencies)
        
        if all_oracle_features:
            md.append("## 감지된 Oracle 특화 기능\n")
            for feature in sorted(all_oracle_features):
                md.append(f"- {feature}")
            md.append("")
        
        if all_external_deps:
            md.append("## 감지된 외부 의존성\n")
            for dep in sorted(all_external_deps):
                md.append(f"- {dep}")
            md.append("")
        
        # 변환 가이드 (전체 감지된 기능에 대한 가이드)
        if all_oracle_features or all_external_deps:
            from src.formatters.conversion_guide_provider import ConversionGuideProvider
            guide_provider = ConversionGuideProvider(target_db.lower())
            
            # 모든 기능과 의존성을 합쳐서 변환 가이드 가져오기
            all_items = list(all_oracle_features) + list(all_external_deps)
            conversion_guides = guide_provider.get_conversion_guide(all_items)
            
            if conversion_guides:
                md.append("## 변환 가이드\n")
                md.append("| Oracle 기능 | 대체 방법 |")
                md.append("|------------|----------|")
                
                for feature in sorted(conversion_guides.keys()):
                    guide = conversion_guides[feature]
                    md.append(f"| {feature} | {guide} |")
                
                md.append("")
        
        # 개별 객체 분석 결과
        if batch_result.get('results'):
            md.append("## 📝 개별 객체 분석 결과\n")
            
            for i, obj_result in enumerate(batch_result['results'], 1):
                analysis = obj_result['analysis']
                
                md.append(f"### {i}. {obj_result['owner']}.{obj_result['object_name']}\n")
                md.append(f"- **타입**: {obj_result['object_type']}")
                md.append(f"- **라인 범위**: {obj_result['line_range']}")
                md.append(f"- **원점수 (Raw Score)**: {analysis.total_score:.2f}")
                md.append(f"- **정규화 점수**: {analysis.normalized_score:.2f}/10")
                md.append(f"- **복잡도 레벨**: {analysis.complexity_level.value}")
                md.append(f"- **추천사항**: {analysis.recommendation}\n")
                
                # 세부 점수
                md.append("#### 세부 점수\n")
                md.append("| 항목 | 점수 |")
                md.append("|------|------|")
                md.append(f"| 기본 점수 | {analysis.base_score:.2f} |")
                md.append(f"| 코드 복잡도 | {analysis.code_complexity:.2f} |")
                md.append(f"| Oracle 특화 기능 | {analysis.oracle_features:.2f} |")
                md.append(f"| 비즈니스 로직 | {analysis.business_logic:.2f} |")
                md.append(f"| 변환 난이도 | {analysis.conversion_difficulty:.2f} |")
                md.append("")
                
                # 감지된 Oracle 특화 기능
                if analysis.detected_oracle_features:
                    md.append("**감지된 Oracle 특화 기능**:")
                    for feature in analysis.detected_oracle_features[:5]:  # 상위 5개만
                        md.append(f"- {feature}")
                    if len(analysis.detected_oracle_features) > 5:
                        md.append(f"- ... 외 {len(analysis.detected_oracle_features) - 5}개")
                    md.append("")
        
        # 분석 실패 객체
        if batch_result.get('failed'):
            md.append("## ⚠️ 분석 실패 객체\n")
            md.append("| Owner | Type | Name | Error |")
            md.append("|-------|------|------|-------|")
            for failed in batch_result['failed']:
                md.append(f"| {failed['owner']} | {failed['object_type']} | {failed['object_name']} | {failed['error']} |")
            md.append("")
        
        return "\n".join(md)
    
    @staticmethod
    def batch_to_json(batch_result: dict) -> str:
        """배치 PL/SQL 분석 결과를 JSON 형식으로 변환
        
        Args:
            batch_result: 배치 분석 결과 딕셔너리
            
        Returns:
            JSON 형식의 문자열
        """
        # 분석 결과 객체를 직렬화 가능한 형태로 변환
        serializable_result = {
            'total_objects': batch_result['total_objects'],
            'analyzed_objects': batch_result['analyzed_objects'],
            'failed_objects': batch_result['failed_objects'],
            'statistics': batch_result.get('statistics', {}),
            'summary': batch_result.get('summary', {}),
            'results': [],
            'failed': batch_result.get('failed', [])
        }
        
        # 개별 객체 결과 변환
        for obj_result in batch_result.get('results', []):
            analysis = obj_result['analysis']
            serializable_result['results'].append({
                'owner': obj_result['owner'],
                'object_type': obj_result['object_type'],
                'object_name': obj_result['object_name'],
                'line_range': obj_result['line_range'],
                'analysis': {
                    'total_score': analysis.total_score,
                    'normalized_score': analysis.normalized_score,
                    'complexity_level': analysis.complexity_level.value,
                    'recommendation': analysis.recommendation,
                    'object_type': analysis.object_type.value,
                    'target_database': analysis.target_database.value,
                    'base_score': analysis.base_score,
                    'code_complexity': analysis.code_complexity,
                    'oracle_features': analysis.oracle_features,
                    'business_logic': analysis.business_logic,
                    'conversion_difficulty': analysis.conversion_difficulty,
                    'detected_oracle_features': analysis.detected_oracle_features,
                    'detected_external_dependencies': analysis.detected_external_dependencies,
                    'line_count': analysis.line_count,
                    'cursor_count': analysis.cursor_count,
                    'exception_blocks': analysis.exception_blocks,
                    'nesting_depth': analysis.nesting_depth
                }
            })
        
        return json.dumps(serializable_result, indent=2, ensure_ascii=False)
