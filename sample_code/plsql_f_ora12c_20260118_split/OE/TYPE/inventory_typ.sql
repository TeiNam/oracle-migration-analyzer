-- Owner: OE
-- Type: TYPE
-- Name: INVENTORY_TYP
-- Source: plsql_f_ora12c_20260118.out (Lines 458-475)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE "OE"."INVENTORY_TYP"


 AS OBJECT
    ( product_id          NUMBER(6)
    , warehouse           warehouse_typ
    , quantity_on_hand    NUMBER(8)
    ) ;
/
/
