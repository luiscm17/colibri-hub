import { Alert, Box, Paper, Text } from '@mantine/core'
import { IconAlertCircle, IconCheck } from '@tabler/icons-react'
import { useMemo } from 'react'
import { DataGrid, renderTextEditor, type Column } from 'react-data-grid'
import 'react-data-grid/lib/styles.css'
import { DataGridThemeWrapper } from '@/common/grid/DataGridThemeWrapper'
import type { DeliveryGridRow } from '../../model/delivery'
import { DELIVERY_COLUMNS, type DeliveryColumn, type DeliveryFeedback } from '../../model/deliveryGrid'

interface DeliveryGridProps {
  readonly rows: readonly DeliveryGridRow[]
  readonly feedback: ReadonlyMap<string, DeliveryFeedback>
  readonly disabled?: boolean
  readonly onRowsChange: (rows: readonly DeliveryGridRow[]) => void
  readonly onPaste: (rowId: string, column: DeliveryColumn, text: string) => { readonly accepted: boolean }
}

export function DeliveryGrid({ rows, feedback, disabled = false, onRowsChange, onPaste }: DeliveryGridProps) {
  const columns = useMemo<readonly Column<DeliveryGridRow>[]>(() => [
    { key: 'number', name: '#', width: 55, frozen: 'start', renderCell: cell => <Text component="span">{cell.rowIdx + 1}</Text> },
    column('shipmentNumber', 'Remito', 190, disabled, feedback),
    column('baleNumber', 'Fardo', 170, disabled, feedback),
    { key: 'result', name: 'Resultado', width: 220, renderCell: cell => <Result row={cell.row} /> },
  ], [disabled, feedback])
  const invalid = rows.filter(row => !feedback.get(row.rowId)?.empty && (feedback.get(row.rowId)?.duplicate || Object.keys(feedback.get(row.rowId)?.errors ?? {}).some(key => key.startsWith(row.rowId)))).length
  return (
    <Paper component="section" withBorder p="md" aria-label="Planilla de entrega">
      <DataGridThemeWrapper><Box style={{ overflowX: 'auto' }}><DataGrid
        aria-label="Planilla de entrega" aria-describedby="delivery-grid-feedback" columns={columns} rows={rows} rowKeyGetter={row => row.rowId}
        onRowsChange={next => { if (!disabled) onRowsChange(next) }}
        onCellPaste={(args, event) => { event.preventDefault(); if (!disabled && editable(args.column.key) && args.row.result !== 'delivered') onPaste(args.row.rowId, args.column.key, event.clipboardData.getData('text/plain')); return args.row }}
        defaultColumnOptions={{ resizable: true }} style={{ minWidth: 635 }}
      /></Box></DataGridThemeWrapper>
      <Alert id="delivery-grid-feedback" mt="sm" color={invalid ? 'red' : 'green'} variant="light" icon={<IconAlertCircle size={16} />} role={invalid ? 'alert' : 'status'}>
        {invalid ? `${invalid} fila${invalid === 1 ? '' : 's'} requiere${invalid === 1 ? '' : 'n'} corrección.` : 'Ingresá las identidades de los fardos desde sus etiquetas físicas.'}
      </Alert>
    </Paper>
  )
}

function column(key: DeliveryColumn, name: string, width: number, disabled: boolean, feedback: ReadonlyMap<string, DeliveryFeedback>): Column<DeliveryGridRow> {
  return { key, name, width, frozen: key === 'shipmentNumber' ? 'start' : undefined, editable: row => !disabled && row.result !== 'delivered', renderEditCell: renderTextEditor, renderCell: cell => {
    const errors = feedback.get(cell.row.rowId)?.errors ?? {}
    const error = errors[`${cell.row.rowId}.${key}`] ?? errors[`${cell.row.rowId}.identity`]
    return <Text component="span" c={error ? 'red' : undefined} fw={error ? 700 : undefined} title={error} aria-label={error ? `Error: ${error}` : undefined}>{cell.row[key] || '—'}{error ? ' · Error' : ''}</Text>
  } }
}

function Result({ row }: { readonly row: DeliveryGridRow }) {
  if (row.result === 'delivered') return <Text component="span" c="green" fw={700} aria-label="Entregado correctamente"><IconCheck size={14} /> Entregado</Text>
  if (row.result === 'already_delivered') return <Text component="span" c="red">Ya entregado{row.resultMessage ? `: ${row.resultMessage}` : ''}</Text>
  if (row.result === 'not_found') return <Text component="span" c="red">No encontrado{row.resultMessage ? `: ${row.resultMessage}` : ''}</Text>
  return <Text component="span" c="dimmed">Pendiente</Text>
}

function editable(value: string): value is DeliveryColumn { return DELIVERY_COLUMNS.some(column => column === value) }
