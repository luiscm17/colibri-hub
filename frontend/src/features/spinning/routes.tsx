import { Stack, Text, Title } from '@mantine/core'
import { IntegrationState } from './components/IntegrationState'
import type { SpinningGateway } from './integration/contracts'
import { developmentSpinningGateway } from './integration/developmentGateway'
import { unavailableIntegrationState } from './integration/unavailableGateway'
import { SectionWorkspace } from './sections/SectionWorkspace'
import { QualityWorkspace } from './quality/QualityWorkspace'
import { WasteWorkspace } from './waste/WasteWorkspace'
import { ReportingWorkspace } from './reporting/ReportingWorkspace'
import { isSectionWorkspace } from './sections/workspaces'
import { spinningWorkspaces, type SpinningWorkspace } from './workspaces'

export function SpinningRoutePage({ workspace, gateway }: { workspace: SpinningWorkspace; gateway?: SpinningGateway }) {
  const compositionGateway = gateway ?? developmentSpinningGateway
  if (isSectionWorkspace(workspace)) return <><SectionWorkspace workspace={workspace} gateway={compositionGateway} /><ReportingWorkspace gateway={compositionGateway} section={spinningWorkspaces[workspace]} /></>
  if (workspace === 'quality') return <QualityWorkspace gateway={compositionGateway} />
  if (workspace === 'waste') return <WasteWorkspace gateway={compositionGateway} />
  if (workspace === 'consolidated') return <ReportingWorkspace gateway={compositionGateway} />
  return <Stack gap="lg"><div><Title order={1}>{spinningWorkspaces[workspace]}</Title><Text>Hilatura</Text></div><IntegrationState state={unavailableIntegrationState} /></Stack>
}
