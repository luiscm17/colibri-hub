import { Stack, Text, Title } from '@mantine/core'
import { IntegrationState } from './components/IntegrationState'
import { unavailableIntegrationState } from './integration/unavailableGateway'
import { SectionWorkspace } from './sections/SectionWorkspace'
import { isSectionWorkspace } from './sections/workspaces'
import { spinningWorkspaces, type SpinningWorkspace } from './workspaces'

export function SpinningRoutePage({ workspace }: { workspace: SpinningWorkspace }) {
  if (isSectionWorkspace(workspace)) return <SectionWorkspace workspace={workspace} />
  return <Stack gap="lg">
    <div><Title order={1}>{spinningWorkspaces[workspace]}</Title><Text>Yarn Spinning</Text></div>
    <IntegrationState state={unavailableIntegrationState} />
  </Stack>
}
