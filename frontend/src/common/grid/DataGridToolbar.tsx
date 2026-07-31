import { Group } from '@mantine/core'
import type { ReactNode } from 'react'

interface DataGridToolbarProps {
  /** Left-aligned slot (row count, labels) */
  left?: ReactNode
  /** Right-aligned slot (action buttons, search) */
  right?: ReactNode
}

export function DataGridToolbar({ left, right }: DataGridToolbarProps) {
  return (
    <Group justify="space-between" mb="sm">
      {left}
      {right}
    </Group>
  )
}
