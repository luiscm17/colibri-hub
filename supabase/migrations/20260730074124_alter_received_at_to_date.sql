-- Alter received_at from TIMESTAMP WITH TIME ZONE to DATE.
-- Existing timestamptz values are converted to calendar dates using UTC extraction.
-- RLS remains enabled on raw_material_batches and privilege revocations are unaffected
-- because ALTER COLUMN TYPE does not modify RLS policies or granted privileges.

alter table public.raw_material_batches
    alter column received_at type date
    using (received_at at time zone 'UTC')::date;
