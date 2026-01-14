# Statspack 분석 보고서

생성 시간: 2026-01-14 16:45:20

## 1. 시스템 정보 요약

- **데이터베이스 이름**: ORCL01
- **DBID**: 96266285
- **버전**: 19.0.0.0.0
- **배너**: Oracle Database 19c Standard Edition 2 Release 19.0.0.0.0 - Production
- **플랫폼**: Linux_x86_64-bit
- **CPU 개수**: 2
- **CPU 코어 수**: 1
- **물리 메모리**: 15.35 GB
- **인스턴스 수**: 1
- **RDS 환경**: 예
- **캐릭터셋**: AL32UTF8
- **총 DB 크기**: 2 GB

**PL/SQL 코드 통계:**
- **PL/SQL 코드 라인 수**: 6,165
- **패키지 수**: 1

**데이터베이스 오브젝트 통계:**
- **스키마 수**: 2
- **테이블 수**: 73

## 2. 메모리 사용량 통계

| Snap ID | Instance | SGA (GB) | PGA (GB) | Total (GB) |
|---------|----------|----------|----------|------------|
| 2 | 1 | 11.10 | 0.50 | 11.60 |
| 3 | 1 | 11.10 | 0.50 | 11.60 |
| 4 | 1 | 11.10 | 0.50 | 11.60 |
| 5 | 1 | 11.10 | 0.50 | 11.60 |
| 6 | 1 | 11.10 | 0.50 | 11.60 |
| 7 | 1 | 11.10 | 0.50 | 11.60 |
| 8 | 1 | 11.10 | 0.50 | 11.60 |
| 9 | 1 | 11.10 | 0.50 | 11.60 |
| 10 | 1 | 11.10 | 0.50 | 11.60 |
| 11 | 1 | 11.10 | 0.50 | 11.60 |

*(12개 항목 더 있음)*

## 3. 디스크 사용량 통계

| Snap ID | Size (GB) |
|---------|-----------|
| 2 | 2.00 |
| 3 | 2.00 |
| 4 | 2.00 |
| 5 | 2.00 |
| 6 | 2.00 |
| 7 | 2.00 |
| 8 | 2.00 |
| 9 | 2.00 |
| 10 | 2.00 |
| 11 | 2.00 |

*(12개 항목 더 있음)*

## 4. 주요 성능 메트릭 요약

| Snap | Duration (m) | CPU/s | Read IOPS | Write IOPS | Commits/s |
|------|--------------|-------|-----------|------------|-----------|
| 2 | 8.5 | 0.01 | 4.60 | 1.20 | 0.00 |
| 3 | 16.9 | 0.01 | 4.50 | 3.30 | 0.00 |
| 4 | 60.0 | 0.01 | 4.30 | 1.20 | 0.00 |
| 5 | 60.0 | 0.01 | 4.30 | 1.20 | 0.00 |
| 6 | 60.0 | 0.01 | 4.40 | 1.20 | 0.00 |
| 7 | 60.0 | 0.01 | 4.40 | 1.20 | 0.00 |
| 8 | 60.0 | 0.01 | 4.40 | 1.20 | 0.00 |
| 9 | 60.0 | 0.01 | 4.40 | 1.20 | 0.00 |
| 10 | 60.0 | 0.01 | 4.40 | 1.20 | 0.00 |
| 11 | 60.0 | 0.01 | 4.30 | 1.20 | 0.00 |

*(12개 항목 더 있음)*

## 5. Top 대기 이벤트

| Snap ID | Wait Class | Event Name | % DBT | Total Time (s) |
|---------|------------|------------|-------|----------------|
| 2 | System | I/O control file sequential read | 83.02 | 1627867.00 |
| 2 | DB | CPU DB CPU | 80.35 | 1575619.00 |
| 2 | System | I/O control file parallel write | 24.47 | 479882.00 |
| 2 | User | I/O Disk file operations I/O | 10.01 | 196269.00 |
| 2 | System | I/O log file parallel write | 3.06 | 59913.00 |
| 3 | System | I/O control file sequential read | 120.07 | 4202947.00 |
| 3 | DB | CPU DB CPU | 67.61 | 2366699.00 |
| 3 | System | I/O control file parallel write | 28.62 | 1001764.00 |
| 3 | User | I/O Disk file operations I/O | 13.07 | 457491.00 |
| 3 | Other | oracle thread bootstrap | 4.64 | 162419.00 |
| 4 | System | I/O control file sequential read | 105.54 | 12154411.00 |
| 4 | DB | CPU DB CPU | 67.98 | 7829109.00 |
| 4 | System | I/O control file parallel write | 33.10 | 3811506.00 |
| 4 | User | I/O Disk file operations I/O | 11.64 | 1340630.00 |
| 4 | Other | oracle thread bootstrap | 2.68 | 308255.00 |
| 5 | System | I/O control file sequential read | 95.49 | 11890333.00 |
| 5 | DB | CPU DB CPU | 61.16 | 7615544.00 |
| 5 | System | I/O control file parallel write | 29.21 | 3636750.00 |
| 5 | User | I/O Disk file operations I/O | 12.32 | 1533721.00 |
| 5 | Commit | log file sync | 4.54 | 565671.00 |

*(90개 항목 더 있음)*

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
| Automatic Segment Space Management (user) | 1 | 예 |
| Automatic Undo Management | 1 | 예 |
| Bigfile Tablespace | 1 | 예 |
| Character Set | 1 | 예 |
| Deferred Segment Creation | 1 | 예 |
| Extensibility | 1 | 예 |
| LOB | 1 | 예 |
| Locally Managed Tablespaces (system) | 1 | 예 |
| Locally Managed Tablespaces (user) | 1 | 예 |
| Object | 1 | 예 |
| Oracle Call Interface (OCI) | 1 | 예 |
| Oracle Managed Files | 1 | 예 |
| Oracle Utility External Table (ORACLE_LOADER) | 1 | 예 |
| Partitioning (system) | 1 | 예 |
| Resource Manager | 1 | 예 |
| SQL Plan Directive | 1 | 예 |
| SQL*Plus | 1 | 예 |
| SecureFiles (system) | 1 | 예 |
| SecureFiles (user) | 1 | 예 |
| Server Parameter File | 1 | 예 |
| Services | 1 | 예 |
| Unified Audit | 1 | 예 |

## 7. SGA 조정 권장사항

| SGA Size (MB) | Size Factor | Est. DB Time | Est. Physical Reads |
|---------------|-------------|--------------|---------------------|
| 2912 | 0.25 | 1595 | 39565 |
| 4368 | 0.38 | 1595 | 39565 |
| 5824 | 0.50 | 1595 | 39565 |
| 7280 | 0.62 | 1595 | 39565 |
| 8736 | 0.75 | 1595 | 39565 |
| 10192 | 0.88 | 1595 | 39565 |
| 11648 | 1.00 | 1595 | 39565 |
| 13104 | 1.12 | 1595 | 39565 |
| 14560 | 1.25 | 1595 | 39565 |
| 16016 | 1.38 | 1595 | 39565 |

*(5개 항목 더 있음)*

## 8. 마이그레이션 분석 결과

### RDS for Oracle

- **난이도 점수**: 1.00 / 10.0
- **난이도 레벨**: 매우 간단 (Minimal effort)

**점수 구성 요소:**

- 기본 점수 (동일 엔진): 1.00

**RDS 인스턴스 추천:**

- **인스턴스 타입**: db.r6i.large
- **vCPU**: 2
- **메모리**: 16 GiB
- **현재 CPU 사용률**: 0.01%
- **현재 메모리 사용량**: 11.60 GB
- **CPU 여유분**: 99.99%
- **메모리 여유분**: 37.93%

**권장사항:**

- RDS for Oracle은 동일 엔진 마이그레이션으로 호환성이 높습니다.
- 현재 버전 19.0.0.0.0에서 최신 버전으로 업그레이드를 권장합니다.

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
- PL/SQL 코드 변환: 4.00
- Oracle 특화 기능: 9.70

**권장사항:**

- Aurora PostgreSQL은 Oracle과 높은 호환성을 제공합니다.
- PL/SQL 코드를 PL/pgSQL로 변환해야 합니다.
- PL/SQL을 PL/pgSQL로 변환해야 합니다.
- 1개의 패키지를 PostgreSQL 스키마 또는 확장으로 변환해야 합니다.
- 일부 Oracle 특화 기능은 대체 방안이 필요합니다:
- Adaptive Plans: 애플리케이션 레벨에서 구현 필요
- Automatic Maintenance - Optimizer Statistics Gathering: 애플리케이션 레벨에서 구현 필요
- Automatic Maintenance - SQL Tuning Advisor: 애플리케이션 레벨에서 구현 필요
- Automatic Maintenance - Space Advisor: 애플리케이션 레벨에서 구현 필요
- Automatic Reoptimization: 애플리케이션 레벨에서 구현 필요
- Automatic SGA Tuning: 애플리케이션 레벨에서 구현 필요
- Automatic SQL Execution Memory: 애플리케이션 레벨에서 구현 필요
- Automatic Segment Space Management (system): 애플리케이션 레벨에서 구현 필요
- Automatic Segment Space Management (user): 애플리케이션 레벨에서 구현 필요
- Automatic Undo Management: 애플리케이션 레벨에서 구현 필요
- Bigfile Tablespace: 애플리케이션 레벨에서 구현 필요
- Character Set: 애플리케이션 레벨에서 구현 필요
- Deferred Segment Creation: 애플리케이션 레벨에서 구현 필요
- Extensibility: 애플리케이션 레벨에서 구현 필요
- LOB: 애플리케이션 레벨에서 구현 필요
- Locally Managed Tablespaces (system): 애플리케이션 레벨에서 구현 필요
- Locally Managed Tablespaces (user): 애플리케이션 레벨에서 구현 필요
- Object: 애플리케이션 레벨에서 구현 필요
- Oracle Call Interface (OCI): 애플리케이션 레벨에서 구현 필요
- Oracle Managed Files: 애플리케이션 레벨에서 구현 필요
- Oracle Utility External Table (ORACLE_LOADER): 애플리케이션 레벨에서 구현 필요
- Partitioning (system): 네이티브 파티셔닝 지원
- Resource Manager: 애플리케이션 레벨에서 구현 필요
- SQL Plan Directive: 애플리케이션 레벨에서 구현 필요
- SQL*Plus: 애플리케이션 레벨에서 구현 필요
- SecureFiles (system): 애플리케이션 레벨에서 구현 필요
- SecureFiles (user): 애플리케이션 레벨에서 구현 필요
- Server Parameter File: 애플리케이션 레벨에서 구현 필요
- Services: 애플리케이션 레벨에서 구현 필요
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
- PL/SQL 코드 변환 (MySQL 제약): 7.50
- Oracle 특화 기능 (MySQL 제약): 12.61

**권장사항:**

- Aurora MySQL은 Oracle과의 호환성이 제한적입니다.
- 대규모 PL/SQL 코드나 Oracle 특화 기능이 많은 경우 PostgreSQL을 권장합니다.
- PL/SQL 코드를 MySQL 저장 프로시저로 변환하거나 애플리케이션으로 이관해야 합니다.
- PL/SQL을 MySQL 저장 프로시저로 변환하거나 애플리케이션으로 이관해야 합니다.
- 1개의 패키지를 저장 프로시저로 변환하거나 애플리케이션으로 이관해야 합니다.
- 많은 Oracle 특화 기능이 MySQL에서 지원되지 않습니다:
- Adaptive Plans: 애플리케이션 레벨에서 구현 필요
- Automatic Maintenance - Optimizer Statistics Gathering: 애플리케이션 레벨에서 구현 필요
- Automatic Maintenance - SQL Tuning Advisor: 애플리케이션 레벨에서 구현 필요
- Automatic Maintenance - Space Advisor: 애플리케이션 레벨에서 구현 필요
- Automatic Reoptimization: 애플리케이션 레벨에서 구현 필요
- Automatic SGA Tuning: 애플리케이션 레벨에서 구현 필요
- Automatic SQL Execution Memory: 애플리케이션 레벨에서 구현 필요
- Automatic Segment Space Management (system): 애플리케이션 레벨에서 구현 필요
- Automatic Segment Space Management (user): 애플리케이션 레벨에서 구현 필요
- Automatic Undo Management: 애플리케이션 레벨에서 구현 필요
- Bigfile Tablespace: 애플리케이션 레벨에서 구현 필요
- Character Set: 애플리케이션 레벨에서 구현 필요
- Deferred Segment Creation: 애플리케이션 레벨에서 구현 필요
- Extensibility: 애플리케이션 레벨에서 구현 필요
- LOB: 애플리케이션 레벨에서 구현 필요
- Locally Managed Tablespaces (system): 애플리케이션 레벨에서 구현 필요
- Locally Managed Tablespaces (user): 애플리케이션 레벨에서 구현 필요
- Object: 애플리케이션 레벨에서 구현 필요
- Oracle Call Interface (OCI): 애플리케이션 레벨에서 구현 필요
- Oracle Managed Files: 애플리케이션 레벨에서 구현 필요
- Oracle Utility External Table (ORACLE_LOADER): 애플리케이션 레벨에서 구현 필요
- Partitioning (system): 네이티브 파티셔닝 지원 (제한적)
- Resource Manager: 애플리케이션 레벨에서 구현 필요
- SQL Plan Directive: 애플리케이션 레벨에서 구현 필요
- SQL*Plus: 애플리케이션 레벨에서 구현 필요
- SecureFiles (system): 애플리케이션 레벨에서 구현 필요
- SecureFiles (user): 애플리케이션 레벨에서 구현 필요
- Server Parameter File: 애플리케이션 레벨에서 구현 필요
- Services: 애플리케이션 레벨에서 구현 필요
- Unified Audit: 애플리케이션 레벨에서 구현 필요

**경고:**

- ⚠️ 대규모 PL/SQL 코드 변환은 MySQL에서 매우 어렵습니다. PostgreSQL을 고려하세요.
- ⚠️ 많은 Oracle 특화 기능이 사용되고 있습니다. MySQL 호환성을 신중히 검토하세요.

**다음 단계:**

- AWS Schema Conversion Tool (SCT)로 스키마 변환 가능성 평가
- PL/SQL 코드를 MySQL 저장 프로시저 또는 애플리케이션으로 변환
- Oracle 특화 기능의 대체 방안 구현
- AWS DMS로 데이터 마이그레이션
- 광범위한 애플리케이션 테스트 및 검증
