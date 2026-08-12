import { httpJson } from '@/api/httpClient'
import { isApiError } from '@/api/httpError'

export type MutationRecovery = 'reload' | 'last-administrator' | 'clear' | 'preserve'

export class MutationGate {
  private pending = new Set<string>()
  private preview: { fingerprint: string; version: number } | null = null

  tryStart(fingerprint: string) { if (this.pending.has(fingerprint)) return false; this.pending.add(fingerprint); return true }
  finish(fingerprint: string) { this.pending.delete(fingerprint) }
  setPreview(fingerprint: string, version: number) { this.preview = { fingerprint, version } }
  invalidatePreview() { this.preview = null }
  canConfirm(fingerprint: string, version: number) { return this.preview?.fingerprint === fingerprint && this.preview.version === version }
  static recovery(code?: string): MutationRecovery {
    if (code === 'access_version_conflict') return 'reload'
    if (code === 'last_system_administrator_required') return 'last-administrator'
    if (code === 'access_denied' || code === 'authentication_required') return 'clear'
    return 'preserve'
  }
}

export async function mutate<T>(gate: MutationGate, fingerprint: string, path: string, method: 'PUT' | 'PATCH', body: unknown) {
  if (!gate.tryStart(fingerprint)) return { recovery: 'preserve' as const }
  try {
    const result = await httpJson<T>(path, { method, body, recoverAccessDenied: true })
    gate.invalidatePreview()
    return { result, recovery: 'preserve' as const }
  } catch (error) {
    const recovery = MutationGate.recovery(isApiError(error) ? error.code : undefined)
    if (recovery !== 'preserve') gate.invalidatePreview()
    return { recovery }
  } finally { gate.finish(fingerprint) }
}
