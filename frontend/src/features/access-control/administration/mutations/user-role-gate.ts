export type Subject = { subjectId: string; subjectVersion: number; authorityGeneration: string }
type Request = { path: string; method: 'POST' | 'PUT'; body: Record<string, unknown> }
type Preview = { subjectVersion: number; affectedUserCount: number }

const normalized = (roleIds: readonly string[]) => [...new Set(roleIds.map((roleId) => roleId.trim()).filter(Boolean))].sort()
const keyFor = (subject: Subject, roleIds: readonly string[]) => JSON.stringify([subject.subjectId, subject.subjectVersion, subject.authorityGeneration, normalized(roleIds)])

export class UserRoleReplacementGate {
  private pending: { key: string; generation: number } | null = null
  private requestGeneration = 0
  private ready: { key: string; roleIds: string[]; version: number } | null = null
  private applied = false
  private subject: Subject
  private currentRoleIds: readonly string[]

  constructor(subject: Subject, currentRoleIds: readonly string[]) { this.subject = subject; this.currentRoleIds = currentRoleIds }

  previewRequest(roleIds: readonly string[]): Request | null {
    const next = normalized(roleIds)
    if (JSON.stringify(next) === JSON.stringify(normalized(this.currentRoleIds))) return null
    this.ready = null
    this.pending = { key: keyFor(this.subject, next), generation: ++this.requestGeneration }
    return { path: `/access/users/${this.subject.subjectId}/roles/preview`, method: 'POST', body: { role_ids: next } }
  }

  acceptPreview(preview: Preview, roleIds: readonly string[], generation: number): boolean {
    const key = keyFor(this.subject, roleIds)
    if (this.pending?.key !== key || this.pending.generation !== generation || preview.subjectVersion !== this.subject.subjectVersion) return false
    this.pending = null
    this.ready = { key, roleIds: normalized(roleIds), version: preview.subjectVersion }
    return true
  }

  applyRequest(reason = ''): Request | null {
    if (!this.ready || this.applied) return null
    this.applied = true
    return { path: `/access/users/${this.subject.subjectId}/roles`, method: 'PUT', body: { role_ids: this.ready.roleIds, expected_version: this.ready.version, reason } }
  }

  invalidateFor(subject: Subject): void {
    if (keyFor(this.subject, []) !== keyFor(subject, [])) this.invalidate()
  }

  invalidate(): void { this.pending = null; this.ready = null; this.applied = false }

  currentRequestGeneration(): number { return this.pending?.generation ?? 0 }
}
