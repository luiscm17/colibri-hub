import { Alert, Button, Group, Text } from '@mantine/core'
import { useMemo } from 'react'
import { renderTextEditor, type Column } from 'react-data-grid'
import 'react-data-grid/lib/styles.css'
import { DataGridShell } from '@/common/grid/DataGridShell'
import type { ProductionDischargeCatalog, RemoteState } from '../integration/contracts'
import { SelectCellEditor } from '@/common/grid/editors/SelectCellEditor'
import {
  DISCHARGE_EDITABLE_COLUMNS,
  DISCHARGE_COLUMN_LABELS,
  dischargeRowFeedback,
  type DischargeColumn,
  type ProductionDischargeDraft,
  type ProductionDischargeRow,
} from './dischargeModel'
import { hasRovingTitleInput, rovingTitleMachineIds } from './configuration'

interface ProductionDischargeGridProps {
  readonly catalog: RemoteState<ProductionDischargeCatalog>
  readonly draft: ProductionDischargeDraft
  readonly onRowsChange: (rows: readonly ProductionDischargeRow[]) => void
  readonly onAddRow: () => void
  readonly onPaste: (rowId: string, column: DischargeColumn, text: string) => void
}

export function ProductionDischargeGrid({ catalog, draft, onRowsChange, onAddRow, onPaste }: ProductionDischargeGridProps) {
  const feedback = useMemo(() => new Map(draft.rows.map(row => [row.rowId, dischargeRowFeedback(row)])), [draft.rows])
  const invalidCount = [...feedback.values()].filter(row => row.state === 'invalid').length
  const referenceData = catalog.status === 'populated' ? catalog.data : undefined
  const machineOptions = useMemo(() => referenceData?.machines.filter(machine => referenceData.applicableMachineIds.includes(machine.id)).map(machine => ({ value: machine.id, label: machine.label })) ?? [], [referenceData])
  const yarnCountOptions = useMemo(() => referenceData?.yarnCounts.map(yarnCount => ({ value: yarnCount.id, label: yarnCount.label })) ?? [], [referenceData])
  const authorizedRovingTitleMachineIds = useMemo(() => referenceData ? rovingTitleMachineIds(referenceData) : [], [referenceData])
  const rendersRovingTitleInput = referenceData !== undefined && hasRovingTitleInput(referenceData)
  const canSelect = referenceData !== undefined
  const columns = useMemo<readonly Column<ProductionDischargeRow>[]>(() => [
    { key: 'machine', name: DISCHARGE_COLUMN_LABELS.machine, width: 150, editable: canSelect, renderEditCell: canSelect ? props => <SelectCellEditor {...props} data={machineOptions} /> : undefined, renderCell: cell => <Cell row={cell.row} column="machine" /> },
    { key: 'yarnCount', name: DISCHARGE_COLUMN_LABELS.yarnCount, width: 140, editable: canSelect, renderEditCell: canSelect ? props => <SelectCellEditor {...props} data={yarnCountOptions} /> : undefined, renderCell: cell => <Cell row={cell.row} column="yarnCount" /> },
    { key: 'grossWeightKg', name: DISCHARGE_COLUMN_LABELS.grossWeightKg, width: 160, editable: true, renderEditCell: renderTextEditor, renderCell: cell => <Cell row={cell.row} column="grossWeightKg" /> },
    { key: 'operativeSpindleCount', name: DISCHARGE_COLUMN_LABELS.operativeSpindleCount, width: 190, editable: true, renderEditCell: renderTextEditor, renderCell: cell => <Cell row={cell.row} column="operativeSpindleCount" /> },
    { key: 'spindleTareWeightG', name: DISCHARGE_COLUMN_LABELS.spindleTareWeightG, width: 190, editable: true, renderEditCell: renderTextEditor, renderCell: cell => <Cell row={cell.row} column="spindleTareWeightG" /> },
    { key: 'cartWeightKg', name: DISCHARGE_COLUMN_LABELS.cartWeightKg, width: 150, editable: true, renderEditCell: renderTextEditor, renderCell: cell => <Cell row={cell.row} column="cartWeightKg" /> },
    ...(rendersRovingTitleInput ? [{ key: 'rovingCount', name: DISCHARGE_COLUMN_LABELS.rovingCount, width: 180, editable: (row: ProductionDischargeRow) => authorizedRovingTitleMachineIds.includes(row.machine), renderEditCell: renderTextEditor, renderCell: (cell: { readonly row: ProductionDischargeRow }) => <Cell row={cell.row} column="rovingCount" /> }] : []),
    { key: 'observations', name: DISCHARGE_COLUMN_LABELS.observations, width: 220, editable: true, renderEditCell: renderTextEditor, renderCell: cell => <Cell row={cell.row} column="observations" /> },
    { key: 'netWeight', name: DISCHARGE_COLUMN_LABELS.netWeight, width: 180, renderCell: () => <Text component="span">No disponible hasta la confirmación del servidor</Text> },
    { key: 'state', name: 'Estado', width: 210, renderCell: cell => <Text component="span">{label(feedback.get(cell.row.rowId)?.state)}</Text> },
  ], [authorizedRovingTitleMachineIds, canSelect, feedback, machineOptions, rendersRovingTitleInput, yarnCountOptions])
  const feedbackBar = <Alert id="production-discharge-feedback" color={invalidCount ? 'red' : 'blue'} role={invalidCount ? 'alert' : 'status'}>
    {invalidCount ? `${invalidCount} fila${invalidCount === 1 ? '' : 's'} requiere corrección.` : canSelect ? 'Las filas del borrador permanecen locales hasta que el servicio de producción esté disponible.' : 'Las selecciones de máquina y título de hilo no están disponibles hasta que los datos de referencia estén disponibles.'}
  </Alert>
  return <>
    {canSelect && <Text size="sm" c="dimmed" aria-label="Available reference selections">{machineOptions.map(option => option.label).join(', ')} · {yarnCountOptions.map(option => option.label).join(', ')}</Text>}
    <DataGridShell
    toolbar={<Group justify="space-between" mb="sm"><Text fw={600}>Descarga de producción</Text><Button size="xs" onClick={onAddRow} disabled={!canSelect} aria-describedby={!canSelect ? 'production-discharge-feedback' : undefined}>Agregar descarga</Button></Group>}
    statusBar={feedbackBar}
    aria-label="Production Discharge grid"
    aria-describedby="production-discharge-feedback"
    columns={columns}
    rows={draft.rows}
    rowKeyGetter={row => row.rowId}
    onRowsChange={onRowsChange}
    onCellPaste={(args, event) => { event.preventDefault(); if (isDischargeColumn(args.column.key) && (canSelect || !['machine', 'yarnCount'].includes(args.column.key)) && (args.column.key !== 'rovingCount' || authorizedRovingTitleMachineIds.includes(args.row.machine))) onPaste(args.row.rowId, args.column.key, event.clipboardData.getData('text/plain')); return args.row }}
    defaultColumnOptions={{ resizable: true }}
    style={{ minWidth: 1780 }}
    />
  </>
}

function Cell({ row, column }: { readonly row: ProductionDischargeRow; readonly column: DischargeColumn }) {
  const error = dischargeRowFeedback(row).errors[column]
  return <Text component="span" c={error ? 'red' : undefined} title={error} aria-label={error ? `Error: ${error}` : undefined}>{row[column] || '—'}{error ? ' · Error' : ''}</Text>
}

function isDischargeColumn(value: string): value is DischargeColumn { return DISCHARGE_EDITABLE_COLUMNS.some(column => column === value) }

function label(state: ReturnType<typeof dischargeRowFeedback>['state'] | undefined): string {
  return ({ pending: 'Pendiente', invalid: 'No válido', complete: 'Completo', 'acknowledged-no-production': 'Sin producción confirmada' })[state ?? 'pending']
}
