-- Add delivery_date column to raw_material_bales.
-- Add CHECK constraint enforcing the state-date invariant:
--   in_warehouse → delivery_date must be NULL
--   delivered    → delivery_date must be NOT NULL
-- Add performance indexes for status, received_at, and material_type queries.
--
-- The existing ck_raw_material_bales_status constraint, RLS configuration,
-- and privilege revocations remain unaffected by these DDL statements.

alter table public.raw_material_bales
    add column delivery_date date null;

alter table public.raw_material_bales
    add constraint ck_raw_material_bales_status_delivery_date check (
        (status = 'in_warehouse' and delivery_date is null)
        or (status = 'delivered' and delivery_date is not null)
    );

create index ix_raw_material_bales_status
    on public.raw_material_bales (status);

create index ix_raw_material_batches_received_at
    on public.raw_material_batches (received_at);

create index ix_raw_material_bales_material_type
    on public.raw_material_bales (material_type);
