-- 복잡한 데이터 마이그레이션 및 변환 프로시저
-- Oracle 종속 패키지: DBMS_XMLGEN, DBMS_CRYPTO, UTL_HTTP, UTL_MAIL, DBMS_PIPE
CREATE OR REPLACE PACKAGE PKG_DATA_MIGRATION AS
    -- 타입 정의
    TYPE t_migration_result IS RECORD (
        source_table VARCHAR2(100),
        target_table VARCHAR2(100),
        rows_processed NUMBER,
        rows_failed NUMBER,
        execution_time NUMBER,
        status VARCHAR2(50)
    );
    
    TYPE t_migration_results IS TABLE OF t_migration_result;
    
    -- Public 프로시저
    PROCEDURE migrate_table_data(
        p_source_schema IN VARCHAR2,
        p_target_schema IN VARCHAR2,
        p_table_name IN VARCHAR2,
        p_transform_rules IN XMLTYPE DEFAULT NULL,
        p_notify_email IN VARCHAR2 DEFAULT NULL
    );
    
    FUNCTION get_migration_report RETURN t_migration_results PIPELINED;
    
END PKG_DATA_MIGRATION;
/

CREATE OR REPLACE PACKAGE BODY PKG_DATA_MIGRATION AS
    
    -- Private 변수
    g_migration_log t_migration_results := t_migration_results();
    
    -- Private 함수: 데이터 암호화 (DBMS_CRYPTO)
    FUNCTION encrypt_sensitive_data(p_data IN VARCHAR2) RETURN RAW IS
        v_key RAW(32) := UTL_RAW.CAST_TO_RAW('MySecretKey12345678901234567890');
        v_encrypted RAW(2000);
    BEGIN
        v_encrypted := DBMS_CRYPTO.ENCRYPT(
            src => UTL_RAW.CAST_TO_RAW(p_data),
            typ => DBMS_CRYPTO.ENCRYPT_AES256 + DBMS_CRYPTO.CHAIN_CBC + DBMS_CRYPTO.PAD_PKCS5,
            key => v_key
        );
        RETURN v_encrypted;
    END encrypt_sensitive_data;
    
    -- Private 함수: XML 기반 변환 규칙 적용
    FUNCTION apply_transform_rules(
        p_column_name IN VARCHAR2,
        p_column_value IN VARCHAR2,
        p_rules IN XMLTYPE
    ) RETURN VARCHAR2 IS
        v_transformed VARCHAR2(4000);
        v_rule_type VARCHAR2(50);
        v_rule_param VARCHAR2(1000);
    BEGIN
        -- XML에서 변환 규칙 추출
        SELECT 
            EXTRACTVALUE(p_rules, '//rule[@column="' || p_column_name || '"]/@type'),
            EXTRACTVALUE(p_rules, '//rule[@column="' || p_column_name || '"]/@param')
        INTO v_rule_type, v_rule_param
        FROM dual;
        
        -- 규칙 타입에 따른 변환
        CASE v_rule_type
            WHEN 'UPPERCASE' THEN
                v_transformed := UPPER(p_column_value);
            WHEN 'ENCRYPT' THEN
                v_transformed := RAWTOHEX(encrypt_sensitive_data(p_column_value));
            WHEN 'MASK' THEN
                v_transformed := REGEXP_REPLACE(p_column_value, v_rule_param, '***');
            WHEN 'LOOKUP' THEN
                -- 동적 룩업 테이블 조회
                EXECUTE IMMEDIATE 
                    'SELECT new_value FROM ' || v_rule_param || 
                    ' WHERE old_value = :1'
                INTO v_transformed
                USING p_column_value;
            ELSE
                v_transformed := p_column_value;
        END CASE;
        
        RETURN v_transformed;
        
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN p_column_value;
        WHEN OTHERS THEN
            RETURN p_column_value;
    END apply_transform_rules;
    
    -- Private 프로시저: 병렬 처리를 위한 파이프 통신 (DBMS_PIPE)
    PROCEDURE send_progress_update(
        p_pipe_name IN VARCHAR2,
        p_message IN VARCHAR2
    ) IS
        v_status NUMBER;
    BEGIN
        DBMS_PIPE.PACK_MESSAGE(p_message);
        v_status := DBMS_PIPE.SEND_MESSAGE(p_pipe_name, 1);
        
        IF v_status != 0 THEN
            DBMS_OUTPUT.PUT_LINE('Failed to send pipe message: ' || v_status);
        END IF;
    END send_progress_update;
    
    -- Private 프로시저: 이메일 알림 (UTL_MAIL)
    PROCEDURE send_notification_email(
        p_recipient IN VARCHAR2,
        p_subject IN VARCHAR2,
        p_message IN VARCHAR2
    ) IS
    BEGIN
        UTL_MAIL.SEND(
            sender => 'migration@company.com',
            recipients => p_recipient,
            subject => p_subject,
            message => p_message,
            mime_type => 'text/html; charset=us-ascii'
        );
    EXCEPTION
        WHEN OTHERS THEN
            DBMS_OUTPUT.PUT_LINE('Email notification failed: ' || SQLERRM);
    END send_notification_email;
    
    -- Private 프로시저: REST API 호출 (UTL_HTTP)
    PROCEDURE call_external_api(
        p_url IN VARCHAR2,
        p_method IN VARCHAR2,
        p_payload IN VARCHAR2,
        p_response OUT VARCHAR2
    ) IS
        v_req UTL_HTTP.REQ;
        v_resp UTL_HTTP.RESP;
        v_buffer VARCHAR2(32767);
    BEGIN
        -- HTTP 요청 설정
        v_req := UTL_HTTP.BEGIN_REQUEST(p_url, p_method);
        UTL_HTTP.SET_HEADER(v_req, 'Content-Type', 'application/json');
        UTL_HTTP.SET_HEADER(v_req, 'Content-Length', LENGTH(p_payload));
        
        -- 페이로드 전송
        IF p_payload IS NOT NULL THEN
            UTL_HTTP.WRITE_TEXT(v_req, p_payload);
        END IF;
        
        -- 응답 수신
        v_resp := UTL_HTTP.GET_RESPONSE(v_req);
        
        BEGIN
            LOOP
                UTL_HTTP.READ_LINE(v_resp, v_buffer, TRUE);
                p_response := p_response || v_buffer;
            END LOOP;
        EXCEPTION
            WHEN UTL_HTTP.END_OF_BODY THEN
                NULL;
        END;
        
        UTL_HTTP.END_RESPONSE(v_resp);
        
    EXCEPTION
        WHEN OTHERS THEN
            IF v_resp.status_code IS NOT NULL THEN
                UTL_HTTP.END_RESPONSE(v_resp);
            END IF;
            RAISE;
    END call_external_api;
    
    -- Public 프로시저: 테이블 데이터 마이그레이션
    PROCEDURE migrate_table_data(
        p_source_schema IN VARCHAR2,
        p_target_schema IN VARCHAR2,
        p_table_name IN VARCHAR2,
        p_transform_rules IN XMLTYPE DEFAULT NULL,
        p_notify_email IN VARCHAR2 DEFAULT NULL
    ) IS
        v_start_time TIMESTAMP := SYSTIMESTAMP;
        v_end_time TIMESTAMP;
        v_rows_processed NUMBER := 0;
        v_rows_failed NUMBER := 0;
        v_batch_size CONSTANT NUMBER := 10000;
        v_result t_migration_result;
        
        -- 동적 커서
        TYPE t_ref_cursor IS REF CURSOR;
        v_cursor t_ref_cursor;
        
        -- 동적 SQL
        v_select_sql VARCHAR2(4000);
        v_insert_sql VARCHAR2(4000);
        v_column_list VARCHAR2(4000);
        v_xml_data XMLTYPE;
        
        -- BULK COLLECT 타입
        TYPE t_rowid_array IS TABLE OF ROWID;
        TYPE t_varchar_array IS TABLE OF VARCHAR2(4000);
        v_rowids t_rowid_array;
        v_data_array t_varchar_array;
        
    BEGIN
        -- 컬럼 목록 조회
        SELECT LISTAGG(column_name, ',') WITHIN GROUP (ORDER BY column_id)
        INTO v_column_list
        FROM all_tab_columns
        WHERE owner = UPPER(p_source_schema)
        AND table_name = UPPER(p_table_name);
        
        -- 소스 데이터를 XML로 변환 (DBMS_XMLGEN)
        v_select_sql := 'SELECT DBMS_XMLGEN.GETXMLTYPE(''
            SELECT ' || v_column_list || ' 
            FROM ' || p_source_schema || '.' || p_table_name || '
            WHERE ROWNUM <= ' || v_batch_size || '
        '') FROM dual';
        
        -- 배치 처리 루프
        LOOP
            BEGIN
                EXECUTE IMMEDIATE v_select_sql INTO v_xml_data;
                
                EXIT WHEN v_xml_data IS NULL;
                
                -- XML 데이터 파싱 및 변환
                FOR rec IN (
                    SELECT 
                        EXTRACTVALUE(VALUE(t), '//ROW/*[1]') as col1,
                        EXTRACTVALUE(VALUE(t), '//ROW/*[2]') as col2,
                        EXTRACTVALUE(VALUE(t), '//ROW/*[3]') as col3
                    FROM TABLE(XMLSEQUENCE(EXTRACT(v_xml_data, '/ROWSET/ROW'))) t
                ) LOOP
                    BEGIN
                        -- 변환 규칙 적용
                        IF p_transform_rules IS NOT NULL THEN
                            rec.col1 := apply_transform_rules('COL1', rec.col1, p_transform_rules);
                            rec.col2 := apply_transform_rules('COL2', rec.col2, p_transform_rules);
                        END IF;
                        
                        -- 타겟 테이블에 삽입
                        v_insert_sql := 'INSERT INTO ' || p_target_schema || '.' || p_table_name ||
                                       ' VALUES (:1, :2, :3)';
                        EXECUTE IMMEDIATE v_insert_sql USING rec.col1, rec.col2, rec.col3;
                        
                        v_rows_processed := v_rows_processed + 1;
                        
                        -- 진행 상황 업데이트 (파이프 통신)
                        IF MOD(v_rows_processed, 1000) = 0 THEN
                            send_progress_update(
                                'MIGRATION_PIPE',
                                'Processed ' || v_rows_processed || ' rows for ' || p_table_name
                            );
                        END IF;
                        
                    EXCEPTION
                        WHEN OTHERS THEN
                            v_rows_failed := v_rows_failed + 1;
                            -- 에러 로깅
                            INSERT INTO migration_error_log (
                                table_name, error_message, error_data, error_time
                            ) VALUES (
                                p_table_name, SQLERRM, rec.col1 || '|' || rec.col2, SYSTIMESTAMP
                            );
                    END;
                END LOOP;
                
                COMMIT;
                
                -- 다음 배치 준비
                v_select_sql := REPLACE(v_select_sql, 
                    'WHERE ROWNUM <= ' || v_batch_size,
                    'WHERE ROWNUM <= ' || v_batch_size || ' AND rowid > last_processed_rowid'
                );
                
            EXCEPTION
                WHEN NO_DATA_FOUND THEN
                    EXIT;
            END;
        END LOOP;
        
        v_end_time := SYSTIMESTAMP;
        
        -- 결과 기록
        v_result.source_table := p_source_schema || '.' || p_table_name;
        v_result.target_table := p_target_schema || '.' || p_table_name;
        v_result.rows_processed := v_rows_processed;
        v_result.rows_failed := v_rows_failed;
        v_result.execution_time := EXTRACT(SECOND FROM (v_end_time - v_start_time));
        v_result.status := CASE 
            WHEN v_rows_failed = 0 THEN 'SUCCESS'
            WHEN v_rows_failed < v_rows_processed * 0.05 THEN 'SUCCESS_WITH_ERRORS'
            ELSE 'FAILED'
        END;
        
        g_migration_log.EXTEND;
        g_migration_log(g_migration_log.COUNT) := v_result;
        
        -- 외부 API 호출 (마이그레이션 완료 알림)
        DECLARE
            v_api_response VARCHAR2(4000);
            v_json_payload VARCHAR2(1000);
        BEGIN
            v_json_payload := '{"table":"' || p_table_name || 
                            '","rows":' || v_rows_processed || 
                            ',"status":"' || v_result.status || '"}';
            
            call_external_api(
                'https://api.company.com/migration/notify',
                'POST',
                v_json_payload,
                v_api_response
            );
        EXCEPTION
            WHEN OTHERS THEN
                DBMS_OUTPUT.PUT_LINE('API call failed: ' || SQLERRM);
        END;
        
        -- 이메일 알림
        IF p_notify_email IS NOT NULL THEN
            send_notification_email(
                p_notify_email,
                'Migration Completed: ' || p_table_name,
                '<html><body>' ||
                '<h2>Migration Summary</h2>' ||
                '<p>Table: ' || p_table_name || '</p>' ||
                '<p>Rows Processed: ' || v_rows_processed || '</p>' ||
                '<p>Rows Failed: ' || v_rows_failed || '</p>' ||
                '<p>Status: ' || v_result.status || '</p>' ||
                '</body></html>'
            );
        END IF;
        
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            -- 에러 알림
            IF p_notify_email IS NOT NULL THEN
                send_notification_email(
                    p_notify_email,
                    'Migration Failed: ' || p_table_name,
                    'Error: ' || SQLERRM
                );
            END IF;
            RAISE;
    END migrate_table_data;
    
    -- Public 함수: 마이그레이션 리포트 생성 (Pipelined Function)
    FUNCTION get_migration_report RETURN t_migration_results PIPELINED IS
    BEGIN
        FOR i IN 1..g_migration_log.COUNT LOOP
            PIPE ROW(g_migration_log(i));
        END LOOP;
        RETURN;
    END get_migration_report;
    
END PKG_DATA_MIGRATION;
/

-- 사용 예제
/*
-- 변환 규칙 XML 정의
DECLARE
    v_rules XMLTYPE := XMLTYPE('
        <rules>
            <rule column="SSN" type="ENCRYPT"/>
            <rule column="EMAIL" type="MASK" param="@.*"/>
            <rule column="STATUS" type="LOOKUP" param="status_mapping_table"/>
        </rules>
    ');
BEGIN
    PKG_DATA_MIGRATION.migrate_table_data(
        p_source_schema => 'OLD_SCHEMA',
        p_target_schema => 'NEW_SCHEMA',
        p_table_name => 'CUSTOMERS',
        p_transform_rules => v_rules,
        p_notify_email => 'admin@company.com'
    );
END;
/

-- 마이그레이션 리포트 조회
SELECT * FROM TABLE(PKG_DATA_MIGRATION.get_migration_report());
*/
