"""
마이그레이션 의사결정 엔진

Oracle 데이터베이스의 AWS 클라우드 마이그레이션 시 최적의 전략을 결정합니다.
"""

from typing import Optional, List, Tuple
from .data_models import IntegratedAnalysisResult, AnalysisMetrics, MigrationStrategy


class ReplatformReason:
    """Replatform 선택 이유를 나타내는 클래스"""
    
    # 이유 코드 상수
    HIGH_SQL_COMPLEXITY = "high_sql_complexity"
    HIGH_PLSQL_COMPLEXITY = "high_plsql_complexity"
    HIGH_COMPLEXITY_RATIO = "high_complexity_ratio"
    HIGH_COMPLEXITY_COUNT = "high_complexity_count"
    VERY_HIGH_DIFFICULTY = "very_high_difficulty"
    LARGE_PLSQL_COUNT = "large_plsql_count"
    
    # 이유별 설명 (한국어)
    DESCRIPTIONS_KO = {
        HIGH_SQL_COMPLEXITY: "SQL 평균 복잡도가 매우 높음 (6.0 이상)",
        HIGH_PLSQL_COMPLEXITY: "PL/SQL 평균 복잡도가 매우 높음 (6.0 이상)",
        HIGH_COMPLEXITY_RATIO: "고난이도 오브젝트 비율이 높음 (25% 이상)",
        HIGH_COMPLEXITY_COUNT: "고난이도 오브젝트 절대 개수가 많음 (20개 이상)",
        VERY_HIGH_DIFFICULTY: "코드량이 매우 많고 복잡도가 높음 (10만줄 이상)",
        LARGE_PLSQL_COUNT: "PL/SQL 오브젝트 개수가 매우 많음 (500개 이상)",
    }
    
    # 이유별 설명 (영어)
    DESCRIPTIONS_EN = {
        HIGH_SQL_COMPLEXITY: "Very high SQL average complexity (≥6.0)",
        HIGH_PLSQL_COMPLEXITY: "Very high PL/SQL average complexity (≥6.0)",
        HIGH_COMPLEXITY_RATIO: "High ratio of complex objects (≥25%)",
        HIGH_COMPLEXITY_COUNT: "Large number of complex objects (≥20)",
        VERY_HIGH_DIFFICULTY: "Very large codebase with high complexity (≥100K lines)",
        LARGE_PLSQL_COUNT: "Very large number of PL/SQL objects (≥500)",
    }


class MigrationDecisionEngine:
    """
    마이그레이션 의사결정 엔진

    PL/SQL 개수와 복잡도를 2차원으로 고려하여 최적의 전략을 결정합니다.

    의사결정 매트릭스 (PL/SQL 개수 x 복잡도):

    복잡도 높음(6.0+) + 많음(100+)  → Replatform (변환 불가능)
    복잡도 높음(6.0+) + 중간(50-100) → Replatform (위험 높음)
    복잡도 높음(6.0+) + 적음(50-)   → PostgreSQL (신중한 변환)

    복잡도 중간(3.5-6.0) + 많음(100+)  → PostgreSQL (변환 가능)
    복잡도 중간(3.5-6.0) + 중간(50-100) → PostgreSQL (적합)
    복잡도 중간(3.5-6.0) + 적음(50-)   → PostgreSQL (권장)

    복잡도 낮음(3.5-) + 많음(100+)  → PostgreSQL (변환 용이하나 작업량 많음)
    복잡도 낮음(3.5-) + 중간(20-100) → PostgreSQL 또는 MySQL
    복잡도 낮음(3.5-) + 적음(20-)   → MySQL (강력 추천)
    """

    # 임계값 상수 (THRESHOLD_IMPROVEMENT_PROPOSAL.md 기반)
    # Replatform 조건
    REPLATFORM_SQL_COMPLEXITY = 6.0  # 기존 7.0 → 6.0
    REPLATFORM_PLSQL_COMPLEXITY = 6.0  # 기존 7.0 → 6.0
    REPLATFORM_HIGH_COMPLEXITY_RATIO = 0.25  # 기존 0.30 → 0.25
    REPLATFORM_HIGH_COMPLEXITY_COUNT = 20  # 신규: 절대 개수 조건
    REPLATFORM_LARGE_PLSQL_COUNT = 500  # 신규: PL/SQL 오브젝트 개수 조건
    REPLATFORM_HIGH_DIFFICULTY_SCORE = 6  # 신규: 난이도 점수 조건

    # MySQL 조건
    MYSQL_PLSQL_COMPLEXITY = 3.5  # 기존 5.0 → 3.5
    MYSQL_SQL_COMPLEXITY = 4.0  # 기존 5.0 → 4.0
    MYSQL_PLSQL_COUNT = 20  # 기존 50 → 20

    # 공통 조건
    BULK_OPERATION_THRESHOLD = 10  # 유지
    
    def __init__(self):
        """의사결정 엔진 초기화"""
        self._replatform_reasons: List[str] = []

    def decide_strategy(self, integrated_result: IntegratedAnalysisResult) -> MigrationStrategy:
        """
        최적의 마이그레이션 전략을 결정합니다.

        의사결정 로직:
        1. PL/SQL 개수와 복잡도를 2차원으로 평가
        2. 복잡도가 높고 개수가 많으면 → Replatform
        3. 복잡도가 낮고 개수가 적으면 → MySQL (강력 추천)
        4. 중간 영역 → PostgreSQL
        5. BULK 연산이 많으면 PostgreSQL 우선

        Args:
            integrated_result: 통합 분석 결과

        Returns:
            MigrationStrategy: 추천 전략
        """
        # Replatform 이유 초기화
        self._replatform_reasons = []
        
        metrics = integrated_result.metrics

        # PL/SQL 개수 (AWR 통계 우선, 없으면 분석 파일 개수)
        plsql_count = self._get_plsql_count(metrics)
        plsql_complexity = metrics.avg_plsql_complexity

        # 1. Replatform 조건: 복잡도 높음 + 개수 많음
        if self._should_replatform(metrics, plsql_count, plsql_complexity):
            return MigrationStrategy.REPLATFORM

        # 2. BULK 연산이 많으면 PostgreSQL 우선 (MySQL은 BULK 미지원)
        if metrics.bulk_operation_count >= self.BULK_OPERATION_THRESHOLD:
            return MigrationStrategy.REFACTOR_POSTGRESQL

        # 3. MySQL 조건: 복잡도 낮음 + 개수 적음
        if self._should_refactor_mysql(metrics, plsql_count, plsql_complexity):
            return MigrationStrategy.REFACTOR_MYSQL

        # 4. 기본값: PostgreSQL (중간 영역)
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
        Replatform 조건 확인 (개선된 임계값 적용)

        조건 (OR 관계):
        1. SQL 복잡도 매우 높음 (평균 6.0 이상) - 기존 7.0에서 하향
        2. PL/SQL 복잡도 매우 높음 (평균 6.0 이상) - 기존 7.0에서 하향
        3. 복잡 오브젝트 비율 25% 이상 - 기존 30%에서 하향
        4. 복잡 오브젝트 절대 개수 20개 이상 - 신규 추가
        5. 난이도 매우 높음 (100,000줄 이상) + 복잡도 높음 (6.0 이상)
        6. PL/SQL 오브젝트 개수 500개 이상 - 신규 추가
        7. 리팩토링 난이도 점수 6점 이상 - 신규 추가

        참고: THRESHOLD_IMPROVEMENT_PROPOSAL.md
        - 코드 라인 수 기반 조건 제거 (의사결정 자율성 보장)

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

        # 3. 복잡 오브젝트 비율 매우 높음
        if metrics.high_complexity_ratio >= self.REPLATFORM_HIGH_COMPLEXITY_RATIO:
            self._replatform_reasons.append(ReplatformReason.HIGH_COMPLEXITY_RATIO)
            should_replatform = True

        # 4. 복잡 오브젝트 절대 개수 (신규 조건)
        # 대규모 시스템에서 비율만으로는 위험 과소평가 방지
        high_count = metrics.high_complexity_sql_count + metrics.high_complexity_plsql_count
        if high_count >= self.REPLATFORM_HIGH_COMPLEXITY_COUNT:
            self._replatform_reasons.append(ReplatformReason.HIGH_COMPLEXITY_COUNT)
            should_replatform = True

        # 5. 난이도 매우 높음 + 복잡도 높음
        difficulty = self._assess_migration_difficulty(metrics)
        if difficulty == "very_high" and plsql_complexity >= self.REPLATFORM_PLSQL_COMPLEXITY:
            self._replatform_reasons.append(ReplatformReason.VERY_HIGH_DIFFICULTY)
            should_replatform = True
        
        # 6. PL/SQL 오브젝트 개수 매우 많음 (신규 조건)
        # 500개 이상이면 리팩토링 작업량이 너무 많음
        if plsql_count >= self.REPLATFORM_LARGE_PLSQL_COUNT:
            self._replatform_reasons.append(ReplatformReason.LARGE_PLSQL_COUNT)
            should_replatform = True
        
        # 7. 리팩토링 난이도 점수 기반 (신규 조건)
        # 난이도 점수가 높으면 리팩토링보다 Replatform이 적합
        difficulty_score = self._calculate_difficulty_score(metrics)
        if difficulty_score >= self.REPLATFORM_HIGH_DIFFICULTY_SCORE:
            # 이미 다른 이유가 없는 경우에만 추가 (중복 방지)
            if not should_replatform:
                self._replatform_reasons.append(ReplatformReason.HIGH_COMPLEXITY_COUNT)
                should_replatform = True

        return should_replatform
    
    def _calculate_difficulty_score(self, metrics: AnalysisMetrics) -> int:
        """
        리팩토링 난이도 점수 계산
        
        rationale.py의 _calculate_final_difficulty와 동일한 로직
        
        Args:
            metrics: 분석 메트릭
            
        Returns:
            int: 난이도 점수 (0~13)
        """
        score = 0
        
        # PL/SQL 복잡도 기반 (0~3점)
        if metrics.avg_plsql_complexity:
            if metrics.avg_plsql_complexity >= 7.0:
                score += 3
            elif metrics.avg_plsql_complexity >= 5.0:
                score += 2
            elif metrics.avg_plsql_complexity >= 3.0:
                score += 1
        
        # PL/SQL 코드량 기반 (0~3점)
        plsql_lines = metrics.awr_plsql_lines or 0
        if isinstance(plsql_lines, str):
            plsql_lines = self._extract_number(plsql_lines)
        if plsql_lines >= 100000:
            score += 3
        elif plsql_lines >= 50000:
            score += 2
        elif plsql_lines >= 10000:
            score += 1
        
        # 고난이도 오브젝트 비율 기반 (0~2점)
        if metrics.high_complexity_plsql_count is not None and metrics.total_plsql_count:
            ratio = metrics.high_complexity_plsql_count / metrics.total_plsql_count
            if ratio >= 0.3:
                score += 2
            elif ratio >= 0.1:
                score += 1
        
        # 고난이도 오브젝트 절대 개수 기반 (0~3점)
        high_count = (metrics.high_complexity_plsql_count or 0) + (metrics.high_complexity_sql_count or 0)
        if high_count >= 100:
            score += 3
        elif high_count >= 50:
            score += 2
        elif high_count >= 20:
            score += 1
        
        # 패키지 개수 기반 (0~2점)
        if metrics.awr_package_count:
            if metrics.awr_package_count >= 100:
                score += 2
            elif metrics.awr_package_count >= 50:
                score += 1
        
        return score

    def _should_refactor_mysql(
        self, metrics: AnalysisMetrics, plsql_count: int, plsql_complexity: float
    ) -> bool:
        """
        Aurora MySQL 조건 확인 (개선된 임계값 적용)

        조건 (AND 관계):
        1. PL/SQL 복잡도 낮음 (평균 3.5 이하) - 기존 5.0에서 하향
        2. SQL 복잡도 낮음 (평균 4.0 이하) - 기존 5.0에서 하향
        3. 개수 적음 (20개 미만) - 기존 50개에서 하향
        4. BULK 연산 적음 (10개 미만) - 유지

        참고: THRESHOLD_IMPROVEMENT_PROPOSAL.md
        - MySQL Stored Procedure는 권장하지 않음
        - 복잡도 3.5 이상에서 애플리케이션 이관 비용 급증
        - 20개 이상 이관 시 전담 팀 필요

        Args:
            metrics: 분석 메트릭
            plsql_count: PL/SQL 오브젝트 개수
            plsql_complexity: PL/SQL 평균 복잡도

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

        # 4. BULK 연산 적음 (MySQL 미지원)
        if metrics.bulk_operation_count >= self.BULK_OPERATION_THRESHOLD:
            return False

        return True
