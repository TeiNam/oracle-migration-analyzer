# Oracle Complexity Analyzer

Oracle SQL 및 PL/SQL 코드의 복잡도를 분석하여 PostgreSQL 또는 MySQL로의 마이그레이션 난이도를 0-10 척도로 평가하는 Python 기반 도구입니다.

## 주요 기능

- ✅ **SQL 쿼리 복잡도 분석**: 6가지 카테고리로 구조적 복잡성 평가
- ✅ **PL/SQL 오브젝트 분석**: Package, Procedure, Function, Trigger 등 분석
- ✅ **타겟 DB별 가중치**: PostgreSQL/MySQL 각각에 최적화된 복잡도 계산
- ✅ **Oracle 특화 기능 감지**: CONNECT BY, PIVOT, 분석 함수 등 자동 감지
- ✅ **변환 가이드 제공**: 감지된 Oracle 기능에 대한 타겟 DB별 대체 방법 제시
- ✅ **폴더 일괄 분석**: 병렬 처리로 대량 파일 빠른 분석
- ✅ **다양한 출력 형식**: JSON, Markdown, 콘솔 출력 지원

## 설치

### 요구사항

- Python 3.8 이상
- pip 패키지 관리자

### 설치 방법

```bash
# 저장소 클론
git clone <repository-url>
cd oracle-complexity-analyzer

# 가상 환경 생성 (권장)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 패키지 설치 (개발 모드)
pip install -e .
```

## 사용 방법

### 기본 사용법

```bash
# 도움말 보기
oracle-complexity-analyzer --help

# 버전 확인
oracle-complexity-analyzer --version
```

### 단일 파일 분석

```bash
# PostgreSQL 타겟으로 SQL 파일 분석 (기본값)
oracle-complexity-analyzer -f query.sql

# MySQL 타겟으로 PL/SQL 파일 분석
oracle-complexity-analyzer -f package.pls -t mysql

# 결과를 JSON 파일로 저장
oracle-complexity-analyzer -f query.sql -o json

# 결과를 Markdown 파일로 저장
oracle-complexity-analyzer -f query.sql -o markdown

# 콘솔 출력 + JSON/Markdown 파일 저장
oracle-complexity-analyzer -f query.sql -o both
```

### 폴더 일괄 분석

```bash
# 폴더 내 모든 SQL/PL/SQL 파일 분석 (요약만)
oracle-complexity-analyzer -d /path/to/sql/files

# MySQL 타겟으로 폴더 분석
oracle-complexity-analyzer -d /path/to/sql/files -t mysql

# 개별 파일 상세 결과 포함 (권장)
oracle-complexity-analyzer -d /path/to/sql/files --details

# 병렬 워커 수 지정 (기본값: 4)
oracle-complexity-analyzer -d /path/to/sql/files -w 8

# JSON/Markdown 형식으로 결과 저장
oracle-complexity-analyzer -d /path/to/sql/files -o json
oracle-complexity-analyzer -d /path/to/sql/files -o markdown

# 진행 상황 표시 비활성화
oracle-complexity-analyzer -d /path/to/sql/files --no-progress

# 실전 예제: sample_code 폴더의 모든 파일을 PostgreSQL 타겟으로 분석
oracle-complexity-analyzer -d sample_code -t postgresql --details -o markdown
```

### 출력 디렉토리 지정

```bash
# 기본 출력 디렉토리: reports/YYYYMMDD/
oracle-complexity-analyzer -f query.sql -o json

# 사용자 지정 출력 디렉토리
oracle-complexity-analyzer -f query.sql -o json --output-dir my_reports
```

## 명령줄 옵션

### 필수 옵션 (둘 중 하나 선택)

- `-f FILE`, `--file FILE`: 분석할 단일 SQL/PL/SQL 파일 경로
- `-d DIR`, `--directory DIR`: 분석할 폴더 경로 (하위 폴더 포함)

### 선택 옵션

- `-t DB`, `--target DB`: 타겟 데이터베이스 선택
  - `postgresql`, `pg`: PostgreSQL (기본값)
  - `mysql`, `my`: MySQL

- `-o FORMAT`, `--output FORMAT`: 출력 형식 선택
  - `console`: 콘솔 출력만 (기본값)
  - `json`: JSON 파일로 저장
  - `markdown`: Markdown 파일로 저장
  - `both`: 콘솔 출력 + JSON/Markdown 파일 저장

- `--output-dir DIR`: 출력 디렉토리 경로 (기본값: `reports`)

- `-w N`, `--workers N`: 병렬 처리 워커 수 (폴더 분석 시, 기본값: CPU 코어 수)

- `--details`: 배치 분석 시 개별 파일 상세 결과 포함

- `--no-progress`: 진행 상황 표시 비활성화

- `-v`, `--version`: 버전 정보 출력

- `-h`, `--help`: 도움말 출력

## 지원 파일 확장자

- `.sql`: SQL 쿼리 파일
- `.pls`: PL/SQL 파일
- `.pkb`: Package Body 파일
- `.pks`: Package Specification 파일
- `.prc`: Procedure 파일
- `.fnc`: Function 파일
- `.trg`: Trigger 파일

## 출력 예시

### 콘솔 출력

```
================================================================================
📊 Oracle 복잡도 분석 결과
================================================================================

타겟 데이터베이스: postgresql
복잡도 점수: 5.23 / 10
복잡도 레벨: 복잡
권장사항: 상당한 재작성

📈 세부 점수:
  - 구조적 복잡성: 1.50
  - Oracle 특화 기능: 2.00
  - 함수/표현식: 1.00
  - 데이터 볼륨: 0.50
  - 실행 복잡성: 0.23
  - 변환 난이도: 0.00

🔍 감지된 Oracle 특화 기능:
  - CONNECT BY
  - ROWNUM

🔧 감지된 Oracle 특화 함수:
  - DECODE
  - NVL

💡 변환 가이드:
  - CONNECT BY: WITH RECURSIVE
  - ROWNUM: LIMIT/OFFSET
  - DECODE: CASE
  - NVL: COALESCE

================================================================================
```

### 배치 분석 콘솔 출력

```
================================================================================
📊 Oracle 복잡도 분석 배치 리포트
================================================================================

분석 시간: 20260114_153045
타겟 데이터베이스: postgresql

전체 파일 수: 25
분석 성공: 23
분석 실패: 2
평균 복잡도 점수: 4.56 / 10

📈 복잡도 레벨별 분포:
  매우 간단       :   3 ( 13.0%) ██
  간단           :   8 ( 34.8%) ██████
  중간           :   7 ( 30.4%) ██████
  복잡           :   4 ( 17.4%) ███
  매우 복잡       :   1 (  4.3%) 
  극도로 복잡     :   0 (  0.0%) 

🔥 복잡도 높은 파일 Top 10:
   1. /path/to/complex_package.pkb                                  8.45
   2. /path/to/hierarchical_query.sql                               7.23
   3. /path/to/pivot_analysis.sql                                   6.78
   ...

================================================================================
```

## Python API 사용

CLI 외에도 Python 코드에서 직접 사용할 수 있습니다.

### 단일 파일 분석 예제

자세한 예제는 `example_usage.py` 파일을 참조하세요.

```python
from src.oracle_complexity_analyzer import (
    OracleComplexityAnalyzer,
    TargetDatabase
)

# 분석기 생성
analyzer = OracleComplexityAnalyzer(
    target_database=TargetDatabase.POSTGRESQL,
    output_dir="reports"
)

# SQL 쿼리 분석
sql_query = """
SELECT * FROM employees e
WHERE e.department_id IN (
    SELECT d.department_id 
    FROM departments d 
    WHERE d.location_id = 1000
)
"""

result = analyzer.analyze_sql(sql_query)
print(f"복잡도 점수: {result.normalized_score:.2f}")
print(f"복잡도 레벨: {result.complexity_level.value}")

# 파일 분석
result = analyzer.analyze_file("query.sql")

# 결과 저장
json_path = analyzer.export_json(result, "analysis_result.json")
md_path = analyzer.export_markdown(result, "analysis_report.md")
```

### 폴더 배치 분석 예제

자세한 예제는 `example_batch_usage.py` 파일을 참조하세요.

```python
from src.oracle_complexity_analyzer import (
    OracleComplexityAnalyzer,
    BatchAnalyzer,
    TargetDatabase
)

# 분석기 생성
analyzer = OracleComplexityAnalyzer(
    target_database=TargetDatabase.POSTGRESQL,
    output_dir="reports"
)

# 폴더 일괄 분석 (병렬 처리)
batch_analyzer = BatchAnalyzer(analyzer, max_workers=4)
batch_result = batch_analyzer.analyze_folder("/path/to/sql/files")

print(f"전체 파일: {batch_result.total_files}")
print(f"분석 성공: {batch_result.success_count}")
print(f"평균 점수: {batch_result.average_score:.2f}")

# 배치 결과 저장
json_path = batch_analyzer.export_batch_json(batch_result, include_details=True)
md_path = batch_analyzer.export_batch_markdown(batch_result, include_details=False)
```

### CLI vs Python API 선택 가이드

- **CLI 사용 권장**: 빠른 분석, 스크립트 자동화, 배치 작업
- **Python API 사용 권장**: 커스텀 워크플로우, 다른 도구와 통합, 결과 후처리

**참고**: 폴더 배치 분석은 CLI의 `-d` 플래그를 사용하는 것이 가장 간단합니다.
```bash
# CLI로 배치 분석 (권장)
oracle-complexity-analyzer -d sample_code --details -o markdown
```

## 복잡도 계산 방식

### SQL 쿼리 복잡도 (6가지 카테고리)

1. **구조적 복잡성**: JOIN 개수, 서브쿼리 깊이, CTE, 집합 연산자
2. **Oracle 특화 기능**: CONNECT BY, PIVOT, MODEL, 분석 함수
3. **함수/표현식**: 집계 함수, UDF, CASE 표현식, 정규식
4. **데이터 볼륨**: 쿼리 길이 기반 추정
5. **실행 복잡성**: ORDER BY, GROUP BY, HAVING, 조인 깊이
6. **변환 난이도**: 힌트 개수 기반

### PL/SQL 오브젝트 복잡도 (5-7가지 카테고리)

1. **기본 점수**: 오브젝트 타입별 기본 복잡도
2. **코드 복잡도**: 라인 수, 커서, 예외 처리, 중첩 깊이
3. **Oracle 특화 기능**: BULK 연산, 동적 SQL, 패키지 호출
4. **비즈니스 로직**: 트랜잭션 처리, 계산, 검증
5. **AI 변환 난이도**: 컨텍스트 의존성, 외부 의존성
6. **MySQL 제약** (MySQL 타겟만): 데이터 타입, 트리거, 뷰 제약
7. **애플리케이션 이관 페널티** (MySQL 타겟만): Package/Procedure/Function

### 복잡도 레벨 분류

| 점수 범위 | 레벨 | 권장사항 |
|----------|------|---------|
| 0-1 | 매우 간단 | 자동 변환 |
| 1-3 | 간단 | 함수 대체 |
| 3-5 | 중간 | 부분 재작성 |
| 5-7 | 복잡 | 상당한 재작성 |
| 7-9 | 매우 복잡 | 대부분 재작성 |
| 9-10 | 극도로 복잡 | 완전 재설계 |

## 문서

자세한 내용은 `docs/` 폴더의 문서를 참조하세요:

- `complexity_postgresql.md`: PostgreSQL 타겟 복잡도 계산 공식
- `complexity_mysql.md`: MySQL 타겟 복잡도 계산 공식
- `oracle_complexity_formula.md`: 전체 복잡도 계산 공식
- `migration_guide_aurora_pg16.md`: Aurora PostgreSQL 16 마이그레이션 가이드
- `migration_guide_aurora_mysql80.md`: Aurora MySQL 8.0 마이그레이션 가이드

## 테스트

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함 테스트
pytest --cov=src --cov-report=html

# 특정 테스트만 실행
pytest tests/test_sql_parser.py

# 속성 기반 테스트만 실행
pytest -m property
```

## 개발

```bash
# 코드 포맷팅
black src tests

# 린팅
flake8 src tests

# 타입 체크
mypy src
```

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

## 문의

문제가 발생하거나 질문이 있으시면 이슈를 등록해주세요.
