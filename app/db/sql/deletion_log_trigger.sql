DO $$
DECLARE
    tbl_name text;
    trigger_name text;
BEGIN
    FOR tbl_name IN 
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename != 'deletion_log'
    LOOP
        trigger_name := tbl_name || '_deletion_log_trigger';

        EXECUTE format('DROP TRIGGER IF EXISTS %I ON %I', 
                        trigger_name, tbl_name);

        EXECUTE format('CREATE TRIGGER %I 
                        BEFORE DELETE ON %I
                        FOR EACH ROW
                        EXECUTE FUNCTION deletion_log_trigger()', 
                        trigger_name, tbl_name);
    END LOOP;
END;
$$;