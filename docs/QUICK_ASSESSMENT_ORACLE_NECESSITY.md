# DBCSI 기반 Oracle 필수 여부 빠른 판단 가이드

> 작성일: 2026-01-28
> 상태: 제안 (Proposal)
> 관련 문서: [ANALYSIS_MODES_AND_DATA_REQUIREMENTS.md](ANALYSIS_MODES_AND_DATA_REQUIREMENTS.md)

## 📋 개요

이 문서는 DBCSI(AWR/Statspack) 데이터만으로 Oracle 유지 필요성과 오픈소스 전환 가능성을 빠르게 판단하는 방법을 설명합니다.

**목적**: 상세 코드 분석 없이 초기 방향성 결정
**신뢰도**: 60-70% (상세 분석으로 보완 필요)
**소요 시간**: 30분 이내

---

## 🎯 판단 결과 유형

| 결과 | 의미 | 다음 단계 |
|------|------|----------|
| 🔴 **ORACLE_REQUIRED** | Oracle 유지 권장 또는 아키텍처 변경 필수 | Replatform 검토 |
| 🟢 **OPEN_SOURCE_POSSIBLE** | 오픈소스 전환 가능성 높음 | 상세 분석 후 PostgreSQL/MySQL 선택 |
| 🟠 **NEEDS_DETAILED_ANALYSIS** | 추가 분석 필요 | PL/SQL + SQL 복잡도 분석 진행 |

---

## 📊 판단 기준 상세

### 🔴 Oracle 필수 조건 (하나라도 해당되면)

#### 1. RAC(Real Application Clusters) 사용

| DBCSI 필드 | 조건 | 판단 |
|-----------|------|------|
| `INSTANCES` | > 1 | 🔴 Oracle 필수 또는 아키텍처 변경 |

```
~~BEGIN-OS-INFORMATION~~
INSTANCES                                                        2
~~END-OS-INFORMATION~~
```

**의미**: 
- 고가용성을 위해 다중 인스턴스 구성
- 오픈소스로 전환 시 아키텍처 재설계 필요 (Aurora Multi-AZ, Global Database 등)

**대응 방안**:
- Replatform (RDS for Oracle) 유지
- 또는 Aurora + Read Replica + Global Database로 재설계


#### 2. 대규모 PL/SQL 코드베이스

| DBCSI 필드 | 조건 | 판단 |
|-----------|------|------|
| `COUNT_LINES_PLSQL` | ≥ 100,000 | 🔴 Replatform 권장 |
| `COUNT_LINES_PLSQL` | 50,000 - 100,000 | 🟠 상세 분석 필요 |

```
~~BEGIN-OS-INFORMATION~~
COUNT_LINES_PLSQL                                                125000
~~END-OS-INFORMATION~~
```

**의미**:
- 10만줄 이상의 PL/SQL 변환은 비용/시간 측면에서 비효율적
- 변환 비용이 Replatform 비용을 초과할 가능성 높음

**비용 비교** (10만줄 기준):
| 전략 | 예상 비용 | 예상 기간 |
|------|----------|----------|
| Refactor (변환) | $1.5M - $2M | 18-24개월 |
| Replatform (유지) | $0.5M - $0.8M | 3-6개월 |

#### 3. Oracle EE 전용 기능 사용 (user 레벨)

| DBCSI FEATURES | 조건 | 판단 |
|----------------|------|------|
| `Advanced Compression (user)` | CURRENTLY_USED = TRUE | 🟠 대체 방안 검토 |
| `OLAP (user)` | CURRENTLY_USED = TRUE | 🔴 대체 어려움 |
| `Data Mining (user)` | CURRENTLY_USED = TRUE | 🔴 대체 어려움 |
| `Spatial and Graph (user)` | CURRENTLY_USED = TRUE | 🟠 PostGIS로 대체 가능 |
| `Advanced Security (user)` | CURRENTLY_USED = TRUE | 🟠 대체 방안 검토 |
| `Label Security (user)` | CURRENTLY_USED = TRUE | 🔴 대체 어려움 |
| `Database Vault (user)` | CURRENTLY_USED = TRUE | 🔴 대체 어려움 |
| `Real Application Testing (user)` | CURRENTLY_USED = TRUE | 🟠 대체 방안 검토 |

**주의**: `(system)` 접미사가 붙은 기능은 Oracle 내부 사용이므로 무시

```
~~BEGIN-FEATURES~~
NAME                                                             DETECTED_USAGES TOTAL_SAMPLES CURRE
Advanced Compression (user)                                                   15             1 TRUE
~~END-FEATURES~~
```

#### 4. 복잡한 분산 아키텍처

| DBCSI 필드 | 조건 | 판단 |
|-----------|------|------|
| `COUNT_DB_LINKS` | ≥ 5 | 🟠 아키텍처 검토 필요 |
| `COUNT_DB_LINKS` | ≥ 10 | 🔴 복잡한 분산 시스템 |

**의미**:
- 다수의 DB Link는 분산 트랜잭션, 원격 조인 등 복잡한 패턴 사용 가능성
- 오픈소스 전환 시 애플리케이션 레벨 재설계 필요

---

### 🟢 오픈소스 가능 조건 (모두 만족해야)

#### 체크리스트

| # | 조건 | DBCSI 필드 | 기준값 |
|---|------|-----------|--------|
| 1 | 단일 인스턴스 | `INSTANCES` | = 1 |
| 2 | 소규모 PL/SQL | `COUNT_LINES_PLSQL` | < 20,000 |
| 3 | 적은 프로시저 | `COUNT_PROCEDURE` | < 50 |
| 4 | 적은 함수 | `COUNT_FUNCTION` | < 30 |
| 5 | 적은 패키지 | `COUNT_PACKAGE` | < 20 |
| 6 | 작은 DB 크기 | `TOTAL_DB_SIZE_GB` | < 500 |
| 7 | EE 기능 미사용 | FEATURES (user) | 없음 |
| 8 | 적은 DB Link | `COUNT_DB_LINKS` | < 3 |

#### 이상적인 오픈소스 전환 대상 예시

```
~~BEGIN-OS-INFORMATION~~
INSTANCES                                                        1
COUNT_LINES_PLSQL                                                8500
COUNT_PROCEDURE                                                  25
COUNT_FUNCTION                                                   12
COUNT_PACKAGE                                                    5
TOTAL_DB_SIZE_GB                                                 150
COUNT_DB_LINKS                                                   1
~~END-OS-INFORMATION~~

~~BEGIN-FEATURES~~
(EE 전용 기능 없음 또는 system만 존재)
~~END-FEATURES~~
```

**판단**: 🟢 **OPEN_SOURCE_POSSIBLE**
- 변환 작업량 적음
- 비용 효율적인 마이그레이션 가능
- PostgreSQL 또는 MySQL 선택 가능


---

### 🟠 상세 분석 필요 조건 (중간 영역)

다음 조건에 해당하면 DBCSI만으로 판단하기 어렵습니다.

| 조건 | 범위 | 추가 분석 필요 사항 |
|------|------|-------------------|
| 중간 규모 PL/SQL | 20,000 - 100,000줄 | PL/SQL 복잡도 분석 |
| 중간 규모 프로시저 | 50 - 200개 | 개별 복잡도 분석 |
| EE 기능 일부 사용 | 1-2개 | 대체 방안 검토 |
| 중간 규모 DB | 500GB - 2TB | 마이그레이션 전략 검토 |

**권장 다음 단계**:
1. PL/SQL 복잡도 분석 실행
2. SQL 복잡도 분석 실행 (가능한 경우)
3. Full 모드 또는 DB-Only 모드로 상세 분석

---

## 🔄 판단 플로우차트

```
                        ┌─────────────────────┐
                        │   DBCSI 데이터 수집   │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │   RAC 사용 여부?     │
                        │   (INSTANCES > 1)   │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
              ┌─────────┐                   ┌─────────┐
              │   Yes   │                   │   No    │
              └────┬────┘                   └────┬────┘
                   │                             │
                   ▼                             ▼
        ┌─────────────────┐          ┌─────────────────────┐
        │ 🔴 ORACLE_REQUIRED │          │  PL/SQL 규모 확인    │
        │ (아키텍처 변경 필요) │          │ (COUNT_LINES_PLSQL) │
        └─────────────────┘          └──────────┬──────────┘
                                               │
                              ┌────────────────┼────────────────┐
                              │                │                │
                              ▼                ▼                ▼
                        ┌──────────┐    ┌──────────┐    ┌──────────┐
                        │ ≥ 100,000 │    │ 20K-100K │    │ < 20,000 │
                        └─────┬────┘    └─────┬────┘    └─────┬────┘
                              │               │               │
                              ▼               ▼               ▼
                   ┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
                   │ 🔴 ORACLE_REQUIRED │ │ 🟠 상세 분석  │ │  EE 기능 확인    │
                   │ (Replatform 권장) │ │    필요     │ │ (FEATURES user) │
                   └─────────────────┘ └─────────────┘ └────────┬────────┘
                                                               │
                                                  ┌────────────┴────────────┐
                                                  │                         │
                                                  ▼                         ▼
                                            ┌──────────┐             ┌──────────┐
                                            │ EE 사용   │             │ EE 미사용 │
                                            └─────┬────┘             └─────┬────┘
                                                  │                       │
                                                  ▼                       ▼
                                        ┌─────────────┐       ┌─────────────────────┐
                                        │ 🟠 상세 분석  │       │  기타 조건 확인       │
                                        │    필요     │       │ (프로시저, DB크기 등) │
                                        └─────────────┘       └──────────┬──────────┘
                                                                        │
                                                           ┌────────────┴────────────┐
                                                           │                         │
                                                           ▼                         ▼
                                                     ┌──────────┐             ┌──────────┐
                                                     │ 조건 충족  │             │ 조건 미충족│
                                                     └─────┬────┘             └─────┬────┘
                                                           │                       │
                                                           ▼                       ▼
                                              ┌─────────────────────┐    ┌─────────────┐
                                              │ 🟢 OPEN_SOURCE_POSSIBLE │    │ 🟠 상세 분석  │
                                              └─────────────────────┘    │    필요     │
                                                                        └─────────────┘
```

---

## 📋 Quick Assessment 체크시트

### 입력 데이터 (DBCSI에서 추출)

| 항목 | 값 | 비고 |
|------|-----|------|
| INSTANCES | ___ | 1이면 단일, 2이상이면 RAC |
| COUNT_LINES_PLSQL | ___ | PL/SQL 총 라인 수 |
| COUNT_PROCEDURE | ___ | 프로시저 개수 |
| COUNT_FUNCTION | ___ | 함수 개수 |
| COUNT_PACKAGE | ___ | 패키지 개수 |
| TOTAL_DB_SIZE_GB | ___ | DB 크기 (GB) |
| COUNT_DB_LINKS | ___ | DB Link 개수 |
| EE 기능 (user) | ___ | 사용 중인 EE 기능 목록 |

### 판단 결과

| 체크 | 조건 | 결과 |
|------|------|------|
| ☐ | INSTANCES > 1 | → 🔴 ORACLE_REQUIRED |
| ☐ | COUNT_LINES_PLSQL ≥ 100,000 | → 🔴 ORACLE_REQUIRED |
| ☐ | EE 기능 (user) 다수 사용 | → 🔴 또는 🟠 |
| ☐ | 모든 오픈소스 조건 충족 | → 🟢 OPEN_SOURCE_POSSIBLE |
| ☐ | 위 조건 모두 해당 안됨 | → 🟠 NEEDS_DETAILED_ANALYSIS |

**최종 판단**: ________________


---

## 💡 판단 기준의 근거

### PL/SQL 라인 수 기준 (20,000 / 100,000)

| 라인 수 | 변환 예상 시간 | 변환 예상 비용 | 권장 전략 |
|--------|--------------|--------------|----------|
| < 20,000 | 3-6개월 | $100K-$300K | Refactor |
| 20,000-50,000 | 6-12개월 | $300K-$700K | 상세 분석 후 결정 |
| 50,000-100,000 | 12-18개월 | $700K-$1.5M | 상세 분석 후 결정 |
| ≥ 100,000 | 18개월+ | $1.5M+ | Replatform 권장 |

**계산 근거**:
- 평균 변환 속도: 100줄/시간 (AI 도구 활용 시)
- 시니어 개발자 시급: $100/시간
- 테스트/검증 오버헤드: 변환 시간의 50%

### 프로시저/함수 개수 기준 (50 / 30)

| 개수 | 의미 | 변환 복잡도 |
|------|------|-----------|
| < 30 | 소규모 | 낮음 - 개별 변환 가능 |
| 30-100 | 중규모 | 중간 - 체계적 접근 필요 |
| > 100 | 대규모 | 높음 - 자동화 도구 필수 |

### DB 크기 기준 (500GB)

| 크기 | 마이그레이션 방식 | 다운타임 |
|------|----------------|---------|
| < 100GB | 온라인 마이그레이션 | 최소 |
| 100-500GB | 하이브리드 | 수 시간 |
| 500GB-2TB | 오프라인 권장 | 수 일 |
| > 2TB | 단계적 마이그레이션 | 수 주 |

---

## ⚠️ 한계점 및 주의사항

### DBCSI만으로 판단할 수 없는 것들

| 항목 | 이유 | 보완 방법 |
|------|------|----------|
| **비즈니스 로직 복잡도** | 코드 내용 분석 필요 | PL/SQL 복잡도 분석 |
| **Oracle 전용 SQL 문법** | SQL 패턴 분석 필요 | SQL 복잡도 분석 |
| **성능 요구사항** | 워크로드 특성 분석 필요 | 성능 테스트 |
| **동시성 패턴** | 락/세션 분석 필요 | Wait Event 분석 |
| **외부 시스템 연동** | 아키텍처 분석 필요 | 인터뷰/문서 검토 |

### 오판 가능성

| 시나리오 | 오판 유형 | 결과 |
|---------|---------|------|
| 소규모지만 복잡한 로직 | 🟢로 판단했으나 실제 🟠 | 변환 비용 초과 |
| 대규모지만 단순한 로직 | 🔴로 판단했으나 실제 🟢 | 불필요한 Replatform |
| EE 기능 대체 가능 | 🔴로 판단했으나 실제 🟢 | 기회 손실 |

**권장사항**: Quick Assessment는 초기 방향성 결정용이며, 최종 결정 전 반드시 상세 분석 수행

---

## 🔧 구현 제안

### CLI 옵션 추가

```bash
# Quick Assessment 실행
python -m src.migration_recommendation.cli \
    --dbcsi-file awr_report.out \
    --mode quick \
    --output quick_assessment.md

# 출력 예시
=====================================
Oracle Migration Quick Assessment
=====================================

입력 데이터:
- INSTANCES: 1
- COUNT_LINES_PLSQL: 8,500
- COUNT_PROCEDURE: 25
- COUNT_FUNCTION: 12
- TOTAL_DB_SIZE_GB: 150
- EE Features (user): None

판단 결과: 🟢 OPEN_SOURCE_POSSIBLE

권장 다음 단계:
1. PL/SQL 복잡도 분석 실행
2. PostgreSQL vs MySQL 비교 분석
3. 마이그레이션 로드맵 수립
```

### 코드 구현 예시

```python
# src/migration_recommendation/quick_assessor.py

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class AssessmentResult(Enum):
    ORACLE_REQUIRED = "oracle_required"
    OPEN_SOURCE_POSSIBLE = "open_source_possible"
    NEEDS_DETAILED_ANALYSIS = "needs_detailed_analysis"

@dataclass
class QuickAssessment:
    result: AssessmentResult
    confidence: float  # 0.0 - 1.0
    reasons: List[str]
    recommendations: List[str]

class QuickAssessor:
    """DBCSI 기반 빠른 평가기"""
    
    # 임계값 상수
    PLSQL_LINES_HIGH = 100000
    PLSQL_LINES_MEDIUM = 20000
    PROCEDURE_COUNT_LOW = 50
    FUNCTION_COUNT_LOW = 30
    PACKAGE_COUNT_LOW = 20
    DB_SIZE_LOW = 500  # GB
    DB_LINKS_LOW = 3
    
    # EE 전용 기능 목록
    EE_ONLY_FEATURES = [
        "Advanced Compression",
        "OLAP",
        "Data Mining",
        "Spatial and Graph",
        "Advanced Security",
        "Label Security",
        "Database Vault",
        "Real Application Testing",
    ]
    
    def assess(self, dbcsi_data) -> QuickAssessment:
        """빠른 평가 수행"""
        os_info = dbcsi_data.os_info
        features = dbcsi_data.features
        
        reasons = []
        
        # 1. RAC 체크
        if self._is_rac(os_info):
            reasons.append("RAC 구성 감지 (INSTANCES > 1)")
            return QuickAssessment(
                result=AssessmentResult.ORACLE_REQUIRED,
                confidence=0.9,
                reasons=reasons,
                recommendations=["Replatform 또는 아키텍처 재설계 검토"]
            )
        
        # 2. 대규모 PL/SQL 체크
        plsql_lines = os_info.count_lines_plsql or 0
        if plsql_lines >= self.PLSQL_LINES_HIGH:
            reasons.append(f"대규모 PL/SQL ({plsql_lines:,}줄)")
            return QuickAssessment(
                result=AssessmentResult.ORACLE_REQUIRED,
                confidence=0.85,
                reasons=reasons,
                recommendations=["Replatform 권장 (변환 비용 > 유지 비용)"]
            )
        
        # 3. EE 기능 체크
        ee_features_used = self._check_ee_features(features)
        if ee_features_used:
            reasons.append(f"EE 기능 사용: {', '.join(ee_features_used)}")
            return QuickAssessment(
                result=AssessmentResult.NEEDS_DETAILED_ANALYSIS,
                confidence=0.7,
                reasons=reasons,
                recommendations=["EE 기능 대체 방안 검토 필요"]
            )
        
        # 4. 오픈소스 가능 조건 체크
        if self._check_open_source_conditions(os_info):
            reasons.append("모든 오픈소스 전환 조건 충족")
            return QuickAssessment(
                result=AssessmentResult.OPEN_SOURCE_POSSIBLE,
                confidence=0.75,
                reasons=reasons,
                recommendations=[
                    "PL/SQL 복잡도 분석으로 PostgreSQL/MySQL 선택",
                    "마이그레이션 로드맵 수립"
                ]
            )
        
        # 5. 중간 영역
        reasons.append("중간 규모 - 상세 분석 필요")
        return QuickAssessment(
            result=AssessmentResult.NEEDS_DETAILED_ANALYSIS,
            confidence=0.6,
            reasons=reasons,
            recommendations=[
                "PL/SQL 복잡도 분석 실행",
                "SQL 복잡도 분석 실행 (가능한 경우)"
            ]
        )
    
    def _is_rac(self, os_info) -> bool:
        return (os_info.instances or 1) > 1
    
    def _check_ee_features(self, features) -> List[str]:
        """사용 중인 EE 전용 기능 목록 반환"""
        used = []
        for feature in features:
            if "(user)" in feature.name and feature.currently_used:
                for ee_feature in self.EE_ONLY_FEATURES:
                    if ee_feature in feature.name:
                        used.append(feature.name)
        return used
    
    def _check_open_source_conditions(self, os_info) -> bool:
        """오픈소스 전환 조건 모두 충족 여부"""
        return all([
            (os_info.instances or 1) == 1,
            (os_info.count_lines_plsql or 0) < self.PLSQL_LINES_MEDIUM,
            (os_info.count_procedures or 0) < self.PROCEDURE_COUNT_LOW,
            (os_info.count_functions or 0) < self.FUNCTION_COUNT_LOW,
            (os_info.count_packages or 0) < self.PACKAGE_COUNT_LOW,
            (os_info.total_db_size_gb or 0) < self.DB_SIZE_LOW,
        ])
```


---

## 📊 실제 사례 분석

### 사례 1: 🟢 오픈소스 전환 적합

```
DBCSI 데이터:
- INSTANCES: 1
- COUNT_LINES_PLSQL: 8,500
- COUNT_PROCEDURE: 25
- COUNT_FUNCTION: 12
- COUNT_PACKAGE: 5
- TOTAL_DB_SIZE_GB: 150
- COUNT_DB_LINKS: 1
- EE Features (user): 없음

판단: 🟢 OPEN_SOURCE_POSSIBLE (신뢰도 75%)

근거:
- 단일 인스턴스
- 소규모 PL/SQL (8,500줄 < 20,000줄)
- 적은 오브젝트 수
- EE 기능 미사용

권장:
- PostgreSQL 또는 MySQL 선택을 위한 상세 분석
- 예상 마이그레이션 기간: 3-4개월
- 예상 비용: $100K-$150K
```

### 사례 2: 🔴 Oracle 유지 권장

```
DBCSI 데이터:
- INSTANCES: 2 (RAC)
- COUNT_LINES_PLSQL: 185,000
- COUNT_PROCEDURE: 450
- COUNT_FUNCTION: 230
- COUNT_PACKAGE: 85
- TOTAL_DB_SIZE_GB: 2,500
- COUNT_DB_LINKS: 12
- EE Features (user): Advanced Compression, Partitioning

판단: 🔴 ORACLE_REQUIRED (신뢰도 90%)

근거:
- RAC 구성 (다중 인스턴스)
- 대규모 PL/SQL (185,000줄)
- 다수의 DB Link (분산 아키텍처)
- EE 기능 사용

권장:
- Replatform (RDS for Oracle) 권장
- 또는 장기 계획으로 아키텍처 재설계 검토
- 예상 Replatform 기간: 3-6개월
- 예상 비용: $300K-$500K
```

### 사례 3: 🟠 상세 분석 필요

```
DBCSI 데이터:
- INSTANCES: 1
- COUNT_LINES_PLSQL: 45,000
- COUNT_PROCEDURE: 120
- COUNT_FUNCTION: 65
- COUNT_PACKAGE: 25
- TOTAL_DB_SIZE_GB: 800
- COUNT_DB_LINKS: 3
- EE Features (user): Partitioning

판단: 🟠 NEEDS_DETAILED_ANALYSIS (신뢰도 60%)

근거:
- 중간 규모 PL/SQL (20,000 < 45,000 < 100,000)
- EE 기능 일부 사용 (Partitioning)
- 중간 규모 DB (800GB)

권장:
- PL/SQL 복잡도 분석 실행
- Partitioning 대체 방안 검토 (PostgreSQL 네이티브 파티셔닝)
- 상세 분석 후 최종 결정
```

---

## 📚 관련 문서

| 문서 | 설명 |
|------|------|
| [ANALYSIS_MODES_AND_DATA_REQUIREMENTS.md](ANALYSIS_MODES_AND_DATA_REQUIREMENTS.md) | 분석 모드 및 데이터 요구사항 |
| [DBCSI_REPORT_DATA_ENHANCEMENT.md](DBCSI_REPORT_DATA_ENHANCEMENT.md) | DBCSI 리포트 데이터 확장 제안 |
| [THRESHOLD_IMPROVEMENT_PROPOSAL.md](THRESHOLD_IMPROVEMENT_PROPOSAL.md) | 임계값 개선 제안 |
| [WHAT_IS_ORACLE_MIGRATION_ANALYZER.md](WHAT_IS_ORACLE_MIGRATION_ANALYZER.md) | 도구 소개 |

---

## 📝 문서 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0 | 2026-01-28 | 초안 작성 |

---

## 🏁 결론

### Quick Assessment의 가치

| 장점 | 설명 |
|------|------|
| **빠른 판단** | 30분 내 초기 방향성 결정 |
| **비용 절감** | 불필요한 상세 분석 방지 |
| **명확한 기준** | 객관적 데이터 기반 판단 |

### 한계

| 한계 | 대응 |
|------|------|
| 코드 복잡도 미반영 | 상세 분석으로 보완 |
| 비즈니스 로직 미반영 | 인터뷰/문서 검토로 보완 |
| 60-70% 신뢰도 | 최종 결정 전 상세 분석 필수 |

### 권장 워크플로우

```
1. Quick Assessment (DBCSI만) → 초기 방향성
2. DB-Only 분석 (DBCSI + PL/SQL) → 상세 검토
3. Full 분석 (필요시) → 최종 결정
4. PoC/파일럿 → 검증
5. 본 마이그레이션 → 실행
```

---

> **참고**: 이 문서는 기능 제안서이며, 실제 구현은 별도 검토 후 진행됩니다.
