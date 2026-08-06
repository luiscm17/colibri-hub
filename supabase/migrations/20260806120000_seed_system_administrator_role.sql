-- Seed the system_administrator role and ensure access_control scope exists.
-- Required before bootstrap CLI can create the initial administrator.

-- 1. Insert the system_administrator role (is_system_administrator = true).
-- The unique index uq_access_roles_single_sysadmin guarantees at most one.
insert into public.access_roles (role_code, role_name, description, is_system_administrator, is_active)
values (
    'system_administrator',
    'System Administrator',
    'Full system access. Bypasses scope-level permission checks.',
    true,
    true
)
on conflict (role_code) do nothing;

-- 2. Ensure access_control scope is registered (from the definition catalog).
-- The scope definition already exists from the seed migration; this creates
-- the active scope row so that authorize_action can resolve it.
insert into public.access_scopes (definition_key, scope_code, scope_name, owning_context, description, is_active)
select
    sd.definition_key,
    sd.scope_code,
    sd.scope_name,
    sd.owning_context,
    sd.description,
    true
from public.access_scope_definitions sd
where sd.definition_key = 'access_control'
on conflict (definition_key) do nothing;
