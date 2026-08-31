import { Alert, Text } from '@mantine/core'
import type { RemoteState } from '../integration/contracts'

type UnavailableState = Extract<RemoteState<unknown>, { status: 'unavailable' }>

export function IntegrationState({ state }: { state: UnavailableState }) {
  return <Alert title="Integration unavailable" role="status" aria-live="polite">
    <Text>{state.message}</Text>
    <Text size="sm">No records, calculations, or outcomes are available until the service is delivered.</Text>
  </Alert>
}
