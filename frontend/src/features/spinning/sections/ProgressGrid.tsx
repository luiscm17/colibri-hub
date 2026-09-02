import { Alert, Text } from '@mantine/core'
import { useMemo } from 'react'
import { renderTextEditor, type Column } from 'react-data-grid'
import 'react-data-grid/lib/styles.css'
import { DataGridShell } from '@/common/grid/DataGridShell'
import type { ProductionDischargeCatalog, RemoteState } from '../integration/contracts'
import { replaceProgressRows, type ProgressDraft, type ProgressRow } from './progressModel'

interface ProgressGridProps {
  readonly catalog: RemoteState<ProductionDischargeCatalog>
  readonly draft: ProgressDraft
  readonly onDraftChange: (draft: ProgressDraft) => void
}

export function ProgressGrid({ catalog, draft, onDraftChange }: ProgressGridProps) {
  const columns = useMemo<readonly Column<ProgressRow>[]>(() => [
    readOnlyColumn('number', 'No', 70),
    readOnlyColumn('machine', 'Máquina', 150),
    readOnlyColumn('yarnTitle', 'Título', 120),
    readOnlyColumn('type', 'Tipo', 120),
    editableColumn('grossWeightG', 'P. Bruto [g]', 140),
    editableColumn('tareWeightG', 'Tara [g]', 120),
    editableColumn('spindleCount', 'No. Husos', 120),
    editableColumn('inputWeightKg', 'Peso Entrada [kg]', 170),
    editableColumn('outputWeightKg', 'Peso Salida [kg]', 160),
    editableColumn('dischargeWeightKg', 'Peso Descarga [kg]', 180),
    editableColumn('hours', 'Horas [hr]', 120),
    editableColumn('observations', 'Observaciones', 220),
  ], [])
  return <DataGridShell
    toolbar={<Text fw={600}>Avance</Text>}
    statusBar={<Alert role="status" color="blue">{catalog.status === 'populated' ? 'Las filas del roster y las proyecciones son suministradas por el servicio.' : 'El roster de avance no está disponible hasta que el servicio esté disponible.'}</Alert>}
    aria-label="Progress roster grid"
    columns={columns}
    rows={draft.rows}
    rowKeyGetter={row => row.rowId}
    onRowsChange={rows => onDraftChange(replaceProgressRows(draft, rows))}
    defaultColumnOptions={{ resizable: true }}
    style={{ minWidth: 1810 }}
  />
}

type ProgressColumn = 'grossWeightG' | 'tareWeightG' | 'spindleCount' | 'inputWeightKg' | 'outputWeightKg' | 'dischargeWeightKg' | 'hours' | 'observations'

function readOnlyColumn(key: keyof ProgressRow, name: string, width: number): Column<ProgressRow> {
  return { key, name, width, renderCell: cell => <Text component="span">{String(cell.row[key]) || '—'}</Text> }
}

function editableColumn(key: ProgressColumn, name: string, width: number): Column<ProgressRow> {
  return { key, name, width, editable: true, renderEditCell: renderTextEditor, renderCell: cell => <Text component="span">{cell.row[key] || '—'}</Text> }
}
