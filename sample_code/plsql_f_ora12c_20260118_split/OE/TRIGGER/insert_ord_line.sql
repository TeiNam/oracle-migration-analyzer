-- Owner: OE
-- Type: TRIGGER
-- Name: INSERT_ORD_LINE
-- Source: plsql_f_ora12c_20260118.out (Lines 134-154)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TRIGGER "OE"."INSERT_ORD_LINE"
  BEFORE INSERT ON order_items
  FOR EACH ROW
  DECLARE
    new_line number;
  BEGIN
    SELECT (NVL(MAX(line_item_id),0)+1) INTO new_line
      FROM order_items
      WHERE order_id = :new.order_id;
    :new.line_item_id := new_line;
  END;
/
ALTER TRIGGER "OE"."INSERT_ORD_LINE" ENABLE;
/
