import { SensitiveMutationGate, normalizedRoleIds } from './sensitive-mutation-gate'

export type Subject = { subjectId: string; subjectVersion: number; authorityGeneration: string }
type Request = { path: string; method: 'POST' | 'PUT'; body: Record<string, unknown> }
type Preview = { subjectVersion: number; affectedUserCount: number }

export class UserRoleReplacementGate {
  private readonly gate: SensitiveMutationGate<string[]>
  private readonly subject: Subject

  constructor(subject: Subject, currentRoleIds: readonly string[]) { this.subject = subject; this.gate = new SensitiveMutationGate('user-role-replacement', subject, [...currentRoleIds], normalizedRoleIds) }

  previewRequest(roleIds: readonly string[], reason = ''): Request | null {
    const pending = this.gate.beginPreview([...roleIds], reason)
    return pending ? { path: `/access/users/${this.subject.subjectId}/roles/preview`, method: 'POST', body: { role_ids: normalizedRoleIds(roleIds) } } : null
  }

  acceptPreview(preview: Preview, roleIds: readonly string[], generation: number, reason = ''): boolean {
    return this.gate.acceptPreview(preview, [...roleIds], reason, generation)
  }

  applyRequest(): Request | null {
    const accepted = this.gate.beginApply()
    return accepted ? { path: `/access/users/${this.subject.subjectId}/roles`, method: 'PUT', body: { role_ids: accepted.draft, expected_version: accepted.version, reason: accepted.reason } } : null
  }

  invalidateFor(subject: Subject): void {
    this.gate.invalidateFor(subject)
  }

  invalidate(): void { this.gate.invalidate() }

  currentRequestGeneration(): number { return this.gate.currentRequestGeneration() }
  previewSignal(): AbortSignal | undefined { return this.gate.previewSignal() }
  confirm(): boolean { return this.gate.confirm() }
}
