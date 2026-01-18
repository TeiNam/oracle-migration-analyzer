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
spool check_plsql_ee_&&inst_name&&today&&suffix

PROMPT
PROMPT ============================================================================
PROMPT =                                                                          =
PROMPT =     AWS ProServe Migration ORACLE to RDS                                 =
PROMPT =     Oracle Migration CHECK SCRIPT Ver.1.0                                =
PROMPT =                                                                          =
PROMPT =     Made by - Tei Nam                                                    =
PROMPT =     Create date. 2026/01/16                                              =
PROMPT =     Modify date. 2026/01/16                                              =
PROMPT =                                                                          =
PROMPT ============================================================================

set head off
set feedback off

select BANNER from v$version;

set head on

col VERSION for a12
col COMP_NAME for a40
col SCHEMA for a12
col status for a13
select  COMP_NAME  ,VERSION ,SCHEMA, STATUS  from   dba_registry
/


PROMPT
PROMPT
PROMPT
PROMPT ===============================================================
PROMPT = 1. User Information                                         =
PROMPT =    1.1 DB Users                                             =
PROMPT =    1.2 User Table Information                               =
PROMPT =    1.3 User Objects Count                                   =
PROMPT =    1.4 User Procedures Information                          =
PROMPT ===============================================================



PROMPT
PROMPT
PROMPT 1.1 DB Users
PROMPT ===============================================================

col username for a30
col DEFAULT_TABLESPACE for a24
col TEMPORARY_TABLESPACE for a18
col ACCOUNT_STATUS for a20
col PROFILE for a10

select USERNAME, DEFAULT_TABLESPACE, TEMPORARY_TABLESPACE, PROFILE, ACCOUNT_STATUS
from dba_users
where ACCOUNT_STATUS = 'OPEN'
order by 5 desc,1, 2
/

PROMPT
PROMPT
PROMPT 1.2 User Table Information
PROMPT ===============================================================


COL owner FOR A20
COL table_name FOR A60
COL tablespace_name FOR A14
COL last_analyzed FOR A13
COL partitioned FOR A11

WITH TM_TB_SIZE AS (
    SELECT 
        owner,
        segment_name AS table_name,
        bytes,
        (bytes/1024)/1024 AS table_size
    FROM dba_segments
    WHERE segment_type = 'TABLE'
)
SELECT 
    a.owner,
    a.table_name,
    a.tablespace_name AS "TABLESPACE",
    a.num_rows AS "ROWS",
    b.table_size AS "TABLE_SIZE(MB)",
    a.blocks,    
    a.partitioned,
    a.last_analyzed    
FROM dba_tables a
LEFT JOIN TM_TB_SIZE b 
    ON a.owner = b.owner 
   AND a.table_name = b.table_name
WHERE a.owner IN (
    SELECT username 
    FROM dba_users 
    WHERE account_status = 'OPEN'
      AND oracle_maintained = 'N'
)
AND a.num_rows > 0
ORDER BY a.owner, a.num_rows DESC;



PROMPT
PROMPT
PROMPT 1.3 User Objects Count
PROMPT ===============================================================


COL owner FOR A15
COL tables FOR 999999
COL views FOR 999999
COL mviews FOR 999999
COL procedures FOR 999999
COL functions FOR 999999
COL packages FOR 999999
COL pkg_bodies FOR 999999
COL triggers FOR 999999
COL jobs FOR 999999
COL schedules FOR 999999
COL programs FOR 999999
COL total FOR 999999

SELECT 
    owner,
    SUM(CASE WHEN object_type = 'TABLE' THEN 1 ELSE 0 END) AS tables,
    SUM(CASE WHEN object_type = 'VIEW' THEN 1 ELSE 0 END) AS views,
    SUM(CASE WHEN object_type = 'MATERIALIZED VIEW' THEN 1 ELSE 0 END) AS mviews,
    SUM(CASE WHEN object_type = 'PROCEDURE' THEN 1 ELSE 0 END) AS procedures,
    SUM(CASE WHEN object_type = 'FUNCTION' THEN 1 ELSE 0 END) AS functions,
    SUM(CASE WHEN object_type = 'PACKAGE' THEN 1 ELSE 0 END) AS packages,
    SUM(CASE WHEN object_type = 'PACKAGE BODY' THEN 1 ELSE 0 END) AS pkg_bodies,
    SUM(CASE WHEN object_type = 'TRIGGER' THEN 1 ELSE 0 END) AS triggers,
    SUM(CASE WHEN object_type = 'JOB' THEN 1 ELSE 0 END) AS jobs,
    SUM(CASE WHEN object_type = 'SCHEDULE' THEN 1 ELSE 0 END) AS schedules,
    SUM(CASE WHEN object_type = 'PROGRAM' THEN 1 ELSE 0 END) AS programs,
    COUNT(*) AS total
FROM dba_objects o
WHERE o.owner IN (
    SELECT username 
    FROM dba_users 
    WHERE account_status = 'OPEN'
      AND oracle_maintained = 'N'
)
AND o.object_type IN ('TABLE', 'VIEW', 'MATERIALIZED VIEW', 'PROCEDURE', 
                       'FUNCTION', 'PACKAGE', 'PACKAGE BODY', 'TRIGGER',
                       'JOB', 'SCHEDULE', 'PROGRAM')
GROUP BY ROLLUP(owner)
ORDER BY 
    CASE WHEN owner IS NULL THEN 1 ELSE 0 END,
    owner;


PROMPT
PROMPT
PROMPT 1.4 User Procedures Information
PROMPT ===============================================================

set feedback off

COL owner FOR A15
COL object_name FOR A30
COL lines FOR 999999

BREAK ON owner SKIP 1 ON REPORT
COMPUTE SUM LABEL 'User Total:' OF lines ON owner
COMPUTE SUM LABEL '** GRAND TOTAL **' OF lines ON REPORT

SELECT 
    owner,
    name AS object_name,
    COUNT(*) AS lines
FROM dba_source
WHERE owner IN (
    SELECT username 
    FROM dba_users 
    WHERE account_status = 'OPEN'
      AND oracle_maintained = 'N'
)
AND type = 'PROCEDURE'
GROUP BY owner, name
ORDER BY owner, name;

CLEAR BREAKS
CLEAR COMPUTES


PROMPT
PROMPT
PROMPT
PROMPT ===============================================================
PROMPT = 2. Oracle Enterprise Edition                                =
PROMPT =    2.1 EE to SE Summary                                     =
PROMPT =    2.2 EE usage status                                      =
PROMPT ===============================================================


PROMPT
PROMPT
PROMPT 2.1 EE to SE Summary
PROMPT ===============================================================

COL feature FOR A40
COL cnt FOR 9999 HEAD "COUNT"
COL impact FOR A50

SELECT 
    feature,
    COUNT(*) AS cnt,
    CASE feature
        WHEN 'Partitioning' THEN '테이블 재생성 필요 (파티션 제거)'
        WHEN 'Bitmap Index' THEN 'B-Tree 인덱스로 변경 필요'
        WHEN 'Advanced Compression' THEN 'BASIC 압축 또는 비압축으로 변경'
        WHEN 'Advanced Index Compression' THEN '압축 해제 또는 BASIC으로 변경'
        WHEN 'MView Query Rewrite' THEN 'Query Rewrite 비활성화'
        WHEN 'SecureFiles Compression/Dedup' THEN 'LOB 압축/중복제거 비활성화'
        WHEN 'Transparent Data Encryption' THEN '암호화 해제 필요'
        ELSE '확인 필요'
    END AS impact
FROM (
    SELECT 'Partitioning' AS feature FROM dba_part_tables
    WHERE owner IN (SELECT username FROM dba_users WHERE account_status = 'OPEN' AND oracle_maintained = 'N')
    UNION ALL
    SELECT 'Partitioning' FROM dba_part_indexes
    WHERE owner IN (SELECT username FROM dba_users WHERE account_status = 'OPEN' AND oracle_maintained = 'N')
    UNION ALL
    SELECT 'Bitmap Index' FROM dba_indexes
    WHERE index_type = 'BITMAP'
      AND owner IN (SELECT username FROM dba_users WHERE account_status = 'OPEN' AND oracle_maintained = 'N')
    UNION ALL
    SELECT 'Advanced Compression' FROM dba_tables
    WHERE compress_for IN ('OLTP', 'QUERY HIGH', 'QUERY LOW', 'ARCHIVE HIGH', 'ARCHIVE LOW')
      AND owner IN (SELECT username FROM dba_users WHERE account_status = 'OPEN' AND oracle_maintained = 'N')
    UNION ALL
    SELECT 'MView Query Rewrite' FROM dba_mviews
    WHERE rewrite_enabled = 'Y'
      AND owner IN (SELECT username FROM dba_users WHERE account_status = 'OPEN' AND oracle_maintained = 'N')
    UNION ALL
    SELECT 'SecureFiles Compression/Dedup' FROM dba_lobs
    WHERE (compression NOT IN ('NONE', 'NO') OR deduplication NOT IN ('NONE', 'NO'))
      AND owner IN (SELECT username FROM dba_users WHERE account_status = 'OPEN' AND oracle_maintained = 'N')
    UNION ALL
    SELECT 'Transparent Data Encryption' FROM dba_encrypted_columns
    WHERE owner IN (SELECT username FROM dba_users WHERE account_status = 'OPEN' AND oracle_maintained = 'N')
)
GROUP BY feature
ORDER BY cnt DESC;


PROMPT
PROMPT
PROMPT 2.2 EE usage status
PROMPT ===============================================================

set head on


COL feature FOR A35
COL owner FOR A15
COL object_name FOR A30
COL object_type FOR A15

-- EE → SE 이관 시 변경 필요한 실제 오브젝트 목록
SELECT * FROM (
    -- 1. 파티션 테이블
    SELECT 
        'Partitioning' AS feature,
        owner,
        table_name AS object_name,
        'TABLE' AS object_type
    FROM dba_part_tables
    WHERE owner IN (
        SELECT username FROM dba_users 
        WHERE account_status = 'OPEN' AND oracle_maintained = 'N'
    )
    UNION ALL
    -- 2. 파티션 인덱스
    SELECT 
        'Partitioning' AS feature,
        owner,
        index_name,
        'INDEX'
    FROM dba_part_indexes
    WHERE owner IN (
        SELECT username FROM dba_users 
        WHERE account_status = 'OPEN' AND oracle_maintained = 'N'
    )
    UNION ALL
    -- 3. Bitmap 인덱스
    SELECT 
        'Bitmap Index' AS feature,
        owner,
        index_name,
        'INDEX'
    FROM dba_indexes
    WHERE index_type = 'BITMAP'
      AND owner IN (
        SELECT username FROM dba_users 
        WHERE account_status = 'OPEN' AND oracle_maintained = 'N'
    )
    UNION ALL
    -- 4. 압축 테이블 (OLTP/HCC)
    SELECT 
        'Advanced Compression' AS feature,
        owner,
        table_name,
        'TABLE'
    FROM dba_tables
    WHERE compress_for IN ('OLTP', 'QUERY HIGH', 'QUERY LOW', 'ARCHIVE HIGH', 'ARCHIVE LOW')
      AND owner IN (
        SELECT username FROM dba_users 
        WHERE account_status = 'OPEN' AND oracle_maintained = 'N'
    )
    UNION ALL
    -- 5. 압축 인덱스 (Advanced)
    SELECT 
        'Advanced Index Compression' AS feature,
        owner,
        index_name,
        'INDEX'
    FROM dba_indexes
    WHERE compression = 'ADVANCED HIGH' OR compression = 'ADVANCED LOW'
      AND owner IN (
        SELECT username FROM dba_users 
        WHERE account_status = 'OPEN' AND oracle_maintained = 'N'
    )
    UNION ALL
    -- 6. MView Query Rewrite
    SELECT 
        'MView Query Rewrite' AS feature,
        owner,
        mview_name,
        'MVIEW'
    FROM dba_mviews
    WHERE rewrite_enabled = 'Y'
      AND owner IN (
        SELECT username FROM dba_users 
        WHERE account_status = 'OPEN' AND oracle_maintained = 'N'
    )
    UNION ALL
    -- 7. SecureFiles (Compression/Dedup)
    SELECT 
        'SecureFiles Compression/Dedup' AS feature,
        owner,
        table_name,
        'LOB'
    FROM dba_lobs
    WHERE (compression NOT IN ('NONE', 'NO') OR deduplication NOT IN ('NONE', 'NO'))
      AND owner IN (
        SELECT username FROM dba_users 
        WHERE account_status = 'OPEN' AND oracle_maintained = 'N'
    )
    UNION ALL
    -- 8. TDE 암호화 테이블스페이스/컬럼
    SELECT 
        'Transparent Data Encryption' AS feature,
        owner,
        table_name,
        'ENCRYPTED COLUMN'
    FROM dba_encrypted_columns
    WHERE owner IN (
        SELECT username FROM dba_users 
        WHERE account_status = 'OPEN' AND oracle_maintained = 'N'
    )
)
ORDER BY feature, owner, object_name;

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