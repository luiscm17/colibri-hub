import { Text } from '@mantine/core'
import { renderTextEditor, type Column } from 'react-data-grid'
import type { SpinningWorkspace } from '../workspaces'
import { productionRowState, type DischargeColumn, type ProductionDischargeRow, type ProductionRowState } from './dischargeModel'

export function productionDischargeColumns(workspace: SpinningWorkspace): readonly Column<ProductionDischargeRow>[] {
  const isSkeining = workspace === 'skeining'
  const isPreparation = workspace === 'preparation'
  return [
    readOnlyColumn('number', 'No', 70),
    readOnlyColumn('machine', 'Máquina', 150),
    readOnlyColumn('type', 'Tipo', 120),
    ...(isPreparation ? [
      editableColumn('grossWeightKg', 'Peso Bruto', 160),
      editableColumn('spindleCount', 'Núm. Mechas', 140),
      readOnlyColumn('defaultPackageTareWeightKg', 'Peso Cañete [kg]', 190),
      readOnlyColumn('defaultCartWeightKg', 'Peso Tacho [kg]', 180),
      projectionColumn('netWeightKg', 'Peso Neto [kg]', 160),
    ] : isSkeining ? [
      readOnlyColumn('yarnTitle', 'Título', 120),
      editableColumn('skeinQuantity', 'Cantidad de Madejas', 170),
      editableColumn('skeinUnitWeightG', 'Peso/u Madeja [g]', 170),
      projectionColumn('netWeightKg', 'Peso Neto [kg]', 160),
      editableColumn('operator', 'Operador', 150),
    ] : [
      readOnlyColumn('yarnTitle', 'Título', 120),
      editableColumn('grossWeightKg', 'Peso Bruto [kg]', 160),
      editableColumn('spindleCount', 'No. Husos', 120),
      editableColumn('packageTareWeightG', 'Peso Cañete/Canilla [g]', 210),
      editableColumn('cartWeightKg', 'Peso Tacho/Carro [kg]', 190),
      projectionColumn('netWeightKg', 'Peso Neto [kg]', 160),
    ]),
    editableColumn('observations', 'Observaciones', 220),
    stateColumn(workspace),
  ]
}

function readOnlyColumn(key: keyof ProductionDischargeRow, name: string, width: number): Column<ProductionDischargeRow> {
  return { key, name, width, renderCell: cell => <Text component="span">{String(cell.row[key]) || '—'}</Text> }
}

function editableColumn(key: DischargeColumn, name: string, width: number): Column<ProductionDischargeRow> {
  return { key, name, width, editable: true, renderEditCell: renderTextEditor, renderCell: cell => <Text component="span">{cell.row[key] || '—'}</Text> }
}

function projectionColumn(key: string, name: string, width: number): Column<ProductionDischargeRow> {
  return { key, name, width, renderCell: cell => <Text component="span">{cell.row.projections[key] ?? '—'}</Text> }
}

function stateColumn(workspace: SpinningWorkspace): Column<ProductionDischargeRow> {
  return { key: 'entryState', name: 'Estado local', width: 190, renderCell: cell => <Text component="span">{stateLabels[productionRowState(cell.row, workspace)]}</Text> }
}

const stateLabels: Readonly<Record<ProductionRowState, string>> = {
  pending: 'Pendiente',
  invalid: 'Requiere corrección',
  complete: 'Sintaxis completa',
  'acknowledged-no-production': 'Sin producción indicada',
}
