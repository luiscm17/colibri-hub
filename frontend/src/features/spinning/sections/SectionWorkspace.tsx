import { NativeSelect, Stack, Text, TextInput, Title } from '@mantine/core'
import { useEffect, useState } from 'react'
import { IntegrationState } from '../components/IntegrationState'
import type { ProductionDischargeCatalog, RemoteState, SpinningGateway } from '../integration/contracts'
import { unavailableIntegrationState, unavailableSpinningGateway } from '../integration/unavailableGateway'
import { spinningWorkspaces, type SpinningWorkspace } from '../workspaces'
import { sectionGridConfig } from './configuration'
import { ProductionDischargeGrid } from './ProductionDischargeGrid'
import { appendDischargeRow, createDischargeDraft, pasteDischargeRows, replaceDischargeRows } from './dischargeModel'

export function SectionWorkspace({ workspace, gateway = unavailableSpinningGateway }: { workspace: SpinningWorkspace; gateway?: SpinningGateway }) {
  const [businessDate, setBusinessDate] = useState('')
  const [shift, setShift] = useState('')
  const [draft, setDraft] = useState(createDischargeDraft)
  const [catalog, setCatalog] = useState<RemoteState<ProductionDischargeCatalog>>({ status: 'loading' })
  const config = sectionGridConfig(workspace)

  useEffect(() => {
    const controller = new AbortController()
    void gateway.getProductionDischargeCatalog({ section: workspace, businessDate, shift }, controller.signal).then(result => {
      if (!controller.signal.aborted) setCatalog(result)
    })
    return () => controller.abort()
  }, [businessDate, gateway, shift, workspace])

  return <Stack gap="lg">
    <div>
      <Title order={1}>{spinningWorkspaces[workspace]}</Title>
      <Text>Yarn Spinning section-close workspace</Text>
    </div>
    <TextInput label="Business date" type="date" value={businessDate} onChange={(event) => setBusinessDate(event.currentTarget.value)} />
    <NativeSelect label="Shift" data={[{ value: '', label: 'Choose a shift' }, { value: 'first', label: 'First shift' }, { value: 'second', label: 'Second shift' }, { value: 'third', label: 'Third shift' }]} value={shift} onChange={(event) => setShift(event.currentTarget.value)} />
    {config.discharge ? <ProductionDischargeGrid catalog={catalog} draft={draft} onRowsChange={rows => setDraft(current => replaceDischargeRows(current, rows))} onAddRow={() => setDraft(appendDischargeRow)} onPaste={(rowId, column, text) => setDraft(current => pasteDischargeRows(current, rowId, column, text))} /> : <Text>Production Discharge is not configured for this section.</Text>}
    <Text>Production drafts remain local; submission is unavailable until the service is delivered.</Text>
    <IntegrationState state={unavailableIntegrationState} />
  </Stack>
}
