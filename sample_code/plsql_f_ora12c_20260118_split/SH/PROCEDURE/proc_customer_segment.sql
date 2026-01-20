-- Owner: SH
-- Type: PROCEDURE
-- Name: PROC_CUSTOMER_SEGMENT
-- Source: plsql_f_ora12c_20260118.out (Lines 898-922)
-- ============================================================

CREATE OR REPLACE EDITIONABLE PROCEDURE "SH"."PROC_CUSTOMER_SEGMENT" (
    p_min_purchase  IN  NUMBER,
    p_customer_cnt  OUT NUMBER
) AS
BEGIN
    SELECT COUNT(DISTINCT cust_id) INTO p_customer_cnt
    FROM sh.sales
    GROUP BY cust_id
    HAVING SUM(amount_sold) >= p_min_purchase;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        p_customer_cnt := 0;
END;
/



Report Completed Time
===============================================================
2026-01-18   17:48:44
/
