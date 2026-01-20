-- Owner: OE
-- Type: TRIGGER
-- Name: ORDERS_ITEMS_TRG
-- Source: plsql_f_ora12c_20260118.out (Lines 155-174)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TRIGGER "OE"."ORDERS_ITEMS_TRG" INSTEAD OF INSERT ON NESTED
 TABLE order_item_list OF oc_orders FOR EACH ROW
DECLARE
    prod  product_information_typ;
BEGIN
    SELECT DEREF(:NEW.product_ref) INTO prod FROM DUAL;
    INSERT INTO order_items VALUES (prod.product_id, :NEW.order_id,
                                    :NEW.line_item_id, :NEW.unit_price,
                                    :NEW.quantity);
END;
/
ALTER TRIGGER "OE"."ORDERS_ITEMS_TRG" ENABLE;
/
