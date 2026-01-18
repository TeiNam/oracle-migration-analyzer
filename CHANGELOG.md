# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

