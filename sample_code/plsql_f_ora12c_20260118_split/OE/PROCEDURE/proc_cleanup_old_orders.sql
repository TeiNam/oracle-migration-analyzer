-- Owner: OE
-- Type: PROCEDURE
-- Name: PROC_CLEANUP_OLD_ORDERS
-- Source: plsql_f_ora12c_20260118.out (Lines 56-81)
-- ============================================================

CREATE OR REPLACE EDITIONABLE PROCEDURE "OE"."PROC_CLEANUP_OLD_ORDERS" (
    p_days_old    IN  NUMBER DEFAULT 365,
    p_deleted_cnt OUT NUMBER
) AS
BEGIN
    DELETE FROM oe.order_items
    WHERE order_id IN (
        SELECT order_id FROM oe.orders
        WHERE order_date < SYSDATE - p_days_old
    );

    DELETE FROM oe.orders
    WHERE order_date < SYSDATE - p_days_old;

    p_deleted_cnt := SQL%ROWCOUNT;
    COMMIT;
END;
/
/
