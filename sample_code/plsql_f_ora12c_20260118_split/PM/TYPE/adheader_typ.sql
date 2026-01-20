-- Owner: PM
-- Type: TYPE
-- Name: ADHEADER_TYP
-- Source: plsql_f_ora12c_20260118.out (Lines 800-817)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE "PM"."ADHEADER_TYP"

  AS OBJECT
    ( header_name        VARCHAR2(256)
    , creation_date      DATE
    , header_text        VARCHAR2(1024)
    , logo               BLOB
    );
/
/
