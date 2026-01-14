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
