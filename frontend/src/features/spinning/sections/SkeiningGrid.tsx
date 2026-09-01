import { Alert, Button, Group, Text } from '@mantine/core'
import { useMemo } from 'react'
import { renderTextEditor, type Column } from 'react-data-grid'
import 'react-data-grid/lib/styles.css'
import { DataGridShell } from '@/common/grid/DataGridShell'
import { SelectCellEditor } from '@/common/grid/editors/SelectCellEditor'
import type { ProductionDischargeCatalog, RemoteState } from '../integration/contracts'
import { SKEINING_COLUMN_LABELS, skeiningRowErrors, type SkeiningDraft, type SkeiningRow } from './skeiningModel'

interface SkeiningGridProps {
  readonly catalog: RemoteState<ProductionDischargeCatalog>
  readonly draft: SkeiningDraft
  readonly onRowsChange: (rows: readonly SkeiningRow[]) => void
  readonly onAddRow: () => void
}

export function SkeiningGrid({ catalog, draft, onRowsChange, onAddRow }: SkeiningGridProps) {
  const referenceData = catalog.status === 'populated' ? catalog.data : undefined
  const canSelect = referenceData !== undefined
  const machineOptions = useMemo(() => referenceData?.machines.filter(machine => referenceData.applicableMachineIds.includes(machine.id)).map(machine => ({ value: machine.id, label: machine.label })) ?? [], [referenceData])
  const yarnCountOptions = useMemo(() => referenceData?.yarnCounts.map(yarnCount => ({ value: yarnCount.id, label: yarnCount.label })) ?? [], [referenceData])
  const invalidCount = draft.rows.filter(row => Object.keys(skeiningRowErrors(row)).length > 0).length
  const columns = useMemo<readonly Column<SkeiningRow>[]>(() => [
    selectColumn('machine', SKEINING_COLUMN_LABELS.machine, 150, canSelect, machineOptions),
    selectColumn('yarnCount', SKEINING_COLUMN_LABELS.yarnCount, 140, canSelect, yarnCountOptions),
    textColumn('skeinQuantity', SKEINING_COLUMN_LABELS.skeinQuantity, 175),
    textColumn('estimatedUnitWeightKg', SKEINING_COLUMN_LABELS.estimatedUnitWeightKg, 210),
    textColumn('operator', SKEINING_COLUMN_LABELS.operator, 180),
    textColumn('observations', SKEINING_COLUMN_LABELS.observations, 220),
    { key: 'derivedTotalWeightKg', name: SKEINING_COLUMN_LABELS.derivedTotalWeightKg, width: 210, renderCell: () => <Text component="span">No disponible hasta la confirmación del servidor</Text> },
  ], [canSelect, machineOptions, yarnCountOptions])

  return <DataGridShell
    toolbar={<Group justify="space-between" mb="sm"><Text fw={600}>Producción de madejas</Text><Button size="xs" onClick={onAddRow} disabled={!canSelect}>Agregar fila</Button></Group>}
    statusBar={<Alert color={invalidCount ? 'red' : 'blue'} role={invalidCount ? 'alert' : 'status'}>{invalidCount ? `${invalidCount} fila${invalidCount === 1 ? '' : 's'} requiere corrección.` : canSelect ? 'El peso total se mostrará únicamente cuando el servidor confirme el resultado.' : 'Las selecciones de máquina y título de hilo no están disponibles hasta que los datos de referencia estén disponibles.'}</Alert>}
    aria-label="Skeining production grid"
    columns={columns}
    rows={draft.rows}
    rowKeyGetter={row => row.rowId}
    onRowsChange={onRowsChange}
    defaultColumnOptions={{ resizable: true }}
    style={{ minWidth: 1285 }}
  />
}

function selectColumn(key: 'machine' | 'yarnCount', name: string, width: number, editable: boolean, data: { value: string; label: string }[]): Column<SkeiningRow> {
  return { key, name, width, editable, renderEditCell: editable ? props => <SelectCellEditor {...props} data={data} /> : undefined, renderCell: cell => <Cell row={cell.row} column={key} /> }
}

function textColumn(key: Exclude<keyof SkeiningRow, 'rowId' | 'machine' | 'yarnCount'>, name: string, width: number): Column<SkeiningRow> {
  return { key, name, width, editable: true, renderEditCell: renderTextEditor, renderCell: cell => <Cell row={cell.row} column={key} /> }
}

function Cell({ row, column }: { readonly row: SkeiningRow; readonly column: keyof Omit<SkeiningRow, 'rowId'> }) {
  const error = skeiningRowErrors(row)[column as keyof ReturnType<typeof skeiningRowErrors>]
  return <Text component="span" c={error ? 'red' : undefined} title={error}>{row[column] || '—'}{error ? ' · Error' : ''}</Text>
}
