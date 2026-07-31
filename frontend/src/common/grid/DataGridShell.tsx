import { Box, Paper } from '@mantine/core'
import { forwardRef } from 'react'
import { DataGrid, type DataGridProps, type DataGridHandle } from 'react-data-grid'
import type { ReactNode } from 'react'
import { DataGridThemeWrapper } from './DataGridThemeWrapper'
import classes from './DataGridThemeWrapper.module.css'

type Density = 'compact' | 'normal'

interface DataGridShellProps<R, SR = unknown, K extends React.Key = React.Key>
  extends DataGridProps<R, SR, K> {
  /** Density preset controlling row height and cell padding */
  density?: Density
  /** Optional toolbar rendered above the grid */
  toolbar?: ReactNode
  /** Optional status bar rendered below the grid */
  statusBar?: ReactNode
}

function DataGridShellInner<R, SR = unknown, K extends React.Key = React.Key>(
  { density = 'normal', toolbar, statusBar, ...gridProps }: DataGridShellProps<R, SR, K>,
  ref: React.Ref<DataGridHandle>,
) {
  const densityClass = classes[density]

  return (
    <Paper withBorder p="md">
      {toolbar}
      <DataGridThemeWrapper className={densityClass}>
        <Box style={{ overflowX: 'auto' }}>
          <DataGrid {...gridProps} ref={ref} />
        </Box>
      </DataGridThemeWrapper>
      {statusBar}
    </Paper>
  )
}

export const DataGridShell = forwardRef(DataGridShellInner) as <
  R,
  SR = unknown,
  K extends React.Key = React.Key,
>(
  props: DataGridShellProps<R, SR, K> & { ref?: React.Ref<DataGridHandle> },
) => React.ReactElement | null

