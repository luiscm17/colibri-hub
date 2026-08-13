type Definition = Readonly<{ definitionKey: string; isRegistered: boolean }>
type Scope = Readonly<{ scopeId: string; version: number }>

export function unregisteredDefinitions(definitions: readonly Definition[]): Definition[] {
  return definitions.filter((definition) => !definition.isRegistered)
}

export function scopeRegistrationRequest(definitionKey: string) {
  return { path: '/access/scopes', method: 'POST' as const, body: { definition_key: definitionKey, reason: '' } }
}

export function scopeStatusRequest(scope: Scope, isActive: boolean) {
  return { path: `/access/scopes/${scope.scopeId}/status`, method: 'PATCH' as const, body: { is_active: isActive, expected_version: scope.version, reason: '' } }
}

export function auditValues(entry: Record<string, unknown>): string[] {
  return ['performed_by_user_id', 'occurred_at', 'reason', 'subject_id', 'change_kind'].map((key) => typeof entry[key] === 'string' ? entry[key] : '')
}
