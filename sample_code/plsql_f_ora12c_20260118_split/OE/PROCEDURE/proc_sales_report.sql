-- Owner: OE
-- Type: PROCEDURE
-- Name: PROC_SALES_REPORT
-- Source: plsql_f_ora12c_20260118.out (Lines 82-102)
-- ============================================================

CREATE OR REPLACE EDITIONABLE PROCEDURE "OE"."PROC_SALES_REPORT" (
    p_start_date  IN  DATE,
    p_end_date    IN  DATE,
    p_total       OUT NUMBER,
    p_order_cnt   OUT NUMBER
) AS
BEGIN
    SELECT NVL(SUM(order_total), 0), COUNT(*)
    INTO p_total, p_order_cnt
    FROM oe.orders
    WHERE order_date BETWEEN p_start_date AND p_end_date;
END;
/
/
