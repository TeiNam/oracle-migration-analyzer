-- Owner: SH
-- Type: PROCEDURE
-- Name: PROC_AGGREGATE_SALES
-- Source: plsql_f_ora12c_20260118.out (Lines 847-874)
-- ============================================================

CREATE OR REPLACE EDITIONABLE PROCEDURE "SH"."PROC_AGGREGATE_SALES" (
    p_year    IN  NUMBER,
    p_quarter IN  NUMBER DEFAULT NULL
) AS
    v_total NUMBER;
BEGIN
    IF p_quarter IS NULL THEN
        SELECT NVL(SUM(amount_sold), 0) INTO v_total
        FROM sh.sales
        WHERE EXTRACT(YEAR FROM time_id) = p_year;
    ELSE
        SELECT NVL(SUM(amount_sold), 0) INTO v_total
        FROM sh.sales
        WHERE EXTRACT(YEAR FROM time_id) = p_year
          AND CEIL(EXTRACT(MONTH FROM time_id) / 3) = p_quarter;
    END IF;

    DBMS_OUTPUT.PUT_LINE('Total Sales: ' || TO_CHAR(v_total, '999,999,999.99'));
END;
/
/
