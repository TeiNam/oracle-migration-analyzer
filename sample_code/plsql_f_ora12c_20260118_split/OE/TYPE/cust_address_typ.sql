-- Owner: OE
-- Type: TYPE
-- Name: CUST_ADDRESS_TYP
-- Source: plsql_f_ora12c_20260118.out (Lines 426-444)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE "OE"."CUST_ADDRESS_TYP"

  AS OBJECT
    ( street_address     VARCHAR2(40)
    , postal_code        VARCHAR2(10)
    , city               VARCHAR2(30)
    , state_province     VARCHAR2(10)
    , country_id         CHAR(2)
    );
/
/
