import { NativeSelect, Stack, Text, TextInput, Title } from '@mantine/core'
import { useEffect, useState } from 'react'
import { IntegrationState } from '../components/IntegrationState'
import type { ProductionDischargeCatalog, RemoteState, SpinningGateway } from '../integration/contracts'
import { unavailableIntegrationState, unavailableSpinningGateway } from '../integration/unavailableGateway'
import { spinningWorkspaces, type SpinningWorkspace } from '../workspaces'
import { sectionGridConfig } from './configuration'
import { ProductionDischargeGrid } from './ProductionDischargeGrid'
import { appendDischargeRow, createDischargeDraft, pasteDischargeRows, replaceDischargeRows } from './dischargeModel'
import { ProgressGrid } from './ProgressGrid'
import { createProgressDraft } from './progressModel'

export function SectionWorkspace({ workspace, gateway = unavailableSpinningGateway }: { workspace: SpinningWorkspace; gateway?: SpinningGateway }) {
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

  return <Stack gap="lg">
    <div>
      <Title order={1}>{spinningWorkspaces[workspace]}</Title>
      <Text>Área de trabajo de cierre de sección de Hilatura</Text>
    </div>
    <TextInput label="Fecha operativa" type="date" value={businessDate} onChange={(event) => setBusinessDate(event.currentTarget.value)} />
    <NativeSelect label="Turno" data={[{ value: '', label: 'Seleccione un turno' }, { value: 'first', label: 'Primer turno' }, { value: 'second', label: 'Segundo turno' }, { value: 'third', label: 'Tercer turno' }]} value={shift} onChange={(event) => setShift(event.currentTarget.value)} />
    {config.discharge ? <ProductionDischargeGrid catalog={catalog} draft={draft} onRowsChange={rows => setDraft(current => replaceDischargeRows(current, rows))} onAddRow={() => setDraft(appendDischargeRow)} onPaste={(rowId, column, text) => setDraft(current => pasteDischargeRows(current, rowId, column, text))} /> : <Text>La descarga de producción no está configurada para esta sección.</Text>}
    {config.progress && <ProgressGrid identity={{ section: workspace, businessDate, shift }} catalog={catalog} draft={progressDraft} gateway={gateway} onDraftChange={setProgressDraft} />}
    <Text>Los borradores de producción permanecen locales; el envío no está disponible hasta que el servicio esté disponible.</Text>
    <IntegrationState state={unavailableIntegrationState} />
  </Stack>
}
