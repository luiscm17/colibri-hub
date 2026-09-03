import { Group, NativeSelect, Stack, Text, TextInput, Title } from '@mantine/core'
import { useEffect, useState } from 'react'
import { IntegrationState } from '../components/IntegrationState'
import type { ProductionDischargeCatalog, RemoteState, SpinningGateway } from '../integration/contracts'
import { developmentSpinningGateway } from '../integration/developmentGateway'
import { unavailableIntegrationState } from '../integration/unavailableGateway'
import { spinningWorkspaces, type SpinningWorkspace } from '../workspaces'
import { sectionGridConfig } from './configuration'
import { ProductionDischargeGrid } from './ProductionDischargeGrid'
import { applyProductionRoster, createDischargeDraft, pasteDischargeRows, replaceDischargeRows } from './dischargeModel'
import { ProgressGrid } from './ProgressGrid'
import { applyProgressRoster, createProgressDraft } from './progressModel'

export function SectionWorkspace({ workspace, gateway = developmentSpinningGateway }: { workspace: SpinningWorkspace; gateway?: SpinningGateway }) {
  const [businessDate, setBusinessDate] = useState('')
  const [shift, setShift] = useState('')
  const [draft, setDraft] = useState(createDischargeDraft)
  const [progressDraft, setProgressDraft] = useState(createProgressDraft)
  const [catalog, setCatalog] = useState<RemoteState<ProductionDischargeCatalog>>({ status: 'loading' })
  const config = sectionGridConfig(workspace)

  useEffect(() => {
    const controller = new AbortController()
    void gateway.getProductionDischargeCatalog({ section: workspace, businessDate, shift }, controller.signal).then(result => {
      if (!controller.signal.aborted) setCatalog(result)
    })
    return () => controller.abort()
  }, [businessDate, gateway, shift, workspace])

  const rosterDraft = catalog.status === 'populated' ? applyProductionRoster(draft, catalog.data.productionRoster) : draft
  const rosterProgressDraft = catalog.status === 'populated' ? applyProgressRoster(progressDraft, catalog.data.progressRoster) : progressDraft

  return <Stack gap="lg">
    <div>
      <Title order={1}>{spinningWorkspaces[workspace]}</Title>
      <Text>Área de trabajo de cierre de sección de Hilatura</Text>
    </div>
    <Group grow align="end">
      <NativeSelect label="Turno" data={[{ value: '', label: 'Seleccione un turno' }, { value: 'A', label: 'Turno A' }, { value: 'B', label: 'Turno B' }, { value: 'C', label: 'Turno C' }]} value={shift} onChange={(event) => setShift(event.currentTarget.value)} />
      <TextInput label="Supervisor" />
      <TextInput label="Fecha" type="date" value={businessDate} onChange={(event) => setBusinessDate(event.currentTarget.value)} />
      <TextInput label="Encargado" />
    </Group>
    {config.discharge ? <ProductionDischargeGrid workspace={workspace} catalog={catalog} draft={rosterDraft} onRowsChange={rows => setDraft(replaceDischargeRows(rosterDraft, rows))} onPaste={(rowId, column, text) => setDraft(pasteDischargeRows(rosterDraft, rowId, column, text))} /> : <Text>La descarga de producción no está configurada para esta sección.</Text>}
    {config.progress && <ProgressGrid catalog={catalog} draft={rosterProgressDraft} onDraftChange={setProgressDraft} />}
    <Text>Los borradores de producción permanecen locales; el envío no está disponible hasta que el servicio esté disponible.</Text>
    <IntegrationState state={unavailableIntegrationState} />
  </Stack>
}
