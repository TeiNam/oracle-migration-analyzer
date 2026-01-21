"""
근거 생성기

마이그레이션 추천 근거를 생성합니다.
"""

import logging
from typing import List
from ..data_models import AnalysisMetrics, MigrationStrategy, Rationale

# 로거 초기화
logger = logging.getLogger(__name__)


class RationaleGenerator:
    """
    근거 생성기
    
    전략별로 성능/복잡도/비용/운영 카테고리의 근거를 생성합니다.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    def generate_rationales(
        self,
        strategy: MigrationStrategy,
        metrics: AnalysisMetrics
    ) -> List[Rationale]:
        """
        추천 근거 생성 (3-5개)
        
        전략별로 성능/복잡도/비용/운영 카테고리의 근거를 생성합니다.
        
        Args:
            strategy: 추천 전략
            metrics: 분석 메트릭
            
        Returns:
            List[Rationale]: 추천 근거 리스트 (3-5개)
        """
        if strategy == MigrationStrategy.REPLATFORM:
            return self._generate_replatform_rationales(metrics)
        elif strategy == MigrationStrategy.REFACTOR_MYSQL:
            return self._generate_mysql_rationales(metrics)
        else:  # REFACTOR_POSTGRESQL
            return self._generate_postgresql_rationales(metrics)
    
    def _generate_replatform_rationales(self, metrics: AnalysisMetrics) -> List[Rationale]:
        """Replatform 전략 근거 생성"""
        rationales = []
        
        # PL/SQL 개수 계산 (AWR 우선)
        plsql_count = self._get_plsql_count(metrics)
        
        # PL/SQL 라인 수 계산
        plsql_lines = metrics.awr_plsql_lines or 0
        if isinstance(plsql_lines, str):
            plsql_lines = self._extract_number(plsql_lines)
        if plsql_lines == 0:
            plsql_lines = metrics.total_plsql_count * 200
        
        # 1. 코드 규모 및 작업 복잡도 근거 (5만 줄 이상 + 복잡도 중간 이하)
        if plsql_lines >= 50000 and metrics.avg_plsql_complexity < 7.0:
            # 코드 규모 분류
            if plsql_lines >= 100000:
                scale_text = "대규모"
                refactor_scope = "매우 광범위한"
            elif plsql_lines >= 70000:
                scale_text = "중대규모"
                refactor_scope = "광범위한"
            else:
                scale_text = "중규모"
                refactor_scope = "상당한"
            
            rationales.append(Rationale(
                category="cost",
                reason=f"**PL/SQL 코드 {plsql_lines:,}줄({scale_text})을 Refactor하려면 {refactor_scope} 코드 변환 작업이 필요하며, 변환 과정에서 예상치 못한 이슈 발생 가능성이 높습니다.** 반면 Replatform은 EE 전용 기능(전체의 5-10% 추정)만 검토하면 되므로 작업 범위가 훨씬 제한적이고 위험도가 낮습니다. 대부분의 코드는 변경 없이 그대로 사용 가능합니다.",
                supporting_data={
                    "plsql_lines": plsql_lines,
                    "scale": scale_text,
                    "refactor_scope": refactor_scope,
                    "avg_complexity": metrics.avg_plsql_complexity,
                    "ee_feature_ratio": "5-10%",
                    "refactor_risks": [
                        "코드 변환 중 비즈니스 로직 변경 위험",
                        "의존성 관계 파악 및 관리 복잡도",
                        "변환 후 성능 저하 가능성",
                        "광범위한 회귀 테스트 필요"
                    ],
                    "replatform_advantages": [
                        "코드 변경 최소화로 비즈니스 로직 안정성 유지",
                        "EE 전용 기능만 선별적으로 검토",
                        "기존 성능 특성 유지",
                        "제한적인 테스트 범위"
                    ],
                    "reference": "AWS Database Migration Best Practices"
                }
            ))
        
        # 2. 코드 복잡도 + 개수 근거 (복잡도 레벨 텍스트 추가)
        complexity_level_sql = self._get_complexity_level_text(metrics.avg_sql_complexity)
        complexity_level_plsql = self._get_complexity_level_text(metrics.avg_plsql_complexity)
        
        if metrics.avg_sql_complexity >= 7.0 or metrics.avg_plsql_complexity >= 7.0:
            if plsql_count >= 100:
                rationales.append(Rationale(
                    category="complexity",
                    reason=f"현재 시스템의 평균 코드 복잡도는 SQL {metrics.avg_sql_complexity:.1f}({complexity_level_sql}), PL/SQL {metrics.avg_plsql_complexity:.1f}({complexity_level_plsql}) 수준입니다. PL/SQL 오브젝트가 {plsql_count}개로 매우 많아 코드 안정성을 위해 Refactor보다는 Replatform을 권장하며, 전환 작업에 드는 리소스가 많아 단기간 전환이 어려울 것으로 판단됩니다",
                    supporting_data={
                        "avg_sql_complexity": metrics.avg_sql_complexity,
                        "avg_plsql_complexity": metrics.avg_plsql_complexity,
                        "plsql_count": plsql_count,
                        "complexity_level_sql": complexity_level_sql,
                        "complexity_level_plsql": complexity_level_plsql
                    }
                ))
            elif plsql_count >= 50:
                rationales.append(Rationale(
                    category="complexity",
                    reason=f"현재 시스템의 평균 코드 복잡도는 SQL {metrics.avg_sql_complexity:.1f}({complexity_level_sql}), PL/SQL {metrics.avg_plsql_complexity:.1f}({complexity_level_plsql}) 수준입니다. PL/SQL 오브젝트가 {plsql_count}개로 많아 코드 안정성을 위해 Replatform을 권장하며, 변환 작업의 리스크가 높습니다",
                    supporting_data={
                        "avg_sql_complexity": metrics.avg_sql_complexity,
                        "avg_plsql_complexity": metrics.avg_plsql_complexity,
                        "plsql_count": plsql_count,
                        "complexity_level_sql": complexity_level_sql,
                        "complexity_level_plsql": complexity_level_plsql
                    }
                ))
            else:
                rationales.append(Rationale(
                    category="complexity",
                    reason=f"현재 시스템의 평균 코드 복잡도는 SQL {metrics.avg_sql_complexity:.1f}({complexity_level_sql}), PL/SQL {metrics.avg_plsql_complexity:.1f}({complexity_level_plsql}) 수준으로, 대규모 코드 변경 시 안정성 리스크가 있어 Replatform을 권장합니다",
                    supporting_data={
                        "avg_sql_complexity": metrics.avg_sql_complexity,
                        "avg_plsql_complexity": metrics.avg_plsql_complexity,
                        "complexity_level_sql": complexity_level_sql,
                        "complexity_level_plsql": complexity_level_plsql
                    }
                ))
        elif plsql_count >= 100:
            # 복잡도는 낮지만 개수가 많은 경우
            rationales.append(Rationale(
                category="complexity",
                reason=f"현재 시스템의 평균 코드 복잡도는 SQL {metrics.avg_sql_complexity:.1f}({complexity_level_sql}), PL/SQL {metrics.avg_plsql_complexity:.1f}({complexity_level_plsql}) 수준입니다. 하지만 PL/SQL 오브젝트가 {plsql_count}개로 매우 많아 코드 안정성을 위해 Refactor보다는 Replatform을 권장하며, 전환 작업에 드는 리소스가 많아 단기간 전환이 어려울 것으로 판단됩니다",
                supporting_data={
                    "avg_sql_complexity": metrics.avg_sql_complexity,
                    "avg_plsql_complexity": metrics.avg_plsql_complexity,
                    "plsql_count": plsql_count,
                    "complexity_level_sql": complexity_level_sql,
                    "complexity_level_plsql": complexity_level_plsql
                }
            ))
        
        # 3. 복잡 오브젝트 비율 근거
        if metrics.high_complexity_ratio >= 0.3:
            rationales.append(Rationale(
                category="complexity",
                reason=f"전체 오브젝트의 {metrics.high_complexity_ratio*100:.1f}%가 복잡도 7.0 이상으로 분류되어 코드 변경 위험이 높습니다",
                supporting_data={
                    "high_complexity_count": metrics.high_complexity_sql_count + metrics.high_complexity_plsql_count,
                    "total_count": metrics.total_sql_count + metrics.total_plsql_count,
                    "ratio": metrics.high_complexity_ratio
                }
            ))
        
        # 4. 코드 변경 위험 근거
        rationales.append(Rationale(
            category="operations",
            reason="RDS Oracle SE2로 이관하여 코드 변경을 최소화하고 마이그레이션 위험을 낮출 수 있습니다",
            supporting_data={}
        ))
        
        # 5. 성능 메트릭 근거 (선택적)
        if metrics.avg_cpu_usage > 70:
            rationales.append(Rationale(
                category="performance",
                reason=f"높은 CPU 사용률({metrics.avg_cpu_usage:.1f}%)로 인해 성능 최적화가 필요하며, RDS Oracle SE2로 기존 성능을 유지할 수 있습니다",
                supporting_data={"avg_cpu_usage": metrics.avg_cpu_usage}
            ))
        
        # 6. 빠른 마이그레이션 근거
        if len(rationales) < 5:
            rationales.append(Rationale(
                category="operations",
                reason="약 8-12주 내에 마이그레이션을 완료할 수 있어 빠른 클라우드 전환이 가능합니다",
                supporting_data={}
            ))
        
        return rationales[:5]  # 최대 5개
    
    def _generate_mysql_rationales(self, metrics: AnalysisMetrics) -> List[Rationale]:
        """Aurora MySQL 전략 근거 생성"""
        rationales = []
        plsql_count = self._get_plsql_count(metrics)
        
        # 1. 단순 코드 + 적은 개수 근거
        rationales.append(Rationale(
            category="complexity",
            reason=f"평균 SQL 복잡도({metrics.avg_sql_complexity:.1f})와 PL/SQL 복잡도({metrics.avg_plsql_complexity:.1f})가 낮고, PL/SQL 오브젝트가 {plsql_count}개로 적어 애플리케이션 레벨 이관이 매우 용이합니다",
            supporting_data={
                "avg_sql_complexity": metrics.avg_sql_complexity,
                "avg_plsql_complexity": metrics.avg_plsql_complexity,
                "plsql_count": plsql_count
            }
        ))
        
        # 2. 작업 기간 근거
        if plsql_count < 20:
            rationales.append(Rationale(
                category="operations",
                reason=f"PL/SQL 오브젝트가 {plsql_count}개로 매우 적어 단기간 내 이관이 가능합니다",
                supporting_data={"plsql_count": plsql_count}
            ))
        else:
            rationales.append(Rationale(
                category="operations",
                reason=f"PL/SQL 오브젝트가 {plsql_count}개로 적어 애플리케이션 레벨로 이관이 가능합니다",
                supporting_data={"plsql_count": plsql_count}
            ))
        
        # 3. 비용 절감 근거
        rationales.append(Rationale(
            category="cost",
            reason="Aurora MySQL은 오픈소스 기반으로 Oracle 라이선스 비용이 없어 TCO를 크게 절감할 수 있습니다",
            supporting_data={}
        ))
        
        # 4. BULK 연산 경고
        if metrics.bulk_operation_count >= 10:
            rationales.append(Rationale(
                category="performance",
                reason=f"BULK 연산이 {metrics.bulk_operation_count}개 발견되었습니다. MySQL은 BULK 연산 미지원으로 성능 저하 가능성이 있으므로 주의가 필요합니다",
                supporting_data={"bulk_operation_count": metrics.bulk_operation_count}
            ))
        
        # 5. 클라우드 네이티브 근거
        if len(rationales) < 5:
            rationales.append(Rationale(
                category="operations",
                reason="Aurora MySQL의 자동 스케일링, 자동 백업 등 클라우드 네이티브 기능을 활용할 수 있습니다",
                supporting_data={}
            ))
        
        return rationales[:5]
    
    def _generate_postgresql_rationales(self, metrics: AnalysisMetrics) -> List[Rationale]:
        """Aurora PostgreSQL 전략 근거 생성"""
        rationales = []
        plsql_count = self._get_plsql_count(metrics)
        difficulty = self._assess_migration_difficulty(metrics)
        difficulty_text = self._get_difficulty_text(difficulty)
        
        # 1. PL/pgSQL 호환성 + 개수/복잡도 + 난이도 근거
        if plsql_count >= 100:
            rationales.append(Rationale(
                category="complexity",
                reason=f"PL/SQL 오브젝트가 {plsql_count}개로 많지만, 평균 복잡도({metrics.avg_plsql_complexity:.1f})가 중간 수준으로 PL/pgSQL 변환이 가능합니다. PL/pgSQL은 Oracle PL/SQL의 70-75%를 커버합니다. 마이그레이션 난이도는 {difficulty_text}입니다",
                supporting_data={
                    "plsql_count": plsql_count,
                    "avg_plsql_complexity": metrics.avg_plsql_complexity,
                    "difficulty": difficulty
                }
            ))
        elif plsql_count >= 50:
            rationales.append(Rationale(
                category="complexity",
                reason=f"PL/SQL 오브젝트가 {plsql_count}개이고 평균 복잡도({metrics.avg_plsql_complexity:.1f})가 중간 수준으로, PL/pgSQL로 대부분 변환이 가능합니다. 마이그레이션 난이도는 {difficulty_text}입니다",
                supporting_data={
                    "plsql_count": plsql_count,
                    "avg_plsql_complexity": metrics.avg_plsql_complexity
                }
            ))
        elif metrics.avg_plsql_complexity >= 7.0:
            rationales.append(Rationale(
                category="complexity",
                reason=f"PL/SQL 오브젝트가 {plsql_count}개로 적지만 평균 복잡도({metrics.avg_plsql_complexity:.1f})가 높아 신중한 변환이 필요합니다. PL/pgSQL은 Oracle PL/SQL의 70-75%를 커버합니다",
                supporting_data={
                    "plsql_count": plsql_count,
                    "avg_plsql_complexity": metrics.avg_plsql_complexity
                }
            ))
        else:
            rationales.append(Rationale(
                category="complexity",
                reason="PL/pgSQL은 Oracle PL/SQL의 70-75%를 커버하여 대부분의 로직을 변환할 수 있습니다",
                supporting_data={}
            ))
        
        # 2. BULK 연산 성능 근거
        if metrics.bulk_operation_count >= 10:
            rationales.append(Rationale(
                category="performance",
                reason=f"BULK 연산이 {metrics.bulk_operation_count}개 발견되었습니다. PostgreSQL은 순수 SQL 또는 Chunked Batch로 대체 가능합니다 (성능 차이 20-50%)",
                supporting_data={"bulk_operation_count": metrics.bulk_operation_count}
            ))
        
        # 3. 복잡도 범위 근거
        if 5.0 <= metrics.avg_sql_complexity < 7.0:
            rationales.append(Rationale(
                category="complexity",
                reason=f"평균 SQL 복잡도({metrics.avg_sql_complexity:.1f})가 중간 수준으로 PostgreSQL 변환이 적합합니다",
                supporting_data={"avg_sql_complexity": metrics.avg_sql_complexity}
            ))
        
        # 4. 비용 절감 근거
        rationales.append(Rationale(
            category="cost",
            reason="Aurora PostgreSQL은 오픈소스 기반으로 Oracle 라이선스 비용이 없어 TCO를 절감할 수 있습니다",
            supporting_data={}
        ))
        
        # 5. PL/SQL 복잡도 근거
        if metrics.avg_plsql_complexity >= 5.0 and len(rationales) < 5:
            rationales.append(Rationale(
                category="complexity",
                reason=f"PL/SQL 평균 복잡도({metrics.avg_plsql_complexity:.1f})가 중간 수준으로 PL/pgSQL 변환이 가능합니다",
                supporting_data={"avg_plsql_complexity": metrics.avg_plsql_complexity}
            ))
        
        # 6. 클라우드 네이티브 근거
        if len(rationales) < 3:
            rationales.append(Rationale(
                category="operations",
                reason="Aurora PostgreSQL의 자동 스케일링, 자동 백업 등 클라우드 네이티브 기능을 활용할 수 있습니다",
                supporting_data={}
            ))
        
        return rationales[:5]
    
    # Helper methods
    
    def _get_plsql_count(self, metrics: AnalysisMetrics) -> int:
        """PL/SQL 오브젝트 개수 계산 (AWR 우선)"""
        if any([metrics.awr_procedure_count, metrics.awr_function_count, metrics.awr_package_count]):
            count = 0
            if metrics.awr_procedure_count:
                count += self._extract_number(metrics.awr_procedure_count)
            if metrics.awr_function_count:
                count += self._extract_number(metrics.awr_function_count)
            if metrics.awr_package_count:
                count += self._extract_number(metrics.awr_package_count)
            return count
        return metrics.total_plsql_count
    
    def _extract_number(self, value) -> int:
        """문자열이나 숫자에서 숫자 값 추출"""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            import re
            numbers = re.findall(r'\d+', value)
            if numbers:
                return int(numbers[-1])
        return 0
    
    def _assess_migration_difficulty(self, metrics: AnalysisMetrics) -> str:
        """PL/SQL 라인 수 기반 마이그레이션 난이도 평가"""
        plsql_lines = metrics.awr_plsql_lines or 0
        if isinstance(plsql_lines, str):
            plsql_lines = self._extract_number(plsql_lines)
        
        if plsql_lines == 0:
            plsql_lines = metrics.total_plsql_count * 200
        
        if plsql_lines < 20000:
            return "low"
        elif plsql_lines < 50000:
            return "medium"
        elif plsql_lines < 100000:
            return "high"
        else:
            return "very_high"
    
    def _get_difficulty_text(self, difficulty: str) -> str:
        """난이도 레벨을 한국어 텍스트로 변환"""
        difficulty_map = {
            "low": "낮음 (3~6개월 예상)",
            "medium": "중간 (6~12개월 예상)",
            "high": "높음 (12~18개월 예상)",
            "very_high": "매우 높음 (18개월 이상 예상)"
        }
        return difficulty_map.get(difficulty, "중간")
    
    def _get_complexity_level_text(self, complexity: float) -> str:
        """복잡도 점수를 레벨 텍스트로 변환
        
        Args:
            complexity: 복잡도 점수 (0.0 ~ 10.0)
            
        Returns:
            str: 복잡도 레벨 텍스트
            
        기준:
            - 0~1: 매우 간단
            - 1~3: 간단 (낮음)
            - 3~5: 중간
            - 5~7: 복잡 (높음)
            - 7~9: 매우 복잡
            - 9~10: 극도로 복잡
        """
        if complexity < 1.0:
            return "매우 낮음"
        elif complexity < 3.0:
            return "낮음"
        elif complexity < 5.0:
            return "중간"
        elif complexity < 7.0:
            return "높음"
        elif complexity < 9.0:
            return "매우 높음"
        else:
            return "극도로 높음"
