-- Owner: OE
-- Type: TYPE
-- Name: CATEGORY_TYP
-- Source: plsql_f_ora12c_20260118.out (Lines 316-337)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE "OE"."CATEGORY_TYP"

 AS OBJECT
    ( category_name           VARCHAR2(50)
    , category_description    VARCHAR2(1000)
    , category_id             NUMBER(2)
    , NOT instantiable
      MEMBER FUNCTION category_describe RETURN VARCHAR2
      )
  NOT INSTANTIABLE NOT FINAL
 ALTER TYPE "OE"."CATEGORY_TYP"
 ADD ATTRIBUTE (parent_category_id number(2)) CASCADE
/
/
