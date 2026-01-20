-- Owner: OE
-- Type: TYPE
-- Name: LINEITEM_T
-- Source: plsql_f_ora12c_20260118.out (Lines 534-545)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE "OE"."LINEITEM_T" AS OBJECT ("SYS_XDBPD$" "XDB"."XDB$RAW_LIST_T","ITEMNUMBER" NUMBER(38),"DESCRIPTION" VARCHAR2(256 CHAR),"PART" "PART_T")NOT FINAL INSTANTIABLE
/
/
