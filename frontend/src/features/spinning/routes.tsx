import { Stack, Text, Title } from '@mantine/core'
import { IntegrationState } from './components/IntegrationState'
import type { SpinningGateway } from './integration/contracts'
import { unavailableIntegrationState } from './integration/unavailableGateway'
import { SectionWorkspace } from './sections/SectionWorkspace'
import { SkeiningWorkspace } from './sections/SkeiningWorkspace'
import { QualityWorkspace } from './quality/QualityWorkspace'
import { isSectionWorkspace } from './sections/workspaces'
import { spinningWorkspaces, type SpinningWorkspace } from './workspaces'

export function SpinningRoutePage({ workspace, gateway }: { workspace: SpinningWorkspace; gateway?: SpinningGateway }) {
  if (isSectionWorkspace(workspace)) return <SectionWorkspace workspace={workspace} />
  if (workspace === 'skeining') return <SkeiningWorkspace gateway={gateway} />
  if (workspace === 'quality') return <QualityWorkspace gateway={gateway} />
  return <Stack gap="lg">
    <div><Title order={1}>{spinningWorkspaces[workspace]}</Title><Text>Hilatura</Text></div>
    <IntegrationState state={unavailableIntegrationState} />
  </Stack>
}
