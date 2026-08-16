export type SensitiveSubject = { subjectId: string; subjectVersion: number; authorityGeneration: string }

type Preview = { subjectVersion: number }
type Pending = { fingerprint: string; generation: number; controller: AbortController }
type Ready<T> = { fingerprint: string; draft: T; version: number; reason: string }
export type GateOutcome = '401' | '403' | 'access_version_conflict' | 'last_system_administrator_required' | 'failure'

export const normalizedRoleIds = (roleIds: readonly string[]) => [...new Set(roleIds.map((roleId) => roleId.trim()).filter(Boolean))].sort()

export class SensitiveMutationGate<T> {
  private pending: Pending | null = null
  private ready: Ready<T> | null = null
  private generation = 0
  private applying = false
  private confirmed = false
  private readonly operation: string
  private readonly subject: SensitiveSubject
  private readonly baseline: T
  private readonly normalize: (draft: T) => T

  constructor(operation: string, subject: SensitiveSubject, baseline: T, normalize: (draft: T) => T = (draft) => draft) {
    this.operation = operation
    this.subject = subject
    this.baseline = baseline
    this.normalize = normalize
  }

  beginPreview(draft: T, reason: string): { generation: number; signal: AbortSignal } | null {
    const normalized = this.normalize(draft)
    if (this.same(normalized, this.normalize(this.baseline)) || this.pending) return null
    this.clearGate()
    const generation = ++this.generation
    const controller = new AbortController()
    this.pending = { fingerprint: this.fingerprint(normalized, reason, generation), generation, controller }
    return { generation, signal: controller.signal }
  }

  acceptPreview(preview: Preview, draft: T, reason: string, generation: number): boolean {
    const normalized = this.normalize(draft)
    const fingerprint = this.fingerprint(normalized, reason, generation)
    if (!this.pending || this.pending.fingerprint !== fingerprint || preview.subjectVersion !== this.subject.subjectVersion || this.pending.controller.signal.aborted) return false
    this.pending = null
    this.ready = { fingerprint, draft: normalized, version: preview.subjectVersion, reason }
    return true
  }

  confirm(): boolean { this.confirmed = Boolean(this.ready) && !this.applying; return this.confirmed }

  beginApply(): { draft: T; version: number; reason: string } | null {
    if (!this.ready || !this.confirmed || this.applying) return null
    this.applying = true
    return { draft: this.ready.draft, version: this.ready.version, reason: this.ready.reason }
  }

  invalidate(): void { this.pending?.controller.abort(); this.clearGate() }
  invalidateForReason(reason: string): void { void reason; this.invalidate() }
  invalidateFor(subject: SensitiveSubject): void { if (JSON.stringify(this.subject) !== JSON.stringify(subject)) this.invalidate() }
  handleOutcome(outcome: GateOutcome): void { void outcome; this.invalidate() }
  hasProtectedState(): boolean { return this.pending !== null || this.ready !== null || this.applying }
  currentRequestGeneration(): number { return this.pending?.generation ?? 0 }
  previewSignal(): AbortSignal | undefined { return this.pending?.controller.signal }

  private clearGate(): void { this.pending = null; this.ready = null; this.applying = false; this.confirmed = false }
  private fingerprint(draft: T, reason: string, generation: number): string { return JSON.stringify([this.operation, this.subject.subjectId, this.subject.subjectVersion, this.subject.authorityGeneration, draft, reason, generation]) }
  private same(left: T, right: T): boolean { return JSON.stringify(left) === JSON.stringify(right) }
}
