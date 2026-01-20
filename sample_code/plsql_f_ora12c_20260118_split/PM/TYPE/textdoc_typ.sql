-- Owner: PM
-- Type: TYPE
-- Name: TEXTDOC_TYP
-- Source: plsql_f_ora12c_20260118.out (Lines 831-846)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE "PM"."TEXTDOC_TYP"

  AS OBJECT
    ( document_typ      VARCHAR2(32)
    , formatted_doc     BLOB
    ) ;
/
/
