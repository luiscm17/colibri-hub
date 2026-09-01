import type { RemoteState, SpinningGateway } from './contracts'

export const unavailableIntegrationState: Extract<RemoteState<never>, { status: 'unavailable' }> = {
  status: 'unavailable',
  message: 'La integración de Hilatura no está disponible.',
  retryable: false,
}

export const unavailableSpinningGateway: SpinningGateway = {
  getIntegrationState: async () => unavailableIntegrationState,
  getSectionContext: async () => unavailableIntegrationState,
  getProductionDischargeCatalog: async () => unavailableIntegrationState,
  getProgressContinuity: async () => unavailableIntegrationState,
  getQualityProfiles: async () => unavailableIntegrationState,
}
