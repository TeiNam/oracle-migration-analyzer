-- Owner: OE
-- Type: TYPE
-- Name: CUSTOMER_TYP
-- Source: plsql_f_ora12c_20260118.out (Lines 402-425)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE "OE"."CUSTOMER_TYP"
 AS OBJECT
    ( customer_id        NUMBER(6)
    , cust_first_name    VARCHAR2(20)
    , cust_last_name     VARCHAR2(20)
    , cust_address       cust_address_typ
    , phone_numbers      phone_list_typ
    , nls_language       VARCHAR2(3)
    , nls_territory      VARCHAR2(40)
    , credit_limit       NUMBER(9,2)
    , cust_email         VARCHAR2(40)
    , cust_orders        order_list_typ
    )
NOT FINAL;
/
/
