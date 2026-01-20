-- Owner: SH
-- Type: PROCEDURE
-- Name: PROC_CHANNEL_PERFORMANCE
-- Source: plsql_f_ora12c_20260118.out (Lines 875-897)
-- ============================================================

CREATE OR REPLACE EDITIONABLE PROCEDURE "SH"."PROC_CHANNEL_PERFORMANCE" (
    p_channel_id  IN  NUMBER,
    p_start_date  IN  DATE,
    p_end_date    IN  DATE,
    p_revenue     OUT NUMBER,
    p_trans_cnt   OUT NUMBER
) AS
BEGIN
    SELECT NVL(SUM(amount_sold), 0), COUNT(*)
    INTO p_revenue, p_trans_cnt
    FROM sh.sales
    WHERE channel_id = p_channel_id
      AND time_id BETWEEN p_start_date AND p_end_date;
END;
/
/
