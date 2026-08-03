create table public.access_bootstrap_lock (
    id smallint not null constraint pk_access_bootstrap_lock primary key,
    constraint ck_access_bootstrap_lock_singleton check (id = 1)
);
insert into public.access_bootstrap_lock (id) values (1);

create table public.access_profiles (
    id uuid not null default gen_random_uuid(), subject varchar(255) not null,
    code varchar(80) not null, is_active boolean not null default true,
    constraint pk_access_profiles primary key (id),
    constraint uq_access_profiles_subject unique (subject),
    constraint uq_access_profiles_code unique (code),
    constraint ck_access_profiles_subject check (btrim(subject) <> ''),
    constraint ck_access_profiles_code check (btrim(code) <> '')
);
create table public.access_roles (
    id uuid not null default gen_random_uuid(), code varchar(80) not null,
    is_active boolean not null default true,
    constraint pk_access_roles primary key (id),
    constraint uq_access_roles_code unique (code),
    constraint ck_access_roles_code check (btrim(code) <> '')
);
create table public.access_scopes (
    id uuid not null default gen_random_uuid(), code varchar(160) not null,
    is_active boolean not null default true,
    constraint pk_access_scopes primary key (id),
    constraint uq_access_scopes_code unique (code),
    constraint ck_access_scopes_code check (code = btrim(code) and code <> '')
);
create table public.access_role_permissions (
    id uuid not null default gen_random_uuid(), role_id uuid not null, action varchar(16) not null,
    scope_id uuid not null, constraint pk_access_role_permissions primary key (id),
    constraint fk_access_role_permissions_role foreign key (role_id) references public.access_roles(id) on delete restrict,
    constraint fk_access_role_permissions_scope foreign key (scope_id) references public.access_scopes(id) on delete restrict,
    constraint uq_access_role_permissions_role_action_scope unique (role_id, action, scope_id),
    constraint ck_access_role_permissions_action check (action in ('read', 'write'))
);
create table public.access_role_assignments (
    id uuid not null default gen_random_uuid(), profile_id uuid not null, role_id uuid not null,
    is_active boolean not null default true, is_current boolean not null default true,
    constraint pk_access_role_assignments primary key (id),
    constraint fk_access_role_assignments_profile foreign key (profile_id) references public.access_profiles(id) on delete restrict,
    constraint fk_access_role_assignments_role foreign key (role_id) references public.access_roles(id) on delete restrict
);
create unique index uq_access_role_assignments_current_pair on public.access_role_assignments(profile_id, role_id) where is_current;
create table public.access_change_audit (
    id uuid not null default gen_random_uuid(), actor_profile_id uuid null, affected_profile_id uuid not null,
    change_kind varchar(80) not null, reason varchar(500) null, operation_id varchar(120) not null,
    before jsonb not null, after jsonb not null, occurred_at timestamptz not null default now(),
    constraint pk_access_change_audit primary key (id),
    constraint fk_access_change_audit_actor foreign key (actor_profile_id) references public.access_profiles(id) on delete restrict,
    constraint fk_access_change_audit_affected foreign key (affected_profile_id) references public.access_profiles(id) on delete restrict,
    constraint uq_access_change_audit_operation unique (operation_id),
    constraint ck_access_change_audit_actor check ((change_kind = 'initial_bootstrap' and actor_profile_id is null and reason is null) or (change_kind <> 'initial_bootstrap' and actor_profile_id is not null and reason is not null)),
    constraint ck_access_change_audit_redacted check (before ? 'redacted' or change_kind = 'initial_bootstrap')
);

create index ix_access_profiles_active_subject on public.access_profiles(subject) where is_active;
create index ix_access_role_assignments_current on public.access_role_assignments(profile_id, role_id) where is_current;
create index ix_access_operational_administrators on public.access_role_assignments(role_id, profile_id) where is_current and is_active;

create function public.access_reject_profile_identity_change() returns trigger language plpgsql as $$
begin if new.subject is distinct from old.subject or new.code is distinct from old.code then raise exception 'Access profile identity is immutable'; end if; return new; end $$;
create function public.access_reject_scope_identity_change() returns trigger language plpgsql as $$
begin if new.code is distinct from old.code then raise exception 'Access scope identity is immutable'; end if; return new; end $$;
create trigger trg_access_profiles_identity_immutable before update on public.access_profiles for each row execute function public.access_reject_profile_identity_change();
create trigger trg_access_scopes_identity_immutable before update on public.access_scopes for each row execute function public.access_reject_scope_identity_change();
create function public.access_reject_audit_mutation() returns trigger language plpgsql as $$ begin raise exception 'Access audit is append-only'; end $$;
create trigger trg_access_change_audit_immutable before update or delete on public.access_change_audit for each row execute function public.access_reject_audit_mutation();

alter table public.access_bootstrap_lock enable row level security;
alter table public.access_profiles enable row level security;
alter table public.access_roles enable row level security;
alter table public.access_scopes enable row level security;
alter table public.access_role_permissions enable row level security;
alter table public.access_role_assignments enable row level security;
alter table public.access_change_audit enable row level security;
revoke all privileges on table public.access_bootstrap_lock, public.access_profiles, public.access_roles, public.access_scopes, public.access_role_permissions, public.access_role_assignments, public.access_change_audit from anon, authenticated, service_role;
revoke execute on function public.access_reject_profile_identity_change(), public.access_reject_scope_identity_change(), public.access_reject_audit_mutation() from public, anon, authenticated, service_role;
