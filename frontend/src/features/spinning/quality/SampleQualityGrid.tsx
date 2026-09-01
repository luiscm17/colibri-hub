import { Alert, Group, Text } from '@mantine/core'
import { useMemo } from 'react'
import { renderTextEditor, type Column } from 'react-data-grid'
import 'react-data-grid/lib/styles.css'
import { DataGridShell } from '@/common/grid/DataGridShell'
import type { QualityMeasurement } from '../integration/contracts'
import { sampleMeasurementValidationError, sampleQualityRows, type SampleQualityRow } from './qualityModel'

interface SampleQualityGridProps {
  readonly measurements: readonly QualityMeasurement[]
  readonly values: Readonly<Record<string, string>>
  readonly onValueChange: (measurementId: string, value: string) => void
}

export function SampleQualityGrid({ measurements, values, onValueChange }: SampleQualityGridProps) {
  const rows = useMemo<readonly SampleQualityRow[]>(
    () => sampleQualityRows(measurements, values),
    [measurements, values],
  )
  const invalidCount = rows.filter(row => sampleMeasurementValidationError(row) !== undefined).length
  const columns = useMemo<readonly Column<SampleQualityRow>[]>(() => [
    { key: 'label', name: 'Medición', width: 240, frozen: 'start' },
    { key: 'unit', name: 'Unidad', width: 110 },
    { key: 'value', name: 'Valor de muestra', width: 170, editable: true, renderEditCell: renderTextEditor, renderCell: cell => <ValueCell row={cell.row} /> },
    { key: 'serverResult', name: 'Resultado del servidor', width: 210, renderCell: cell => <Text component="span">{cell.row.serverResult ?? 'Pendiente de confirmación del servidor'}</Text> },
    { key: 'toleranceStatus', name: 'Tolerancia', width: 190, renderCell: cell => <ToleranceCell status={cell.row.toleranceStatus} /> },
  ], [])

  return <DataGridShell
    toolbar={<Group justify="space-between" mb="sm"><Text fw={600}>Muestra: {measurements.length} mediciones configuradas</Text></Group>}
    statusBar={<Alert id="sample-quality-grid-feedback" color={invalidCount ? 'red' : 'blue'} role={invalidCount ? 'alert' : 'status'}>{invalidCount ? `${invalidCount} medición${invalidCount === 1 ? '' : 'es'} requiere corrección.` : 'Los resultados y la tolerancia son confirmados únicamente por el servidor.'}</Alert>}
    aria-label="Planilla de muestra de calidad"
    aria-describedby="sample-quality-grid-feedback"
    columns={columns}
    rows={rows}
    rowKeyGetter={row => row.id}
    onRowsChange={nextRows => nextRows.forEach(row => {
      if ((values[row.id] ?? '') !== row.value) onValueChange(row.id, row.value)
    })}
    defaultColumnOptions={{ resizable: true }}
    style={{ minWidth: 920 }}
  />
}

function ValueCell({ row }: { readonly row: SampleQualityRow }) {
  const error = sampleMeasurementValidationError(row)
  return <Text component="span" c={error ? 'red' : undefined} title={error} aria-label={error ? `Error: ${error}` : undefined}>{row.value || '—'}{error ? ' · Error' : ''}</Text>
}

function ToleranceCell({ status }: { readonly status: QualityMeasurement['toleranceStatus'] }) {
  const detail = {
    pending: { label: 'Pendiente', color: 'dimmed' },
    'within-tolerance': { label: 'Dentro de tolerancia', color: 'green' },
    'out-of-tolerance': { label: 'Fuera de tolerancia', color: 'red' },
    unavailable: { label: 'No disponible', color: 'dimmed' },
  }[status]
  return <Text component="span" c={detail.color}>{detail.label}</Text>
}
