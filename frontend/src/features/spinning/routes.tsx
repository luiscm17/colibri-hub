import { Stack, Text, Title } from '@mantine/core'
import { IntegrationState } from './components/IntegrationState'
import { unavailableIntegrationState } from './integration/unavailableGateway'
import { spinningWorkspaces, type SpinningWorkspace } from './workspaces'

export function SpinningRoutePage({ workspace }: { workspace: SpinningWorkspace }) {
  return <Stack gap="lg">
    <div><Title order={1}>{spinningWorkspaces[workspace]}</Title><Text>Yarn Spinning</Text></div>
    <IntegrationState state={unavailableIntegrationState} />
  </Stack>
}
