-- Access Control Administration: clean-break migration
-- Drops spine-era tables and recreates with full spec schema (§11).
-- Pre-launch: no production data to preserve.

-- 1. Drop spine tables, triggers, and functions
drop trigger if exists trg_access_change_audit_immutable on public.access_change_audit;
drop trigger if exists trg_access_scopes_identity_immutable on public.access_scopes;
drop trigger if exists trg_access_profiles_identity_immutable on public.access_profiles;
drop function if exists public.access_reject_audit_mutation();
drop function if exists public.access_reject_scope_identity_change();
drop function if exists public.access_reject_profile_identity_change();
drop table if exists public.access_change_audit;
drop table if exists public.access_role_assignments;
drop table if exists public.access_role_permissions;
drop table if exists public.access_scopes;
drop table if exists public.access_roles;
drop table if exists public.access_profiles;
drop table if exists public.access_bootstrap_lock;

-- 2. Create scope definition catalog (immutable, product-versioned)
create table public.access_scope_definitions (
    definition_key varchar(160) not null,
    scope_code varchar(160) not null,
    scope_name varchar(200) not null,
    owning_context varchar(200) not null,
    description text not null,
    supported_actions text[] not null,
    constraint pk_access_scope_definitions primary key (definition_key),
    constraint uq_access_scope_definitions_code unique (scope_code),
    constraint ck_access_scope_definitions_key check (btrim(definition_key) <> ''),
    constraint ck_access_scope_definitions_code check (btrim(scope_code) <> '')
);

-- 3. Create access_users (was access_profiles)
create table public.access_users (
    user_id uuid not null default gen_random_uuid(),
    identity_subject text not null,
    user_code varchar(40) not null,
    display_name text not null,
    is_active boolean not null default true,
    authorization_version bigint not null default 1,
    version bigint not null default 1,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint pk_access_users primary key (user_id),
    constraint uq_access_users_identity_subject unique (identity_subject),
    constraint uq_access_users_user_code unique (user_code),
    constraint ck_access_users_identity_subject check (btrim(identity_subject) <> ''),
    constraint ck_access_users_user_code check (btrim(user_code) <> ''),
    constraint ck_access_users_version check (version >= 1),
    constraint ck_access_users_authorization_version check (authorization_version >= 1)
);

-- 4. Create access_roles
create table public.access_roles (
    role_id uuid not null default gen_random_uuid(),
    role_code varchar(80) not null,
    role_name varchar(200) not null,
    description text,
    is_system_administrator boolean not null default false,
    is_active boolean not null default true,
    version bigint not null default 1,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint pk_access_roles primary key (role_id),
    constraint uq_access_roles_role_code unique (role_code),
    constraint ck_access_roles_role_code check (btrim(role_code) <> ''),
    constraint ck_access_roles_version check (version >= 1)
);
-- At most one system administrator role
create unique index uq_access_roles_single_sysadmin
    on public.access_roles (is_system_administrator) where is_system_administrator;

-- 5. Create access_scopes (references definition catalog)
create table public.access_scopes (
    scope_id uuid not null default gen_random_uuid(),
    definition_key varchar(160) not null,
    scope_code varchar(160) not null,
    scope_name varchar(200) not null,
    owning_context varchar(200) not null,
    description text not null,
    is_active boolean not null default true,
    version bigint not null default 1,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint pk_access_scopes primary key (scope_id),
    constraint uq_access_scopes_definition_key unique (definition_key),
    constraint uq_access_scopes_scope_code unique (scope_code),
    constraint fk_access_scopes_definition foreign key (definition_key)
        references public.access_scope_definitions (definition_key) on delete restrict,
    constraint ck_access_scopes_scope_code check (scope_code = btrim(scope_code) and scope_code <> ''),
    constraint ck_access_scopes_version check (version >= 1)
);

-- 6. Create access_role_permissions
create table public.access_role_permissions (
    role_permission_id uuid not null default gen_random_uuid(),
    role_id uuid not null,
    scope_id uuid not null,
    action varchar(24) not null,
    created_by_user_id uuid not null,
    created_at timestamptz not null default now(),
    constraint pk_access_role_permissions primary key (role_permission_id),
    constraint fk_access_role_permissions_role foreign key (role_id)
        references public.access_roles (role_id) on delete restrict,
    constraint fk_access_role_permissions_scope foreign key (scope_id)
        references public.access_scopes (scope_id) on delete restrict,
    constraint fk_access_role_permissions_created_by foreign key (created_by_user_id)
        references public.access_users (user_id) on delete restrict,
    constraint uq_access_role_permissions_triple unique (role_id, scope_id, action),
    constraint ck_access_role_permissions_action check (
        action in ('read', 'write', 'edit', 'edit_outside_window', 'manage_access')
    )
);

-- 7. Create access_user_role_assignments
create table public.access_user_role_assignments (
    assignment_id uuid not null default gen_random_uuid(),
    user_id uuid not null,
    role_id uuid not null,
    assigned_by_user_id uuid not null,
    assigned_at timestamptz not null default now(),
    revoked_by_user_id uuid,
    revoked_at timestamptz,
    revoke_reason text,
    constraint pk_access_user_role_assignments primary key (assignment_id),
    constraint fk_access_assignments_user foreign key (user_id)
        references public.access_users (user_id) on delete restrict,
    constraint fk_access_assignments_role foreign key (role_id)
        references public.access_roles (role_id) on delete restrict,
    constraint fk_access_assignments_assigned_by foreign key (assigned_by_user_id)
        references public.access_users (user_id) on delete restrict,
    constraint fk_access_assignments_revoked_by foreign key (revoked_by_user_id)
        references public.access_users (user_id) on delete restrict,
    constraint ck_access_assignments_revocation check (
        (revoked_at is null and revoked_by_user_id is null and revoke_reason is null) or
        (revoked_at is not null and revoked_by_user_id is not null and revoke_reason is not null)
    )
);
-- Only one current (non-revoked) assignment per user+role
create unique index uq_access_assignments_current
    on public.access_user_role_assignments (user_id, role_id) where revoked_at is null;

-- 8. Create access_change_audits
create table public.access_change_audits (
    access_change_audit_id uuid not null default gen_random_uuid(),
    operation_id uuid not null,
    change_kind varchar(80) not null,
    subject_type varchar(40) not null,
    subject_id uuid not null,
    performed_by_user_id uuid,
    reason text,
    before_values jsonb not null default '{}'::jsonb,
    after_values jsonb not null default '{}'::jsonb,
    occurred_at timestamptz not null default now(),
    constraint pk_access_change_audits primary key (access_change_audit_id),
    constraint fk_access_change_audits_performer foreign key (performed_by_user_id)
        references public.access_users (user_id) on delete restrict,
    constraint ck_access_change_audits_actor check (
        (change_kind = 'initial_bootstrap' and performed_by_user_id is null) or
        (change_kind <> 'initial_bootstrap' and performed_by_user_id is not null)
    )
);
create index ix_access_change_audits_subject on public.access_change_audits (subject_type, subject_id);
create index ix_access_change_audits_recent on public.access_change_audits (occurred_at desc);

-- 9. Immutability triggers
create function public.access_reject_user_identity_change() returns trigger language plpgsql as $$
begin
    if new.identity_subject is distinct from old.identity_subject
       or new.user_code is distinct from old.user_code then
        raise exception 'Access user identity is immutable';
    end if;
    return new;
end $$;

create function public.access_reject_scope_identity_change() returns trigger language plpgsql as $$
begin
    if new.definition_key is distinct from old.definition_key
       or new.scope_code is distinct from old.scope_code then
        raise exception 'Access scope identity is immutable';
    end if;
    return new;
end $$;

create function public.access_reject_audit_mutation() returns trigger language plpgsql as $$
begin
    raise exception 'Access audit is append-only';
end $$;

create function public.access_reject_definition_mutation() returns trigger language plpgsql as $$
begin
    raise exception 'Scope definitions are immutable';
end $$;

create trigger trg_access_users_identity_immutable
    before update on public.access_users
    for each row execute function public.access_reject_user_identity_change();

create trigger trg_access_scopes_identity_immutable
    before update on public.access_scopes
    for each row execute function public.access_reject_scope_identity_change();

create trigger trg_access_change_audits_immutable
    before update or delete on public.access_change_audits
    for each row execute function public.access_reject_audit_mutation();

create trigger trg_access_scope_definitions_immutable
    before update or delete on public.access_scope_definitions
    for each row execute function public.access_reject_definition_mutation();

-- 10. RLS and privilege revocation
alter table public.access_scope_definitions enable row level security;
alter table public.access_users enable row level security;
alter table public.access_roles enable row level security;
alter table public.access_scopes enable row level security;
alter table public.access_role_permissions enable row level security;
alter table public.access_user_role_assignments enable row level security;
alter table public.access_change_audits enable row level security;

revoke all privileges on table
    public.access_scope_definitions,
    public.access_users,
    public.access_roles,
    public.access_scopes,
    public.access_role_permissions,
    public.access_user_role_assignments,
    public.access_change_audits
from anon, authenticated, service_role;

revoke execute on function
    public.access_reject_user_identity_change(),
    public.access_reject_scope_identity_change(),
    public.access_reject_audit_mutation(),
    public.access_reject_definition_mutation()
from public, anon, authenticated, service_role;
