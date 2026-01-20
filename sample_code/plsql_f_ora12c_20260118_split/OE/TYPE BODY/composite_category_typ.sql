-- Owner: OE
-- Type: TYPE BODY
-- Name: COMPOSITE_CATEGORY_TYP
-- Source: plsql_f_ora12c_20260118.out (Lines 770-784)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE BODY "OE"."COMPOSITE_CATEGORY_TYP" AS
    OVERRIDING MEMBER FUNCTION category_describe RETURN VARCHAR2 IS
    BEGIN
      RETURN 'composite_category_typ';
    END;
   END;
/
/
