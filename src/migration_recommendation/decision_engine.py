"""
마이그레이션 의사결정 엔진

Oracle 데이터베이스의 AWS 클라우드 마이그레이션 시 최적의 전략을 결정합니다.

의사결정 기준:
1. Replatform: 복잡도가 매우 높거나 변환이 거의 불가능한 경우
2. PostgreSQL: 중간 복잡도이거나 PostgreSQL 친화적 기능 사용 시
3. MySQL: 복잡도가 낮고 단순한 CRUD 위주인 경우

PostgreSQL vs MySQL 선택 기준 (기술적 근거):
- CTE (WITH 절): PostgreSQL이 더 강력한 지원 (재귀 CTE 포함)
- 윈도우 함수: PostgreSQL이 더 다양한 기능 지원
- BULK 연산: PostgreSQL은 ARRAY로 대체 가능, MySQL은 미지원
- JSON 처리: PostgreSQL이 더 강력 (JSONB 타입)
- 트랜잭션 격리: PostgreSQL이 더 엄격한 ACID 지원
- 외부 의존성: DBMS_LOB, UTL_FILE 등은 PostgreSQL이 더 나은 대안 제공
"""

from typing import Optional, List, Tuple, Dict, Any
from .data_models import IntegratedAnalysisResult, AnalysisMetrics, MigrationStrategy


class ReplatformReason:
    """Replatform 선택 이유를 나타내는 클래스"""
    
    # 이유 코드 상수
    HIGH_SQL_COMPLEXITY = "high_sql_complexity"
    HIGH_PLSQL_COMPLEXITY = "high_plsql_complexity"
    HIGH_COMPLEXITY_RATIO = "high_complexity_ratio"
    HIGH_COMPLEXITY_COUNT = "high_complexity_count"
    LARGE_CODEBASE_HIGH_COMPLEXITY = "large_codebase_high_complexity"
    LARGE_PLSQL_COUNT = "large_plsql_count"
    
    # 이유별 설명 (한국어)
    DESCRIPTIONS_KO = {
        HIGH_SQL_COMPLEXITY: "SQL 평균 복잡도가 매우 높음 (7.5 이상)",
        HIGH_PLSQL_COMPLEXITY: "PL/SQL 평균 복잡도가 매우 높음 (7.0 이상)",
        HIGH_COMPLEXITY_RATIO: "고난이도 오브젝트 비율이 높음 (25% 이상, 모수 70개 이상)",
        HIGH_COMPLEXITY_COUNT: "고난이도 오브젝트 절대 개수가 많음 (50개 이상)",
        LARGE_CODEBASE_HIGH_COMPLEXITY: "코드량이 매우 많고 복잡도가 높음 (20만줄 이상 + 복잡도 7.5 이상)",
        LARGE_PLSQL_COUNT: "PL/SQL 오브젝트 개수가 매우 많음 (500개 이상)",
    }
    
    # 이유별 설명 (영어)
    DESCRIPTIONS_EN = {
        HIGH_SQL_COMPLEXITY: "Very high SQL average complexity (≥7.5)",
        HIGH_PLSQL_COMPLEXITY: "Very high PL/SQL average complexity (≥7.0)",
        HIGH_COMPLEXITY_RATIO: "High ratio of complex objects (≥25%, min 70 objects)",
        HIGH_COMPLEXITY_COUNT: "Large number of complex objects (≥50)",
        LARGE_CODEBASE_HIGH_COMPLEXITY: "Very large codebase with high complexity (≥200K lines + complexity ≥7.5)",
        LARGE_PLSQL_COUNT: "Very large number of PL/SQL objects (≥500)",
    }


class PostgreSQLPreferenceReason:
    """PostgreSQL 선호 이유를 나타내는 클래스"""
    
    # 이유 코드 상수
    CTE_USAGE = "cte_usage"
    ANALYTIC_FUNCTIONS = "analytic_functions"
    BULK_OPERATIONS = "bulk_operations"
    COMPLEX_TRANSACTIONS = "complex_transactions"
    EXTERNAL_DEPENDENCIES = "external_dependencies"
    ADVANCED_FEATURES = "advanced_features"
    MEDIUM_COMPLEXITY = "medium_complexity"
    
    # 이유별 설명 (한국어)
    DESCRIPTIONS_KO = {
        CTE_USAGE: "CTE (WITH 절) 사용 - PostgreSQL이 더 강력한 지원 제공",
        ANALYTIC_FUNCTIONS: "분석 함수(윈도우 함수) 사용 - PostgreSQL이 더 다양한 기능 지원",
        BULK_OPERATIONS: "BULK 연산 사용 - PostgreSQL은 ARRAY로 대체 가능, MySQL은 미지원",
        COMPLEX_TRANSACTIONS: "복잡한 트랜잭션 제어 - PostgreSQL이 더 엄격한 ACID 지원",
        EXTERNAL_DEPENDENCIES: "외부 패키지 의존성 - PostgreSQL이 더 나은 대안 제공",
        ADVANCED_FEATURES: "고급 기능 사용 - PostgreSQL이 더 호환성 높음",
        MEDIUM_COMPLEXITY: "중간 복잡도 - PostgreSQL이 PL/pgSQL로 변환 용이",
    }
    
    # 이유별 설명 (영어)
    DESCRIPTIONS_EN = {
        CTE_USAGE: "CTE (WITH clause) usage - PostgreSQL provides stronger support",
        ANALYTIC_FUNCTIONS: "Analytic functions usage - PostgreSQL supports more features",
        BULK_OPERATIONS: "BULK operations - PostgreSQL can use ARRAY, MySQL doesn't support",
        COMPLEX_TRANSACTIONS: "Complex transaction control - PostgreSQL has stricter ACID",
        EXTERNAL_DEPENDENCIES: "External package dependencies - PostgreSQL has better alternatives",
        ADVANCED_FEATURES: "Advanced features - PostgreSQL has higher compatibility",
        MEDIUM_COMPLEXITY: "Medium complexity - PostgreSQL PL/pgSQL conversion is easier",
    }


class MigrationDecisionEngine:
    """
    마이그레이션 의사결정 엔진

    PL/SQL 개수와 복잡도를 2차원으로 고려하여 최적의 전략을 결정합니다.
    PostgreSQL vs MySQL 선택 시 기술적 근거를 기반으로 판단합니다.

    의사결정 매트릭스 (PL/SQL 개수 x 복잡도):

    복잡도 높음(6.0+) + 많음(100+)  → Replatform (변환 불가능)
    복잡도 높음(6.0+) + 중간(50-100) → Replatform (위험 높음)
    복잡도 높음(6.0+) + 적음(50-)   → PostgreSQL (신중한 변환)

    복잡도 중간(3.5-6.0) + 많음(100+)  → PostgreSQL (변환 가능)
    복잡도 중간(3.5-6.0) + 중간(50-100) → PostgreSQL (적합)
    복잡도 중간(3.5-6.0) + 적음(50-)   → PostgreSQL (권장)

    복잡도 낮음(3.5-) + 많음(100+)  → PostgreSQL (변환 용이하나 작업량 많음)
    복잡도 낮음(3.5-) + 중간(20-100) → PostgreSQL 또는 MySQL (기술적 근거 기반)
    복잡도 낮음(3.5-) + 적음(20-)   → MySQL (강력 추천, 단 PostgreSQL 친화 기능 없을 때)
    
    PostgreSQL vs MySQL 선택 기준 (기술적 근거):
    - CTE (WITH 절) 3개 이상 → PostgreSQL (MySQL 8.0 이전 미지원, 8.0 이후도 제한적)
    - 분석 함수(윈도우 함수) 5개 이상 → PostgreSQL (더 다양한 기능 지원)
    - BULK 연산 10개 이상 → PostgreSQL (ARRAY로 대체 가능, MySQL 미지원)
    - 복잡한 트랜잭션 제어 → PostgreSQL (SAVEPOINT, 중첩 트랜잭션 등)
    - 외부 패키지 의존성 → PostgreSQL (DBMS_LOB, UTL_FILE 등 대안 제공)
    - 고급 기능 (PIPELINED, REF CURSOR 등) → PostgreSQL (더 높은 호환성)
    """

    # 임계값 상수 (AI 시대 기준 상향 조정)
    # Replatform 조건
    REPLATFORM_SQL_COMPLEXITY = 7.5  # AI 도움으로 복잡한 SQL도 변환 용이
    REPLATFORM_PLSQL_COMPLEXITY = 7.0  # 애플리케이션 레벨 이관 공수 감소
    REPLATFORM_HIGH_COMPLEXITY_RATIO = 0.25  # 고난이도 비율 25% 이상
    REPLATFORM_HIGH_COMPLEXITY_RATIO_MIN_COUNT = 70  # 비율 조건 적용 최소 모수
    REPLATFORM_HIGH_COMPLEXITY_COUNT = 50  # 고난이도 오브젝트 절대 개수
    REPLATFORM_LARGE_PLSQL_COUNT = 500  # PL/SQL 오브젝트 개수 조건
    REPLATFORM_LARGE_CODEBASE_LINES = 200000  # 대규모 코드베이스 기준 (20만줄)
    REPLATFORM_LARGE_CODEBASE_COMPLEXITY = 7.5  # 대규모 코드베이스 복잡도 기준

    # MySQL 조건
    MYSQL_PLSQL_COMPLEXITY = 3.5  # 기존 5.0 → 3.5
    MYSQL_SQL_COMPLEXITY = 4.0  # 기존 5.0 → 4.0
    MYSQL_PLSQL_COUNT = 20  # 기존 50 → 20

    # PostgreSQL 선호 조건 (기술적 근거 기반)
    POSTGRESQL_CTE_THRESHOLD = 3  # CTE 3개 이상이면 PostgreSQL 선호
    POSTGRESQL_ANALYTIC_THRESHOLD = 5  # 분석 함수 5개 이상이면 PostgreSQL 선호
    POSTGRESQL_BULK_THRESHOLD = 10  # BULK 연산 10개 이상이면 PostgreSQL 필수
    
    # PostgreSQL 선호 외부 패키지 (MySQL에서 대안 제공 어려움)
    POSTGRESQL_PREFERRED_PACKAGES = {
        'DBMS_LOB',  # PostgreSQL: Large Object 지원
        'UTL_FILE',  # PostgreSQL: pg_read_file, COPY 등
        'DBMS_CRYPTO',  # PostgreSQL: pgcrypto 확장
        'DBMS_SQL',  # PostgreSQL: EXECUTE 동적 SQL
        'DBMS_XMLGEN',  # PostgreSQL: XML 함수 지원
        'DBMS_XMLPARSER',  # PostgreSQL: XML 파싱 지원
        'DBMS_AQ',  # PostgreSQL: pg_notify, LISTEN/NOTIFY
    }
    
    # PostgreSQL 선호 고급 기능
    POSTGRESQL_PREFERRED_FEATURES = {
        'PIPELINED',  # PostgreSQL: RETURNS SETOF로 대체
        'REF CURSOR',  # PostgreSQL: REFCURSOR 지원
        'OBJECT TYPE',  # PostgreSQL: 복합 타입 지원
        'VARRAY',  # PostgreSQL: ARRAY 타입
        'NESTED TABLE',  # PostgreSQL: ARRAY 타입
    }
    
    def __init__(self):
        """의사결정 엔진 초기화"""
        self._replatform_reasons: List[str] = []
        self._postgresql_preference_reasons: List[str] = []

    def decide_strategy(self, integrated_result: IntegratedAnalysisResult) -> MigrationStrategy:
        """
        최적의 마이그레이션 전략을 결정합니다.

        의사결정 로직:
        1. PL/SQL 개수와 복잡도를 2차원으로 평가
        2. 복잡도가 높고 개수가 많으면 → Replatform
        3. PostgreSQL 친화적 기능 사용 시 → PostgreSQL
        4. 복잡도가 낮고 개수가 적고 PostgreSQL 친화 기능 없으면 → MySQL
        5. 그 외 → PostgreSQL (기본값)

        Args:
            integrated_result: 통합 분석 결과

        Returns:
            MigrationStrategy: 추천 전략
        """
        # 이유 초기화
        self._replatform_reasons = []
        self._postgresql_preference_reasons = []
        
        metrics = integrated_result.metrics

        # PL/SQL 개수 (AWR 통계 우선, 없으면 분석 파일 개수)
        plsql_count = self._get_plsql_count(metrics)
        plsql_complexity = metrics.avg_plsql_complexity

        # 1. Replatform 조건: 복잡도 높음 + 개수 많음
        if self._should_replatform(metrics, plsql_count, plsql_complexity):
            return MigrationStrategy.REPLATFORM

        # 2. PostgreSQL 선호 조건 확인 (기술적 근거 기반)
        postgresql_score = self._calculate_postgresql_preference_score(metrics)
        
        # 3. MySQL 조건: 복잡도 낮음 + 개수 적음 + PostgreSQL 선호 이유 없음
        if self._should_refactor_mysql(metrics, plsql_count, plsql_complexity, postgresql_score):
            return MigrationStrategy.REFACTOR_MYSQL

        # 4. 기본값: PostgreSQL (중간 영역 또는 PostgreSQL 친화적 기능 사용)
        return MigrationStrategy.REFACTOR_POSTGRESQL
    
    def get_replatform_reasons(self) -> List[str]:
        """
        Replatform 선택 이유 목록 반환
        
        decide_strategy() 호출 후에 사용해야 합니다.
        
        Returns:
            List[str]: Replatform 선택 이유 코드 목록
        """
        return self._replatform_reasons.copy()
    
    def get_replatform_reasons_text(self, language: str = "ko") -> List[str]:
        """
        Replatform 선택 이유를 텍스트로 반환
        
        Args:
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            List[str]: Replatform 선택 이유 텍스트 목록
        """
        descriptions = (
            ReplatformReason.DESCRIPTIONS_KO if language == "ko" 
            else ReplatformReason.DESCRIPTIONS_EN
        )
        return [descriptions.get(reason, reason) for reason in self._replatform_reasons]
    
    def get_postgresql_preference_reasons(self) -> List[str]:
        """
        PostgreSQL 선호 이유 목록 반환
        
        decide_strategy() 호출 후에 사용해야 합니다.
        
        Returns:
            List[str]: PostgreSQL 선호 이유 코드 목록
        """
        return self._postgresql_preference_reasons.copy()
    
    def get_postgresql_preference_reasons_text(self, language: str = "ko") -> List[str]:
        """
        PostgreSQL 선호 이유를 텍스트로 반환
        
        Args:
            language: 언어 ("ko" 또는 "en")
            
        Returns:
            List[str]: PostgreSQL 선호 이유 텍스트 목록
        """
        descriptions = (
            PostgreSQLPreferenceReason.DESCRIPTIONS_KO if language == "ko" 
            else PostgreSQLPreferenceReason.DESCRIPTIONS_EN
        )
        return [descriptions.get(reason, reason) for reason in self._postgresql_preference_reasons]
    
    def _calculate_postgresql_preference_score(self, metrics: AnalysisMetrics) -> int:
        """
        PostgreSQL 선호 점수 계산 (기술적 근거 기반)
        
        각 조건에 해당하면 점수를 부여하고, 총점이 높을수록 PostgreSQL 선호
        
        Args:
            metrics: 분석 메트릭
            
        Returns:
            int: PostgreSQL 선호 점수 (0 이상)
        """
        score = 0
        
        # 1. BULK 연산 (필수 조건 - MySQL 미지원)
        if metrics.bulk_operation_count >= self.POSTGRESQL_BULK_THRESHOLD:
            score += 3  # 높은 가중치
            self._postgresql_preference_reasons.append(PostgreSQLPreferenceReason.BULK_OPERATIONS)
        
        # 2. Oracle 특화 기능 분석 (detected_oracle_features_summary 활용)
        oracle_features = metrics.detected_oracle_features_summary or {}
        
        # CTE 사용 여부 (Oracle 특화 기능에서 확인)
        # 참고: SQL 분석 결과에서 CTE 개수를 직접 가져올 수 없으므로
        # 복잡도가 중간 이상이면 CTE 사용 가능성 높음으로 간주
        if metrics.avg_sql_complexity >= 3.5:
            score += 1
            if PostgreSQLPreferenceReason.MEDIUM_COMPLEXITY not in self._postgresql_preference_reasons:
                self._postgresql_preference_reasons.append(PostgreSQLPreferenceReason.MEDIUM_COMPLEXITY)
        
        # 3. 고급 기능 사용 여부
        advanced_features_count = 0
        for feature in self.POSTGRESQL_PREFERRED_FEATURES:
            if feature in oracle_features:
                advanced_features_count += oracle_features[feature]
        
        if advanced_features_count > 0:
            score += 2
            self._postgresql_preference_reasons.append(PostgreSQLPreferenceReason.ADVANCED_FEATURES)
        
        # 4. 외부 패키지 의존성
        external_deps = metrics.detected_external_dependencies_summary or {}
        postgresql_preferred_deps_count = 0
        for dep in self.POSTGRESQL_PREFERRED_PACKAGES:
            if dep in external_deps:
                postgresql_preferred_deps_count += external_deps[dep]
        
        if postgresql_preferred_deps_count > 0:
            score += 2
            self._postgresql_preference_reasons.append(PostgreSQLPreferenceReason.EXTERNAL_DEPENDENCIES)
        
        # 5. 분석 함수 사용 (복잡도 기반 추정)
        # 복잡도가 높을수록 분석 함수 사용 가능성 높음
        if metrics.avg_sql_complexity >= 4.5:
            score += 1
            if PostgreSQLPreferenceReason.ANALYTIC_FUNCTIONS not in self._postgresql_preference_reasons:
                self._postgresql_preference_reasons.append(PostgreSQLPreferenceReason.ANALYTIC_FUNCTIONS)
        
        return score

    def _assess_migration_difficulty(self, metrics: AnalysisMetrics) -> str:
        """
        PL/SQL 라인 수 기반 마이그레이션 난이도 평가

        난이도 기준:
        - 낮음: ~20,000줄 (3~6개월)
        - 중간: 20,000~50,000줄 (6~12개월)
        - 높음: 50,000~100,000줄 (12~18개월)
        - 매우 높음: 100,000줄 이상 (18개월 이상)

        Args:
            metrics: 분석 메트릭

        Returns:
            str: 난이도 레벨 (low, medium, high, very_high)
        """
        plsql_lines = metrics.awr_plsql_lines or 0
        if isinstance(plsql_lines, str):
            plsql_lines = self._extract_number(plsql_lines)

        if plsql_lines == 0:
            # AWR 데이터 없으면 분석 파일 기반 추정
            # 평균 파일당 200줄로 가정
            plsql_lines = metrics.total_plsql_count * 200

        if plsql_lines < 20000:
            return "low"
        elif plsql_lines < 50000:
            return "medium"
        elif plsql_lines < 100000:
            return "high"
        else:
            return "very_high"

    def _get_plsql_count(self, metrics: AnalysisMetrics) -> int:
        """
        PL/SQL 오브젝트 개수 계산

        AWR 통계가 있으면 우선 사용, 없으면 분석 파일 개수 사용

        Args:
            metrics: 분석 메트릭

        Returns:
            int: PL/SQL 오브젝트 개수
        """
        # AWR 통계 우선 (프로시저 + 함수 + 패키지)
        if any(
            [metrics.awr_procedure_count, metrics.awr_function_count, metrics.awr_package_count]
        ):
            count = 0
            if metrics.awr_procedure_count:
                count += self._extract_number(metrics.awr_procedure_count)
            if metrics.awr_function_count:
                count += self._extract_number(metrics.awr_function_count)
            if metrics.awr_package_count:
                count += self._extract_number(metrics.awr_package_count)
            return count

        # AWR 통계 없으면 분석 파일 개수
        return metrics.total_plsql_count

    def _extract_number(self, value) -> int:
        """
        문자열이나 숫자에서 숫자 값 추출

        Args:
            value: 숫자 또는 문자열 (예: 318, "318", "BODY 318")

        Returns:
            int: 추출된 숫자
        """
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            # 문자열에서 숫자만 추출 (예: "BODY 318" -> 318)
            import re

            numbers = re.findall(r"\d+", value)
            if numbers:
                return int(numbers[-1])  # 마지막 숫자 사용
        return 0

    def _should_replatform(
        self, metrics: AnalysisMetrics, plsql_count: int, plsql_complexity: float
    ) -> bool:
        """
        Replatform 조건 확인 (AI 시대 기준 상향 조정)

        조건 (OR 관계):
        1. SQL 복잡도 매우 높음 (평균 7.5 이상)
        2. PL/SQL 복잡도 매우 높음 (평균 7.0 이상)
        3. 복잡 오브젝트 비율 25% 이상 (모수 70개 이상일 때만)
        4. 복잡 오브젝트 절대 개수 50개 이상
        5. 대규모 코드베이스 + 높은 복잡도 (20만줄 이상 + 복잡도 7.5 이상)
        6. PL/SQL 오브젝트 개수 500개 이상

        Args:
            metrics: 분석 메트릭
            plsql_count: PL/SQL 오브젝트 개수
            plsql_complexity: PL/SQL 평균 복잡도

        Returns:
            bool: Replatform 조건 만족 여부
        """
        should_replatform = False

        # 1. SQL 복잡도 매우 높음 (변환 거의 불가능)
        if metrics.avg_sql_complexity >= self.REPLATFORM_SQL_COMPLEXITY:
            self._replatform_reasons.append(ReplatformReason.HIGH_SQL_COMPLEXITY)
            should_replatform = True

        # 2. PL/SQL 복잡도 매우 높음 (변환 거의 불가능)
        if plsql_complexity >= self.REPLATFORM_PLSQL_COMPLEXITY:
            self._replatform_reasons.append(ReplatformReason.HIGH_PLSQL_COMPLEXITY)
            should_replatform = True

        # 3. 복잡 오브젝트 비율 매우 높음 (모수 70개 이상일 때만 의미 있음)
        total_objects = metrics.total_sql_count + metrics.total_plsql_count
        if (total_objects >= self.REPLATFORM_HIGH_COMPLEXITY_RATIO_MIN_COUNT and
            metrics.high_complexity_ratio >= self.REPLATFORM_HIGH_COMPLEXITY_RATIO):
            self._replatform_reasons.append(ReplatformReason.HIGH_COMPLEXITY_RATIO)
            should_replatform = True

        # 4. 복잡 오브젝트 절대 개수 50개 이상
        high_count = (metrics.high_complexity_sql_count or 0) + (metrics.high_complexity_plsql_count or 0)
        if high_count >= self.REPLATFORM_HIGH_COMPLEXITY_COUNT:
            self._replatform_reasons.append(ReplatformReason.HIGH_COMPLEXITY_COUNT)
            should_replatform = True

        # 5. 대규모 코드베이스 + 높은 복잡도 (20만줄 이상 + 복잡도 7.5 이상)
        plsql_lines = metrics.awr_plsql_lines or 0
        if isinstance(plsql_lines, str):
            plsql_lines = self._extract_number(plsql_lines)
        if (plsql_lines >= self.REPLATFORM_LARGE_CODEBASE_LINES and 
            plsql_complexity >= self.REPLATFORM_LARGE_CODEBASE_COMPLEXITY):
            self._replatform_reasons.append(ReplatformReason.LARGE_CODEBASE_HIGH_COMPLEXITY)
            should_replatform = True
        
        # 6. PL/SQL 오브젝트 개수 500개 이상
        if plsql_count >= self.REPLATFORM_LARGE_PLSQL_COUNT:
            self._replatform_reasons.append(ReplatformReason.LARGE_PLSQL_COUNT)
            should_replatform = True

        return should_replatform
    
    def _should_refactor_mysql(
        self, metrics: AnalysisMetrics, plsql_count: int, plsql_complexity: float,
        postgresql_score: int
    ) -> bool:
        """
        Aurora MySQL 조건 확인 (개선된 임계값 + 기술적 근거 적용)

        조건 (AND 관계):
        1. PL/SQL 복잡도 낮음 (평균 3.5 이하) - 기존 5.0에서 하향
        2. SQL 복잡도 낮음 (평균 4.0 이하) - 기존 5.0에서 하향
        3. 개수 적음 (20개 미만) - 기존 50개에서 하향
        4. PostgreSQL 선호 점수 낮음 (2점 미만) - 신규 추가
        5. BULK 연산 적음 (10개 미만) - 유지

        참고: THRESHOLD_IMPROVEMENT_PROPOSAL.md
        - MySQL Stored Procedure는 권장하지 않음
        - 복잡도 3.5 이상에서 애플리케이션 이관 비용 급증
        - 20개 이상 이관 시 전담 팀 필요
        
        PostgreSQL 선호 점수가 2점 이상이면 MySQL 대신 PostgreSQL 선택:
        - CTE, 분석 함수, BULK 연산, 외부 패키지 등 사용 시

        Args:
            metrics: 분석 메트릭
            plsql_count: PL/SQL 오브젝트 개수
            plsql_complexity: PL/SQL 평균 복잡도
            postgresql_score: PostgreSQL 선호 점수

        Returns:
            bool: Aurora MySQL 조건 만족 여부
        """
        # 1. PL/SQL 복잡도 낮음 (애플리케이션 이관 비용 고려)
        if plsql_complexity > self.MYSQL_PLSQL_COMPLEXITY:
            return False

        # 2. SQL 복잡도 낮음 (MySQL 호환성 고려)
        if metrics.avg_sql_complexity > self.MYSQL_SQL_COMPLEXITY:
            return False

        # 3. 개수 적음 (이관 작업량 고려)
        if plsql_count >= self.MYSQL_PLSQL_COUNT:
            return False

        # 4. PostgreSQL 선호 점수 낮음 (기술적 근거 기반)
        # 점수가 2점 이상이면 PostgreSQL이 더 적합
        if postgresql_score >= 2:
            return False

        # 5. BULK 연산 적음 (MySQL 미지원)
        if metrics.bulk_operation_count >= self.POSTGRESQL_BULK_THRESHOLD:
            return False

        return True
