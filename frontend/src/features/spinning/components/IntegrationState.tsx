import { Alert, Text } from '@mantine/core'
import type { RemoteState } from '../integration/contracts'

type UnavailableState = Extract<RemoteState<unknown>, { status: 'unavailable' }>

export function IntegrationState({ state }: { state: UnavailableState }) {
  return <Alert title="Integración no disponible" role="status" aria-live="polite">
    <Text>{state.message}</Text>
    <Text size="sm">No hay registros, cálculos ni resultados disponibles hasta que el servicio esté disponible.</Text>
  </Alert>
}
