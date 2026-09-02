import { Group, Stack, Text, Title } from '@mantine/core'
import { useEffect, useMemo, useState } from 'react'
import { renderTextEditor, type Column } from 'react-data-grid'
import 'react-data-grid/lib/styles.css'
import { DataGridShell } from '@/common/grid/DataGridShell'
import { DataGridStatusBar } from '@/common/grid/DataGridStatusBar'
import type { RemoteState, SpinningGateway, WasteCaptureCatalog } from '../integration/contracts'
import { developmentSpinningGateway } from '../integration/developmentGateway'
import { unavailableIntegrationState } from '../integration/unavailableGateway'
import { createWasteDraft, replaceWasteRows, type WasteRow } from './wasteModel'

const gridRowHeight = 35
const gridHeaderRowHeight = 35

export function WasteWorkspace({ gateway = developmentSpinningGateway }: { gateway?: SpinningGateway }) {
  const [draft, setDraft] = useState(createWasteDraft)
  const [catalog, setCatalog] = useState<RemoteState<WasteCaptureCatalog>>({ status: 'loading' })

  useEffect(() => {
    const controller = new AbortController()
    const loadCatalog = gateway.getWasteCaptureCatalog ?? (() => Promise.resolve(unavailableIntegrationState))
    void loadCatalog(controller.signal).then(result => {
      if (controller.signal.aborted) return
      setCatalog(result)
      if (result.status === 'populated') setDraft(createWasteDraft(result.data.rows))
    })
    return () => controller.abort()
  }, [gateway])

  const references = catalog.status === 'populated' ? catalog.data : undefined
  const columns = useMemo<readonly Column<WasteRow>[]>(() => [
    { key: 'number', name: 'No', width: 65, frozen: 'start', renderCell: cell => <Text component="span">{cell.row.number}</Text> },
    { key: 'section', name: 'Sección', width: 160, frozen: 'start', renderCell: cell => <Text component="span">{cell.row.section}</Text> },
    { key: 'machine', name: 'Máquina', width: 260, frozen: 'start', renderCell: cell => <Text component="span">{cell.row.machine}</Text> },
    { key: 'weightKg', name: 'Peso [kg]', width: 130, frozen: 'start', editable: Boolean(references), renderEditCell: renderTextEditor },
    { key: 'total', name: 'Total', width: 260, frozen: 'start', renderCell: () => <Text component="span" c="dimmed">{references?.totalKg ?? 'Pendiente de confirmación del servidor'}</Text> },
  ], [references])

  return <Stack gap="lg">
    <div><Title order={1}>Desperdicio</Title><Text>Registro independiente de desperdicio real pesado</Text></div>
    {references && <Group gap="xl" aria-label="Contexto operativo de desperdicio"><Text><b>Turno:</b> {references.context.shift}</Text><Text><b>Supervisor:</b> {references.context.supervisor}</Text><Text><b>Fecha:</b> {references.context.businessDate}</Text><Text><b>Encargado:</b> {references.context.recorder}</Text></Group>}
    <DataGridShell
      toolbar={<Group justify="space-between" mb="sm"><Text fw={600}>Registro de desperdicio</Text><Text c="dimmed">Total: {references?.totalKg ?? 'Pendiente de confirmación del servidor'}</Text></Group>}
      statusBar={<DataGridStatusBar type="info" message={references ? 'Registre únicamente el peso real pesado. Las madejas fuera de especificación se reprocesan y no son desperdicio.' : 'Las referencias de desperdicio no están disponibles hasta que el servicio esté disponible.'} />}
      aria-label="Waste capture grid"
      columns={columns}
      rows={draft.rows}
      rowKeyGetter={row => row.rowId}
      onRowsChange={rows => setDraft(current => replaceWasteRows(current, rows))}
      defaultColumnOptions={{ resizable: true }}
      rowHeight={gridRowHeight}
      headerRowHeight={gridHeaderRowHeight}
      style={{ minWidth: 875, height: gridHeaderRowHeight + draft.rows.length * gridRowHeight }}
    />
  </Stack>
}
