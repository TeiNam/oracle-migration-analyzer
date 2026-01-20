-- Owner: OE
-- Type: FUNCTION
-- Name: GET_PHONE_NUMBER_F
-- Source: plsql_f_ora12c_20260118.out (Lines 32-55)
-- ============================================================

CREATE OR REPLACE EDITIONABLE FUNCTION "OE"."GET_PHONE_NUMBER_F"
  (p_in INTEGER, p_phonelist phone_list_typ)
RETURN VARCHAR2 AS
  TYPE phone_list IS VARRAY(5) OF VARCHAR2(25);
  phone_out varchar2(25) := null;
  v_size INTEGER;
BEGIN
    IF p_phonelist.FIRST IS NULL OR
       p_in > (p_phonelist.LAST + 1) - p_phonelist.FIRST THEN
      RETURN phone_out;
    ELSE
      phone_out := p_phonelist(p_in);
      RETURN phone_out;
    END IF;
END;
/
/
