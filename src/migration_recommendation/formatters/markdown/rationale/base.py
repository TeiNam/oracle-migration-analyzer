"""
추천 근거 포맷터 - 공통 유틸리티

복잡도 레벨 변환, 난이도 계산 등 공통 기능을 제공합니다.
"""

from typing import Dict
from ....data_models import AnalysisMetrics


def get_complexity_level(score: float) -> str:
    """복잡도 점수를 레벨로 변환 (한국어)"""
    if score < 2.0:
        return "매우 낮음"
    elif score < 4.0:
        return "낮음"
    elif score < 6.0:
        return "중간"
    elif score < 8.0:
        return "높음"
    else:
        return "매우 높음"


def get_complexity_level_en(score: float) -> str:
    """복잡도 점수를 레벨로 변환 (영어)"""
    if score < 2.0:
        return "Very Low"
    elif score < 4.0:
        return "Low"
    elif score < 6.0:
        return "Medium"
    elif score < 8.0:
        return "High"
    else:
        return "Very High"


def calculate_final_difficulty(metrics: AnalysisMetrics) -> str:
    """최종 난이도 계산 (AI 시대 기준 조정)
    
    난이도 점수 산정 기준:
    - SQL 평균 복잡도: 0~3점 (신규)
    - PL/SQL 평균 복잡도: 0~3점
    - PL/SQL 코드량: 0~3점
    - 고난이도 오브젝트 비율: 0~2점 (모수 70개 이상)
    - 고난이도 오브젝트 절대 개수: 0~3점
    - 고위험 Oracle 패키지: 0~3점 (신규)
    - 중위험 Oracle 패키지: 0~2점 (신규)
    
    총점 기준:
    - 0~3점: low
    - 4~7점: medium
    - 8~11점: high
    - 12점 이상: very_high
    """
    score = 0
    
    # SQL 복잡도 기반 (0~3점) - 신규
    if metrics.avg_sql_complexity:
        if metrics.avg_sql_complexity >= 7.5:
            score += 3
        elif metrics.avg_sql_complexity >= 6.0:
            score += 2
        elif metrics.avg_sql_complexity >= 4.5:
            score += 1
    
    # PL/SQL 복잡도 기반 (0~3점) - 임계값 상향
    if metrics.avg_plsql_complexity:
        if metrics.avg_plsql_complexity >= 7.5:
            score += 3
        elif metrics.avg_plsql_complexity >= 6.0:
            score += 2
        elif metrics.avg_plsql_complexity >= 4.5:
            score += 1
    
    # PL/SQL 코드량 기반 (0~3점) - 임계값 상향
    plsql_lines = metrics.awr_plsql_lines or 0
    if isinstance(plsql_lines, str):
        import re
        numbers = re.findall(r"\d+", str(plsql_lines))
        plsql_lines = int(numbers[-1]) if numbers else 0
    if plsql_lines >= 200000:
        score += 3
    elif plsql_lines >= 100000:
        score += 2
    elif plsql_lines >= 50000:
        score += 1
    
    # 고난이도 오브젝트 비율 기반 (0~2점) - 모수 조건 추가
    total_objects = (metrics.total_plsql_count or 0) + (metrics.total_sql_count or 0)
    if total_objects >= 70:  # 모수 70개 이상일 때만 비율 의미 있음
        high_count = (
            (metrics.high_complexity_plsql_count or 0) + 
            (metrics.high_complexity_sql_count or 0)
        )
        if total_objects > 0:
            ratio = high_count / total_objects
            if ratio >= 0.30:
                score += 2
            elif ratio >= 0.20:
                score += 1
    
    # 고난이도 오브젝트 절대 개수 기반 (0~3점) - 임계값 상향
    high_count = (
        (metrics.high_complexity_plsql_count or 0) + 
        (metrics.high_complexity_sql_count or 0)
    )
    if high_count >= 100:
        score += 3
    elif high_count >= 50:
        score += 2
    elif high_count >= 30:
        score += 1
    
    # 고위험 Oracle 패키지 기반 (0~3점) - 신규
    high_risk_packages = {
        'UTL_FILE', 'UTL_HTTP', 'UTL_SMTP', 'UTL_TCP',
        'DBMS_AQ', 'DBMS_PIPE', 'DBMS_ALERT'
    }
    external_deps = metrics.detected_external_dependencies_summary or {}
    high_risk_count = sum(external_deps.get(pkg, 0) for pkg in high_risk_packages)
    if high_risk_count >= 50:
        score += 3
    elif high_risk_count >= 20:
        score += 2
    elif high_risk_count >= 5:
        score += 1
    
    # 중위험 Oracle 패키지 기반 (0~2점) - 신규
    medium_risk_packages = {
        'DBMS_LOB', 'DBMS_SCHEDULER', 'DBMS_JOB',
        'DBMS_CRYPTO', 'DBMS_SQL', 'DBMS_XMLGEN'
    }
    medium_risk_count = sum(external_deps.get(pkg, 0) for pkg in medium_risk_packages)
    if medium_risk_count >= 30:
        score += 2
    elif medium_risk_count >= 10:
        score += 1
    
    if score >= 12:
        return "very_high"
    elif score >= 8:
        return "high"
    elif score >= 4:
        return "medium"
    else:
        return "low"


# Oracle 기능 영향도 매핑
ORACLE_FEATURE_IMPACT_MAP: Dict[str, str] = {
    'NESTED TABLE': '🔴 높음',
    'OBJECT TYPE': '🔴 높음',
    'VARRAY': '🟠 중간',
    'CONNECT BY': '🔴 높음',
    'ROWNUM': '🟢 낮음',
    'ROWID': '🟠 중간',
    'DUAL': '🟢 낮음',
    'DECODE': '🟢 낮음',
    'NVL': '🟢 낮음',
    'NVL2': '🟢 낮음',
    'SYSDATE': '🟢 낮음',
    'SYSTIMESTAMP': '🟢 낮음',
    'SEQUENCE': '🟢 낮음',
    'AUTONOMOUS_TRANSACTION': '🔴 높음',
    'BULK COLLECT': '🟠 중간',
    'FORALL': '🟠 중간',
    'REF CURSOR': '🟠 중간',
    'PIPELINED': '🔴 높음',
    'PARALLEL': '🟠 중간',
}


# 외부 의존성 대체 방법 매핑
EXTERNAL_DEPENDENCY_REPLACEMENT_MAP: Dict[str, str] = {
    'DBMS_OUTPUT': 'RAISE NOTICE (PostgreSQL) / SELECT (MySQL)',
    'DBMS_LOB': '네이티브 LOB 함수',
    'DBMS_SQL': '동적 SQL (EXECUTE)',
    'DBMS_SCHEDULER': 'pg_cron / Event Scheduler',
    'DBMS_JOB': 'pg_cron / Event Scheduler',
    'UTL_FILE': 'COPY 명령 / LOAD DATA',
    'UTL_HTTP': 'http 확장 / 애플리케이션 레이어',
    'UTL_MAIL': '애플리케이션 레이어',
    'DBMS_CRYPTO': 'pgcrypto / AES_ENCRYPT',
    'DBMS_RANDOM': 'random() / RAND()',
    'DBMS_LOCK': 'Advisory Lock / GET_LOCK',
    'DBMS_PIPE': '애플리케이션 레이어',
    'DBMS_ALERT': 'LISTEN/NOTIFY / 애플리케이션',
    'DBMS_APPLICATION_INFO': '세션 변수',
    'DBMS_SESSION': '세션 함수',
    'DBMS_METADATA': '정보 스키마 쿼리',
    'DBMS_STATS': 'ANALYZE / ANALYZE TABLE',
    'DBMS_UTILITY': '개별 함수로 대체',
}
