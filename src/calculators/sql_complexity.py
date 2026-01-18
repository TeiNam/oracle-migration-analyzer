"""
SQL 복잡도 계산

SQL 쿼리의 복잡도를 계산하는 메서드들을 제공합니다.
"""

import logging
from src.oracle_complexity_analyzer import (
    TargetDatabase,
    SQLAnalysisResult,
    ORACLE_SPECIFIC_SYNTAX,
    ORACLE_SPECIFIC_FUNCTIONS,
)
from src.parsers.sql_parser import SQLParser

# 로거 초기화
logger = logging.getLogger(__name__)


class SQLComplexityCalculator:
    """SQL 복잡도 계산 믹스인 클래스"""
    
    def calculate_sql_complexity(self, parser: SQLParser) -> SQLAnalysisResult:
        """SQL 쿼리 복잡도 계산
        
        Requirements 12.1을 구현합니다.
        
        Args:
            parser: SQL 파서 객체
            
        Returns:
            SQLAnalysisResult: SQL 분석 결과
        """
        logger.info(f"SQL 복잡도 계산 시작 (타겟: {self.target.value})")
        
        # 각 카테고리별 점수 계산
        logger.info("구조적 복잡성 계산 중")
        structural = self._calculate_structural_complexity(parser)
        
        logger.info("Oracle 특화 기능 점수 계산 중")
        oracle_specific = self._calculate_oracle_specific_score(parser)
        
        logger.info("함수/표현식 점수 계산 중")
        functions = self._calculate_functions_score(parser)
        
        logger.info("데이터 볼륨 점수 계산 중")
        data_volume = self._calculate_data_volume_score(len(parser.query))
        
        logger.info("실행 복잡성 점수 계산 중")
        execution = self._calculate_execution_complexity(parser)
        
        logger.info("변환 난이도 점수 계산 중")
        conversion = self._calculate_conversion_difficulty(parser)
        
        # 총점 계산
        total_score = (
            structural +
            oracle_specific +
            functions +
            data_volume +
            execution +
            conversion
        )
        
        # 점수 정규화 및 레벨 분류
        normalized_score = self._normalize_score(total_score)
        complexity_level = self._get_complexity_level(normalized_score)
        recommendation = self._get_recommendation(complexity_level)
        
        logger.info(f"SQL 복잡도 계산 완료 (정규화 점수: {normalized_score:.2f}, 레벨: {complexity_level.value})")
        
        # 결과 객체 생성
        result = SQLAnalysisResult(
            query=parser.query,
            target_database=self.target,
            total_score=total_score,
            normalized_score=normalized_score,
            complexity_level=complexity_level,
            recommendation=recommendation,
            structural_complexity=structural,
            oracle_specific_features=oracle_specific,
            functions_expressions=functions,
            data_volume=data_volume,
            execution_complexity=execution,
            conversion_difficulty=conversion,
            detected_oracle_features=parser.detect_oracle_features(),
            detected_oracle_functions=parser.detect_oracle_functions(),
            detected_hints=parser.count_hints(),
            join_count=parser.count_joins(),
            subquery_depth=parser.calculate_subquery_depth(),
            cte_count=parser.count_ctes(),
            set_operators_count=parser.count_set_operators(),
        )
        
        return result
    
    def _calculate_structural_complexity(self, parser: SQLParser) -> float:
        """구조적 복잡성 점수 계산
        
        Requirements 1.1-1.5를 구현합니다.
        - 1.1: JOIN 개수에 따른 점수 계산
        - 1.2: 서브쿼리 중첩 깊이에 따른 점수 계산
        - 1.3: CTE 개수에 따른 점수 계산
        - 1.4: 집합 연산자 개수에 따른 점수 계산
        - 1.5: 풀스캔 페널티 (MySQL만)
        
        Args:
            parser: SQL 파서 객체
            
        Returns:
            float: 구조적 복잡성 점수
        """
        logger.debug("구조적 복잡성 계산 시작")
        score = 0.0
        
        # 1.1: JOIN 점수 계산
        join_count = parser.count_joins()
        logger.debug(f"JOIN 개수: {join_count}")
        for threshold, threshold_score in self.weights.join_thresholds:
            if join_count <= threshold:
                score += threshold_score
                logger.debug(f"JOIN 점수: {threshold_score}")
                break
        
        # 1.2: 서브쿼리 중첩 깊이 점수 계산
        subquery_depth = parser.calculate_subquery_depth()
        logger.debug(f"서브쿼리 중첩 깊이: {subquery_depth}")
        if subquery_depth == 0:
            pass  # 0점
        elif subquery_depth <= 2:
            # 임계값 테이블에서 찾기
            for threshold, threshold_score in self.weights.subquery_thresholds:
                if subquery_depth <= threshold:
                    score += threshold_score
                    logger.debug(f"서브쿼리 점수: {threshold_score}")
                    break
        else:
            # 3 이상인 경우
            if self.target == TargetDatabase.POSTGRESQL:
                # PostgreSQL: 1.5 + min(1, (depth-2)*0.5)
                subquery_score = 1.5 + min(1.0, (subquery_depth - 2) * 0.5)
                score += subquery_score
                logger.debug(f"서브쿼리 점수 (PostgreSQL): {subquery_score}")
            else:  # MySQL
                # MySQL: 4.0 + min(2, depth-2)
                subquery_score = 4.0 + min(2.0, subquery_depth - 2)
                score += subquery_score
                logger.debug(f"서브쿼리 점수 (MySQL): {subquery_score}")
        
        # 1.3: CTE 점수 계산
        cte_count = parser.count_ctes()
        cte_score = min(self.weights.cte_max, cte_count * self.weights.cte_coefficient)
        logger.debug(f"CTE 개수: {cte_count}, 점수: {cte_score}")
        score += cte_score
        
        # 1.4: 집합 연산자 점수 계산
        set_operators_count = parser.count_set_operators()
        set_score = min(
            self.weights.set_operator_max,
            set_operators_count * self.weights.set_operator_coefficient
        )
        logger.debug(f"집합 연산자 개수: {set_operators_count}, 점수: {set_score}")
        score += set_score
        
        # 1.5: 풀스캔 페널티 (MySQL만)
        if self.target == TargetDatabase.MYSQL and parser.has_fullscan_risk():
            logger.debug(f"풀스캔 위험 감지, 페널티: {self.weights.fullscan_penalty}")
            score += self.weights.fullscan_penalty
        
        final_score = min(score, self.weights.max_structural)
        logger.debug(f"구조적 복잡성 최종 점수: {final_score}")
        return final_score
    
    def _calculate_oracle_specific_score(self, parser: SQLParser) -> float:
        """Oracle 특화 기능 점수 계산
        
        Requirements 2.1-2.5를 구현합니다.
        - 2.1: CONNECT BY (2점)
        - 2.2: 분석 함수 (min(3, count))
        - 2.3: PIVOT/UNPIVOT (2점)
        - 2.4: MODEL 절 (3점)
        - 2.5: 기타 Oracle 특화 문법
        
        Args:
            parser: SQL 파서 객체
            
        Returns:
            float: Oracle 특화 기능 점수
        """
        score = 0.0
        detected_features = parser.detect_oracle_features()
        
        # 2.1: CONNECT BY 계층적 쿼리 (2점)
        if 'CONNECT BY' in detected_features:
            score += 2.0
        
        # 2.2: 분석 함수 (OVER 절) - min(3, count)
        analytic_count = parser.count_analytic_functions()
        score += min(3.0, analytic_count)
        
        # 2.3: PIVOT/UNPIVOT (2점)
        if 'PIVOT' in detected_features or 'UNPIVOT' in detected_features:
            score += 2.0
        
        # 2.4: MODEL 절 (3점)
        if 'MODEL' in detected_features:
            score += 3.0
        
        # 2.5: 기타 Oracle 특화 문법
        # ORACLE_SPECIFIC_SYNTAX에 정의된 점수 합산
        for feature in detected_features:
            if feature in ORACLE_SPECIFIC_SYNTAX:
                feature_score = ORACLE_SPECIFIC_SYNTAX[feature]
                # CONNECT BY, PIVOT, MODEL은 이미 계산했으므로 제외
                if feature not in ['CONNECT BY', 'PIVOT', 'UNPIVOT', 'MODEL']:
                    score += feature_score
        
        return min(score, 3.0)  # 최대 3.0점
    
    def _calculate_oracle_function_score(self, parser: SQLParser) -> float:
        """Oracle 특화 함수 점수 계산
        
        Requirements 3.1, 3.2를 구현합니다.
        - 3.1: 각 Oracle 특화 함수당 0.5점
        - 3.2: MySQL 타겟에서 특수 집계 함수 추가 페널티
        
        Args:
            parser: SQL 파서 객체
            
        Returns:
            float: Oracle 특화 함수 점수
        """
        score = 0.0
        detected_functions = parser.detect_oracle_functions()
        
        # 3.1: 각 Oracle 특화 함수당 0.5점
        for func in detected_functions:
            if func in ORACLE_SPECIFIC_FUNCTIONS:
                score += ORACLE_SPECIFIC_FUNCTIONS[func]
        
        # 3.2: MySQL 타겟에서 특수 집계 함수 추가 페널티
        if self.target == TargetDatabase.MYSQL:
            if 'MEDIAN' in detected_functions or any('PERCENTILE' in f for f in detected_functions):
                score += 0.5
            if 'LISTAGG' in detected_functions:
                score += 0.3
            if 'XMLAGG' in detected_functions:
                score += 0.5
            # KEEP 절 감지 (간단한 문자열 검색)
            if 'KEEP' in parser.normalized_query:
                score += 0.5
        
        return score
    
    def _calculate_functions_score(self, parser: SQLParser) -> float:
        """함수/표현식 점수 계산
        
        Requirements 4.1-4.5를 구현합니다.
        - 4.1: 집계 함수 (min(2, count*0.5))
        - 4.2: 사용자 정의 함수 (min(2, count*0.5))
        - 4.3: CASE 표현식 (min(2, count*0.5))
        - 4.4: 정규식 함수 (1점)
        - 4.5: WHERE 절 없이 COUNT(*) 사용 (MySQL만, 0.5점)
        
        Args:
            parser: SQL 파서 객체
            
        Returns:
            float: 함수/표현식 점수
        """
        score = 0.0
        
        # 4.1: 집계 함수 점수
        agg_count = parser.count_aggregate_functions()
        score += min(2.0, agg_count * 0.5)
        
        # 4.2: 사용자 정의 함수 점수
        # SQLParser에서 potential_udf를 계산하는 메서드가 있다고 가정
        # 실제로는 parser에 해당 메서드가 없을 수 있으므로 0으로 처리
        # TODO: SQLParser에 count_user_defined_functions() 메서드 추가 필요
        # udf_count = parser.count_user_defined_functions()
        # score += min(2.0, udf_count * 0.5)
        
        # 4.3: CASE 표현식 점수
        case_count = parser.count_case_expressions()
        score += min(2.0, case_count * 0.5)
        
        # 4.4: 정규식 함수 점수
        detected_functions = parser.detect_oracle_functions()
        regex_functions = ['REGEXP_LIKE', 'REGEXP_SUBSTR', 'REGEXP_REPLACE', 'REGEXP_INSTR']
        has_regex = any(func in detected_functions for func in regex_functions)
        if has_regex:
            score += 1.0
        
        # 4.5: MySQL 타겟에서 WHERE 절 없이 COUNT(*) 사용 (0.5점 페널티)
        if self.target == TargetDatabase.MYSQL:
            # WHERE 절이 없고 COUNT(*)가 있는지 확인
            if 'COUNT' in parser.normalized_query and 'WHERE' not in parser.normalized_query:
                score += 0.5
        
        # Oracle 특화 함수 점수 추가 (Requirements 3.1, 3.2)
        for func in detected_functions:
            if func in ORACLE_SPECIFIC_FUNCTIONS:
                score += ORACLE_SPECIFIC_FUNCTIONS[func]
        
        # MySQL 타겟에서 특수 집계 함수 추가 페널티 (Requirements 3.2)
        if self.target == TargetDatabase.MYSQL:
            if 'MEDIAN' in detected_functions or any('PERCENTILE' in f for f in detected_functions):
                score += 0.5
            if 'LISTAGG' in detected_functions:
                score += 0.3
            if 'XMLAGG' in detected_functions:
                score += 0.5
            # KEEP 절 감지 (간단한 문자열 검색)
            if 'KEEP' in parser.normalized_query:
                score += 0.5
        
        return min(score, 2.5)  # 최대 2.5점
    
    def _calculate_data_volume_score(self, query_length: int) -> float:
        """데이터 처리 볼륨 점수 계산
        
        Requirements 5.1-5.4를 구현합니다.
        - 5.1: 200자 미만 = 0.5점
        - 5.2: 200-500자 = PostgreSQL 1.0점, MySQL 1.2점
        - 5.3: 500-1000자 = PostgreSQL 1.5점, MySQL 2.0점
        - 5.4: 1000자 이상 = PostgreSQL 2.0점, MySQL 2.5점
        
        Args:
            query_length: 쿼리 길이 (문자 수)
            
        Returns:
            float: 데이터 볼륨 점수
        """
        if query_length < 200:
            return self.weights.data_volume_scores['small']  # 0.5
        elif query_length < 500:
            return self.weights.data_volume_scores['medium']  # PostgreSQL 1.0, MySQL 1.2
        elif query_length < 1000:
            return self.weights.data_volume_scores['large']  # PostgreSQL 1.5, MySQL 2.0
        else:
            return self.weights.data_volume_scores['xlarge']  # PostgreSQL 2.0, MySQL 2.5
    
    def _calculate_execution_complexity(self, parser: SQLParser) -> float:
        """실행 계획 복잡성 점수 계산
        
        Requirements 6.1-6.7을 구현합니다.
        - 6.1: PostgreSQL에서 join_count > 5 또는 subquery_depth > 2 (0.5점)
        - 6.2: MySQL에서 join_count > 3 또는 subquery_depth > 1 (1.5점)
        - 6.3: ORDER BY (PostgreSQL 0.2점, MySQL 0.5점)
        - 6.4: GROUP BY (PostgreSQL 0.2점, MySQL 0.5점)
        - 6.5: HAVING (PostgreSQL 0.2점, MySQL 0.5점)
        - 6.6: MySQL에서 파생 테이블 (min(1.0, count*0.5))
        - 6.7: MySQL에서 성능 페널티 요소
        
        Args:
            parser: SQL 파서 객체
            
        Returns:
            float: 실행 복잡성 점수
        """
        score = 0.0
        
        join_count = parser.count_joins()
        subquery_depth = parser.calculate_subquery_depth()
        
        # 6.1, 6.2: 조인 깊이 페널티
        if self.target == TargetDatabase.POSTGRESQL:
            if join_count > 5 or subquery_depth > 2:
                score += self.weights.execution_scores['join_depth']  # 0.5
        else:  # MySQL
            if join_count > 3 or subquery_depth > 1:
                score += self.weights.execution_scores['join_depth']  # 1.5
        
        # 6.3: ORDER BY
        if 'ORDER BY' in parser.normalized_query:
            score += self.weights.execution_scores['order_by']
        
        # 6.4: GROUP BY
        if 'GROUP BY' in parser.normalized_query:
            score += self.weights.execution_scores['group_by']
        
        # 6.5: HAVING
        if 'HAVING' in parser.normalized_query:
            score += self.weights.execution_scores['having']
        
        # MySQL 전용 페널티
        if self.target == TargetDatabase.MYSQL:
            # 6.6: 파생 테이블 (min(1.0, count*0.5))
            derived_table_count = parser.count_derived_tables()
            if derived_table_count > 0:
                score += min(1.0, derived_table_count * self.weights.execution_scores['derived_table'])
            
            # 6.7: 성능 페널티 요소
            penalties = parser.has_performance_penalties()
            
            if penalties.get('distinct', False):
                score += self.weights.execution_scores['distinct']  # 0.3
            
            if penalties.get('or_conditions', False):
                score += self.weights.execution_scores['or_conditions']  # 0.3
            
            if penalties.get('like_pattern', False):
                score += self.weights.execution_scores['like_pattern']  # 0.3
            
            if penalties.get('function_in_where', False):
                score += self.weights.execution_scores['function_in_where']  # 0.5
        
        # 최대 점수 제한
        max_execution = 1.0 if self.target == TargetDatabase.POSTGRESQL else 2.5
        return min(score, max_execution)
    
    def _calculate_conversion_difficulty(self, parser: SQLParser) -> float:
        """변환 난이도 점수 계산 (힌트 + Oracle 특화 기능 포함)
        
        Requirements 7.1-7.5를 구현합니다.
        
        힌트 점수:
        - 7.1: 힌트 개수 계산
        - 7.2: 0개 = 0점
        - 7.3: 1-2개 = 0.5점
        - 7.4: 3-5개 = 1.0점
        - 7.5: 6개 이상 = 1.5점
        
        Oracle 특화 기능 변환 난이도:
        - 각 기능별로 변환 난이도 가중치 적용
        - 매우 어려운 기능 (MODEL, CONNECT BY 등): 1.0점
        - 어려운 기능 (PIVOT, MERGE 등): 0.5점
        - 보통 기능 (ROWNUM, DECODE 등): 0.3점
        - 최대 3.0점
        
        Args:
            parser: SQL 파서 객체
            
        Returns:
            float: 변환 난이도 점수 (최대 4.5점)
        """
        score = 0.0
        
        # 1. 힌트 점수 계산
        hints = parser.count_hints()
        hint_count = len(hints)
        
        if hint_count == 0:
            hint_score = 0.0
        elif hint_count <= 2:
            hint_score = 0.5
        elif hint_count <= 5:
            hint_score = 1.0
        else:
            hint_score = 1.5
        
        score += hint_score
        
        # 2. Oracle 특화 기능 변환 난이도 계산
        detected_features = parser.detect_oracle_features()
        
        # 변환 난이도 가중치 정의
        feature_difficulty = {
            # 매우 어려운 기능 (1.0점)
            'MODEL': 1.0,
            'CONNECT BY': 1.0,
            'START WITH': 0.5,  # CONNECT BY와 함께 사용되므로 0.5점
            'PRIOR': 0.3,  # CONNECT BY와 함께 사용되므로 0.3점
            'FLASHBACK': 1.0,
            'MATERIALIZED VIEW': 1.0,
            
            # 어려운 기능 (0.5점)
            'PIVOT': 0.5,
            'UNPIVOT': 0.5,
            'MERGE': 0.5,
            'XMLTABLE': 0.5,
            'XMLQUERY': 0.5,
            'XMLEXISTS': 0.5,
            'MATCH_RECOGNIZE': 0.5,
            
            # 보통 기능 (0.3점)
            'ROWNUM': 0.3,
            'DECODE': 0.3,
            'DUAL': 0.1,  # 간단하지만 변환 필요
            'LEVEL': 0.3,
            'SYS_CONNECT_BY_PATH': 0.3,
            'CONNECT_BY_ROOT': 0.3,
            'CONNECT_BY_ISLEAF': 0.3,
            'CONNECT_BY_ISCYCLE': 0.3,
            
            # 기타 기능 (0.2점)
            'ROWID': 0.2,
            'SYSDATE': 0.1,
            'SYSTIMESTAMP': 0.1,
        }
        
        feature_score = 0.0
        for feature in detected_features:
            if feature in feature_difficulty:
                feature_score += feature_difficulty[feature]
        
        # Oracle 특화 기능 점수는 최대 3.0점
        feature_score = min(feature_score, 3.0)
        score += feature_score
        
        # 전체 변환 난이도는 최대 4.5점 (힌트 1.5 + 기능 3.0)
        return min(score, 4.5)
