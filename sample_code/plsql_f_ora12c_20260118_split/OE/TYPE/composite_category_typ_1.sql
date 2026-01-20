-- Owner: OE
-- Type: TYPE
-- Name: COMPOSITE_CATEGORY_TYP
-- Source: plsql_f_ora12c_20260118.out (Lines 363-386)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE "OE"."COMPOSITE_CATEGORY_TYP"

 UNDER category_typ
      (
    subcategory_ref_list subcategory_ref_list_typ
      , OVERRIDING MEMBER FUNCTION  category_describe RETURN VARCHAR2
      )
  NOT FINAL;
/
CREATE OR REPLACE EDITIONABLE TYPE BODY "OE"."COMPOSITE_CATEGORY_TYP" AS
    OVERRIDING MEMBER FUNCTION category_describe RETURN VARCHAR2 IS
    BEGIN
      RETURN 'composite_category_typ';
    END;
   END;
/
/
