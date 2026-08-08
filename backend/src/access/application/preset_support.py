"""Shared validation and mapping for role-preset use cases."""
from access.application.results import PermissionResult, RolePresetResult
from access.domain.actions import PRIVILEGED_ACTIONS, Action, Permission
from access.domain.errors import AccessScopeNotFound, DuplicateRolePermission, InactiveAccessScope, InvalidAccessAction, PrivilegedActionRequiresSystemAdministrator, UnsupportedActionForScope

def validate_permissions(inputs, scopes, definitions) -> set[Permission]:
    result, seen = set(), set()
    for item in inputs:
        try: action = Action(item.action)
        except ValueError: raise InvalidAccessAction()
        if action in PRIVILEGED_ACTIONS: raise PrivilegedActionRequiresSystemAdministrator()
        scope = scopes.find_by_id(item.scope_id)
        if scope is None: raise AccessScopeNotFound()
        if not scope.is_active: raise InactiveAccessScope()
        definition = definitions.get(scope.definition_key)
        if definition and action not in definition.supported_actions: raise UnsupportedActionForScope()
        if (action, scope.scope_id) in seen: raise DuplicateRolePermission()
        seen.add((action, scope.scope_id)); result.add(Permission(action, scope.scope_code))
    return result

def result(preset) -> RolePresetResult:
    return RolePresetResult(preset.preset_id, preset.preset_code, preset.preset_name, preset.description, preset.is_active, preset.version, [PermissionResult(str(p.action), p.scope_code) for p in sorted(preset.permissions, key=lambda p: (p.action, p.scope_code))])
