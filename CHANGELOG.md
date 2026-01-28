# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-01-28

### Changed - PL/SQL 복잡도 점수 개선 (PLSQL_COMPLEXITY_SCORE_IMPROVEMENT.md 기반)

**점수 계수 상향 조정**
- 커서 점수: 0.3/개 → 0.5/개, 최대 1.0 → 2.0
  - 커서 4개 이상에서도 차등 점수 적용
- 동적 SQL 점수: 0.5/개 → 0.8/개, 최대 1.0 → 2.0
  - 동적 SQL 복잡도를 더 정확히 반영
- 예외 처리 점수: 0.2/개 → 0.4/개, 최대 0.5 → 1.0
  - Oracle 예외 변환 난이도 반영

**외부 의존성 차등 점수 적용**
- 패키지별 실제 변환 난이도 반영 (기존: 균일 0.5점)
- 매우 어려움 (1.5~2.0점): UTL_FILE, UTL_HTTP, DBMS_SCHEDULER, DBMS_PIPE, DBMS_ALERT, DBMS_LOCK, DBMS_AQ
- 어려움 (0.8~1.2점): UTL_MAIL, UTL_SMTP, DBMS_JOB, DBMS_CRYPTO, DBMS_SQL, DBMS_XMLGEN 등
- 중간 (0.3~0.5점): DBMS_LOB, DBMS_RANDOM, DBMS_UTILITY
- 쉬움 (0.2점): DBMS_OUTPUT
- 최대 점수: 1.0 → 3.0

**코드 라인 수 기준 세분화**
- 50줄 미만: 0.3점 (신규)
- 50-100줄: 0.5점
- 2000-5000줄: 3.0점 (신규)
- 5000줄 이상: 3.5점 (신규)

**신규 감지 항목 추가**
- 타입 참조: %TYPE (0.3~0.5점/개), %ROWTYPE (0.5~0.8점/개)
- 사용자 정의 타입: RECORD (0.5~0.8점/개), TABLE OF (0.8~1.2점/개), VARRAY (0.8~1.2점/개), INDEX BY (1.0~1.5점/개)
- RETURNING INTO: PostgreSQL 0.3점/개, MySQL 0.8점/개
- RAISE_APPLICATION_ERROR: PostgreSQL 0.3점/개, MySQL 0.5점/개
- 조건부 컴파일 ($IF/$ELSE/$END): 0.5점/블록
- 동적 DDL (EXECUTE IMMEDIATE + CREATE/DROP/ALTER): 0.5점/개
- Oracle 전용 예외 (NO_DATA_FOUND, TOO_MANY_ROWS 등): 0.1점/개
- SQLCODE/SQLERRM 사용: 0.2점

**추가 외부 패키지 감지**
- DBMS_PIPE, DBMS_ALERT, DBMS_LOCK, DBMS_AQ
- DBMS_XMLGEN, DBMS_XMLPARSER, DBMS_METADATA
- DBMS_STATS, DBMS_PROFILER, DBMS_TRACE
- UTL_RAW, UTL_ENCODE, UTL_COMPRESS, UTL_I18N
- DBMS_RANDOM, DBMS_UTILITY

### Added
- `count_type_references()`: %TYPE, %ROWTYPE 참조 개수 계산
- `count_user_defined_types()`: RECORD, TABLE OF, VARRAY, INDEX BY 개수 계산
- `count_returning_into()`: RETURNING INTO 절 개수 계산
- `count_raise_application_error()`: RAISE_APPLICATION_ERROR 개수 계산
- `count_conditional_compilation()`: 조건부 컴파일 블록 개수 계산
- `count_dynamic_ddl()`: 동적 DDL 개수 계산
- `detect_oracle_specific_exceptions()`: Oracle 전용 예외 감지
- `has_sqlcode_sqlerrm()`: SQLCODE/SQLERRM 사용 여부 감지
- `EXTERNAL_DEPENDENCY_SCORES`: 외부 의존성 차등 점수 상수

### Fixed
- 테스트 케이스 업데이트 (기본 점수 변경 반영)
- 신규 기능 테스트 33개 추가

**예상 효과**
- 점수-난이도 상관관계: 65% → 85% 향상
- 과대평가 비율: 35% → 15% 감소
- 리소스 예측 정확도: 60% → 80% 향상

**참고 문서**
- `new_docs/PLSQL_COMPLEXITY_SCORE_IMPROVEMENT.md`

## [2.1.0] - 2026-01-28

### Changed - 임계값 개선 (THRESHOLD_IMPROVEMENT_PROPOSAL.md 기반)

**마이그레이션 의사결정 임계값 조정**
- Replatform 복잡도 임계값: 7.0 → 6.0 (SQL/PL-SQL 모두)
  - 복잡도 6.0 이상에서 변환 실패율 급증하는 실제 프로젝트 경험 반영
  - 보수적 접근으로 프로젝트 실패 위험 감소
- MySQL 복잡도 임계값: PL/SQL 5.0 → 3.5, SQL 5.0 → 4.0
  - MySQL Stored Procedure 권장하지 않는 정책 반영
  - 복잡도 3.5 이상에서 애플리케이션 이관 비용 급증
- MySQL PL/SQL 개수 임계값: 50개 → 20개
  - 20개 이상 이관 시 전담 팀 필요한 실제 작업량 반영
- 복잡 오브젝트 비율 임계값: 30% → 25%
  - 더 보수적인 기준으로 위험 감소
- 복잡 오브젝트 절대 개수 조건 추가: 20개 이상
  - 대규모 시스템에서 비율만으로는 위험 과소평가 방지
- 코드 라인 수 기반 Replatform 조건 제거
  - 의사결정 자율성 보장 (비용 효율성은 고객 판단)

**PL/SQL 기본 점수 하향 조정**
- PostgreSQL 타겟:
  - PACKAGE: 7.0 → 4.0
  - PROCEDURE: 5.0 → 2.5
  - FUNCTION: 4.0 → 2.0
  - TRIGGER: 6.0 → 3.5
  - VIEW: 2.0 → 1.0
  - MATERIALIZED_VIEW: 4.0 → 2.5
- MySQL 타겟:
  - PACKAGE: 8.0 → 5.0
  - PROCEDURE: 6.0 → 3.5
  - FUNCTION: 5.0 → 3.0
  - TRIGGER: 7.0 → 4.5
  - VIEW: 2.0 → 1.0
  - MATERIALIZED_VIEW: 5.0 → 3.5
- 기본 점수는 "최소 복잡도"를 의미하도록 조정
- 단순한 코드가 높은 점수를 받는 문제 해결

**영향**
- 더 정확한 마이그레이션 전략 추천
- 프로젝트 실패율 감소 예상 (15% → 5%)
- 일정 지연율 감소 예상 (40% → 20%)
- Replatform 정확도 향상 예상 (70% → 85%)
- MySQL 추천 정확도 향상 예상 (60% → 80%)

**하위 호환성**
- 기존 분석 결과와 새 분석 결과가 다를 수 있음
- 테스트 케이스 모두 업데이트 완료 (12개 테스트 통과)
- 리포트에 사용된 임계값 명시 권장

**참고 문서**
- `new_docs/THRESHOLD_IMPROVEMENT_PROPOSAL.md`

## [2.0.0] - 2026-01-19

### 주요 변경사항
이번 릴리스는 대규모 코드 품질 개선 작업의 결과물입니다. 모든 기능은 하위 호환성을 유지하면서 코드 구조와 품질이 크게 향상되었습니다.

### Added
- **문서화 완성**
  - README_EN.md 추가 (영문 문서)
  - docs 폴더 영문 문서 추가 (migration_guide_EN.md 등)
  - 한/영 문서 상호 링크 추가

- **공통 유틸리티 모듈**
  - `src/utils/cli_helpers.py`: CLI 헬퍼 함수 (파일 타입 감지, 출력 경로 생성 등)
  - `src/utils/file_utils.py`: 파일 처리 유틸리티
  - `src/utils/logging_utils.py`: 로깅 표준화 유틸리티

- **타입 힌트 완성**
  - `src/types.py`: 공통 타입 별칭 정의
  - `mypy.ini`: mypy 설정 파일 추가
  - 주요 모듈에 타입 힌트 추가

### Changed
- **대규모 모듈화 작업**
  - `oracle_complexity_analyzer.py` (1200줄) → 9개 모듈로 분리
  - `dbcsi/migration_analyzer.py` (1100줄) → 9개 모듈로 분리
  - `migration_recommendation/report_generator.py` (800줄) → 6개 모듈로 분리
  - `calculators/complexity_calculator.py` (900줄) → 4개 모듈로 분리
  - `parsers/plsql_parser.py` (900줄) → 5개 모듈로 분리
  - `dbcsi/formatters/awr_formatter.py` (700줄) → 7개 모듈로 분리
  - `migration_recommendation/formatters.py` (700줄) → 9개 모듈로 분리
  - `dbcsi/batch_analyzer.py` (600줄) → 6개 모듈로 분리
  - `dbcsi/data_models.py` (560줄) → 6개 모듈로 분리
  - `oracle_complexity_analyzer/batch_analyzer.py` (528줄) → 3개 모듈로 분리
  - `dbcsi/cli.py` (523줄) → 4개 모듈로 분리

- **로깅 표준화**
  - 모든 `print(..., file=sys.stderr)` → `logger.error()` 변경
  - 일관된 로그 포맷 적용
  - 예외 처리 표준화

- **테스트 개선**
  - 전체 테스트 커버리지: 78% (목표 70% 초과)
  - 654개 테스트 통과 (99.5% 통과율)
  - 속성 기반 테스트 추가

### Fixed
- CLI 헬퍼 테스트 10개 수정 (stderr 캡처)
- 의사결정 엔진 테스트 5개 수정 (Replatform 조건 단순화)
- ConversionGuideProvider 테스트 1개 수정 (enum 비교)
- 포맷터 통합 테스트 4개 수정 (한/영 헤더 허용)
- DBCSI CLI 테스트 6개 수정 (출력 파일 경로 명시)

### Technical Details
- **파일 크기 개선**
  - 500줄 이상 파일: 11개 → 2개 (82% 감소)
  - 최대 파일 크기: 1200줄 → 568줄 (53% 감소)

- **코드 품질 메트릭**
  - 테스트 커버리지: 78%
  - 테스트 통과율: 99.5% (654/657)
  - mypy 타입 체크: 94개 경고 (완화된 설정)
  - 성능: 변화 없음 (테스트 실행 시간 11초 유지)

### Migration Guide
이번 릴리스는 하위 호환성을 유지합니다. 기존 코드는 수정 없이 그대로 사용할 수 있습니다.

**Import 경로 변경 (선택사항)**
```python
# 기존 (여전히 작동함)
from src.oracle_complexity_analyzer import OracleComplexityAnalyzer

# 새로운 방식 (권장)
from src.oracle_complexity_analyzer.analyzer import OracleComplexityAnalyzer
```

**CLI 사용법 변경 없음**
```bash
# 모든 CLI 명령어는 동일하게 작동
python -m src.oracle_complexity_analyzer --file query.sql
python -m src.dbcsi.cli --file statspack.out
python -m src.migration_recommendation.cli --reports-dir reports/
```

### Breaking Changes
없음. 모든 변경사항은 하위 호환성을 유지합니다.

### Deprecated
없음.

### Removed
없음.

### Security
- 입력 검증 강화
- 예외 처리 개선
- 로깅을 통한 보안 이벤트 추적

---

## [1.0.0] - 2025-XX-XX

### Added
- 초기 릴리스
- Oracle SQL/PL-SQL 복잡도 분석 기능
- Statspack/AWR 분석 기능
- 마이그레이션 추천 기능
- CLI 인터페이스
- JSON/Markdown 출력 지원

