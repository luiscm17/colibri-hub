import { isApiError } from '@/api/httpError'

const ACTIONS = new Set(['read', 'write', 'edit', 'edit_outside_window', 'manage_access'])

type AccessAction = 'read' | 'write' | 'edit' | 'edit_outside_window' | 'manage_access'

export type AccessHandoff =
  | { condition: 'unresolved' | 'password-change-required' | 'ended' }
  | { condition: 'unavailable'; retryable: boolean }
  | { condition: 'eligible'; accountId: string; handoffId: string }

export type AccessRequirement =
  | { action: AccessAction; scope: string }
  | { anyOf: readonly AccessRequirement[] }
  | { allOf: readonly AccessRequirement[] }

export interface AccessSnapshot {
  userId: string
  userCode: string
  displayName: string
  authorizationVersion: number
  allows(requirement: AccessRequirement): boolean
}

export type AccessState =
  | { status: 'waiting-for-authentication' }
  | { status: 'loading' }
  | { status: 'ready'; snapshot: AccessSnapshot }
  | { status: 'blocked'; reason: 'profile_not_found' | 'profile_inactive' }
  | { status: 'unavailable'; retryable: boolean }

export type AccessMeFetcher = (signal: AbortSignal) => Promise<unknown>

type AccessIdentity = Readonly<{ accountId: string; handoffId: string }>
type Permission = Readonly<{ action: AccessAction; scope: string }>

export function createAccessSnapshot(response: unknown): AccessSnapshot | null {
  if (!isRecord(response) || !isNonEmptyString(response.user_id) || !isNonEmptyString(response.user_code) || !isNonEmptyString(response.display_name) || response.is_active !== true || !isRecord(response.authorization)) {
    return null
  }

  const authorization = response.authorization
  if (!isNonNegativeInteger(authorization.version) || typeof authorization.is_global !== 'boolean' || !Array.isArray(authorization.actions) || !Array.isArray(authorization.permissions)) {
    return null
  }

  const permissions = authorization.permissions.flatMap((permission): Permission[] => {
    if (!isRecord(permission) || !isAction(permission.action) || !isNonEmptyString(permission.scope_code)) return []
    return [{ action: permission.action, scope: permission.scope_code }]
  })
  if (permissions.length !== authorization.permissions.length) return null

  const actions = authorization.actions.filter(isAction)
  if (actions.length !== authorization.actions.length) return null
  if (authorization.is_global ? permissions.length > 0 : actions.length > 0) return null

  const allowed = (requirement: AccessRequirement): boolean => {
    if ('anyOf' in requirement) return requirement.anyOf.some(allowed)
    if ('allOf' in requirement) return requirement.allOf.every(allowed)
    if (authorization.is_global) return actions.includes(requirement.action)
    return permissions.some((permission) => permission.action === requirement.action && permission.scope === requirement.scope)
  }

  return {
    userId: response.user_id,
    userCode: response.user_code,
    displayName: response.display_name,
    authorizationVersion: authorization.version,
    allows: allowed,
  }
}

export class AccessController {
  private state: AccessState = { status: 'waiting-for-authentication' }
  private identity: AccessIdentity | null = null
  private generation = 0
  private operation: AbortController | null = null
  private readonly listeners = new Set<(state: AccessState) => void>()

  private readonly getAccess: AccessMeFetcher

  constructor(getAccess: AccessMeFetcher) {
    this.getAccess = getAccess
  }

  getState(): AccessState {
    return this.state
  }

  subscribe(listener: (state: AccessState) => void): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  async acceptHandoff(handoff: AccessHandoff): Promise<void> {
    if (handoff.condition === 'eligible') {
      const identity = { accountId: handoff.accountId, handoffId: handoff.handoffId }
      if (this.isSameIdentity(identity)) return
      this.identity = identity
      await this.load()
      return
    }

    this.identity = null
    this.abortCurrent()
    this.publish(handoff.condition === 'unavailable'
      ? { status: 'unavailable', retryable: handoff.retryable }
      : { status: 'waiting-for-authentication' })
  }

  async refresh(): Promise<void> {
    if (this.identity) await this.load()
  }

  async retry(): Promise<void> {
    if (this.identity && this.state.status === 'unavailable' && this.state.retryable) await this.load()
  }

  clear(): void {
    this.identity = null
    this.abortCurrent()
    this.publish({ status: 'waiting-for-authentication' })
  }

  private async load(): Promise<void> {
    const identity = this.identity
    if (!identity) return
    this.abortCurrent()
    const operation = new AbortController()
    this.operation = operation
    const generation = ++this.generation
    this.publish({ status: 'loading' })

    try {
      const snapshot = createAccessSnapshot(await this.getAccess(operation.signal))
      if (!this.isCurrent(identity, generation, operation)) return
      this.publish(snapshot ? { status: 'ready', snapshot } : { status: 'unavailable', retryable: true })
    } catch (error) {
      if (!this.isCurrent(identity, generation, operation) || isAborted(error)) return
      this.publish(normalizeAccessError(error))
    }
  }

  private abortCurrent(): void {
    this.operation?.abort()
    this.operation = null
  }

  private isSameIdentity(identity: AccessIdentity): boolean {
    return this.identity?.accountId === identity.accountId && this.identity.handoffId === identity.handoffId
  }

  private isCurrent(identity: AccessIdentity, generation: number, operation: AbortController): boolean {
    return this.isSameIdentity(identity) && this.generation === generation && this.operation === operation && !operation.signal.aborted
  }

  private publish(state: AccessState): void {
    this.state = state
    this.listeners.forEach((listener) => listener(state))
  }
}

function normalizeAccessError(error: unknown): AccessState {
  if (isApiError(error)) {
    if (error.status === 404 && error.code === 'profile_not_found') return { status: 'blocked', reason: 'profile_not_found' }
    if (error.status === 403 && error.code === 'profile_inactive') return { status: 'blocked', reason: 'profile_inactive' }
    if (error.status === 401 || error.code === 'authentication_required') return { status: 'waiting-for-authentication' }
  }
  return { status: 'unavailable', retryable: true }
}

function isAborted(error: unknown): boolean {
  return isApiError(error) && error.kind === 'aborted'
}

function isAction(value: unknown): value is AccessAction {
  return typeof value === 'string' && ACTIONS.has(value)
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0
}

function isNonNegativeInteger(value: unknown): value is number {
  return typeof value === 'number' && Number.isInteger(value) && value >= 0
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}
