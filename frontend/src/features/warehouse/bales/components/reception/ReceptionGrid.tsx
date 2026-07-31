import { Alert, Text } from '@mantine/core'
import { IconAlertCircle } from '@tabler/icons-react'
import { useEffect, useMemo, useRef } from 'react'
import { renderTextEditor, type Column, type DataGridHandle } from 'react-data-grid'
import 'react-data-grid/lib/styles.css'
import { DataGridShell } from '@/common/grid/DataGridShell'
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
  readonly errors?: Readonly<Record<string, string>>
  readonly disabled?: boolean
}

export function ReceptionGrid({ rows, feedback, onRowsChange, onPaste, errors = {}, disabled = false }: ReceptionGridProps) {
  const gridRef = useRef<DataGridHandle>(null)
  const columns = useMemo<readonly Column<ReceptionGridRow>[]>(() => [
    {
      key: 'baleNumber',
      name: 'Fardo',
      width: 130,
      frozen: 'start',
      editable: !disabled,
      renderEditCell: disabled ? undefined : renderTextEditor,
      renderCell: cell => <CellValue value={cell.row.baleNumber} feedback={feedback.get(cell.row.rowId)} error={errors[`${cell.row.rowId}:baleNumber`]} />,
    },
    ...editableColumns(feedback, errors, disabled),
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
  ], [disabled, errors, feedback])

  const localErrorCount = [...feedback.values()].filter(row => row.status === 'partial' || row.status === 'invalid').length
  const remoteErrorKey = Object.keys(errors)[0]
  const remoteErrorCount = Object.keys(errors).length
  const firstRemoteMessage = remoteErrorKey ? errors[remoteErrorKey] : undefined

  useEffect(() => {
    if (!remoteErrorKey) return
    const separator = remoteErrorKey.lastIndexOf(':')
    const rowIdx = rows.findIndex(row => row.rowId === remoteErrorKey.slice(0, separator))
    const idx = RECEPTION_EDITABLE_COLUMNS.indexOf(remoteErrorKey.slice(separator + 1) as ReceptionEditableColumn)
    if (rowIdx < 0 || idx < 0) return
    gridRef.current?.scrollToCell({ rowIdx, idx })
    gridRef.current?.setActivePosition({ rowIdx, idx })
    gridRef.current?.element?.focus()
  }, [remoteErrorKey, rows])

  const feedbackBar = (
    <Alert
      id="reception-grid-feedback"
      mt="sm"
      color={localErrorCount + remoteErrorCount > 0 ? 'red' : 'green'}
      variant="light"
      icon={<IconAlertCircle size={16} />}
      role={remoteErrorCount > 0 ? 'alert' : 'status'}
    >
      {remoteErrorCount > 0
        ? `${remoteErrorCount} campo${remoteErrorCount === 1 ? '' : 's'} del servidor requiere${remoteErrorCount === 1 ? '' : 'n'} corrección. ${firstRemoteMessage}`
        : localErrorCount > 0
        ? `${localErrorCount} fila${localErrorCount === 1 ? '' : 's'} requiere${localErrorCount === 1 ? '' : 'n'} corrección.`
        : 'No hay filas con errores.'}
    </Alert>
  )

  return (
    <DataGridShell
      ref={gridRef}
      density="normal"
      statusBar={feedbackBar}
      aria-label="Planilla de fardos"
      aria-describedby="reception-grid-feedback"
      columns={columns}
      rows={rows}
      rowKeyGetter={row => row.rowId}
      onRowsChange={nextRows => {
        if (!disabled) onRowsChange(nextRows)
      }}
      onCellPaste={(args, event) => {
        event.preventDefault()
        if (disabled) return args.row
        const column = args.column.key
        if (!isEditableColumn(column)) return args.row
        onPaste(args.row.rowId, column, event.clipboardData.getData('text/plain'))
        return args.row
      }}
      defaultColumnOptions={{ resizable: true }}
      style={{ minWidth: 810 }}
    />
  )
}

function editableColumns(feedback: ReadonlyMap<string, ReceptionRowFeedback>, errors: Readonly<Record<string, string>>, disabled: boolean): readonly Column<ReceptionGridRow>[] {
  return [
    editableColumn('materialType', 'Material', 150, feedback, errors, disabled),
    editableColumn('dtex', 'Dtex', 110, feedback, errors, disabled),
    editableColumn('grossWeightKg', 'Peso bruto (kg)', 155, feedback, errors, disabled),
    editableColumn('containerWeightKg', 'Tara (kg)', 130, feedback, errors, disabled),
  ]
}

function editableColumn(
  key: ReceptionEditableColumn,
  name: string,
  width: number,
  feedback: ReadonlyMap<string, ReceptionRowFeedback>,
  errors: Readonly<Record<string, string>>,
  disabled: boolean,
): Column<ReceptionGridRow> {
  return {
    key,
    name,
    width,
    editable: !disabled,
    renderEditCell: disabled ? undefined : renderTextEditor,
    renderCell: cell => <CellValue value={cell.row[key]} feedback={feedback.get(cell.row.rowId)} error={errors[`${cell.row.rowId}:${key}`]} />,
  }
}

function CellValue({ value, feedback, error }: { readonly value: string; readonly feedback?: ReceptionRowFeedback; readonly error?: string }) {
  const hasError = Boolean(error) || feedback?.status === 'partial' || feedback?.status === 'invalid'
  return <Text component="span" c={hasError ? 'red' : undefined} fw={feedback?.isDuplicate ? 700 : undefined} title={error} aria-label={error ? `Error: ${error}` : undefined}>{value || '—'}{error ? ' · Error' : ''}</Text>
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
