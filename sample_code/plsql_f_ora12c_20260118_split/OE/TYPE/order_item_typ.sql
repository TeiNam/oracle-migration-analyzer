-- Owner: OE
-- Type: TYPE
-- Name: ORDER_ITEM_TYP
-- Source: plsql_f_ora12c_20260118.out (Lines 570-588)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE "OE"."ORDER_ITEM_TYP"

 AS OBJECT
    ( order_id           NUMBER(12)
    , line_item_id       NUMBER(3)
    , unit_price         NUMBER(8,2)
    , quantity           NUMBER(8)
    , product_ref  REF   product_information_typ
    ) ;
/
/
