-- Owner: OE
-- Type: TRIGGER
-- Name: PURCHASEORDER$xd
-- Source: plsql_f_ora12c_20260118.out (Lines 194-204)
-- ============================================================

CREATE OR REPLACE EDITIONABLE TRIGGER "OE"."PURCHASEORDER$xd" after delete or update on "OE"."PURCHASEORDER" for each row BEGIN  IF (deleting) THEN xdb.xdb_pitrig_pkg.pitrig_del('OE','PURCHASEORDER', :old.sys_nc_oid$, '481E89C4A1385B7FE065D5F3EDFC1B7E' ); END IF;   IF (updating) THEN xdb.xdb_pitrig_pkg.pitrig_upd('OE','PURCHASEORDER', :old.sys_nc_oid$, '481E89C4A1385B7FE065D5F3EDFC1B7E', user ); END IF; END;
/
ALTER TRIGGER "OE"."PURCHASEORDER$xd" ENABLE;
/
