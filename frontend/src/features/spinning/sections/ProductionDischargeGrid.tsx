import { Alert, Text } from '@mantine/core'
import { useMemo } from 'react'
import 'react-data-grid/lib/styles.css'
import { DataGridShell } from '@/common/grid/DataGridShell'
import type { ProductionDischargeCatalog, RemoteState } from '../integration/contracts'
import type { SpinningWorkspace } from '../workspaces'
import { type DischargeColumn, type ProductionDischargeDraft, type ProductionDischargeRow } from './dischargeModel'
import { productionDischargeColumns } from './productionDischargeColumns'

interface ProductionDischargeGridProps {
  readonly workspace: SpinningWorkspace
  readonly catalog: RemoteState<ProductionDischargeCatalog>
  readonly draft: ProductionDischargeDraft
  readonly onRowsChange: (rows: readonly ProductionDischargeRow[]) => void
  readonly onPaste: (rowId: string, column: DischargeColumn, text: string) => void
}

export function ProductionDischargeGrid({ workspace, catalog, draft, onRowsChange, onPaste }: ProductionDischargeGridProps) {
  const columns = useMemo(() => productionDischargeColumns(workspace), [workspace])

  const rosterAvailable = catalog.status === 'populated'
  return <DataGridShell
    toolbar={<Text fw={600}>Descarga de producción</Text>}
    statusBar={<Alert role="status" color="blue">{rosterAvailable ? 'Las filas del roster y las proyecciones son suministradas por el servicio.' : 'El roster de producción no está disponible hasta que el servicio esté disponible.'}</Alert>}
    aria-label="Production roster grid"
    columns={columns}
    rows={draft.rows}
    rowKeyGetter={row => row.rowId}
    onRowsChange={onRowsChange}
    onCellPaste={(args, event) => { event.preventDefault(); if (isDischargeColumn(args.column.key)) onPaste(args.row.rowId, args.column.key, event.clipboardData.getData('text/plain')); return args.row }}
    defaultColumnOptions={{ resizable: true }}
    style={{ minWidth: workspace === 'preparation' ? 1490 : workspace === 'skeining' ? 1320 : 1700 }}
  />
}

function isDischargeColumn(value: string): value is DischargeColumn {
  return ['grossWeightKg', 'spindleCount', 'packageTareWeightG', 'cartWeightKg', 'skeinQuantity', 'skeinUnitWeightG', 'operator', 'observations'].includes(value)
}
