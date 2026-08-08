-- Reusable role-preset templates. Derived roles retain copied permissions only.
create table public.access_role_presets (
    preset_id uuid not null default gen_random_uuid(), preset_code varchar(80) not null,
    preset_name varchar(200) not null, description text, is_active boolean not null default true,
    version bigint not null default 1, created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
    constraint pk_access_role_presets primary key (preset_id),
    constraint uq_access_role_presets_preset_code unique (preset_code),
    constraint ck_access_role_presets_preset_code check (preset_code = btrim(preset_code) and preset_code <> ''),
    constraint ck_access_role_presets_version check (version >= 1)
);
create table public.access_role_preset_permissions (
    preset_permission_id uuid not null default gen_random_uuid(), preset_id uuid not null, scope_id uuid not null,
    action varchar(24) not null, created_by_user_id uuid not null, created_at timestamptz not null default now(),
    constraint pk_access_role_preset_permissions primary key (preset_permission_id),
    constraint fk_access_preset_permissions_preset foreign key (preset_id) references public.access_role_presets (preset_id) on delete restrict,
    constraint fk_access_preset_permissions_scope foreign key (scope_id) references public.access_scopes (scope_id) on delete restrict,
    constraint fk_access_preset_permissions_created_by foreign key (created_by_user_id) references public.access_users (user_id) on delete restrict,
    constraint uq_access_role_preset_permissions_triple unique (preset_id, scope_id, action),
    constraint ck_access_role_preset_permissions_action check (action in ('read', 'write', 'edit', 'edit_outside_window', 'manage_access'))
);
alter table public.access_role_presets enable row level security;
alter table public.access_role_preset_permissions enable row level security;
revoke all privileges on table public.access_role_presets, public.access_role_preset_permissions from anon, authenticated, service_role;
