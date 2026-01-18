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
spool check_mig_&&inst_name&&today&&suffix

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
PROMPT ===============================================================
PROMPT = 0. Database Information                                     =
PROMPT =    0.1 DB Information                                       =
PROMPT =    0.2 NLS Character Set                                    =
PROMPT =    0.3 H/W Information                                      =
PROMPT ===============================================================

PROMPT
PROMPT
PROMPT 0.1 DB Information
PROMPT ===============================================================

set feedback off
col dbname   NEW_VALUE dbname
col now      NEW_VALUE today
col month    NEW_VALUE month
col instance NEW_VALUE instance
col thread   NEW_VALUE thread_number

col thread for 999
col instance for a14
col dbname for a14
col host_name for a16
col platform_name for a30 HEADING 'PLATFORM'
col version for a10
col log_mode for a16

SELECT
    b.thread# thread,
    b.instance_name instance,
    a.name dbname,
    b.host_name,
    a.platform_name,
    b.version,
    a.log_mode
FROM v$database a, v$instance b
/


PROMPT
PROMPT === Archive log ===
archive log list;


PROMPT
PROMPT
PROMPT 0.2 Character Set
PROMPT ===============================================================

col PARAMETER for a30
col "CharacterSET" for a30

set head on

SELECT
    PARAMETER,
    VALUE "CharacterSET"
FROM V$NLS_PARAMETERS
WHERE parameter in ('NLS_CHARACTERSET','NLS_NCHAR_CHARACTERSET')
/

PROMPT
PROMPT
PROMPT 0.3 H/W Information
PROMPT ===============================================================

col stat_name for a30 HEADING 'Statistic'
col value for a20 HEADING 'Value'

SELECT
    'CPU Count (Oracle)' as stat_name,
    TO_CHAR(value) as value
FROM v$osstat
WHERE stat_name = 'NUM_CPUS'
UNION ALL
SELECT
    'CPU Core Count' as stat_name,
    TO_CHAR(value) as value
FROM v$osstat
WHERE stat_name = 'NUM_CPU_CORES'
UNION ALL
SELECT
    'CPU Socket Count' as stat_name,
    TO_CHAR(value) as value
FROM v$osstat
WHERE stat_name = 'NUM_CPU_SOCKETS'
UNION ALL
SELECT
    'Physical Memory (GB)' as stat_name
    ,TO_CHAR(ROUND(value/1024/1024/1024,2)) as value
FROM v$osstat
WHERE stat_name = 'PHYSICAL_MEMORY_BYTES'
/



PROMPT
PROMPT
PROMPT
PROMPT ===============================================================
PROMPT = 1. SGA                                                      =
PROMPT =    1.1 SGA Total Size (MB)                                  =
PROMPT =    1.2 Shared Pool and Buffer Cache (MB)                    =
PROMPT =    1.3 SGA Cache Efficiency                                 =
PROMPT ===============================================================


PROMPT
PROMPT
PROMPT 1.1 SGA
PROMPT ===============================================================

set head on

col "SGA Parameter" for a24
col "Size (MB)" for a10
select NAME "SGA Parameter", to_char(round(VALUE/1024/2014,2),'99,999.99') "Size (MB)" from v$parameter
where name like 'sga_%'
/

set head off

select 'SGA Used Total Size: '||TO_CHAR(round(sum(bytes)/1024/1024,2),'999,999.99')||' MB'
from v$sgastat
/

set head on

PROMPT
PROMPT
PROMPT 1.2 Shared Pool and Buffer Cache (MB)
PROMPT ===============================================================

col name        FORMAT a15              HEADING 'Name'
col pool        FORMAT a15              HEADING 'Pool Name'
col tbytes      FORMAT 999,999,999.99       HEADING 'Total Size(MB)'
col ubytes      FORMAT 999,999,999.99       HEADING 'Used Size(MB)'
col usedp    FORMAT a8          HEADING 'Used(%)'
col fbytes      FORMAT 999,999,999.99       HEADING 'Free Size(MB)'
col freep    FORMAT a8          HEADING 'Free(%)'

SELECT a.pool AS pool, a.tbytes/1024/1024 AS tbytes
      ,(a.tbytes-b.fbytes)/1024/1024 AS ubytes
      ,b.fbytes/1024/1024 AS fbytes
      ,ROUND((((a.tbytes-b.fbytes)/a.tbytes)*100),2)||'%' AS usedp
      ,ROUND(((b.fbytes/a.tbytes)*100),2)||'%' AS freep
FROM (SELECT pool
            ,SUM(bytes) AS tbytes
      FROM v$sgastat
      WHERE pool='shared pool'
      GROUP BY pool) a
    ,(SELECT pool
            ,bytes AS fbytes
      FROM v$sgastat
      WHERE pool='shared pool'
      AND name='free memory') b
WHERE a.pool='shared pool'
union all
SELECT a.name AS name
      ,SUM(a.bytes)/1024/1024 AS tbytes
      ,SUM(b.ubytes)/1024/1024 AS ubytes
      ,SUM(a.bytes-b.ubytes)/1024/1024 AS fbytes
      ,ROUND(SUM(b.ubytes)/SUM(a.bytes)*100,2)||'%' AS usedp
      ,ROUND(SUM((a.bytes-b.ubytes)/a.bytes)*100,2)||'%' AS freep
FROM v$sgastat a
    ,(SELECT COUNT(1)*8192 AS ubytes
      FROM v$bh) b
WHERE a.name='buffer_cache'
GROUP BY a.name
/

PROMPT
PROMPT
PROMPT 1.3 SGA Cache Efficiency
PROMPT ===============================================================

COL metric FOR A35
COL ratio FOR A15
COL status FOR A10

SELECT 
    'Library Cache Hit Ratio' AS metric,
    TO_CHAR(TRUNC((1 - SUM(reloads)/SUM(pins))*100,2))||' %' AS ratio,
    CASE WHEN (1 - SUM(reloads)/SUM(pins))*100 < 99 THEN 'WARNING' ELSE 'OK' END AS status
FROM v$librarycache
UNION ALL
SELECT 
    'Data Dictionary Hit Ratio',
    TO_CHAR(TRUNC((1 - SUM(getmisses)/SUM(gets))*100,2))||' %',
    CASE WHEN (1 - SUM(getmisses)/SUM(gets))*100 < 95 THEN 'WARNING' ELSE 'OK' END
FROM v$rowcache WHERE gets > 0
UNION ALL
SELECT 
    'Buffer Cache Hit Ratio',
    TO_CHAR(TRUNC((1 - (phy.value/(cur.value+con.value)))*100,2))||' %',
    CASE WHEN (1 - (phy.value/(cur.value+con.value)))*100 < 95 THEN 'WARNING' ELSE 'OK' END
FROM (SELECT value FROM v$sysstat WHERE name='db block gets') cur
    ,(SELECT value FROM v$sysstat WHERE name='consistent gets') con
    ,(SELECT value FROM v$sysstat WHERE name='physical reads') phy;

PROMPT
PROMPT
PROMPT
PROMPT ===============================================================
PROMPT = 2. PGA                                                      =
PROMPT =    2.1 PGA, UGA Usage (MB)                                  =
PROMPT =    2.2 Session Check                                        =
PROMPT =    2.3 PGA Usage per Client (MB)                            =
PROMPT ===============================================================



PROMPT
PROMPT
PROMPT 2.1 PGA, UGA Usage
PROMPT ===============================================================


col sum for a40 HEADING 'PGA, UGA session memory';
col uga_sum for a10;
col pga_sum for a10;

select 'Current PGA, UGA session memory SUM:' as sum,
       sum(decode(c.name, 'session pga memory', trunc(value/1024/1024,2))) ||' MB' pga_sum,
       sum(decode(c.name, 'session uga memory', trunc(value/1024/1024,2))) ||' MB' uga_sum
from v$session a, v$sesstat b, v$statname c
where a.sid = b.sid
and b.statistic# = c.statistic#
and c.name like 'session%'
/


PROMPT
PROMPT
PROMPT 2.2 Session Check
PROMPT ===============================================================

col data for a65 HEADING 'Session';

select 'Current Session / Max Value / Limit Value : '|| CURRENT_UTILIZATION||' / '||MAX_UTILIZATION||' / '||to_number(INITIAL_ALLOCATION)||' ' as "data"
from V$RESOURCE_LIMIT where RESOURCE_NAME = 'sessions'
/


PROMPT
PROMPT
PROMPT 2.3 PGA Usage per Client (MB)
PROMPT ===============================================================

select machine,status,count(*) cnt,
       round(sum(pga_used_mem)/1024/1024) "PGA Total(MB)",
       round(sum(pga_used_mem)/count(*)/1024/1024) "PGA per Client(MB)"
from v$session s, v$process p
where 1=1
--and s.status='active'
and s.paddr=p.addr
and type <> 'BACKGROUND'
group by machine,status
order by 1
/


PROMPT
PROMPT
PROMPT
PROMPT ===============================================================
PROMPT = 3. Datafile and Tablespace                                  =
PROMPT =    3.1 Datafile Size(GB)                                    =
PROMPT =    3.2 Tablespace usage                                     =
PROMPT =    3.3 Temp Tablespace usage                                =
PROMPT =    3.4 Datafile Stat                                        =
PROMPT =    3.5 Disk Physical I/O                                    =
PROMPT =    3.6 Internal and External Sort                           =
PROMPT ===============================================================


PROMPT
PROMPT
PROMPT 3.1 Datafile Size(GB)
PROMPT ===============================================================

col data_files_sum for 999,999,999,999.99
col free_space_sum for 999,999,999,999.99
col extents for 999,999,999,999.99
col tbs for a60 HEADING "Used / Total (Free) (GB)"

select 'TBS Size: '||(data_files_sum - free_space_sum) || ' GB / '|| data_files_sum || ' GB  (free    '|| free_space_sum || ' GB)' AS tbs
from
(select round(sum(bytes)/1024/1024/1024,2) data_files_sum from dba_data_files),
(select round(sum(bytes)/1024/1024/1024,2) free_space_sum from dba_free_space)
/



PROMPT
PROMPT
PROMPT 3.2 Tablespace usage
PROMPT ===============================================================

COL Tablespace for a30

select DISTINCT df.tablespace_name "Tablespace",
round(df.TBS_byte /1048576,2) "Total(MB)",
round(fs.Free_byte /1048576,2) "Free(MB)",
round(((df.TBS_byte - fs.Free_byte)/df.TBS_byte) *100,0) "Used(%)",
db.autoextensible
--,round((df.TBS_byte - fs.Free_byte)/1048576,2) "Used(MB)",
--round((fs.Free_byte/df.TBS_byte)*100,0) "Free(%)"
from ( select tablespace_name, sum(bytes) TBS_byte
from dba_data_files group by tablespace_name ) df,
( select tablespace_name, max(bytes) Max_free, sum(bytes) Free_byte
from dba_free_space group by tablespace_name ) fs,
dba_data_files db
where df.tablespace_name = fs.tablespace_name
and df.tablespace_name = db.tablespace_name
order by 1
/


PROMPT
PROMPT
PROMPT 3.3 Temp Tablespace usage
PROMPT ===============================================================

col "File Name" for a40
col "Tablespace" for a10
col "File#" for 99
col "Rel.File#" for 99
col status for a9
col "Size(MB)" for a12
col "AutoExt." for a8
col "Increment(MB)" for a13

select
 file_id "File#",
 relative_fno "Rel.File#",
 a.tablespace_name "Tablespace",
 file_name "File Name",
 to_char(round(bytes/1048576),'999,999.99') "Size(MB)",
 decode(autoextensible,'NO','n/a',to_char(increment_by*block_size/1024/1024)) "Increment(MB)",
 status "Status",
 autoextensible "Auto Ext."
from dba_temp_files a,
     (select tablespace_name,block_size from dba_tablespaces) b
where a.tablespace_name=b.tablespace_name
order by 1,2;



PROMPT
PROMPT
PROMPT 3.4 Datafile Stat
PROMPT ===============================================================


col Tablespace for a20
col LOCATION for a56
col ON_STAT for a8
col status for a10
col MB for 999,999,999.99

select tablespace_name "Tablespace", file_name "LOCATION", bytes/1024/1024 "MB"
from dba_data_files
order by 1,3,2 ASC
/


PROMPT
PROMPT
PROMPT 3.5 Disk Physical I/O
PROMPT ===============================================================

CREATE OR REPLACE VIEW tot_read_writes
AS
SELECT SUM(phyrds) phys_reads
      ,SUM(phywrts) phys_wrts
FROM v$filestat
/

col tablespace_name     FORMAT a20              HEADING 'Tablespace'
col name                FORMAT a56              HEADING 'Datafile'
col read_pct            FORMAT 999.99           HEADING 'Reads%'
col wrts_pct            FORMAT 999.99           HEADING 'Writes%'

SELECT tablespace_name
      ,name
      ,phyrds*100/trw.phys_reads read_pct
      ,phywrts*100/trw.phys_wrts wrts_pct
--      ,phyrds
--      ,phywrts
FROM v$datafile df
    ,v$filestat fs
    ,tot_read_writes trw
    ,dba_data_files ts
WHERE df.file#=fs.file#
AND df.file#=ts.file_id
ORDER BY 1
/

DROP VIEW tot_read_writes
/


PROMPT
PROMPT
PROMPT 3.6 Internal and External Sort
PROMPT ===============================================================

col disksortratio       FORMAT a36              HEADING 'Disk Sort Ratio|(If higher, increase SORT_AREA_SIZE)'
col disksorts   FORMAT 999,999,999,999  HEADING 'Disk Sorts'
col memorysorts FORMAT 999,999,999,999  HEADING 'Memory Sorts'
col rowssorted  FORMAT 999,999,999,999  HEADING 'Rows Sorted'

SELECT ROUND(d.value/decode((m.value+d.value),0,1,
            (m.value+d.value))*100)||'%' AS disksortratio
      ,d.value AS disksorts
      ,m.value AS memorysorts
      ,r.value AS rowssorted
FROM v$sysstat m
    ,v$sysstat d
    ,v$sysstat r
WHERE m.name='sorts (memory)'
AND d.name='sorts (disk)'
AND r.name='sorts (rows)'
/



PROMPT
PROMPT
PROMPT
PROMPT ===============================================================
PROMPT = 4. Redo Log                                                 =
PROMPT =    4.1 Redo Log Buffer Size (MB)                            =
PROMPT =    4.2 Redo Log Status                                      =
PROMPT =    4.3 Redo Log File Wait (100/Day is good)                 =
PROMPT ===============================================================


PROMPT
PROMPT
PROMPT 4.1 Redo Log Buffer Size (MB)
PROMPT ===============================================================

col name FORMAT a15 HEADING 'Buffer Name'
col bytes FORMAT 999,999,999.99       HEADING 'Size(MB)'

SELECT name
      ,SUM(bytes)/1024/1024 AS bytes
FROM v$sgastat
WHERE name='log_buffer'
GROUP BY name
/

PROMPT
PROMPT
PROMPT 4.2 Redo Log Status
PROMPT ===============================================================

col group# for 999
col mb for 9999
col member for a70
col SEQ# for 999,999,999
col status for a8
col archived for a8
col first_change# for 999,999,999,999,999

select 
    a.group#,
    a.member, 
    b.bytes/1024/1024 MB, 
    b.sequence# as "SEQ#",
    b.status, 
    b.archived, 
    b.first_change#
from v$logfile a, v$log b 
where a.group# = b.group# 
order by 1,2;


PROMPT
PROMPT
PROMPT 4.3 Redo Log File Wait (100/Day is good)
PROMPT ===============================================================

PROMPT
PROMPT
PROMPT - Log File Switch Statistics
PROMPT ===========================================

col min FORMAT 999,999,999,999  HEADING 'Min/Day'
col avg FORMAT 999,999,999,999  HEADING 'Avg/Day'
col max FORMAT 999,999,999,999  HEADING 'Max/Day'

SELECT MIN(cnt) AS min
      ,AVG(cnt) AS avg
      ,MAX(cnt) AS max
FROM (SELECT TO_CHAR(first_time,'yyyymmdd') AS day
            ,COUNT(*) AS cnt
      FROM v$log_history
      WHERE thread#=1
      AND TO_CHAR(first_time,'yyyymm')=TO_CHAR(sysdate,'yyyymm')
      GROUP BY TO_CHAR(first_time,'yyyymmdd'))
/

PROMPT
PROMPT
PROMPT - Log File Switch Count Per Day
PROMPT ===========================================

col day for a10 HEADING 'Day/Time';
col 01 for a4
col 02 for a4
col 03 for a4
col 04 for a4
col 05 for a4
col 06 for a4
col 07 for a4
col 08 for a4
col 09 for a4
col 10 for a4
col 11 for a4
col 12 for a4
col 13 for a4
col 14 for a4
col 15 for a4
col 16 for a4
col 17 for a4
col 18 for a4
col 19 for a4
col 20 for a4
col 21 for a4
col 22 for a4
col 23 for a4

SELECT TO_CHAR(first_time,'yyyy-mm-dd') AS day
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'00',1,0)),'99') AS "00"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'01',1,0)),'99') AS "01"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'02',1,0)),'99') AS "02"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'03',1,0)),'99') AS "03"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'04',1,0)),'99') AS "04"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'05',1,0)),'99') AS "05"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'06',1,0)),'99') AS "06"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'07',1,0)),'99') AS "07"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'08',1,0)),'99') AS "08"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'09',1,0)),'99') AS "09"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'10',1,0)),'99') AS "10"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'11',1,0)),'99') AS "11"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'12',1,0)),'99') AS "12"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'13',1,0)),'99') AS "13"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'14',1,0)),'99') AS "14"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'15',1,0)),'99') AS "15"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'16',1,0)),'99') AS "16"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'17',1,0)),'99') AS "17"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'18',1,0)),'99') AS "18"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'19',1,0)),'99') AS "19"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'20',1,0)),'99') AS "20"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'21',1,0)),'99') AS "21"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'22',1,0)),'99') AS "22"
      ,TO_CHAR(SUM(DECODE(TO_CHAR(first_time,'HH24'),'23',1,0)),'99') AS "23"
      ,COUNT(*) AS "Day Sum"
FROM v$log_history
WHERE thread#=1
AND TO_CHAR(first_time,'yyyymm')=TO_CHAR(sysdate,'yyyymm')
GROUP BY TO_CHAR(first_time,'yyyy-mm-dd')
ORDER BY day DESC
/

PROMPT
PROMPT
PROMPT - Redo Log Space Requests
PROMPT ===========================================

col name       FORMAT a30       HEADING 'Name'
col value for 999,999,999 head 'Value|(Near 0 is good, or Increase LOG_BUFFER)'

SELECT 'Redo Log Space Requests' AS name
      ,value
FROM V$SYSSTAT
WHERE name = 'redo log space requests'
/

PROMPT
PROMPT
PROMPT - Redo History
PROMPT ===============================================================

col thread# for 99
col size_m for 999,999,999 HEADING 'Size(MB)';
col log_c for 999,999 HEADING 'Log Count';
col log_size for 999,999,999 HEADING 'Log Size(MB)';

select a.thread#,a.log_month as month, a.log_cnt * b.log_size as size_m, a.log_cnt as log_c, b.log_size as log_size
from
(select THREAD#,to_char(first_time, 'yyyy-mm')log_month, count(*) log_cnt from v$log_history
group by thread#,to_char(first_time, 'yyyy-mm')) a,
(select thread#, avg(bytes/1048576) log_size from v$log group by thread#) b
where a.thread#=b.thread#
order by a.log_month
/


PROMPT
PROMPT
PROMPT
PROMPT ===============================================================
PROMPT = 5. User Information                                         =
PROMPT =    5.1 DB Users                                             =
PROMPT =    5.2 User Table Information                               =
PROMPT =    5.3 User Objects Count                                   =
PROMPT =    5.4 User Procedures Information                          =
PROMPT ===============================================================



PROMPT
PROMPT
PROMPT 5.1 DB Users
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
PROMPT 5.2 User Table Information
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
PROMPT 5.3 User Objects Count
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
PROMPT 5.4 User Procedures Information
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
PROMPT = 6. Oracle Enterprise Edition                                =
PROMPT =    6.1 EE to SE Summary                                     =
PROMPT =    6.2 EE usage status                                      =
PROMPT ===============================================================


PROMPT
PROMPT
PROMPT 6.1 EE to SE Summary
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
PROMPT 6.2 EE usage status
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