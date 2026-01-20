-- Owner: OE
-- Type: TYPE
-- Name: WAREHOUSE_TYP
-- Source: plsql_f_ora12c_20260118.out (Lines 733-749)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE "OE"."WAREHOUSE_TYP"

 AS OBJECT
    ( warehouse_id       NUMBER(3)
    , warehouse_name     VARCHAR2(35)
    , location_id        NUMBER(4)
    ) ;
/
/
