CREATE OR REPLACE FUNCTION deletion_log_trigger()
RETURNS TRIGGER AS $$
DECLARE
    user_id INTEGER;
    record_json JSONB;
BEGIN
    user_id := COALESCE(
        NULLIF(current_setting('session.user_id', TRUE), '')::INTEGER, 
        -1
    );
    record_json := to_jsonb(OLD);
    
    INSERT INTO deletion_log (
        deleted_by,
        table_name,
        record_id,
        record_data,
        deleted_at
    ) VALUES (
        user_id,
        TG_TABLE_NAME,
        OLD.id,
        record_json,
        NOW()
    );
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;