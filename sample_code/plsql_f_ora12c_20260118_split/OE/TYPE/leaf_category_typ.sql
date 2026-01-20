-- Owner: OE
-- Type: TYPE
-- Name: LEAF_CATEGORY_TYP
-- Source: plsql_f_ora12c_20260118.out (Lines 476-498)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE "OE"."LEAF_CATEGORY_TYP"

 UNDER category_typ
    (
    product_ref_list    product_ref_list_typ
    , OVERRIDING MEMBER FUNCTION  category_describe RETURN VARCHAR2
    );
/
CREATE OR REPLACE EDITIONABLE TYPE BODY "OE"."LEAF_CATEGORY_TYP" AS
    OVERRIDING MEMBER FUNCTION  category_describe RETURN VARCHAR2 IS
    BEGIN
       RETURN  'leaf_category_typ';
    END;
   END;
/
/
