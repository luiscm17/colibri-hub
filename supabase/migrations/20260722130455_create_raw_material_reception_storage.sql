create table public.raw_material_batches (
    id uuid not null,
    received_at timestamp with time zone not null,
    shipment_number character varying(10) not null,
    provider_name text not null,

    constraint pk_raw_material_batches
        primary key (id),

    constraint uq_raw_material_batches_shipment_number
        unique (shipment_number)
);

create table public.raw_material_bales (
    id uuid not null,
    raw_material_batch_id uuid not null,
    bale_number character varying(10) not null,
    material_type character varying(20) not null,
    dtex numeric not null,
    gross_weight_kg numeric not null,
    container_weight_kg numeric not null,
    status character varying(40) not null,

    constraint pk_raw_material_bales
        primary key (id),

    constraint fk_raw_material_bales_raw_material_batch_id
        foreign key (raw_material_batch_id)
        references public.raw_material_batches(id)
        on delete restrict,

    constraint uq_raw_material_bales_raw_material_batch_bale_number
        unique (raw_material_batch_id, bale_number),

    constraint ck_raw_material_bales_status
        check (status in ('in_warehouse', 'delivered'))
);

create index ix_raw_material_bales_raw_material_batch_id
    on public.raw_material_bales (raw_material_batch_id);

alter table public.raw_material_batches
    enable row level security;

alter table public.raw_material_bales
    enable row level security;

revoke all privileges
    on public.raw_material_batches, public.raw_material_bales
    from anon, authenticated, service_role;
