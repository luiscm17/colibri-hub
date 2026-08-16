import { SensitiveMutationGate, type SensitiveSubject } from './sensitive-mutation-gate'

export type PermissionInput = { action: string; scopeId: string }
export type SharedRoleDraft = { roleName: string; description: string | null; permissions: readonly PermissionInput[] }

type Preview = { subjectVersion: number }
type Request = { path: string; method: 'POST' | 'PUT'; body: Record<string, unknown>; signal?: AbortSignal }

const normalizePermissions = (permissions: readonly PermissionInput[]) => [...new Map(permissions.map((permission) => [`${permission.action.trim()}\0${permission.scopeId.trim()}`, { action: permission.action.trim(), scopeId: permission.scopeId.trim() }])).values()].filter((permission) => permission.action && permission.scopeId).sort((left, right) => `${left.action}\0${left.scopeId}`.localeCompare(`${right.action}\0${right.scopeId}`))
const normalizeDraft = (draft: SharedRoleDraft): SharedRoleDraft => ({ roleName: draft.roleName.trim(), description: draft.description?.trim() || null, permissions: normalizePermissions(draft.permissions) })
const wirePermissions = (permissions: readonly PermissionInput[]) => permissions.map(({ action, scopeId }) => ({ action, scope_id: scopeId }))

export class SharedRolePermissionGate {
  private readonly gate: SensitiveMutationGate<SharedRoleDraft>
  private readonly subject: SensitiveSubject

  constructor(subject: SensitiveSubject, baseline: SharedRoleDraft) {
    this.subject = subject
    this.gate = new SensitiveMutationGate('shared-role-update', subject, baseline, normalizeDraft)
  }

  previewRequest(draft: SharedRoleDraft, reason: string): Request | null {
    const pending = this.gate.beginPreview(draft, reason.trim())
    if (!pending) return null
    return { path: `/access/roles/${this.subject.subjectId}/preview`, method: 'POST', body: { permissions: wirePermissions(normalizeDraft(draft).permissions) }, signal: pending.signal }
  }

  acceptPreview(preview: Preview, draft: SharedRoleDraft, reason: string, generation: number): boolean {
    return this.gate.acceptPreview(preview, draft, reason.trim(), generation)
  }

  confirm(): boolean { return this.gate.confirm() }

  applyRequest(): Request | null {
    const ready = this.gate.beginApply()
    if (!ready) return null
    return { path: `/access/roles/${this.subject.subjectId}`, method: 'PUT', body: { role_name: ready.draft.roleName, description: ready.draft.description, permissions: wirePermissions(ready.draft.permissions), expected_version: ready.version, reason: ready.reason } }
  }

  invalidate(): void { this.gate.invalidate() }
  currentRequestGeneration(): number { return this.gate.currentRequestGeneration() }
  handleOutcome(outcome: '401' | '403' | 'access_version_conflict' | 'last_system_administrator_required' | 'failure'): void { this.gate.handleOutcome(outcome) }
}
