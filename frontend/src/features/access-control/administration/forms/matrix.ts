export type PermissionPair = Readonly<{ action: string; scopeCode: string }>

export type RolePermissionSource = Readonly<{
  roleId: string
  isActive: boolean
  permissions: readonly PermissionPair[]
}>

export type PermissionScope = Readonly<{
  scopeId: string
  scopeCode: string
  isActive: boolean
  supportedActions: readonly string[]
}>

export function activeRoleIds(roles: readonly RolePermissionSource[]): string[] {
  return roles.filter((role) => role.isActive).map((role) => role.roleId)
}

export function effectivePermissions(roles: readonly RolePermissionSource[]): PermissionPair[] {
  const pairs = new Map<string, PermissionPair>()
  for (const role of roles) {
    if (!role.isActive) continue
    for (const permission of role.permissions) pairs.set(permissionKey(permission), permission)
  }
  return [...pairs.values()].sort(comparePermissions)
}

export function availablePermissionPairs(scopes: readonly PermissionScope[]): PermissionPair[] {
  return scopes.flatMap((scope) => scope.isActive
    ? scope.supportedActions.map((action) => ({ action, scopeCode: scope.scopeCode }))
    : []).sort(comparePermissions)
}

export function isSelectablePermission(permission: PermissionPair, scopes: readonly PermissionScope[]): boolean {
  return availablePermissionPairs(scopes).some((candidate) => permissionKey(candidate) === permissionKey(permission))
}

export function permissionReferenceState(
  permission: PermissionPair,
  scopes: readonly PermissionScope[],
): 'selectable' | 'inactive' | 'unsupported' {
  const scope = scopes.find((candidate) => candidate.scopeCode === permission.scopeCode)
  if (!scope || !scope.supportedActions.includes(permission.action)) return 'unsupported'
  return scope.isActive ? 'selectable' : 'inactive'
}

function permissionKey(permission: PermissionPair): string {
  return `${permission.action}\u0000${permission.scopeCode}`
}

function comparePermissions(left: PermissionPair, right: PermissionPair): number {
  return permissionKey(left).localeCompare(permissionKey(right))
}
