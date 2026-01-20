-- Owner: IX
-- Type: TYPE
-- Name: ORDER_EVENT_TYP
-- Source: plsql_f_ora12c_20260118.out (Lines 13-31)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TYPE "IX"."ORDER_EVENT_TYP" AS OBJECT (
	order_id 	NUMBER(12),
	product_id  	NUMBER(6),
	customer_id	NUMBER(6),
	cust_first_name	VARCHAR2(20),
	cust_last_name	VARCHAR2(20),
	order_status  	NUMBER(2),
	delivery_date	DATE
);
/
/
