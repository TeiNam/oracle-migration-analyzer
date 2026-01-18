# 파일 크기 검증 보고서

**작성일**: 2026-01-19  
**Phase**: 4.27 파일 크기 검증

---

## 요약

- **전체 Python 파일 수**: 60개
- **500줄 이상 파일**: 9개 (15%)
- **300-500줄 파일**: 11개 (18.3%)
- **300줄 미만 파일**: 40개 (66.7%)

---

## 500줄 이상 파일 (즉시 리팩토링 필요)

### 1. src/dbcsi/migration_analyzer/analyzer.py (1,013줄)
**상태**: ⚠️ 긴급 리팩토링 필요  
**현재 책임**:
- 메인 분석 오케스트레이션
- 여러 분석기 통합
- 결과 집계

**제안**:
- 이미 서브 모듈로 분리되어 있으나, analyzer.py 자체가 너무 큼
- 추가 분리 옵션:
  - `orchestrator.py`: 메인 분석 흐름 관리
  - `result_aggregator.py`: 결과 집계 로직
  - `analyzer.py`: 핵심 분석 로직만 유지

### 2. src/calculators/complexity_calculator.py (948줄)
**상태**: ⚠️ 긴급 리팩토링 필요  
**현재 책임**:
- SQL 복잡도 계산
- PL/SQL 복잡도 계산
- 다양한 메트릭 계산

**제안**:
- `src/calculators/` 디렉토리로 변환
  - `sql_complexity.py`: SQL 복잡도 계산
  - `plsql_complexity.py`: PL/SQL 복잡도 계산
  - `metrics.py`: 공통 메트릭 계산
  - `base.py`: 베이스 클래스

### 3. src/parsers/plsql_parser.py (839줄)
**상태**: ⚠️ 긴급 리팩토링 필요  
**현재 책임**:
- PL/SQL 구문 파싱
- 패키지, 프로시저, 함수 파싱
- 복잡한 구문 분석

**제안**:
- `src/parsers/plsql/` 디렉토리로 변환
  - `package_parser.py`: 패키지 파싱
  - `procedure_parser.py`: 프로시저 파싱
  - `function_parser.py`: 함수 파싱
  - `base_parser.py`: 공통 파싱 로직

### 4. src/dbcsi/formatters/awr_formatter.py (649줄)
**상태**: ⚠️ 긴급 리팩토링 필요  
**현재 책임**:
- AWR 리포트 포맷팅
- 다양한 섹션 포맷팅
- Markdown/JSON 출력

**제안**:
- `src/dbcsi/formatters/awr/` 디렉토리로 변환
  - `section_formatters.py`: 섹션별 포맷터
  - `markdown_formatter.py`: Markdown 출력
  - `json_formatter.py`: JSON 출력
  - `base_formatter.py`: 공통 포맷팅 로직

### 5. src/migration_recommendation/formatters.py (633줄)
**상태**: ⚠️ 긴급 리팩토링 필요  
**현재 책임**:
- 추천 리포트 포맷팅
- Markdown 출력
- JSON 출력

**제안**:
- `src/migration_recommendation/formatters/` 디렉토리로 변환
  - `markdown_formatter.py`: Markdown 출력
  - `json_formatter.py`: JSON 출력
  - `section_formatters.py`: 섹션별 포맷터

### 6. src/dbcsi/batch_analyzer.py (598줄)
**상태**: ⚠️ 리팩토링 필요  
**현재 책임**:
- 배치 분석 오케스트레이션
- 파일 처리
- 결과 집계

**제안**:
- `src/dbcsi/batch/` 디렉토리로 변환
  - `analyzer.py`: 메인 배치 분석
  - `file_processor.py`: 파일 처리
  - `result_aggregator.py`: 결과 집계

### 7. src/dbcsi/data_models.py (560줄)
**상태**: ⚠️ 리팩토링 필요  
**현재 책임**:
- 모든 데이터 모델 정의
- 다양한 분석 결과 모델

**제안**:
- `src/dbcsi/models/` 디렉토리로 변환
  - `awr_models.py`: AWR 관련 모델
  - `statspack_models.py`: Statspack 관련 모델
  - `analysis_models.py`: 분석 결과 모델
  - `base_models.py`: 공통 베이스 모델

### 8. src/oracle_complexity_analyzer/batch_analyzer.py (528줄)
**상태**: ⚠️ 리팩토링 필요  
**현재 책임**:
- 배치 분석
- 파일 처리
- 결과 집계

**제안**:
- 기능별 분리:
  - `file_processor.py`: 파일 처리 로직
  - `result_aggregator.py`: 결과 집계
  - `batch_analyzer.py`: 메인 배치 로직 (축소)

### 9. src/dbcsi/cli.py (523줄)
**상태**: ⚠️ 리팩토링 필요  
**현재 책임**:
- CLI 인터페이스
- 인자 파싱
- 명령 실행

**제안**:
- `src/dbcsi/cli/` 디렉토리로 변환
  - `main.py`: 메인 CLI 진입점
  - `argument_parser.py`: 인자 파싱
  - `command_handlers.py`: 명령 핸들러

---

## 300-500줄 파일 (리팩토링 권장)

1. **src/oracle_complexity_analyzer/__main__.py** - 490줄
2. **src/dbcsi/migration_analyzer/complexity_calculators.py** - 488줄
3. **src/migration_recommendation/cli.py** - 481줄
4. **src/formatters/result_formatter.py** - 467줄
5. **src/parsers/sql_parser.py** - 413줄
6. **src/dbcsi/parsers/base_parser.py** - 400줄
7. **src/formatters/conversion_guide_provider.py** - 394줄
8. **src/dbcsi/formatters/statspack_formatter.py** - 389줄
9. **src/dbcsi/parsers/awr_parser.py** - 388줄
10. **src/oracle_complexity_analyzer/analyzer.py** - 369줄
11. **src/migration_recommendation/report_generator/rationale_generator.py** - 366줄

이 파일들은 현재는 허용 가능하지만, 향후 기능 추가 시 500줄을 초과할 가능성이 있습니다.

---

## 권장 조치

### 우선순위 1 (즉시 처리)
1. `src/calculators/complexity_calculator.py` (948줄) → 디렉토리로 변환
2. `src/parsers/plsql_parser.py` (839줄) → 디렉토리로 변환
3. `src/dbcsi/migration_analyzer/analyzer.py` (1,013줄) → 추가 분리

### 우선순위 2 (1주 내 처리)
4. `src/dbcsi/formatters/awr_formatter.py` (649줄) → 디렉토리로 변환
5. `src/migration_recommendation/formatters.py` (633줄) → 디렉토리로 변환
6. `src/dbcsi/batch_analyzer.py` (598줄) → 디렉토리로 변환

### 우선순위 3 (2주 내 처리)
7. `src/dbcsi/data_models.py` (560줄) → 디렉토리로 변환
8. `src/oracle_complexity_analyzer/batch_analyzer.py` (528줄) → 기능별 분리
9. `src/dbcsi/cli.py` (523줄) → 디렉토리로 변환

---

## 예상 작업 시간

| 파일 | 예상 시간 | 난이도 |
|------|-----------|--------|
| complexity_calculator.py | 4시간 | 중 |
| plsql_parser.py | 5시간 | 높음 |
| migration_analyzer/analyzer.py | 4시간 | 중 |
| awr_formatter.py | 3시간 | 중 |
| formatters.py | 3시간 | 중 |
| batch_analyzer.py | 3시간 | 중 |
| data_models.py | 2시간 | 낮음 |
| batch_analyzer.py (oracle) | 2시간 | 낮음 |
| cli.py | 3시간 | 중 |
| **총계** | **29시간** | - |

---

## 성공 기준

- [ ] 모든 파일이 500줄 미만
- [ ] 기존 테스트 모두 통과
- [ ] 기존 import 경로 정상 작동
- [ ] CLI 명령어 정상 작동
- [ ] 성능 저하 없음

---

## 다음 단계

1. Task 4.28-4.36 생성 (9개 파일 리팩토링)
2. 각 파일별 상세 리팩토링 계획 수립
3. 순차적 리팩토링 진행
4. 각 단계마다 테스트 실행 및 검증
