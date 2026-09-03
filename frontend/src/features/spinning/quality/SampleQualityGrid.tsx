import { Group, Text } from '@mantine/core'
import { useMemo } from 'react'
import { renderTextEditor, type Column } from 'react-data-grid'
import 'react-data-grid/lib/styles.css'
import { DataGridShell } from '@/common/grid/DataGridShell'
import { DataGridStatusBar } from '@/common/grid/DataGridStatusBar'
import type { QualitySampleProfile, QualitySampleRecord } from '../integration/contracts'

interface SampleQualityGridProps {
  readonly profile: QualitySampleProfile
  readonly records: readonly QualitySampleRecord[]
  readonly onRecordsChange: (records: readonly QualitySampleRecord[]) => void
}

export function SampleQualityGrid({ profile, records, onRecordsChange }: SampleQualityGridProps) {
  const columns = useMemo<readonly Column<QualitySampleRecord>[]>(() => [
    { key: 'number', name: 'No', width: 70, frozen: 'start' },
    { key: 'section', name: 'Sección', width: 180, frozen: 'start' },
    { key: 'machine', name: 'Máquina', width: 140, frozen: 'start' },
    { key: 'type', name: 'Tipo', width: 100, frozen: 'start' },
    { key: 'yarnTitle', name: 'Título', width: 110, frozen: 'start' },
    ...Array.from({ length: profile.sampleCount }, (_, index): Column<QualitySampleRecord> => ({ key: `sample-${index}`, name: `Muestra ${index + 1}`, width: 120, editable: true, renderEditCell: renderTextEditor, renderCell: cell => <Text component="span">{cell.row.samples[index] || '—'}</Text> })),
    ...profile.resultColumns.map((column): Column<QualitySampleRecord> => ({ key: `projection-${column.id}`, name: column.label, width: 135, renderCell: cell => <Text component="span">{cell.row.projections[column.id] ?? 'Pendiente'}</Text> })),
    ...(profile.supportsObservations ? [{ key: 'observations', name: 'Observaciones', width: 220, editable: true, renderEditCell: renderTextEditor, renderCell: (cell: { row: QualitySampleRecord }) => <Text component="span">{cell.row.observations || '—'}</Text> }] : []),
  ], [profile])

  return <DataGridShell
    toolbar={<Group justify="space-between" mb="sm"><Text fw={600}>Registros de muestra: {records.length}</Text></Group>}
    statusBar={<DataGridStatusBar type="info" message="Las proyecciones son confirmadas únicamente por el servidor." />}
    aria-label="Planilla de muestra de calidad"
    columns={columns}
    rows={records}
    rowKeyGetter={row => row.id}
    onRowsChange={nextRows => onRecordsChange(nextRows.map(row => ({
      ...row,
      samples: Array.from({ length: profile.sampleCount }, (_, index) => {
        const editedValue = (row as Record<string, unknown>)[`sample-${index}`]
        return typeof editedValue === 'string' ? editedValue : row.samples[index] ?? ''
      }),
    })))}
    defaultColumnOptions={{ resizable: true }}
    style={{ minWidth: 2100 }}
  />
}
