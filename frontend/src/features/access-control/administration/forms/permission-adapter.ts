export type PermissionDraft = Readonly<{ action: string; scopeCode: string }>
export type RegisteredScope = Readonly<{ scopeId: string; scopeCode: string; isActive: boolean }>
export type PermissionInput = Readonly<{ action: string; scope_id: string }>

export function toPermissionInputs(drafts: readonly PermissionDraft[], scopes: readonly RegisteredScope[]): PermissionInput[] {
  const scopeIds = new Map(scopes.map((scope) => [scope.scopeCode, scope.scopeId]))
  return drafts.flatMap(({ action, scopeCode }) => {
    const scopeId = scopeIds.get(scopeCode)
    return action.trim() && scopeId ? [{ action: action.trim(), scope_id: scopeId }] : []
  })
}
