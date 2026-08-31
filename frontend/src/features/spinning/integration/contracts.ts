export type RemoteState<T> =
  | { status: 'loading' }
  | { status: 'unavailable'; message: string; retryable: boolean }
  | { status: 'failure'; message: string }
  | { status: 'empty' }
  | { status: 'populated'; data: T }
  | { status: 'stale'; data: T; message: string }
  | { status: 'conflict'; message: string }

export interface SpinningGateway {
  getIntegrationState(signal?: AbortSignal): Promise<RemoteState<never>>
}
