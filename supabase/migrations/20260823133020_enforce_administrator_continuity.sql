-- Administrator continuity is disabled until operations establishes and records
-- two distinct operational System Administrators through controlled initialization
-- or the external recovery runbook.
create table public.access_administrator_continuity (
    id smallint not null,
    enforcement_enabled boolean not null default false,
    enforcement_enabled_at timestamptz,
    enforcement_evidence text,
    constraint pk_access_administrator_continuity primary key (id),
    constraint ck_access_administrator_continuity_singleton check (id = 1),
    constraint ck_access_administrator_continuity_enablement_evidence check (
        (not enforcement_enabled and enforcement_enabled_at is null
            and enforcement_evidence is null)
        or (
            enforcement_enabled
            and enforcement_enabled_at is not null
            and btrim(enforcement_evidence) <> ''
        )
    )
);

insert into public.access_administrator_continuity (id) values (1);

create index ix_authentication_accounts_active_identity_subject
    on public.authentication_accounts (identity_subject)
    where status = 'active';

create index ix_access_users_active_identity_subject
    on public.access_users (identity_subject)
    where is_active;

create index ix_access_assignments_current_role_user
    on public.access_user_role_assignments (role_id, user_id)
    where revoked_at is null;

create view public.access_operational_administrators_preflight
with (security_invoker = true) as
select distinct au.identity_subject
from public.authentication_accounts aa
join public.access_users au
    on au.identity_subject = aa.identity_subject::text
join public.access_user_role_assignments aura
    on aura.user_id = au.user_id and aura.revoked_at is null
join public.access_roles ar
    on ar.role_id = aura.role_id and ar.is_system_administrator
where aa.status = 'active' and au.is_active;

create function public.access_guard_administrator_continuity_enablement()
returns trigger
language plpgsql
as $$
declare
    operational_administrator_count integer;
begin
    if old.enforcement_enabled then
        if new.enforcement_enabled is distinct from old.enforcement_enabled
           or new.enforcement_evidence is distinct from old.enforcement_evidence
           or new.enforcement_enabled_at is distinct from old.enforcement_enabled_at then
            raise exception 'Administrator continuity enforcement evidence is immutable';
        end if;
        return new;
    end if;

    if new.enforcement_enabled then
        select count(*) into operational_administrator_count
        from public.access_operational_administrators_preflight;

        if operational_administrator_count < 2 then
            raise exception
                'Administrator continuity requires two operational System Administrators before enforcement can be enabled';
        end if;

        new.enforcement_enabled_at := now();
    end if;

    return new;
end;
$$;

create trigger trg_access_administrator_continuity_enablement_guard
    before update on public.access_administrator_continuity
    for each row
    execute function public.access_guard_administrator_continuity_enablement();

alter table public.access_administrator_continuity enable row level security;

revoke all privileges on table public.access_administrator_continuity
    from anon, authenticated, service_role;
revoke all privileges on table public.access_operational_administrators_preflight
    from anon, authenticated, service_role;
revoke execute on function public.access_guard_administrator_continuity_enablement()
    from public, anon, authenticated, service_role;
