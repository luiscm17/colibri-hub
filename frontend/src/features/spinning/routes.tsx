import { Stack, Text, Title } from '@mantine/core'
import { IntegrationState } from './components/IntegrationState'
import type { SpinningGateway } from './integration/contracts'
import { developmentSpinningGateway } from './integration/developmentGateway'
import { unavailableIntegrationState } from './integration/unavailableGateway'
import { SectionWorkspace } from './sections/SectionWorkspace'
import { SkeiningWorkspace } from './sections/SkeiningWorkspace'
import { QualityWorkspace } from './quality/QualityWorkspace'
import { WasteWorkspace } from './waste/WasteWorkspace'
import { isSectionWorkspace } from './sections/workspaces'
import { spinningWorkspaces, type SpinningWorkspace } from './workspaces'

export function SpinningRoutePage({ workspace, gateway }: { workspace: SpinningWorkspace; gateway?: SpinningGateway }) {
  const compositionGateway = gateway ?? developmentSpinningGateway
  if (isSectionWorkspace(workspace)) return <SectionWorkspace workspace={workspace} gateway={compositionGateway} />
  if (workspace === 'skeining') return <SkeiningWorkspace gateway={compositionGateway} />
  if (workspace === 'quality') return <QualityWorkspace gateway={compositionGateway} />
  if (workspace === 'waste') return <WasteWorkspace gateway={compositionGateway} />
  return <Stack gap="lg">
    <div><Title order={1}>{spinningWorkspaces[workspace]}</Title><Text>Hilatura</Text></div>
    <IntegrationState state={unavailableIntegrationState} />
  </Stack>
}
