# Oracle PL/SQL 복잡도 분석 결과

## 복잡도 점수 요약

- **오브젝트 타입**: PROCEDURE
- **타겟 데이터베이스**: POSTGRESQL
- **총점**: 7.20
- **정규화 점수**: 3.06 / 10.0
- **복잡도 레벨**: 중간
- **권장사항**: 부분 재작성

## 세부 점수

| 카테고리 | 점수 |
|---------|------|
| 기본 점수 | 5.00 |
| 코드 복잡도 | 1.20 |
| Oracle 특화 기능 | 0.00 |
| 비즈니스 로직 | 1.00 |
| 변환 난이도 | 0.00 |

## 분석 메타데이터

- **코드 라인 수**: 37
- **커서 개수**: 0
- **예외 블록 개수**: 1
- **중첩 깊이**: 4
- **BULK 연산 개수**: 0
- **동적 SQL 개수**: 0

## 원본 코드

```sql
-- Oracle 종속성 낮음: 순수 알고리즘 및 표준 PL/SQL 패턴
CREATE OR REPLACE PROCEDURE low_dep_algo_proc (
    p_input_val IN NUMBER,
    p_result    OUT NUMBER
) IS
    v_temp_val NUMBER := 0;
    v_counter  NUMBER := 0;
    v_threshold CONSTANT NUMBER := 100;
BEGIN
    p_result := 0;
    v_temp_val := p_input_val;

    -- 1. 복잡한 수치 알고리즘 (예: 특정 수열 계산)
    WHILE v_temp_val > 0 LOOP
        v_counter := v_counter + 1;
        
        CASE 
            WHEN MOD(v_temp_val, 3) = 0 THEN
                v_temp_val := v_temp_val / 3;
            WHEN MOD(v_temp_val, 2) = 0 THEN
                v_temp_val := v_temp_val - 5;
            ELSE
                v_temp_val := v_temp_val - 1;
        END CASE;

        -- 비즈니스 임계값 체크
        IF v_counter > v_threshold THEN
            p_result := -1; -- Timeout/Threshold error
            EXIT;
        END IF;

        -- 누적 합산 로직
        p_result := p_result + (v_temp_val * 0.1);
    END LOOP;

    -- 2. 최종 결과 보정
    IF p_result > 0 THEN
        p_result := ROUND(p_result, 2);
    ELSE
        p_result := ABS(p_result);
    END IF;

EXCEPTION
    WHEN VALUE_ERROR THEN
        p_result := NULL;
    WHEN OTHERS THEN
        -- 표준 SQLCODE/SQLERRM 사용
        p_result := SQLCODE;
END low_dep_algo_proc;
```
