set feedback off
set timing off
set head off
clear columns;

column output new_value inst_name
col output for a16
column timecol new_value today
column spool_extension new_value suffix
col timecol for a8

select value || '_' output
from v$parameter
where name = 'instance_name';

select to_char(sysdate,'YYYYMMDD') timecol,'.out' spool_extension
from sys.dual;

set line 250
set pages 2000
set trimspool on
set head on
spool plsql_f_&&inst_name&&today&&suffix

PROMPT
PROMPT ============================================================================
PROMPT =                                                                          =
PROMPT =     AWS ProServe Migration ORACLE to RDS                                 =
PROMPT =     Oracle PLSQL Full CHECK SCRIPT Ver.1.0                               =
PROMPT =                                                                          =
PROMPT =     Made by - Tei Nam                                                    =
PROMPT =     Create date. 2026/01/16                                              =
PROMPT =     Modify date. 2026/01/16                                              =
PROMPT =                                                                          =
PROMPT ============================================================================


-- 대용량 CLOB 출력을 위한 설정
SET LONG 10000000
SET LONGCHUNKSIZE 10000000
SET PAGESIZE 0
SET LINESIZE 32767
SET HEADING OFF
SET FEEDBACK OFF
SET TRIMSPOOL ON
SET ARRAYSIZE 1
SET FLUSH ON

-- DBMS_METADATA 포맷 설정 (가독성 향상)
BEGIN
    -- DDL을 보기 좋게 포맷팅
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'PRETTY', TRUE);
    -- SQL 종료자(;와 /) 추가
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'SQLTERMINATOR', TRUE);
    -- 스토리지 절 제외 (이관 시 불필요)
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'STORAGE', FALSE);
    -- 세그먼트 속성 제외
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'SEGMENT_ATTRIBUTES', FALSE);
    -- 테이블스페이스 정보 제외
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'TABLESPACE', FALSE);
END;
/

SELECT 
    CHR(10) ||
    '-- ============================================================' || CHR(10) ||
    '-- Owner: ' || owner || CHR(10) ||
    '-- Type: ' || object_type || CHR(10) ||
    '-- Name: ' || object_name || CHR(10) ||
    '-- ============================================================' || CHR(10) ||
    DBMS_METADATA.GET_DDL(
        REPLACE(object_type, ' ', '_'),
        object_name, 
        owner
    ) AS ddl_text
FROM dba_objects
WHERE object_type IN (
    'PROCEDURE',
    'FUNCTION',
    'PACKAGE',
    'PACKAGE BODY',
    'TRIGGER',
    'TYPE',
    'TYPE BODY'
)
AND owner IN (
    SELECT username 
    FROM dba_users 
    WHERE account_status = 'OPEN'
      AND oracle_maintained = 'N'
)
AND status = 'VALID'
-- 시스템 생성 오브젝트 제외
AND object_name NOT LIKE 'SYS_YOID%'
AND object_name NOT LIKE 'SYS_PLSQL%'
AND object_name NOT LIKE 'SYS_IOT%'
AND object_name NOT LIKE 'SYS_LOB%'
AND object_name NOT LIKE 'SYS_C%'
AND object_name NOT LIKE 'BIN$%'
AND generated = 'N'  -- 자동 생성된 오브젝트 제외
ORDER BY owner, object_type, object_name;

-- DBMS_METADATA 설정 초기화
BEGIN
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'DEFAULT');
END;
/

set feedback off

PROMPT
PROMPT
PROMPT Report Completed Time
PROMPT ===============================================================

set head off

col date for a21 HEADING 'Report Completed Time';
select to_char(sysdate,'yyyy-mm-dd   HH24:MI:SS') "date" from dual
/

set head on
set feedback on

spool off