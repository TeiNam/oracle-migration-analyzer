-- Owner: OE
-- Type: TRIGGER
-- Name: ORDERS_TRG
-- Source: plsql_f_ora12c_20260118.out (Lines 175-193)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TRIGGER "OE"."ORDERS_TRG" INSTEAD OF INSERT
 ON oc_orders FOR EACH ROW
BEGIN
   INSERT INTO ORDERS (order_id, order_mode, order_total,
                       sales_rep_id, order_status)
               VALUES (:NEW.order_id, :NEW.order_mode,
                       :NEW.order_total, :NEW.sales_rep_id,
                       :NEW.order_status);
END;
/
ALTER TRIGGER "OE"."ORDERS_TRG" ENABLE;
/
