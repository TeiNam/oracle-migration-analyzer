# 분석 모드 및 데이터 요구사항

> 작성일: 2026-01-28
> 상태: 제안 (Proposal)
> 관련 문서: [WHAT_IS_ORACLE_MIGRATION_ANALYZER.md](WHAT_IS_ORACLE_MIGRATION_ANALYZER.md)

## 📋 개요

Oracle Migration Analyzer는 세 가지 데이터 소스를 통합하여 마이그레이션 전략을 추천합니다:

1. **SQL 복잡도 분석**: 서비스 레벨 SQL 쿼리
2. **PL/SQL 복잡도 분석**: 데이터베이스 저장 프로시저/함수/패키지
3. **DBCSI 분석**: AWR/Statspack 성능 리포트

그러나 실제 환경에서는 모든 데이터를 수집하기 어려운 경우가 있습니다. 이 문서는 데이터 가용성에 따른 분석 모드와 각 모드의 신뢰도를 설명합니다.

---

## 🔍 데이터 수집의 현실적 어려움

### 서비스 레벨 SQL 수집이 어려운 경우

| 상황 | 설명 | 빈도 |
|------|------|------|
| **ORM 사용** | JPA, Hibernate, MyBatis 등이 SQL 자동 생성 | 매우 흔함 |
| **동적 쿼리 빌더** | QueryDSL, JOOQ 등 런타임 SQL 생성 | 흔함 |
| **레거시 코드** | SQL이 여러 파일에 분산, 문자열 연결로 구성 | 흔함 |
| **마이크로서비스** | 수십~수백 개 서비스에 SQL 분산 | 증가 추세 |
| **외부 벤더 솔루션** | 소스 코드 접근 불가 | 종종 발생 |
| **보안 제약** | 소스 코드 반출 불가 | 종종 발생 |

### PL/SQL 수집

- ✅ **수집 용이**: `ora_plsql_full.sql` 스크립트로 DB에서 직접 추출
- ✅ **완전성 보장**: 데이터베이스에 존재하는 모든 오브젝트 포함

### DBCSI (AWR/Statspack) 수집

- ✅ **수집 용이**: DBA 권한으로 리포트 생성
- ✅ **실제 워크로드 반영**: 운영 환경의 실제 사용 패턴 포함

---

## 📊 분석 모드 정의

### 모드 비교 요약

| 모드 | 입력 데이터 | 신뢰도 | 분석 시간 | 사용 시나리오 |
|------|------------|--------|----------|--------------|
| **Full** | SQL + PL/SQL + DBCSI | 95% | 1-2일 | 전체 분석 가능 |
| **DB-Only** | PL/SQL + DBCSI | 80% | 2-4시간 | 서비스 SQL 수집 어려움 |
| **Quick** | DBCSI만 | 60% | 30분 | 빠른 사전 평가 |

---

### 모드 1: Full (전체 분석)

#### 입력 데이터

```
┌─────────────────────────────────────────────────────────┐
│                    Full 모드                             │
├─────────────────────────────────────────────────────────┤
│  ✅ 서비스 SQL (.sql 파일들)                             │
│  ✅ PL/SQL (ora_plsql_full.sql 출력)                    │
│  ✅ DBCSI (AWR 또는 Statspack 리포트)                   │
└─────────────────────────────────────────────────────────┘
```

#### 의사결정 로직

```python
# Replatform 조건 (OR)
if avg_sql_complexity >= 7.0:      # SQL 복잡도 매우 높음
    return REPLATFORM
if avg_plsql_complexity >= 7.0:    # PL/SQL 복잡도 매우 높음
    return REPLATFORM
if high_complexity_ratio >= 0.3:   # 복잡 오브젝트 30% 이상
    return REPLATFORM

# MySQL 조건 (AND)
if avg_sql_complexity <= 5.0 and avg_plsql_complexity <= 5.0:
    if plsql_count < 50 and bulk_operations < 10:
        return MYSQL

# 기본값
return POSTGRESQL
```

#### 신뢰도: 95%

- 모든 데이터 소스 활용
- SQL과 PL/SQL 복잡도 모두 실측값 사용
- 가장 정확한 추천 제공

#### 적합한 상황

- 서비스 SQL을 파일로 추출 가능
- 충분한 분석 시간 확보
- 높은 정확도 필요

---

### 모드 2: DB-Only (데이터베이스 전용)

#### 입력 데이터

```
┌─────────────────────────────────────────────────────────┐
│                   DB-Only 모드                           │
├─────────────────────────────────────────────────────────┤
│  ❌ 서비스 SQL (미포함)                                  │
│  ✅ PL/SQL (ora_plsql_full.sql 출력)                    │
│  ✅ DBCSI (AWR 또는 Statspack 리포트)                   │
└─────────────────────────────────────────────────────────┘
```

#### 핵심 가정

| 가정 | 근거 | 유효성 |
|------|------|--------|
| 서비스 SQL은 ORM 기반 단순 CRUD | 현대 애플리케이션 대부분 ORM 사용 | 높음 |
| 복잡한 비즈니스 로직은 PL/SQL에 집중 | Oracle 환경의 일반적 패턴 | 높음 |
| AWR 통계가 실제 워크로드 반영 | 운영 환경 데이터 기반 | 매우 높음 |

#### 의사결정 로직

```python
# SQL 복잡도 추정값 사용
ESTIMATED_SQL_COMPLEXITY = 3.0  # ORM 기반 단순 CRUD 가정

# Replatform 조건 (PL/SQL 기준만)
if avg_plsql_complexity >= 7.0:
    return REPLATFORM
if high_complexity_plsql_ratio >= 0.3:
    return REPLATFORM

# MySQL 조건 (더 보수적)
if avg_plsql_complexity <= 4.0:  # 기존 5.0 → 4.0 (보수적)
    if plsql_count < 30:         # 기존 50 → 30 (보수적)
        if bulk_operations < 10:
            return MYSQL

# 기본값
return POSTGRESQL
```

#### 신뢰도: 80%

**신뢰도 감소 요인**:
- SQL 복잡도가 추정값 (실측값 아님)
- 복잡한 Native SQL이 있을 경우 과소평가 가능

**신뢰도 유지 요인**:
- PL/SQL 복잡도는 실측값
- DBCSI AWR 통계로 실제 워크로드 파악
- 보수적 임계값 적용으로 위험 최소화

#### 적합한 상황

- ORM 기반 애플리케이션 (JPA, Hibernate, MyBatis)
- 서비스 SQL 수집이 현실적으로 어려움
- 복잡한 비즈니스 로직이 PL/SQL에 집중된 환경

#### 부적합한 상황

- Native SQL을 많이 사용하는 레거시 시스템
- 복잡한 리포팅 쿼리가 서비스 레벨에 존재
- 데이터 웨어하우스/분석 워크로드

---

### 모드 3: Quick (빠른 사전 평가)

#### 입력 데이터

```
┌─────────────────────────────────────────────────────────┐
│                    Quick 모드                            │
├─────────────────────────────────────────────────────────┤
│  ❌ 서비스 SQL (미포함)                                  │
│  ❌ PL/SQL (미포함)                                      │
│  ✅ DBCSI (AWR 또는 Statspack 리포트)                   │
└─────────────────────────────────────────────────────────┘
```

#### AWR에서 추출 가능한 정보

| AWR 섹션 | 추출 정보 | 활용 |
|----------|----------|------|
| Database Summary | DB 크기, 버전, 옵션 | 기본 정보 |
| PL/SQL Statistics | 프로시저/함수/패키지 개수, 총 라인 수 | PL/SQL 규모 추정 |
| Top SQL by Elapsed Time | 상위 SQL 실행 시간 | SQL 복잡도 추정 |
| Wait Events | 대기 이벤트 분포 | 성능 특성 파악 |
| Instance Activity | CPU, I/O, 메모리 사용량 | 리소스 요구사항 |

#### 의사결정 로직

```python
# AWR 통계 기반 추정
plsql_lines = awr_plsql_lines or 0
plsql_count = awr_procedure_count + awr_function_count + awr_package_count

# 규모 기반 판단
if plsql_lines >= 100000:  # 10만 줄 이상
    return REPLATFORM      # 변환 비용 > Replatform 비용

if plsql_lines >= 50000:   # 5만 줄 이상
    return POSTGRESQL      # 변환 가능하나 상당한 노력 필요

if plsql_count < 30 and plsql_lines < 10000:
    return MYSQL           # 소규모, 단순 구조

return POSTGRESQL          # 기본값
```

#### 신뢰도: 60%

**신뢰도 감소 요인**:
- SQL/PL/SQL 복잡도 분석 없음
- 코드 품질/패턴 파악 불가
- 규모 기반 추정만 가능

**활용 가치**:
- 빠른 초기 평가 (Go/No-Go 결정)
- 상세 분석 필요 여부 판단
- 프로젝트 규모 추정

#### 적합한 상황

- 마이그레이션 검토 초기 단계
- 빠른 의사결정 필요
- 상세 분석 전 사전 평가

---

## 🔄 모드별 워크플로우

### Full 모드 워크플로우

```
┌──────────────────────────────────────────────────────────────┐
│                      Full 모드 워크플로우                      │
└──────────────────────────────────────────────────────────────┘

1. 데이터 수집 (1-2일)
   ├── 서비스 SQL 추출
   │   ├── 소스 코드에서 .sql 파일 수집
   │   ├── ORM 매핑 파일에서 SQL 추출
   │   └── 로그에서 실행 SQL 캡처
   │
   ├── PL/SQL 추출
   │   └── ora_plsql_full.sql 실행
   │
   └── DBCSI 수집
       └── AWR 또는 Statspack 리포트 생성

2. 분석 실행
   $ python -m src.migration_recommendation.cli \
       --dbcsi-file awr_report.out \
       --sql-dir ./sql_files \
       --plsql-file plsql_export.out \
       --target postgresql

3. 결과 검토
   └── migration_recommendation_report.md
```

### DB-Only 모드 워크플로우

```
┌──────────────────────────────────────────────────────────────┐
│                    DB-Only 모드 워크플로우                     │
└──────────────────────────────────────────────────────────────┘

1. 데이터 수집 (2-4시간)
   ├── PL/SQL 추출
   │   └── ora_plsql_full.sql 실행
   │
   └── DBCSI 수집
       └── AWR 또는 Statspack 리포트 생성

2. 분석 실행
   $ python -m src.migration_recommendation.cli \
       --dbcsi-file awr_report.out \
       --plsql-file plsql_export.out \
       --target postgresql \
       --mode db-only  # DB-Only 모드 명시

3. 결과 검토
   └── migration_recommendation_report.md
       └── ⚠️ "DB-Only 모드" 제한사항 표시
```

### Quick 모드 워크플로우

```
┌──────────────────────────────────────────────────────────────┐
│                     Quick 모드 워크플로우                      │
└──────────────────────────────────────────────────────────────┘

1. 데이터 수집 (30분)
   └── DBCSI 수집
       └── AWR 또는 Statspack 리포트 생성

2. 분석 실행
   $ python -m src.migration_recommendation.cli \
       --dbcsi-file awr_report.out \
       --mode quick  # Quick 모드 명시

3. 결과 검토
   └── quick_assessment_report.md
       └── ⚠️ "Quick 모드 - 상세 분석 권장" 표시
```

---

## 📈 DB-Only 모드 상세 설계

### SQL 복잡도 추정 전략

#### 전략 1: 고정값 사용 (기본)

```python
# ORM 기반 단순 CRUD 가정
ESTIMATED_SQL_COMPLEXITY = 3.0
```

**장점**: 단순, 예측 가능
**단점**: 실제와 괴리 가능

#### 전략 2: AWR Top SQL 기반 추정

AWR 리포트의 "Top SQL by Elapsed Time" 섹션 활용:

```
Top SQL by Elapsed Time
-----------------------
SQL ID        Elapsed(s)  Executions  Elapsed/Exec(s)  %Total
------------  ----------  ----------  ---------------  ------
abc123def456      1,234      10,000           0.12     15.2%
def456ghi789        892       5,000           0.18     11.0%
...
```

**추정 로직**:

```python
def estimate_sql_complexity_from_awr(top_sql_stats: List[dict]) -> float:
    """
    AWR Top SQL 통계에서 SQL 복잡도 추정
    
    추정 기준:
    - 실행당 시간 > 1초: 복잡한 SQL (7.0+)
    - 실행당 시간 0.1-1초: 중간 복잡도 (4.0-7.0)
    - 실행당 시간 < 0.1초: 단순 SQL (1.0-4.0)
    """
    if not top_sql_stats:
        return 3.0  # 기본값
    
    complexity_scores = []
    for sql in top_sql_stats[:10]:  # 상위 10개만
        elapsed_per_exec = sql['elapsed_per_exec']
        
        if elapsed_per_exec > 1.0:
            complexity_scores.append(7.5)
        elif elapsed_per_exec > 0.1:
            complexity_scores.append(5.0)
        else:
            complexity_scores.append(2.5)
    
    return sum(complexity_scores) / len(complexity_scores)
```

**장점**: 실제 워크로드 반영
**단점**: Top SQL만 반영 (전체 SQL 대표성 부족)

#### 전략 3: 하이브리드 (권장)

```python
def estimate_sql_complexity(
    awr_top_sql: Optional[List[dict]] = None,
    application_type: str = "unknown"
) -> float:
    """
    하이브리드 SQL 복잡도 추정
    
    Args:
        awr_top_sql: AWR Top SQL 통계 (있으면 사용)
        application_type: 애플리케이션 유형
            - "orm_based": ORM 기반 (JPA, Hibernate)
            - "native_sql": Native SQL 사용
            - "mixed": 혼합
            - "unknown": 알 수 없음
    """
    # 1. 애플리케이션 유형 기반 기본값
    base_complexity = {
        "orm_based": 2.5,
        "native_sql": 5.0,
        "mixed": 4.0,
        "unknown": 3.5
    }.get(application_type, 3.5)
    
    # 2. AWR Top SQL 보정
    if awr_top_sql:
        awr_estimate = estimate_sql_complexity_from_awr(awr_top_sql)
        # 가중 평균 (AWR 40%, 기본값 60%)
        return awr_estimate * 0.4 + base_complexity * 0.6
    
    return base_complexity
```

### 보수적 임계값 조정

DB-Only 모드에서는 불확실성을 반영하여 임계값을 보수적으로 조정:

| 조건 | Full 모드 | DB-Only 모드 | 변경 이유 |
|------|----------|-------------|----------|
| MySQL 복잡도 상한 | 5.0 | 4.0 | SQL 복잡도 불확실 |
| MySQL PL/SQL 개수 상한 | 50 | 30 | 안전 마진 확보 |
| Replatform 복잡도 하한 | 7.0 | 7.0 | 유지 (PL/SQL 기준) |

### 리포트 출력 형식

#### DB-Only 모드 리포트 헤더

```markdown
# Oracle Migration Recommendation Report

> 생성일: 2026-01-28
> 분석 모드: **DB-Only** ⚠️
> 신뢰도: 80%

---

## ⚠️ 분석 제한사항

이 리포트는 **DB-Only 모드**로 생성되었습니다.

| 데이터 소스 | 상태 | 비고 |
|------------|------|------|
| PL/SQL 분석 | ✅ 포함 | 실측값 사용 |
| DBCSI (AWR) | ✅ 포함 | 실측값 사용 |
| 서비스 SQL | ❌ 미포함 | 추정값 사용 (3.0) |

### 권장사항

- **ORM 기반 애플리케이션**: 현재 결과 신뢰 가능
- **Native SQL 사용**: Full 모드 분석 권장
- **복잡한 리포팅 쿼리 존재**: Full 모드 분석 권장

---
```

#### 신뢰도 표시 섹션

```markdown
## 📊 분석 신뢰도

| 항목 | 신뢰도 | 근거 |
|------|--------|------|
| PL/SQL 복잡도 | 95% | 실측값 |
| SQL 복잡도 | 60% | 추정값 (ORM 가정) |
| 리소스 요구사항 | 90% | AWR 실측값 |
| **종합 신뢰도** | **80%** | - |

### 신뢰도 향상 방법

1. 서비스 SQL 파일 제공 → Full 모드 분석
2. 애플리케이션 유형 명시 (ORM/Native SQL)
3. 샘플 SQL 제공 (대표적인 쿼리 10-20개)
```

---

## 🎯 모드 선택 가이드

### 의사결정 플로우차트

```
                    ┌─────────────────────┐
                    │ 서비스 SQL 수집 가능? │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
        ┌─────────┐                       ┌─────────┐
        │   Yes   │                       │   No    │
        └────┬────┘                       └────┬────┘
             │                                 │
             ▼                                 ▼
      ┌─────────────┐               ┌─────────────────────┐
      │  Full 모드   │               │ PL/SQL 수집 가능?    │
      │  (신뢰도 95%)│               └──────────┬──────────┘
      └─────────────┘                          │
                                  ┌────────────┴────────────┐
                                  │                         │
                                  ▼                         ▼
                            ┌─────────┐               ┌─────────┐
                            │   Yes   │               │   No    │
                            └────┬────┘               └────┬────┘
                                 │                         │
                                 ▼                         ▼
                          ┌─────────────┐           ┌─────────────┐
                          │ DB-Only 모드 │           │  Quick 모드  │
                          │ (신뢰도 80%) │           │ (신뢰도 60%) │
                          └─────────────┘           └─────────────┘
```

### 상황별 권장 모드

| 상황 | 권장 모드 | 이유 |
|------|----------|------|
| 신규 마이그레이션 프로젝트 시작 | Quick → Full | 빠른 평가 후 상세 분석 |
| ORM 기반 최신 애플리케이션 | DB-Only | SQL 수집 어려움, ORM 가정 유효 |
| 레거시 Native SQL 시스템 | Full | SQL 복잡도 실측 필요 |
| 데이터 웨어하우스 | Full | 복잡한 분석 쿼리 존재 |
| 시간 제약 심함 | Quick | 빠른 의사결정 필요 |
| 높은 정확도 필요 | Full | 모든 데이터 활용 |

---

## 🔧 구현 제안

### CLI 인터페이스 확장

```bash
# Full 모드 (기본값)
python -m src.migration_recommendation.cli \
    --dbcsi-file awr.out \
    --sql-dir ./sql \
    --plsql-file plsql.out

# DB-Only 모드
python -m src.migration_recommendation.cli \
    --dbcsi-file awr.out \
    --plsql-file plsql.out \
    --mode db-only \
    --app-type orm_based  # 선택: orm_based, native_sql, mixed

# Quick 모드
python -m src.migration_recommendation.cli \
    --dbcsi-file awr.out \
    --mode quick
```

### 코드 변경 범위

| 파일 | 변경 내용 | 우선순위 |
|------|----------|----------|
| `cli.py` | `--mode`, `--app-type` 옵션 추가 | 높음 |
| `integrator.py` | SQL 없을 때 추정값 사용 로직 | 높음 |
| `decision_engine.py` | 모드별 임계값 분기 | 높음 |
| `data_models.py` | `AnalysisMode` enum 추가 | 중간 |
| `formatters/` | 모드별 리포트 헤더/제한사항 | 중간 |

### 예상 구현 시간

| 단계 | 작업 | 시간 |
|------|------|------|
| Phase 1 | CLI 옵션 + 기본 분기 | 4시간 |
| Phase 2 | DB-Only 로직 구현 | 4시간 |
| Phase 3 | Quick 모드 구현 | 2시간 |
| Phase 4 | 리포트 포맷 수정 | 2시간 |
| Phase 5 | 테스트 + 문서화 | 4시간 |
| **총계** | | **16시간** |

---

## 📚 관련 문서

| 문서 | 설명 |
|------|------|
| [WHAT_IS_ORACLE_MIGRATION_ANALYZER.md](WHAT_IS_ORACLE_MIGRATION_ANALYZER.md) | 도구 소개 |
| [SQL_COMPLEXITY_FORMULA_EXPLAINED.md](SQL_COMPLEXITY_FORMULA_EXPLAINED.md) | SQL 복잡도 공식 |
| [PLSQL_COMPLEXITY_FORMULA_EXPLAINED.md](PLSQL_COMPLEXITY_FORMULA_EXPLAINED.md) | PL/SQL 복잡도 공식 |
| [THRESHOLD_IMPROVEMENT_PROPOSAL.md](THRESHOLD_IMPROVEMENT_PROPOSAL.md) | 임계값 개선 제안 |

---

## 📝 문서 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0 | 2026-01-28 | 초안 작성 |

---

## 🏁 결론

### 핵심 메시지

**PL/SQL + DBCSI만으로도 80% 신뢰도의 유의미한 분석이 가능합니다.**

### 권장 접근법

1. **Quick 모드로 시작**: 30분 내 초기 평가
2. **DB-Only 모드로 상세화**: ORM 기반이면 충분
3. **필요시 Full 모드**: Native SQL 많거나 높은 정확도 필요 시

### 기대 효과

| 효과 | 설명 |
|------|------|
| **접근성 향상** | SQL 수집 어려운 환경에서도 분석 가능 |
| **시간 절약** | DB-Only 모드로 분석 시간 50% 단축 |
| **투명성 확보** | 신뢰도 명시로 사용자 판단 지원 |
| **유연성 제공** | 상황에 맞는 모드 선택 가능 |

---

> **참고**: 이 문서는 기능 제안서이며, 실제 구현은 별도 검토 후 진행됩니다.
