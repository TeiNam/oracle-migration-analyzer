-- Owner: OE
-- Type: TYPE BODY
-- Name: LEAF_CATEGORY_TYP
-- Source: plsql_f_ora12c_20260118.out (Lines 785-799)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE BODY "OE"."LEAF_CATEGORY_TYP" AS
    OVERRIDING MEMBER FUNCTION  category_describe RETURN VARCHAR2 IS
    BEGIN
       RETURN  'leaf_category_typ';
    END;
   END;
/
/
