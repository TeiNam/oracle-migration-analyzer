# Oracle SQL 복잡도 분석 결과

## 복잡도 점수 요약

- **타겟 데이터베이스**: POSTGRESQL
- **총점**: 0.70
- **정규화 점수**: 0.52 / 10.0
- **복잡도 레벨**: 매우 간단
- **권장사항**: 자동 변환

## 세부 점수

| 카테고리 | 점수 |
|---------|------|
| 구조적 복잡성 | 0.00 |
| Oracle 특화 기능 | 0.00 |
| 함수/표현식 | 0.00 |
| 데이터 볼륨 | 0.50 |
| 실행 복잡성 | 0.20 |
| 변환 난이도 | 0.00 |

## 분석 메타데이터

- **JOIN 개수**: 0
- **서브쿼리 중첩 깊이**: 0
- **CTE 개수**: 0
- **집합 연산자 개수**: 0

## 원본 쿼리

```sql
-- 간단한 SELECT 쿼리
SELECT employee_id, first_name, last_name, email
FROM employees
WHERE department_id = 10
ORDER BY last_name;
```
