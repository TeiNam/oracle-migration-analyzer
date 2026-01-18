# Oracle PL/SQL 복잡도 분석 결과

## 복잡도 점수 요약

- **오브젝트 타입**: PROCEDURE
- **타겟 데이터베이스**: MYSQL
- **총점**: 10.50
- **정규화 점수**: 4.47 / 10.0
- **복잡도 레벨**: 중간
- **권장사항**: 부분 재작성

## 세부 점수

| 카테고리 | 점수 |
|---------|------|
| 기본 점수 | 6.00 |
| 코드 복잡도 | 0.70 |
| Oracle 특화 기능 | 2.00 |
| 비즈니스 로직 | 1.30 |
| 변환 난이도 | 0.50 |

## 분석 메타데이터

- **코드 라인 수**: 27
- **커서 개수**: 0
- **예외 블록 개수**: 1
- **중첩 깊이**: 2
- **BULK 연산 개수**: 0
- **동적 SQL 개수**: 0

## 감지된 외부 의존성

- DBMS_SQL

## 변환 가이드

| Oracle 기능 | 대체 방법 |
|------------|----------|
| DBMS_SQL | PREPARE/EXECUTE 동적 SQL |

## 원본 코드

```sql
-- Oracle 종속성 높음: 시스템 관리 및 병렬 처리 패턴
CREATE OR REPLACE PROCEDURE complex_parallel_sys_proc (
    p_table_name IN VARCHAR2,
    p_chunk_size IN NUMBER DEFAULT 5000
) IS
    v_task_name VARCHAR2(100) := 'TASK_' || TO_CHAR(SYSDATE, 'YYYYMMDD_HH24MISS');
    v_sql_stmt  VARCHAR2(1000);
    v_status    NUMBER;
BEGIN
    -- 1. Oracle 세션 모니터링 등록 (Longops 등록)
    DBMS_APPLICATION_INFO.SET_MODULE('BATCH_PROCESSOR', 'INITIALIZING');
    DBMS_APPLICATION_INFO.SET_CLIENT_INFO('Task: ' || v_task_name);

    -- 2. 병렬 작업 생성
    DBMS_PARALLEL_EXECUTE.CREATE_TASK(v_task_name);

    -- 3. ROWID 기준으로 데이터를 청크(Chunk)로 나눔
    DBMS_PARALLEL_EXECUTE.CREATE_CHUNKS_BY_ROWID(v_task_name, 'HR', p_table_name, TRUE, p_chunk_size);

    -- 4. 병렬 실행할 SQL 정의
    v_sql_stmt := 'UPDATE ' || p_table_name || 
                  ' SET salary = salary * 1.05 WHERE rowid BETWEEN :start_id AND :end_id';

    -- 5. 스케줄러를 통한 병렬 실행 (Job 갯수 4개)
    DBMS_PARALLEL_EXECUTE.RUN_TASK(v_task_name, v_sql_stmt, DBMS_SQL.NATIVE, parallel_level => 4);

    -- 6. 실행 상태 확인 루프 (복잡한 상태 체크 로직)
    LOOP
        v_status := DBMS_PARALLEL_EXECUTE.TASK_STATUS(v_task_name);
        EXIT WHEN v_status = DBMS_PARALLEL_EXECUTE.FINISHED;
        DBMS_SESSION.SLEEP(5); -- 21c/23c 이상 권장 패키지
    END LOOP;

    DBMS_PARALLEL_EXECUTE.DROP_TASK(v_task_name);
    DBMS_APPLICATION_INFO.SET_MODULE(NULL, NULL);

EXCEPTION
    WHEN OTHERS THEN
        DBMS_PARALLEL_EXECUTE.DROP_TASK(v_task_name);
        RAISE;
END complex_parallel_sys_proc;
```
