-- Authentication tables: application-owned account state and redacted audit.
-- Provider-owned identity, sessions, and credentials remain in auth.users / auth.sessions.

create table public.authentication_accounts (
    authentication_account_id uuid not null default gen_random_uuid(),
    identity_subject uuid not null,
    normalized_email text not null,
    display_name text not null,
    user_code varchar(40) not null,
    status text not null default 'awaiting_password_change',
    version bigint not null default 1,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint pk_authentication_accounts primary key (authentication_account_id),
    constraint uq_authentication_accounts_identity_subject unique (identity_subject),
    constraint uq_authentication_accounts_normalized_email unique (normalized_email),
    constraint uq_authentication_accounts_user_code unique (user_code),
    constraint ck_authentication_accounts_status check (status in ('awaiting_password_change', 'active', 'disabled')),
    constraint ck_authentication_accounts_version check (version >= 1),
    constraint ck_authentication_accounts_email check (normalized_email = lower(btrim(normalized_email)) and normalized_email <> ''),
    constraint ck_authentication_accounts_display_name check (btrim(display_name) <> ''),
    constraint ck_authentication_accounts_user_code check (btrim(user_code) <> '')
);

create index ix_authentication_accounts_active on public.authentication_accounts(identity_subject) where status <> 'disabled';
create index ix_authentication_accounts_email_lookup on public.authentication_accounts(normalized_email);

create table public.authentication_audits (
    authentication_audit_id uuid not null default gen_random_uuid(),
    operation_id uuid not null,
    event_type text not null,
    outcome text not null default 'succeeded',
    actor_identity_subject uuid null,
    affected_account_id uuid null,
    provider_session_id uuid null,
    reason text null,
    details jsonb not null default '{}',
    occurred_at timestamptz not null default now(),
    constraint pk_authentication_audits primary key (authentication_audit_id),
    constraint fk_authentication_audits_affected_account foreign key (affected_account_id) references public.authentication_accounts(authentication_account_id) on delete restrict,
    constraint ck_authentication_audits_outcome check (outcome in ('succeeded', 'failed')),
    constraint ck_authentication_audits_event_type check (event_type in (
        'account_provisioned', 'password_changed', 'password_reset',
        'account_disabled', 'account_enabled', 'logout',
        'initial_bootstrap', 'login_succeeded', 'login_failed'
    ))
);

create index ix_authentication_audits_account on public.authentication_audits(affected_account_id, occurred_at desc);
create index ix_authentication_audits_recent on public.authentication_audits(occurred_at desc);
create index ix_authentication_audits_operation on public.authentication_audits(operation_id);

-- Immutability: audits are append-only (no UPDATE or DELETE)
create function public.authentication_reject_audit_mutation() returns trigger language plpgsql as $$
begin
    raise exception 'Authentication audit is append-only';
end $$;
create trigger trg_authentication_audits_immutable
    before update or delete on public.authentication_audits
    for each row execute function public.authentication_reject_audit_mutation();

-- Immutability: identity_subject and normalized_email cannot change after creation
create function public.authentication_reject_identity_change() returns trigger language plpgsql as $$
begin
    if new.identity_subject is distinct from old.identity_subject
       or new.normalized_email is distinct from old.normalized_email then
        raise exception 'Authentication account identity is immutable';
    end if;
    return new;
end $$;
create trigger trg_authentication_accounts_identity_immutable
    before update on public.authentication_accounts
    for each row execute function public.authentication_reject_identity_change();

-- Row Level Security: enabled, browser roles revoked
alter table public.authentication_accounts enable row level security;
alter table public.authentication_audits enable row level security;

revoke all privileges on table public.authentication_accounts, public.authentication_audits from anon, authenticated, service_role;
revoke execute on function public.authentication_reject_audit_mutation(), public.authentication_reject_identity_change() from public, anon, authenticated, service_role;
