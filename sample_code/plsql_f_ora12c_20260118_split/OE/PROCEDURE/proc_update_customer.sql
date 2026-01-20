-- Owner: OE
-- Type: PROCEDURE
-- Name: PROC_UPDATE_CUSTOMER
-- Source: plsql_f_ora12c_20260118.out (Lines 103-133)
-- ============================================================

CREATE OR REPLACE EDITIONABLE PROCEDURE "OE"."PROC_UPDATE_CUSTOMER" (
    p_customer_id   IN  NUMBER,
    p_credit_limit  IN  NUMBER DEFAULT NULL,
    p_email         IN  VARCHAR2 DEFAULT NULL
) AS
    v_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM oe.customers
    WHERE customer_id = p_customer_id;

    IF v_count = 0 THEN
        RAISE_APPLICATION_ERROR(-20001, 'Customer not found');
    END IF;

    UPDATE oe.customers
    SET credit_limit = NVL(p_credit_limit, credit_limit),
        cust_email = NVL(p_email, cust_email)
    WHERE customer_id = p_customer_id;

    COMMIT;
END;
/
/
