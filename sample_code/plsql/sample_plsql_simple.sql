-- 단순한 CRUD 프로시저 (MySQL 마이그레이션에 적합)
CREATE OR REPLACE PROCEDURE GET_CUSTOMER_INFO (
    p_customer_id IN NUMBER,
    p_name OUT VARCHAR2,
    p_email OUT VARCHAR2
)
IS
BEGIN
    SELECT name, email
    INTO p_name, p_email
    FROM customers
    WHERE customer_id = p_customer_id;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        p_name := NULL;
        p_email := NULL;
END GET_CUSTOMER_INFO;
/
