-- Owner: OE
-- Type: TYPE BODY
-- Name: CATALOG_TYP
-- Source: plsql_f_ora12c_20260118.out (Lines 750-769)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE BODY "OE"."CATALOG_TYP" AS
  OVERRIDING MEMBER FUNCTION category_describe RETURN varchar2 IS
  BEGIN
    RETURN 'catalog_typ';
  END;
  MEMBER FUNCTION getCatalogName RETURN varchar2 IS
  BEGIN
    RETURN self.category_name;
  END;
END;
/
/
