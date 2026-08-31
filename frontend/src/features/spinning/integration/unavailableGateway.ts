import type { RemoteState, SpinningGateway } from './contracts'

export const unavailableIntegrationState: Extract<RemoteState<never>, { status: 'unavailable' }> = {
  status: 'unavailable',
  message: 'The Yarn Spinning integration is unavailable.',
  retryable: false,
}

export const unavailableSpinningGateway: SpinningGateway = {
  getIntegrationState: async () => unavailableIntegrationState,
}
