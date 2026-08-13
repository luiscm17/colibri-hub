export type RoleSubject = { subjectId: string; subjectVersion: number; authorityGeneration: string }
export type PermissionInput = { action: string; scopeId: string }
type Request = { path: string; method: 'POST' | 'PUT'; body: Record<string, unknown> }
type Preview = { subjectVersion: number; affectedUserCount: number }

const normalized = (permissions: readonly PermissionInput[]) => [...new Map(permissions.map((permission) => [`${permission.action.trim()}\0${permission.scopeId.trim()}`, { action: permission.action.trim(), scopeId: permission.scopeId.trim() }])).values()].filter((permission) => permission.action && permission.scopeId).sort((left, right) => `${left.action}\0${left.scopeId}`.localeCompare(`${right.action}\0${right.scopeId}`))
const keyFor = (subject: RoleSubject, permissions: readonly PermissionInput[]) => JSON.stringify([subject.subjectId, subject.subjectVersion, subject.authorityGeneration, normalized(permissions)])
const wirePermissions = (permissions: readonly PermissionInput[]) => permissions.map(({ action, scopeId }) => ({ action, scope_id: scopeId }))

export class SharedRolePermissionGate {
  private pending: { key: string; generation: number } | null = null
  private requestGeneration = 0
  private ready: { permissions: PermissionInput[]; version: number } | null = null
  private applied = false
  private readonly subject: RoleSubject
  private readonly currentPermissions: readonly PermissionInput[]
  private readonly metadata: { roleName: string; description: string | null }

  constructor(subject: RoleSubject, currentPermissions: readonly PermissionInput[], metadata: { roleName: string; description: string | null }) {
    this.subject = subject
    this.currentPermissions = currentPermissions
    this.metadata = metadata
  }

  previewRequest(permissions: readonly PermissionInput[]): Request | null {
    const next = normalized(permissions)
    if (JSON.stringify(next) === JSON.stringify(normalized(this.currentPermissions))) return null
    if (this.pending) return null
    this.ready = null
    this.pending = { key: keyFor(this.subject, next), generation: ++this.requestGeneration }
    return { path: `/access/roles/${this.subject.subjectId}/preview`, method: 'POST', body: { permissions: wirePermissions(next) } }
  }

  acceptPreview(preview: Preview, permissions: readonly PermissionInput[], generation: number): boolean {
    if (this.pending?.key !== keyFor(this.subject, permissions) || this.pending.generation !== generation || preview.subjectVersion !== this.subject.subjectVersion) return false
    this.pending = null
    this.ready = { permissions: normalized(permissions), version: preview.subjectVersion }
    return true
  }

  applyRequest(reason = ''): Request | null {
    if (!this.ready || this.applied) return null
    this.applied = true
    return { path: `/access/roles/${this.subject.subjectId}`, method: 'PUT', body: { role_name: this.metadata.roleName, description: this.metadata.description, permissions: wirePermissions(this.ready.permissions), expected_version: this.ready.version, reason } }
  }

  invalidate(): void { this.pending = null; this.ready = null; this.applied = false }
  invalidateFor(subject: RoleSubject): void { if (keyFor(this.subject, []) !== keyFor(subject, [])) this.invalidate() }
  currentRequestGeneration(): number { return this.pending?.generation ?? 0 }
}
