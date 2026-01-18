# AWR 상세 분석 보고서

생성 시간: 2026-01-15 21:51:56

## 경영진 요약 (Executive Summary)

### 현재 시스템 개요

현재 **ORA12C** 데이터베이스는 Oracle 12.2.0.1.0 버전으로 운영되고 있으며, 총 **3.0GB**의 데이터를 저장하고 있습니다. 시스템은 **6개의 CPU 코어**와 **7.8GB의 메모리**로 구성되어 있습니다.

### 마이그레이션 권장사항

분석 결과, **RDS for Oracle**로의 마이그레이션이 가장 적합합니다. 예상 난이도는 **복잡 (High effort)**이며, 마이그레이션 점수는 10점 만점에 **7.5점**입니다.

#### 타겟별 마이그레이션 난이도

- **RDS for Oracle**: 복잡 (High effort) (7.5/10.0)
  - 권장 인스턴스: db.r6i.large (2 vCPU, 16 GiB)
- **Aurora PostgreSQL 16**: 매우 복잡 (Very high effort) (10.0/10.0)
- **Aurora MySQL 8.0**: 매우 복잡 (Very high effort) (10.0/10.0)

### 주요 발견사항

- **버퍼 캐시 효율성**: 평균 히트율 99.8% (양호)

### 권장 조치사항

1. RDS for Oracle은 동일 엔진 마이그레이션으로 호환성이 높습니다.
2. Enterprise Edition 기능을 Standard Edition 2에서 지원하는지 확인이 필요합니다.
3. 현재 버전 12.2.0.1.0에서 최신 버전으로 업그레이드를 권장합니다.

### 예상 일정 및 비용

- **예상 마이그레이션 기간**: 3-6개월 이상
- **리스크 수준**: 높음

## 1. 시스템 정보 요약

- **데이터베이스 이름**: ORA12C
- **DBID**: 595413474
- **버전**: 12.2.0.1.0
- **배너**: Oracle Database 12c Enterprise Edition Release 12.2.0.1.0 - 64bit Production
- **플랫폼**: Linux_x86_64-bit
- **CPU 개수**: 6
- **CPU 코어 수**: 6
- **물리 메모리**: 7.75 GB
- **인스턴스 수**: 1
- **RDS 환경**: 아니오
- **캐릭터셋**: AL32UTF8
- **총 DB 크기**: 3 GB

**PL/SQL 코드 통계:**
- **PL/SQL 코드 라인 수**: 274
- **프로시저 수**: 2
- **함수 수**: 1

**데이터베이스 오브젝트 통계:**
- **스키마 수**: 6
- **테이블 수**: 58

## 2. 메모리 사용량 통계

**요약:**
- **총 스냅샷 수**: 14개
- **평균 메모리 사용량**: 4.79 GB (SGA: 4.50 GB, PGA: 0.29 GB)
- **최소 메모리 사용량**: 4.70 GB
- **최대 메모리 사용량**: 4.80 GB

**상세 데이터 (최근 10개):**

| Snap ID | Instance | SGA (GB) | PGA (GB) | Total (GB) |
|---------|----------|----------|----------|------------|
| 17 | 1 | 4.50 | 0.20 | 4.70 |
| 18 | 1 | 4.50 | 0.30 | 4.80 |
| 19 | 1 | 4.50 | 0.30 | 4.80 |
| 20 | 1 | 4.50 | 0.30 | 4.80 |
| 21 | 1 | 4.50 | 0.30 | 4.80 |
| 22 | 1 | 4.50 | 0.30 | 4.80 |
| 23 | 1 | 4.50 | 0.30 | 4.80 |
| 24 | 1 | 4.50 | 0.30 | 4.80 |
| 25 | 1 | 4.50 | 0.30 | 4.80 |
| 26 | 1 | 4.50 | 0.30 | 4.80 |

*전체 14개 중 10개만 표시*

## 3. 디스크 사용량 통계

**요약:**
- **총 스냅샷 수**: 2개
- **평균 디스크 사용량**: 2.03 GB
- **최소 디스크 사용량**: 1.39 GB
- **최대 디스크 사용량**: 2.67 GB

**상세 데이터 (최근 10개):**

| Snap ID | Size (GB) |
|---------|-----------|
| 17 | 1.39 |
| 30 | 2.67 |

## 4. 주요 성능 메트릭 요약

**분석 기간**: 26/01/11 22:32 ~ 26/01/12 00:10

**요약:**
- **총 스냅샷 수**: 3개
- **평균 CPU/s**: 4.17 (최소: 2.20, 최대: 8.10)
- **평균 Read IOPS**: 14.57 (최소: 3.60, 최대: 33.40)
- **평균 Write IOPS**: 2.37 (최소: 0.00, 최대: 3.80)
- **평균 Commits/s**: 0.01 (최소: 0.00, 최대: 0.02)

**상세 데이터 (최근 3개 - 하루 패턴):**

| 시간 | Duration (m) | CPU/s | Read IOPS | Write IOPS | Commits/s |
|------|--------------|-------|-----------|------------|-----------|
| 26/01/11 22:32 | 50.0 | 2.20 | 6.70 | 3.30 | 0.00 |
| 26/01/12 00:00 | 61.0 | 8.10 | 33.40 | 3.80 | 0.02 |
| 26/01/12 00:10 | 10.0 | 2.20 | 3.60 | 0.00 | 0.00 |

## 5. Top 대기 이벤트

**요약:**
- **총 대기 이벤트 수**: 65개
- **주요 대기 클래스**: DB (79997218s), System (17444807s), Other (5719032s)

**상세 데이터 (상위 20개):**

| Snap ID | Wait Class | Event Name | % DBT | Total Time (s) |
|---------|------------|------------|-------|----------------|
| 18 | DB | CPU DB CPU | 76.94 | 75729527.00 |
| 18 | System | I/O log file parallel write | 13.63 | 13418711.00 |
| 18 | User | I/O db file sequential read | 5.60 | 5510398.00 |
| 18 | Other | oracle thread bootstrap | 5.26 | 5178420.00 |
| 18 | System | I/O control file parallel write | 3.11 | 3059085.00 |
| 19 | Other | oracle thread bootstrap | 430.16 | 502365.00 |
| 19 | System | I/O control file parallel write | 236.35 | 276029.00 |
| 19 | System | I/O db file async I/O submit | 164.05 | 191590.00 |
| 19 | DB | CPU DB CPU | 121.73 | 142169.00 |
| 19 | System | I/O log file parallel write | 75.00 | 87590.00 |
| 20 | DB | CPU DB CPU | 89.59 | 762054.00 |
| 20 | System | I/O log file parallel write | 3.78 | 32142.00 |
| 20 | User | I/O direct path write | 0.48 | 4047.00 |
| 20 | Other | PGA memory operation | 0.25 | 2148.00 |
| 20 | System | I/O control file sequential read | 0.17 | 1436.00 |
| 21 | DB | CPU DB CPU | 87.76 | 353571.00 |
| 21 | System | I/O log file parallel write | 7.69 | 30984.00 |
| 21 | Configuration | undo segment extension | 2.69 | 10827.00 |
| 21 | System | I/O control file parallel write | 1.12 | 4493.00 |
| 21 | Other | reliable message | 0.64 | 2596.00 |

*전체 65개 중 20개만 표시*

## 6. 사용된 Oracle 기능 목록

| Feature Name | Detected Usages | Currently Used |
|--------------|-----------------|----------------|
| Adaptive Plans | 1 | 예 |
| Automatic Maintenance - Optimizer Statistics Gathering | 1 | 예 |
| Automatic Maintenance - SQL Tuning Advisor | 1 | 예 |
| Automatic Maintenance - Space Advisor | 1 | 예 |
| Automatic Reoptimization | 1 | 예 |
| Automatic SGA Tuning | 1 | 예 |
| Automatic SQL Execution Memory | 1 | 예 |
| Automatic Segment Space Management (system) | 1 | 예 |
| Automatic Undo Management | 1 | 예 |
| Character Set | 1 | 예 |
| DBMS_STATS Incremental Maintenance | 1 | 예 |
| Deferred Segment Creation | 1 | 예 |
| Locally Managed Tablespaces (system) | 1 | 예 |
| Locally Managed Tablespaces (user) | 1 | 예 |
| Oracle Java Virtual Machine (system) | 1 | 예 |
| Partitioning (system) | 1 | 예 |
| Real Application Security | 1 | 예 |
| SQL Plan Directive | 1 | 예 |
| SecureFiles (system) | 1 | 예 |
| SecureFiles (user) | 1 | 예 |
| Server Parameter File | 1 | 예 |
| Traditional Audit | 1 | 예 |
| Unified Audit | 1 | 예 |

## 7. SGA 조정 권장사항

**요약:**
- **총 권장사항 수**: 13개
- **현재 SGA 크기**: 4800 MB (예상 DB Time: 481, 예상 Physical Reads: 386821)
- **권장 SGA 크기**: 2400 MB (예상 DB Time: 481, 예상 Physical Reads: 386821)

**상세 데이터 (10개 샘플):**

| SGA Size (MB) | Size Factor | Est. DB Time | Est. Physical Reads |
|---------------|-------------|--------------|---------------------|
| 2400 | 0.50 | 481 | 386821 |
| 3000 | 0.62 | 481 | 386821 |
| 3600 | 0.75 | 481 | 386821 |
| 4200 | 0.88 | 481 | 386821 |
| 4800 | 1.00 | 481 | 386821 |
| 5400 | 1.12 | 481 | 386821 |
| 6000 | 1.25 | 481 | 386821 |
| 6600 | 1.38 | 481 | 386821 |
| 7200 | 1.50 | 481 | 386821 |
| 7800 | 1.62 | 481 | 386821 |

*전체 13개 중 10개만 표시*

## 8. 마이그레이션 분석 결과

### RDS for Oracle

- **난이도 점수**: 7.50 / 10.0
- **난이도 레벨**: 복잡 (High effort)

**점수 구성 요소:**

- 기본 점수 (동일 엔진): 1.00
- 에디션 변경 (EE → SE2, 기능 제약): 3.00
- 버전 업그레이드 (12 → 19): 3.50

**RDS 인스턴스 추천:**

- **인스턴스 타입**: db.r6i.large
- **vCPU**: 2
- **메모리**: 16 GiB
- **현재 CPU 사용률**: 8.10%
- **현재 메모리 사용량**: 4.79 GB
- **CPU 여유분**: 25.23%
- **메모리 여유분**: 233.83%

**권장사항:**

- RDS for Oracle은 동일 엔진 마이그레이션으로 호환성이 높습니다.
- Enterprise Edition 기능을 Standard Edition 2에서 지원하는지 확인이 필요합니다.
- 현재 버전 12.2.0.1.0에서 최신 버전으로 업그레이드를 권장합니다.

**다음 단계:**

- RDS for Oracle 인스턴스 사이즈 선택
- Multi-AZ 배포 구성 계획
- 백업 및 복구 전략 수립
- 마이그레이션 도구 선택 (DMS, Data Pump 등)
- 테스트 환경에서 마이그레이션 검증

### Aurora PostgreSQL 16

- **난이도 점수**: 10.00 / 10.0
- **난이도 레벨**: 매우 복잡 (Very high effort)

**점수 구성 요소:**

- 기본 점수 (엔진 변경): 3.00
- PL/SQL 코드 변환: 0.50
- Oracle 특화 기능: 7.60

**권장사항:**

- Aurora PostgreSQL은 Oracle과 높은 호환성을 제공합니다.
- PL/SQL 코드를 PL/pgSQL로 변환해야 합니다.
- PL/SQL을 PL/pgSQL로 변환해야 합니다.
- 프로시저와 함수를 PostgreSQL 함수로 변환해야 합니다.
- 일부 Oracle 특화 기능은 대체 방안이 필요합니다:
- Adaptive Plans: 애플리케이션 레벨에서 구현 필요
- Automatic Maintenance - Optimizer Statistics Gathering: 애플리케이션 레벨에서 구현 필요
- Automatic Maintenance - SQL Tuning Advisor: 애플리케이션 레벨에서 구현 필요
- Automatic Maintenance - Space Advisor: 애플리케이션 레벨에서 구현 필요
- Automatic Reoptimization: 애플리케이션 레벨에서 구현 필요
- Automatic SGA Tuning: 애플리케이션 레벨에서 구현 필요
- Automatic SQL Execution Memory: 애플리케이션 레벨에서 구현 필요
- Automatic Segment Space Management (system): 애플리케이션 레벨에서 구현 필요
- Automatic Undo Management: 애플리케이션 레벨에서 구현 필요
- Character Set: 애플리케이션 레벨에서 구현 필요
- DBMS_STATS Incremental Maintenance: 애플리케이션 레벨에서 구현 필요
- Deferred Segment Creation: 애플리케이션 레벨에서 구현 필요
- Locally Managed Tablespaces (system): 애플리케이션 레벨에서 구현 필요
- Locally Managed Tablespaces (user): 애플리케이션 레벨에서 구현 필요
- Oracle Java Virtual Machine (system): 애플리케이션 레벨에서 구현 필요
- Partitioning (system): 네이티브 파티셔닝 지원
- Real Application Security: 애플리케이션 레벨에서 구현 필요
- SQL Plan Directive: 애플리케이션 레벨에서 구현 필요
- SecureFiles (system): 애플리케이션 레벨에서 구현 필요
- SecureFiles (user): 애플리케이션 레벨에서 구현 필요
- Server Parameter File: 애플리케이션 레벨에서 구현 필요
- Traditional Audit: 애플리케이션 레벨에서 구현 필요
- Unified Audit: 애플리케이션 레벨에서 구현 필요

**다음 단계:**

- AWS Schema Conversion Tool (SCT)로 스키마 변환
- PL/SQL을 PL/pgSQL로 변환
- AWS DMS로 데이터 마이그레이션
- 애플리케이션 연결 문자열 업데이트
- 성능 테스트 및 튜닝

### Aurora MySQL 8.0

- **난이도 점수**: 10.00 / 10.0
- **난이도 레벨**: 매우 복잡 (Very high effort)

**점수 구성 요소:**

- 기본 점수 (엔진 변경 + 제약): 4.00
- PL/SQL 코드 변환 (MySQL 제약): 0.75
- Oracle 특화 기능 (MySQL 제약): 9.88

**권장사항:**

- Aurora MySQL은 Oracle과의 호환성이 제한적입니다.
- 대규모 PL/SQL 코드나 Oracle 특화 기능이 많은 경우 PostgreSQL을 권장합니다.
- PL/SQL 코드를 MySQL 저장 프로시저로 변환하거나 애플리케이션으로 이관해야 합니다.
- PL/SQL을 MySQL 저장 프로시저로 변환하거나 애플리케이션으로 이관해야 합니다.
- 프로시저와 함수를 MySQL 저장 프로시저로 변환해야 합니다.
- 많은 Oracle 특화 기능이 MySQL에서 지원되지 않습니다:
- Adaptive Plans: 애플리케이션 레벨에서 구현 필요
- Automatic Maintenance - Optimizer Statistics Gathering: 애플리케이션 레벨에서 구현 필요
- Automatic Maintenance - SQL Tuning Advisor: 애플리케이션 레벨에서 구현 필요
- Automatic Maintenance - Space Advisor: 애플리케이션 레벨에서 구현 필요
- Automatic Reoptimization: 애플리케이션 레벨에서 구현 필요
- Automatic SGA Tuning: 애플리케이션 레벨에서 구현 필요
- Automatic SQL Execution Memory: 애플리케이션 레벨에서 구현 필요
- Automatic Segment Space Management (system): 애플리케이션 레벨에서 구현 필요
- Automatic Undo Management: 애플리케이션 레벨에서 구현 필요
- Character Set: 애플리케이션 레벨에서 구현 필요
- DBMS_STATS Incremental Maintenance: 애플리케이션 레벨에서 구현 필요
- Deferred Segment Creation: 애플리케이션 레벨에서 구현 필요
- Locally Managed Tablespaces (system): 애플리케이션 레벨에서 구현 필요
- Locally Managed Tablespaces (user): 애플리케이션 레벨에서 구현 필요
- Oracle Java Virtual Machine (system): 애플리케이션 레벨에서 구현 필요
- Partitioning (system): 네이티브 파티셔닝 지원 (제한적)
- Real Application Security: 애플리케이션 레벨에서 구현 필요
- SQL Plan Directive: 애플리케이션 레벨에서 구현 필요
- SecureFiles (system): 애플리케이션 레벨에서 구현 필요
- SecureFiles (user): 애플리케이션 레벨에서 구현 필요
- Server Parameter File: 애플리케이션 레벨에서 구현 필요
- Traditional Audit: 애플리케이션 레벨에서 구현 필요
- Unified Audit: 애플리케이션 레벨에서 구현 필요

**경고:**

- ⚠️ 많은 Oracle 특화 기능이 사용되고 있습니다. MySQL 호환성을 신중히 검토하세요.

**다음 단계:**

- AWS Schema Conversion Tool (SCT)로 스키마 변환 가능성 평가
- PL/SQL 코드를 MySQL 저장 프로시저 또는 애플리케이션으로 변환
- Oracle 특화 기능의 대체 방안 구현
- AWS DMS로 데이터 마이그레이션
- 광범위한 애플리케이션 테스트 및 검증

## 워크로드 패턴 분석

### 워크로드 패턴 요약

- **패턴 타입**: Mixed
- **CPU 비율**: 25.0%
- **I/O 비율**: 0.0%

### 상위 대기 이벤트

| 순위 | 이벤트 이름 | DB Time | 비율 |
|------|-------------|---------|------------|
| 1 | CPU + CPU Wait | 90 | 25.0% |
| 2 | db file sequential read | 90 | 25.0% |
| 3 | SQL*Net more data from client | 90 | 25.0% |
| 4 | Failed Logon Delay | 90 | 25.0% |

### 상위 모듈

| 순위 | 모듈 이름 | DB Time | 비율 |
|------|-------------|---------|------------|
| 1 | SQL*Plus | 180 | 50.0% |
| 2 | SQL Loader Direct Path Load | 90 | 25.0% |
| 3 | sqlplus@oracle-12c (TNS V1-V3) | 90 | 25.0% |

## 버퍼 캐시 효율성 분석

### 히트율 요약

- **평균 히트율**: 99.85%
- **최소 히트율**: 98.76%
- **최대 히트율**: 100.00%
- **현재 버퍼 캐시 크기**: 3.32 GB

### 효율성 평가

✅ **매우 우수**: 버퍼 캐시가 매우 효율적으로 동작하고 있습니다.

## I/O 함수별 분석

### 함수별 I/O 통계

| 함수 이름 | 평균 (MB/s) | 최대 (MB/s) | 총 비율 |
|---------------|----------------|----------------|---------|
| LGWR | 1.65 | 3.00 | 56.9% |
| Others | 0.89 | 2.00 | 30.6% |
| Direct Writes | 1.00 | 2.00 | 12.5% |

## 백분위수 분포 차트

### CPU 사용률 백분위수 분포

| 백분위수 | CPU 코어 수 |
|----------|-------------|

### I/O 부하 백분위수 분포

| 백분위수 | IOPS | MB/s |
|----------|------|------|

### 백분위수 해석 가이드

- **99% (99th percentile)**: 99%의 시간 동안 이 값 이하 (권장 사이징 기준)
- P99 값에 30% 여유분을 추가하여 인스턴스 크기를 결정하는 것을 권장합니다.
