import { Alert, Button, Group, Text } from '@mantine/core'
import { useEffect, useMemo, useRef, useState } from 'react'
import { type Column } from 'react-data-grid'
import 'react-data-grid/lib/styles.css'
import { DataGridShell } from '@/common/grid/DataGridShell'
import { SelectCellEditor } from '@/common/grid/editors/SelectCellEditor'
import type { ProductionDischargeCatalog, ProgressContinuity, ProgressIdentity, RemoteState, SpinningGateway } from '../integration/contracts'
import { appendProgressRow, isCurrentProgressRequest, progressRequestKey, replaceProgressRows, type ProgressDraft, type ProgressRow } from './progressModel'

interface ProgressGridProps {
  readonly identity: Readonly<{ section: string; businessDate: string; shift: string }>
  readonly catalog: RemoteState<ProductionDischargeCatalog>
  readonly draft: ProgressDraft
  readonly gateway: SpinningGateway
  readonly onDraftChange: (draft: ProgressDraft) => void
}

export function ProgressGrid({ identity, catalog, draft, gateway, onDraftChange }: ProgressGridProps) {
  const [continuity, setContinuity] = useState<Record<string, RemoteState<ProgressContinuity>>>({})
  const latestKeys = useRef<Record<string, string>>({})
  const references = catalog.status === 'populated' ? catalog.data : undefined
  const machineOptions = useMemo(() => references?.machines.map(machine => ({ value: machine.id, label: machine.label })) ?? [], [references])
  const yarnCountOptions = useMemo(() => references?.yarnCounts.map(count => ({ value: count.id, label: count.label })) ?? [], [references])

  useEffect(() => {
    const controller = new AbortController()
    const requested = Object.fromEntries(draft.rows.filter(row => row.machineId && row.yarnCountId).map(row => {
      const request: ProgressIdentity = { ...identity, machineId: row.machineId, yarnCountId: row.yarnCountId }
      return [row.rowId, progressRequestKey(request)]
    }))
    latestKeys.current = requested
    for (const row of draft.rows) {
      const requestKey = requested[row.rowId]
      if (!requestKey) continue
      const request: ProgressIdentity = { ...identity, machineId: row.machineId, yarnCountId: row.yarnCountId }
      void gateway.getProgressContinuity(request, controller.signal).then(result => {
        if (!controller.signal.aborted && isCurrentProgressRequest(requestKey, latestKeys.current[row.rowId])) {
          setContinuity(current => ({ ...current, [row.rowId]: result }))
        }
      })
    }
    return () => controller.abort()
  }, [draft.rows, gateway, identity])

  const canSelect = references !== undefined
  const columns = useMemo<readonly Column<ProgressRow>[]>(() => [
    { key: 'machineId', name: 'Máquina', width: 170, editable: canSelect, renderEditCell: canSelect ? props => <SelectCellEditor {...props} data={machineOptions} /> : undefined, renderCell: cell => <Text component="span">{machineOptions.find(option => option.value === cell.row.machineId)?.label ?? '—'}</Text> },
    { key: 'yarnCountId', name: 'Título del hilo', width: 150, editable: canSelect, renderEditCell: canSelect ? props => <SelectCellEditor {...props} data={yarnCountOptions} /> : undefined, renderCell: cell => <Text component="span">{yarnCountOptions.find(option => option.value === cell.row.yarnCountId)?.label ?? '—'}</Text> },
    { key: 'continuity', name: 'Continuidad derivada del servidor', width: 290, renderCell: cell => <Text component="span">{continuityLabel(continuity[cell.row.rowId])}</Text> },
  ], [canSelect, continuity, machineOptions, yarnCountOptions])

  return <DataGridShell
    toolbar={<Group justify="space-between" mb="sm"><Text fw={600}>Avance aplicable</Text><Button size="xs" disabled={!canSelect} onClick={() => onDraftChange(appendProgressRow(draft))}>Agregar identidad de avance</Button></Group>}
    statusBar={<Alert role="status" aria-live="polite" color="blue">{canSelect ? 'La continuidad se muestra solo cuando está confirmada por el servidor.' : 'Las identidades de avance no están disponibles hasta que los datos de referencia estén disponibles.'}</Alert>}
    aria-label="Progress summary grid"
    columns={columns}
    rows={draft.rows}
    rowKeyGetter={row => row.rowId}
    onRowsChange={rows => onDraftChange(replaceProgressRows(draft, rows))}
    defaultColumnOptions={{ resizable: true }}
    style={{ minWidth: 610 }}
  />
}

function continuityLabel(state: RemoteState<ProgressContinuity> | undefined): string {
  if (!state || state.status === 'loading') return 'Esperando una identidad completa.'
  if (state.status === 'unavailable') return 'No disponible hasta que el servicio de continuidad esté disponible.'
  if (state.status !== 'populated') return 'No hay proyección de continuidad disponible.'
  return ({ predecessor: 'Predecesor confirmado por el servidor disponible.', 'no-predecessor': 'No hay predecesor confirmado por el servidor.', 'stale-configuration': 'Configuración desactualizada confirmada por el servidor.' })[state.data.kind]
}
