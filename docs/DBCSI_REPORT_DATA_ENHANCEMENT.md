# DBCSI 리포트 데이터 확장 제안

> 작성일: 2026-01-28
> 상태: ✅ 구현 완료 (Implemented)
> 구현일: 2026-01-28
> 관련 문서: [ANALYSIS_MODES_AND_DATA_REQUIREMENTS.md](ANALYSIS_MODES_AND_DATA_REQUIREMENTS.md)

## 📋 개요

현재 마이그레이션 추천 리포트는 DBCSI(AWR/Statspack)에서 파싱한 데이터 중 일부만 표시하고 있습니다. 이 문서는 DBCSI가 보유한 모든 유용한 데이터를 리포트에 포함하기 위한 개선 방안을 제안합니다.

## ✅ 구현 완료 내역

### 1. DBCSI 리포트 개선 (`dbcsi-analyzer --enhanced`)

새로운 `--enhanced` 옵션을 통해 개선된 리포트 포맷을 사용할 수 있습니다:

```bash
dbcsi-analyzer --file sample.out --enhanced
```

#### 추가된 섹션:
- **📊 데이터베이스 개요**: 기본 정보, 크기/리소스 정보, 마이그레이션 시사점
- **📦 데이터베이스 오브젝트 통계**: PL/SQL 오브젝트, 스키마 오브젝트, 변환 작업량 추정
- **⚡ 성능 메트릭 상세**: CPU, I/O, 트랜잭션, 마이그레이션 시사점
- **⏱️ Top Wait Events**: Wait Class 설명, Top 10 이벤트, 마이그레이션 영향 분석
- **🔧 Oracle 기능 사용 현황**: 영향도 범례, 사용자/시스템 기능 분류, 대응 방안

### 2. Migration Recommendation 리포트 개선 (`migration-recommend --legacy`)

기존 레거시 모드에서도 동일한 개선된 섹션들이 표시됩니다.

## 📁 구현 파일

### DBCSI 포맷터 (새로 생성)
- `src/dbcsi/formatters/sections/__init__.py`
- `src/dbcsi/formatters/sections/database_overview.py`
- `src/dbcsi/formatters/sections/object_statistics.py`
- `src/dbcsi/formatters/sections/performance_metrics.py`
- `src/dbcsi/formatters/sections/wait_events.py`
- `src/dbcsi/formatters/sections/oracle_features.py`

### 수정된 파일
- `src/dbcsi/formatters/statspack_formatter.py` - `to_enhanced_markdown()` 메서드 추가
- `src/dbcsi/cli/argument_parser.py` - `--enhanced` 옵션 추가
- `src/dbcsi/cli/command_handlers.py` - `--enhanced` 옵션 처리

### Migration Recommendation 포맷터 (이전 세션에서 구현)
- `src/migration_recommendation/formatters/markdown/database_overview.py`
- `src/migration_recommendation/formatters/markdown/object_statistics.py`
- `src/migration_recommendation/formatters/markdown/performance_details.py`
- `src/migration_recommendation/formatters/markdown/wait_events.py`
- `src/migration_recommendation/formatters/markdown/oracle_features.py`
- `src/migration_recommendation/formatters/markdown/awr_details.py`

---

## 🔍 현재 상태 분석

### DBCSI 파서가 추출하는 데이터

#### 1. OS-INFORMATION 섹션 (OSInformation)

| 필드 | 설명 | 현재 리포트 표시 |
|------|------|-----------------|
| `statspack_version` | Statspack 버전 | ❌ 미표시 |
| `num_cpus` | CPU 개수 | ❌ 미표시 |
| `num_cpu_cores` | CPU 코어 수 | ❌ 미표시 |
| `physical_memory_gb` | 물리 메모리 (GB) | ❌ 미표시 |
| `platform_name` | 플랫폼 이름 | ❌ 미표시 |
| `version` | Oracle 버전 | ❌ 미표시 |
| `db_name` | 데이터베이스 이름 | ❌ 미표시 |
| `dbid` | 데이터베이스 ID | ❌ 미표시 |
| `banner` | Oracle 배너 | ❌ 미표시 |
| `instances` | 인스턴스 수 (RAC) | ❌ 미표시 |
| `is_rds` | RDS 여부 | ❌ 미표시 |
| `total_db_size_gb` | 전체 DB 크기 (GB) | ❌ 미표시 |
| `count_lines_plsql` | PL/SQL 코드 라인 수 | ✅ 표시 |
| `count_schemas` | 스키마 수 | ❌ 미표시 |
| `count_tables` | 테이블 수 | ❌ 미표시 |
| `count_packages` | 패키지 수 | ✅ 표시 |
| `count_procedures` | 프로시저 수 | ✅ 표시 |
| `count_functions` | 함수 수 | ✅ 표시 |
| `character_set` | 문자셋 | ❌ 미표시 |


#### 2. MEMORY 섹션 (MemoryMetric)

| 필드 | 설명 | 현재 리포트 표시 |
|------|------|-----------------|
| `snap_id` | 스냅샷 ID | ❌ 미표시 |
| `instance_number` | 인스턴스 번호 | ❌ 미표시 |
| `sga_gb` | SGA 크기 (GB) | ❌ 미표시 |
| `pga_gb` | PGA 크기 (GB) | ❌ 미표시 |
| `total_gb` | 총 메모리 (GB) | ⚠️ 평균만 표시 |

#### 3. SIZE-ON-DISK 섹션 (DiskSize)

| 필드 | 설명 | 현재 리포트 표시 |
|------|------|-----------------|
| `snap_id` | 스냅샷 ID | ❌ 미표시 |
| `size_gb` | 디스크 크기 (GB) | ❌ 미표시 |

#### 4. MAIN-METRICS 섹션 (MainMetric)

| 필드 | 설명 | 현재 리포트 표시 |
|------|------|-----------------|
| `snap` | 스냅샷 번호 | ❌ 미표시 |
| `dur_m` | 기간 (분) | ❌ 미표시 |
| `end` | 종료 시간 | ❌ 미표시 |
| `inst` | 인스턴스 번호 | ❌ 미표시 |
| `cpu_per_s` | 초당 CPU 사용량 | ⚠️ 평균만 표시 |
| `read_iops` | 읽기 IOPS | ⚠️ 평균만 표시 |
| `read_mb_s` | 읽기 MB/s | ❌ 미표시 |
| `write_iops` | 쓰기 IOPS | ❌ 미표시 |
| `write_mb_s` | 쓰기 MB/s | ❌ 미표시 |
| `commits_s` | 초당 커밋 수 | ❌ 미표시 |

#### 5. TOP-N-TIMED-EVENTS 섹션 (WaitEvent)

| 필드 | 설명 | 현재 리포트 표시 |
|------|------|-----------------|
| `snap_id` | 스냅샷 ID | ❌ 미표시 |
| `wait_class` | 대기 클래스 | ❌ 미표시 |
| `event_name` | 이벤트 이름 | ❌ 미표시 |
| `pctdbt` | DB Time 비율 | ❌ 미표시 |
| `total_time_s` | 총 대기 시간 (초) | ❌ 미표시 |

#### 6. FEATURES 섹션 (FeatureUsage)

| 필드 | 설명 | 현재 리포트 표시 |
|------|------|-----------------|
| `name` | 기능 이름 | ❌ 미표시 |
| `detected_usages` | 감지된 사용 횟수 | ❌ 미표시 |
| `total_samples` | 총 샘플 수 | ❌ 미표시 |
| `currently_used` | 현재 사용 여부 | ❌ 미표시 |
| `aux_count` | 보조 카운트 | ❌ 미표시 |
| `feature_info` | 기능 정보 | ❌ 미표시 |

#### 7. AWR 특화 섹션 (AWRData)

| 섹션 | 설명 | 현재 리포트 표시 |
|------|------|-----------------|
| `iostat_functions` | 함수별 I/O 통계 | ❌ 미표시 |
| `percentile_cpu` | CPU 백분위수 | ❌ 미표시 |
| `percentile_io` | I/O 백분위수 | ❌ 미표시 |
| `workload_profiles` | 워크로드 프로파일 | ❌ 미표시 |
| `buffer_cache_stats` | 버퍼 캐시 통계 | ❌ 미표시 |

---

## 📊 현재 리포트 표시 현황

### 표시되는 항목 (4개)

```markdown
## AWR/Statspack PL/SQL 통계 (데이터베이스 실제 오브젝트)

- **PL/SQL 코드 라인 수**: 45,230
- **프로시저 수**: 156
- **함수 수**: 89
- **패키지 수**: 34
```

### 누락된 중요 항목

1. **데이터베이스 기본 정보**: 버전, 이름, 크기, 문자셋
2. **오브젝트 통계**: 스키마 수, 테이블 수, 트리거 수, 뷰 수
3. **성능 상세**: 읽기/쓰기 IOPS, 처리량, 커밋 수
4. **대기 이벤트**: Top Wait Events
5. **Oracle 기능 사용 현황**: 사용 중인 Oracle 기능 목록
6. **AWR 특화 데이터**: CPU/IO 백분위수, 워크로드 프로파일

---

## 🎯 개선 제안

### 제안 1: 데이터베이스 개요 섹션 추가

```markdown
## 📊 데이터베이스 개요

> 마이그레이션 대상 Oracle 데이터베이스의 기본 정보입니다.
> 타겟 환경 구성 및 호환성 검토의 기초 자료로 활용됩니다.

### 기본 정보

| 항목 | 값 | 설명 |
|------|-----|------|
| 데이터베이스 이름 | ORCL | 마이그레이션 대상 DB 식별자 |
| Oracle 버전 | 19.3.0.0.0 | 소스 DB 버전. 기능 호환성 검토 기준 |
| 플랫폼 | Linux x86 64-bit | 운영체제 환경 |
| 문자셋 | AL32UTF8 | 문자 인코딩. 타겟 DB 문자셋 설정에 중요 |
| 인스턴스 수 | 2 (RAC) | 1이면 단일 인스턴스, 2 이상이면 RAC 구성 |
| RDS 여부 | No | 이미 AWS RDS인지 여부 |

### 크기 정보

| 항목 | 값 | 설명 |
|------|-----|------|
| 전체 DB 크기 | 1,234 GB | 데이터 파일 총 크기. 스토리지 계획 기준 |
| 물리 메모리 | 256 GB | 서버 총 메모리. 인스턴스 사이징 참고 |
| CPU 코어 수 | 32 | 서버 CPU 코어. vCPU 산정 기준 |

**마이그레이션 시사점**:
- 문자셋이 AL32UTF8이면 Aurora와 호환성 양호
- RAC 구성이면 Aurora Multi-AZ 또는 Global Database 검토 필요
```


### 제안 2: 오브젝트 통계 섹션 확장

```markdown
## 📦 데이터베이스 오브젝트 통계

> 마이그레이션 대상 오브젝트의 전체 현황입니다.
> 오브젝트 유형별 개수를 파악하여 변환 작업량을 추정합니다.

### PL/SQL 오브젝트

> **PL/SQL 오브젝트란?**
> Oracle 데이터베이스에 저장된 프로그램 코드입니다.
> 마이그레이션 시 타겟 DB 문법으로 변환이 필요합니다.

| 오브젝트 유형 | 개수 | 설명 | 변환 난이도 |
|-------------|------|------|------------|
| 패키지 | 34 | 관련 프로시저/함수를 묶은 모듈 | 🔴 높음 (분리 필요) |
| 프로시저 | 156 | 독립 실행 가능한 프로그램 | 🟠 중간 |
| 함수 | 89 | 값을 반환하는 프로그램 | 🟠 중간 |
| 트리거 | 45 | 이벤트 기반 자동 실행 코드 | 🟠 중간 |
| 타입 | 23 | 사용자 정의 데이터 타입 | 🔴 높음 |
| **총 PL/SQL 라인 수** | **45,230** | 전체 코드량 | - |

**변환 작업량 추정**:
- 라인 수 × 평균 변환 시간(20분/100줄) = 약 150시간
- AI 도구 활용 시 40% 단축 가능

### 스키마 오브젝트

> **스키마 오브젝트란?**
> 테이블, 뷰, 인덱스 등 데이터 구조를 정의하는 오브젝트입니다.
> 대부분 자동 변환 도구(SCT)로 처리 가능합니다.

| 오브젝트 유형 | 개수 | 설명 | 변환 방법 |
|-------------|------|------|----------|
| 스키마 | 12 | 오브젝트를 그룹화하는 네임스페이스 | SCT 자동 변환 |
| 테이블 | 456 | 데이터 저장 구조 | SCT 자동 변환 |
| 뷰 | 78 | 가상 테이블 (쿼리 기반) | 일부 수동 검토 필요 |
| 인덱스 | 890 | 검색 성능 최적화 구조 | SCT 자동 변환 |
| 시퀀스 | 34 | 자동 증가 번호 생성기 | SCT 자동 변환 |
| 시노님 | 123 | 오브젝트 별칭 | PostgreSQL: 미지원, 뷰로 대체 |

**마이그레이션 시사점**:
- 시노님이 많으면 PostgreSQL 마이그레이션 시 추가 작업 필요
- 뷰에 Oracle 전용 함수가 있으면 수동 변환 필요
```

### 제안 3: 성능 메트릭 상세 섹션

```markdown
## ⚡ 성능 메트릭 상세

> 이 섹션은 AWR/Statspack에서 수집된 실제 운영 환경의 성능 데이터입니다.
> 마이그레이션 후 타겟 인스턴스 사이징 및 성능 기준선 설정에 활용됩니다.

### CPU 사용량

| 메트릭 | 값 | 설명 |
|--------|-----|------|
| 평균 CPU 사용률 | 45.2% | 분석 기간 동안의 평균 CPU 사용률. 타겟 인스턴스 vCPU 산정 기준 |
| 최대 CPU 사용률 (99th) | 78.5% | 99번째 백분위수. 피크 시간대 제외한 실질적 최대치 |
| 피크 CPU 사용률 | 92.3% | 관측된 최대값. 버스트 용량 계획에 활용 |

### I/O 성능

> **IOPS**: 초당 I/O 작업 수. 스토리지 성능의 핵심 지표
> **처리량(MB/s)**: 초당 전송 데이터량. 대용량 데이터 처리 능력 지표

| 메트릭 | 읽기 | 쓰기 | 합계 | 설명 |
|--------|------|------|------|------|
| 평균 IOPS | 5,234 | 1,234 | 6,468 | 일반적인 워크로드 기준 |
| 평균 처리량 (MB/s) | 156.7 | 45.2 | 201.9 | 데이터 전송 속도 |
| 최대 IOPS (99th) | 12,345 | 3,456 | 15,801 | 피크 시 필요 성능 |

**마이그레이션 시사점**:
- Aurora는 스토리지 I/O가 자동 확장되므로 IOPS 제한 걱정 불필요
- 읽기 비중이 높으면 Read Replica 활용 권장

### 트랜잭션

| 메트릭 | 값 | 설명 |
|--------|-----|------|
| 평균 커밋/초 | 234.5 | 트랜잭션 처리량. OLTP 워크로드 특성 지표 |
| 최대 커밋/초 | 567.8 | 피크 시 트랜잭션 처리 요구량 |

**마이그레이션 시사점**:
- 커밋/초가 높으면 Aurora의 분산 스토리지가 유리 (로그 동기화 오버헤드 감소)
```

### 제안 4: Top Wait Events 섹션

```markdown
## ⏱️ Top Wait Events

> **Wait Event란?**
> Oracle 데이터베이스가 특정 작업을 기다리는 동안 발생하는 이벤트입니다.
> 대기 이벤트 분석을 통해 성능 병목 지점을 파악하고, 마이그레이션 후 주의해야 할 영역을 식별합니다.

### Wait Class 설명

| Wait Class | 설명 | 마이그레이션 고려사항 |
|------------|------|---------------------|
| **User I/O** | 데이터 파일 읽기/쓰기 대기 | 스토리지 성능 중요, Aurora I/O 최적화 검토 |
| **Concurrency** | 락, 래치 등 동시성 제어 대기 | 락 경합 패턴이 타겟 DB에서도 유사하게 발생 가능 |
| **Network** | 네트워크 통신 대기 | 애플리케이션-DB 간 거리, 연결 풀 설정 검토 |
| **Commit** | 트랜잭션 커밋 대기 | Aurora는 분산 로그로 커밋 성능 개선 가능 |
| **Configuration** | 설정 관련 대기 | 타겟 DB 파라미터 튜닝 필요 |

### Top 5 Wait Events

| 순위 | Wait Class | Event Name | DB Time % | 총 대기 시간 | 설명 |
|------|------------|------------|-----------|-------------|------|
| 1 | User I/O | db file sequential read | 25.3% | 1,234초 | 인덱스 스캔 시 단일 블록 읽기 |
| 2 | User I/O | db file scattered read | 15.2% | 756초 | Full Table Scan 시 다중 블록 읽기 |
| 3 | Concurrency | buffer busy waits | 8.7% | 432초 | 동일 블록에 대한 동시 접근 경합 |
| 4 | Network | SQL*Net message from client | 7.5% | 372초 | 클라이언트 응답 대기 (Idle 포함) |
| 5 | Commit | log file sync | 5.2% | 258초 | 리두 로그 디스크 동기화 대기 |

### 마이그레이션 영향 분석

- **User I/O 비중 높음 (40.5%)**: 스토리지 성능이 중요, Aurora I/O 최적화 필요
- **Concurrency 이슈 존재**: 락 경합 패턴 분석 필요
- **Network 대기 존재**: 애플리케이션-DB 간 통신 최적화 검토
```

### 제안 5: Oracle 기능 사용 현황 섹션

```markdown
## 🔧 Oracle 기능 사용 현황

> **이 섹션의 목적**
> Oracle 데이터베이스에서 사용 중인 기능(Feature)을 파악하여 마이그레이션 호환성을 평가합니다.
> 각 기능별로 타겟 데이터베이스에서의 지원 여부와 대체 방안을 제시합니다.

### 마이그레이션 영향도 범례

| 아이콘 | 의미 | 설명 |
|--------|------|------|
| 🟢 | 호환 | 타겟 DB에서 동일/유사 기능 지원 |
| 🟠 | 부분 호환 | 일부 기능 제한 또는 다른 방식으로 구현 필요 |
| 🔴 | 비호환 | 대체 방안 필요 또는 아키텍처 변경 필요 |

### 현재 사용 중인 기능

| 기능 | 사용 횟수 | 영향도 | 설명 | 마이그레이션 대응 |
|------|----------|--------|------|------------------|
| Partitioning | 1,234 | 🟠 | 대용량 테이블 분할 관리 | PostgreSQL: 네이티브 지원, MySQL: 제한적 |
| Advanced Compression | 567 | 🔴 | 데이터 압축으로 스토리지 절감 | Aurora 스토리지 비용 비교 필요 |
| Real Application Clusters | 사용 중 | 🔴 | 다중 인스턴스 고가용성 | Aurora Multi-AZ 또는 Global Database |
| Spatial | 89 | 🟠 | 지리 공간 데이터 처리 | PostGIS 또는 MySQL Spatial 사용 |
| OLAP | 45 | 🔴 | 다차원 분석 기능 | Amazon Redshift 또는 Athena 검토 |
| Data Mining | 12 | 🔴 | 기계 학습 기능 | Amazon SageMaker 연동 |

### 데이터 출처 및 해석

> **중요**: 이 데이터는 Oracle `DBA_FEATURE_USAGE_STATISTICS` 뷰에서 추출됩니다.
> Oracle이 자동으로 기능 사용을 추적하며, **실제 사용된 기능만** 목록에 표시됩니다.
> 목록에 없는 기능은 해당 DB에서 사용하지 않는 것입니다.

| 필드 | 설명 |
|------|------|
| DETECTED_USAGES | 해당 기능이 감지된 횟수 |
| TOTAL_SAMPLES | 총 샘플링 횟수 |
| CURRENTLY_USED | 현재 사용 여부 (TRUE/FALSE) |
| FEATURE_INFO | 기능별 상세 정보 (파티션 수, 설정값 등) |

### 기능 유형 구분 (system vs user)

> **주의**: 기능 이름에 `(system)` 또는 `(user)` 접미사가 붙어 있습니다.
> 마이그레이션 시 **`(user)` 기능에 집중**해야 합니다.

| 접미사 | 의미 | 마이그레이션 영향 |
|--------|------|-----------------|
| `(system)` | Oracle 내부/시스템 스키마에서 사용 | 🟢 대부분 무시 가능 |
| `(user)` | **사용자 애플리케이션에서 사용** | 🔴 **반드시 검토 필요** |
| 없음 | 일반 기능 (컨텍스트에 따라 판단) | 🟠 상황별 판단 |

**예시**:
- `Partitioning (system)`: Oracle 딕셔너리 테이블이 파티셔닝 사용 → 무시
- `Partitioning (user)`: 사용자 테이블이 파티셔닝 사용 → **마이그레이션 시 변환 필요**
- `Locally Managed Tablespaces (system)`: 시스템 테이블스페이스 설정 → 무시
- `Locally Managed Tablespaces (user)`: 사용자 테이블스페이스 설정 → 타겟 DB 설정 참고

### 마이그레이션 영향 요약

- **호환 기능**: 타겟 DB에서 유사 기능 지원
- **대체 필요 기능**: 다른 방식으로 구현 필요
- **아키텍처 변경 필요**: 근본적인 설계 변경 필요

**참고**: 목록에 없는 Oracle EE 기능(Advanced Compression, OLAP, Data Mining 등)은 
해당 DB에서 사용하지 않으므로 마이그레이션 시 고려 대상이 아닙니다.
```


### 제안 6: AWR 특화 데이터 섹션 (AWR 리포트인 경우)

```markdown
## 📈 AWR 상세 분석

> **AWR(Automatic Workload Repository)란?**
> Oracle이 자동으로 수집하는 성능 통계 데이터입니다. 
> Statspack보다 더 상세한 백분위수 분석과 워크로드 프로파일을 제공합니다.
> 이 섹션은 AWR 리포트를 입력한 경우에만 표시됩니다.

### CPU 백분위수 분포

> **백분위수(Percentile)란?**
> 데이터를 크기 순으로 정렬했을 때 특정 위치의 값입니다.
> - **99th**: 상위 1%를 제외한 최대값 (일시적 스파이크 제외)
> - **95th**: 상위 5%를 제외한 값 (일반적인 피크 기준)
> - **Median**: 중앙값 (일반적인 운영 상태)

| 백분위수 | On CPU | On CPU + Resource Mgr | 설명 |
|---------|--------|----------------------|------|
| Maximum | 92 | 95 | 관측된 최대값 (이상치 포함) |
| 99th | 78 | 82 | 실질적 최대 부하 기준 |
| 95th | 65 | 68 | 피크 시간대 일반적 부하 |
| 90th | 58 | 61 | 높은 부하 시간대 |
| Median | 45 | 48 | 일반적인 운영 상태 |

**인스턴스 사이징 권장**:
- 평균(Median) 기준: 50% 여유 확보
- 99th 기준: 버스트 대응 가능한 인스턴스 선택

### I/O 백분위수 분포

> **IOPS vs MB/s**
> - **IOPS**: 초당 I/O 작업 수. 랜덤 I/O 성능 지표 (OLTP에 중요)
> - **MB/s**: 초당 전송량. 순차 I/O 성능 지표 (배치/리포트에 중요)

| 백분위수 | RW IOPS | Read IOPS | Write IOPS | RW MB/s | 설명 |
|---------|---------|-----------|------------|---------|------|
| Maximum | 15,801 | 12,345 | 3,456 | 450 | 최대 I/O 요구량 |
| 99th | 12,500 | 10,000 | 2,500 | 380 | 피크 시 I/O 기준 |
| 95th | 10,000 | 8,000 | 2,000 | 320 | 높은 부하 시 I/O |

**Aurora 스토리지 특성**:
- IOPS 제한 없음 (자동 확장)
- I/O 비용은 사용량 기반 과금

### 버퍼 캐시 효율

> **Buffer Cache Hit Ratio란?**
> 데이터 요청 시 메모리(버퍼 캐시)에서 찾은 비율입니다.
> 높을수록 디스크 I/O가 적어 성능이 좋습니다.
> - **95% 이상**: 양호
> - **90-95%**: 개선 여지 있음
> - **90% 미만**: 메모리 증설 또는 쿼리 최적화 필요

| 메트릭 | 값 | 설명 |
|--------|-----|------|
| 평균 Hit Ratio | 98.5% | 전체 기간 평균 (양호) |
| 최소 Hit Ratio | 95.2% | 최악의 경우에도 양호 |
| DB Cache 크기 | 64 GB | 현재 버퍼 캐시 할당량 |

**마이그레이션 시사점**:
- Hit Ratio가 높으면 현재 메모리 설정이 적절
- Aurora는 버퍼 풀 자동 관리로 튜닝 부담 감소

### Top 워크로드 프로파일

> **워크로드 프로파일이란?**
> 어떤 애플리케이션/모듈이 DB 리소스를 얼마나 사용하는지 보여줍니다.
> - **AAS (Average Active Sessions)**: 평균 활성 세션 수. 동시 부하 지표
> - **DB Time %**: 전체 DB 시간 중 해당 워크로드가 차지하는 비율

| 순위 | Module | Program | AAS | DB Time % | 설명 |
|------|--------|---------|-----|-----------|------|
| 1 | BATCH_JOB | sqlplus | 2.5 | 35.2% | 배치 작업 (야간 처리 추정) |
| 2 | ONLINE_APP | jdbc | 1.8 | 25.3% | 온라인 애플리케이션 |
| 3 | REPORT_SVC | perl | 1.2 | 16.8% | 리포트 서비스 |

**마이그레이션 우선순위 결정**:
- DB Time % 높은 워크로드부터 테스트 우선
- 배치 작업은 마이그레이션 후 성능 검증 필수
```
```

---

## 🔄 데이터 모델 확장 제안

### AnalysisMetrics 확장

```python
@dataclass
class AnalysisMetrics:
    """추출된 분석 메트릭 (확장)"""
    
    # === 기존 필드 ===
    avg_cpu_usage: float
    avg_io_load: float
    avg_memory_usage: float
    avg_sql_complexity: float
    avg_plsql_complexity: float
    # ... (기존 필드 유지)
    
    # === 신규 필드: 데이터베이스 기본 정보 ===
    db_name: Optional[str] = None
    db_version: Optional[str] = None
    platform_name: Optional[str] = None
    character_set: Optional[str] = None
    instance_count: Optional[int] = None
    is_rac: bool = False
    is_rds: bool = False
    total_db_size_gb: Optional[float] = None
    physical_memory_gb: Optional[float] = None
    cpu_cores: Optional[int] = None
    
    # === 신규 필드: 오브젝트 통계 ===
    count_schemas: Optional[int] = None
    count_tables: Optional[int] = None
    count_views: Optional[int] = None
    count_indexes: Optional[int] = None
    count_triggers: Optional[int] = None
    count_types: Optional[int] = None
    count_sequences: Optional[int] = None
    count_synonyms: Optional[int] = None
    
    # === 신규 필드: 성능 상세 ===
    avg_read_iops: Optional[float] = None
    avg_write_iops: Optional[float] = None
    avg_read_mbps: Optional[float] = None
    avg_write_mbps: Optional[float] = None
    avg_commits_per_sec: Optional[float] = None
    peak_cpu_usage: Optional[float] = None
    peak_iops: Optional[float] = None
    
    # === 신규 필드: 대기 이벤트 ===
    top_wait_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # === 신규 필드: Oracle 기능 사용 ===
    oracle_features_used: List[Dict[str, Any]] = field(default_factory=list)
    
    # === 신규 필드: AWR 특화 (Optional) ===
    cpu_percentiles: Optional[Dict[str, float]] = None
    io_percentiles: Optional[Dict[str, float]] = None
    buffer_cache_hit_ratio: Optional[float] = None
    top_workload_profiles: List[Dict[str, Any]] = field(default_factory=list)
```

### Integrator 확장

```python
def extract_metrics(
    self,
    dbcsi_data: Optional[Union[StatspackData, AWRData]],
    sql_analysis: List[SQLAnalysisResult],
    plsql_analysis: List[PLSQLAnalysisResult]
) -> AnalysisMetrics:
    """분석 결과에서 메트릭을 추출합니다 (확장)"""
    
    # 기존 메트릭 추출
    # ...
    
    # 신규: 데이터베이스 기본 정보
    if dbcsi_data and dbcsi_data.os_info:
        os_info = dbcsi_data.os_info
        db_name = os_info.db_name
        db_version = os_info.version
        platform_name = os_info.platform_name
        character_set = os_info.character_set
        instance_count = os_info.instances
        is_rac = (os_info.instances or 1) > 1
        is_rds = os_info.is_rds or False
        total_db_size_gb = os_info.total_db_size_gb
        physical_memory_gb = os_info.physical_memory_gb
        cpu_cores = os_info.num_cpu_cores
        
        # 오브젝트 통계
        count_schemas = os_info.count_schemas
        count_tables = os_info.count_tables
        # ...
    
    # 신규: 대기 이벤트
    if dbcsi_data and dbcsi_data.wait_events:
        top_wait_events = self._extract_top_wait_events(dbcsi_data.wait_events)
    
    # 신규: Oracle 기능 사용
    if dbcsi_data and dbcsi_data.features:
        oracle_features_used = self._extract_features_used(dbcsi_data.features)
    
    # 신규: AWR 특화 데이터
    if isinstance(dbcsi_data, AWRData) and dbcsi_data.is_awr():
        cpu_percentiles = self._extract_cpu_percentiles(dbcsi_data.percentile_cpu)
        io_percentiles = self._extract_io_percentiles(dbcsi_data.percentile_io)
        buffer_cache_hit_ratio = self._calculate_avg_hit_ratio(dbcsi_data.buffer_cache_stats)
        top_workload_profiles = self._extract_top_workloads(dbcsi_data.workload_profiles)
    
    return AnalysisMetrics(
        # 기존 필드
        # ...
        # 신규 필드
        db_name=db_name,
        db_version=db_version,
        # ...
    )
```


---

## 📋 구현 우선순위

### 🔴 우선순위 높음 (Phase 1)

| 항목 | 이유 | 예상 시간 |
|------|------|----------|
| 데이터베이스 기본 정보 | 마이그레이션 계획의 기초 | 2시간 |
| 오브젝트 통계 전체 | PL/SQL 외 오브젝트도 중요 | 2시간 |
| Oracle 기능 사용 현황 | 호환성 평가에 필수 | 3시간 |

### 🟠 우선순위 중간 (Phase 2)

| 항목 | 이유 | 예상 시간 |
|------|------|----------|
| 성능 메트릭 상세 | 인스턴스 사이징에 활용 | 2시간 |
| Top Wait Events | 성능 특성 파악 | 2시간 |
| I/O 상세 (읽기/쓰기 분리) | 스토리지 계획에 활용 | 1시간 |

### 🟢 우선순위 낮음 (Phase 3)

| 항목 | 이유 | 예상 시간 |
|------|------|----------|
| AWR 백분위수 데이터 | 상세 분석용 | 2시간 |
| 워크로드 프로파일 | 고급 분석용 | 2시간 |
| 버퍼 캐시 통계 | 튜닝 참고용 | 1시간 |

### 총 예상 시간: 17시간

---

## 🔧 코드 변경 범위

### 변경 필요 파일

| 파일 | 변경 내용 |
|------|----------|
| `src/migration_recommendation/data_models.py` | `AnalysisMetrics` 필드 추가 |
| `src/migration_recommendation/integrator.py` | 메트릭 추출 로직 확장 |
| `src/migration_recommendation/formatters/markdown/metrics.py` | 리포트 포맷 확장 |
| `src/migration_recommendation/formatters/markdown/__init__.py` | 새 섹션 통합 |

### 신규 생성 파일 (권장)

| 파일 | 내용 |
|------|------|
| `src/migration_recommendation/formatters/markdown/database_overview.py` | DB 개요 섹션 |
| `src/migration_recommendation/formatters/markdown/object_statistics.py` | 오브젝트 통계 섹션 |
| `src/migration_recommendation/formatters/markdown/wait_events.py` | 대기 이벤트 섹션 |
| `src/migration_recommendation/formatters/markdown/oracle_features.py` | Oracle 기능 섹션 |
| `src/migration_recommendation/formatters/markdown/awr_details.py` | AWR 상세 섹션 |

---

## 📊 예상 리포트 구조 (개선 후)

```markdown
# Oracle Migration Recommendation Report

## Executive Summary
(기존 유지)

## 추천 전략
(기존 유지)

## 📊 데이터베이스 개요 (신규)
### 기본 정보
### 크기 정보

## 📦 데이터베이스 오브젝트 통계 (확장)
### PL/SQL 오브젝트
### 스키마 오브젝트

## ⚡ 성능 메트릭 상세 (확장)
### CPU 사용량
### I/O 성능
### 트랜잭션

## ⏱️ Top Wait Events (신규)
### 대기 이벤트 목록
### 마이그레이션 영향 분석

## 🔧 Oracle 기능 사용 현황 (신규)
### 현재 사용 중인 기능
### 마이그레이션 영향 요약

## 📈 AWR 상세 분석 (신규, AWR인 경우만)
### CPU 백분위수 분포
### I/O 백분위수 분포
### 버퍼 캐시 효율
### Top 워크로드 프로파일

## 추천 근거
(기존 유지)

## 대안 전략
(기존 유지)

## 위험 요소
(기존 유지)

## 마이그레이션 로드맵
(기존 유지)

## 분석 메트릭 (부록)
(기존 유지, 상세 데이터 참조용)
```

---

## 🎯 기대 효과

### 정보 완전성

| 항목 | 현재 | 개선 후 |
|------|------|---------|
| 표시되는 DBCSI 데이터 | 20% | 90% |
| 의사결정 지원 정보 | 제한적 | 포괄적 |
| 마이그레이션 계획 수립 | 추가 조사 필요 | 리포트만으로 가능 |

### 사용자 가치

1. **원스톱 리포트**: 추가 데이터 수집 없이 리포트만으로 계획 수립
2. **투명성**: 어떤 데이터를 기반으로 추천했는지 명확히 표시
3. **상세 분석**: 필요시 AWR 상세 데이터까지 확인 가능
4. **호환성 평가**: Oracle 기능 사용 현황으로 호환성 사전 파악

---

## 📚 관련 문서

| 문서 | 설명 |
|------|------|
| [ANALYSIS_MODES_AND_DATA_REQUIREMENTS.md](ANALYSIS_MODES_AND_DATA_REQUIREMENTS.md) | 분석 모드 및 데이터 요구사항 |
| [WHAT_IS_ORACLE_MIGRATION_ANALYZER.md](WHAT_IS_ORACLE_MIGRATION_ANALYZER.md) | 도구 소개 |

---

## 📝 문서 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0 | 2026-01-28 | 초안 작성 |

---

## 🏁 결론

DBCSI 파서는 이미 풍부한 데이터를 추출하고 있지만, 현재 리포트에는 약 20%만 표시되고 있습니다. 제안된 개선을 통해:

1. **데이터베이스 기본 정보**: 버전, 크기, 문자셋 등 기초 정보 제공
2. **오브젝트 통계 확장**: PL/SQL 외 테이블, 뷰, 인덱스 등 전체 오브젝트 현황
3. **성능 메트릭 상세**: 읽기/쓰기 분리, 백분위수 등 상세 성능 데이터
4. **Oracle 기능 사용 현황**: 호환성 평가를 위한 필수 정보
5. **대기 이벤트 분석**: 성능 특성 파악 및 마이그레이션 영향 분석

이를 통해 마이그레이션 추천 리포트가 **원스톱 의사결정 문서**로 기능할 수 있습니다.

---

> **참고**: 이 문서는 기능 제안서이며, 실제 구현은 별도 검토 후 진행됩니다.
