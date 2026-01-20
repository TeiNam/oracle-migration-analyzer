-- Owner: OE
-- Type: TYPE
-- Name: CATALOG_TYP
-- Source: plsql_f_ora12c_20260118.out (Lines 238-265)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE "OE"."CATALOG_TYP"

 UNDER composite_category_typ
      (
    MEMBER FUNCTION getCatalogName RETURN VARCHAR2
       , OVERRIDING MEMBER FUNCTION category_describe RETURN VARCHAR2
      );
/
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
