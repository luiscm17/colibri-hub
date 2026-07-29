import { Alert, Box, Paper, Text } from '@mantine/core'
import { IconAlertCircle } from '@tabler/icons-react'
import { useMemo } from 'react'
import { DataGrid, type Column } from 'react-data-grid'
import 'react-data-grid/lib/styles.css'
import { DataGridThemeWrapper } from '@/common/grid/DataGridThemeWrapper'
import type { ReceptionGridRow } from '../../model/reception'
import {
  RECEPTION_EDITABLE_COLUMNS,
  type ReceptionEditableColumn,
  type ReceptionPastePlan,
  type ReceptionRowFeedback,
} from '../../model/receptionGrid'

interface ReceptionGridProps {
  readonly rows: readonly ReceptionGridRow[]
  readonly feedback: ReadonlyMap<string, ReceptionRowFeedback>
  readonly onRowsChange: (rows: readonly ReceptionGridRow[]) => void
  readonly onPaste: (rowId: string, column: ReceptionEditableColumn, text: string) => ReceptionPastePlan
}

export function ReceptionGrid({ rows, feedback, onRowsChange, onPaste }: ReceptionGridProps) {
  const columns = useMemo<readonly Column<ReceptionGridRow>[]>(() => [
    {
      key: 'baleNumber',
      name: 'Fardo',
      width: 130,
      frozen: 'start',
      editable: true,
      renderCell: cell => <CellValue value={cell.row.baleNumber} feedback={feedback.get(cell.row.rowId)} />,
    },
    ...editableColumns(feedback),
    {
      key: 'netWeightKg',
      name: 'Peso neto (kg)',
      width: 150,
      renderCell: cell => <Text component="span" fw={600}>{cell.row.netWeightKg || '—'}</Text>,
    },
    {
      key: 'status',
      name: 'Estado',
      width: 130,
      renderCell: cell => <Text component="span">{statusLabel(feedback.get(cell.row.rowId))}</Text>,
    },
  ], [feedback])

  const errorCount = [...feedback.values()].filter(row => row.status === 'partial' || row.status === 'invalid').length

  return (
    <Paper component="section" withBorder p="md" aria-label="Planilla de fardos">
      <DataGridThemeWrapper>
        <Box style={{ overflowX: 'auto' }}>
          <DataGrid
            aria-label="Planilla de fardos"
            aria-describedby="reception-grid-feedback"
            columns={columns}
            rows={rows}
            rowKeyGetter={row => row.rowId}
            onRowsChange={onRowsChange}
            onCellPaste={(args, event) => {
              event.preventDefault()
              const column = args.column.key
              if (!isEditableColumn(column)) return args.row
              onPaste(args.row.rowId, column, event.clipboardData.getData('text/plain'))
              return args.row
            }}
            defaultColumnOptions={{ resizable: true }}
            style={{ minWidth: 810 }}
          />
        </Box>
      </DataGridThemeWrapper>
      <Alert
        id="reception-grid-feedback"
        mt="sm"
        color={errorCount > 0 ? 'red' : 'green'}
        variant="light"
        icon={<IconAlertCircle size={16} />}
        role="status"
      >
        {errorCount > 0
          ? `${errorCount} fila${errorCount === 1 ? '' : 's'} requiere${errorCount === 1 ? '' : 'n'} corrección.`
          : 'No hay filas con errores.'}
      </Alert>
    </Paper>
  )
}

function editableColumns(feedback: ReadonlyMap<string, ReceptionRowFeedback>): readonly Column<ReceptionGridRow>[] {
  return [
    editableColumn('materialType', 'Material', 150, feedback),
    editableColumn('dtex', 'Dtex', 110, feedback),
    editableColumn('grossWeightKg', 'Peso bruto (kg)', 155, feedback),
    editableColumn('containerWeightKg', 'Tara (kg)', 130, feedback),
  ]
}

function editableColumn(
  key: ReceptionEditableColumn,
  name: string,
  width: number,
  feedback: ReadonlyMap<string, ReceptionRowFeedback>,
): Column<ReceptionGridRow> {
  return {
    key,
    name,
    width,
    editable: true,
    renderCell: cell => <CellValue value={cell.row[key]} feedback={feedback.get(cell.row.rowId)} />,
  }
}

function CellValue({ value, feedback }: { readonly value: string; readonly feedback?: ReceptionRowFeedback }) {
  const hasError = feedback?.status === 'partial' || feedback?.status === 'invalid'
  return <Text component="span" c={hasError ? 'red' : undefined} fw={feedback?.isDuplicate ? 700 : undefined}>{value || '—'}</Text>
}

function isEditableColumn(value: string): value is ReceptionEditableColumn {
  return RECEPTION_EDITABLE_COLUMNS.some(column => column === value)
}

function statusLabel(feedback: ReceptionRowFeedback | undefined): string {
  if (!feedback || feedback.status === 'empty') return 'Vacía'
  if (feedback.isDuplicate) return 'Duplicada'
  if (feedback.status === 'partial') return 'Incompleta'
  if (feedback.status === 'invalid') return 'Inválida'
  return 'Válida'
}
