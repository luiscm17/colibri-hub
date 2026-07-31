import type { ReactNode } from 'react'
import { Group } from '@mantine/core'
import classes from '@/styles/components/TopBar.module.css'

interface TopBarProps {
  left?: ReactNode
  center?: ReactNode
  right?: ReactNode
}

/**
 * Estructura pura del header. No contiene lógica de negocio.
 * Los controles se componen desde AppLayout vía slots.
 */
export function TopBar({ left, center, right }: TopBarProps) {
  return (
    <Group h="100%" px="md" justify="space-between" wrap="nowrap" className={classes.root}>
      <Group gap="xs" wrap="nowrap">
        {left}
      </Group>
      <Group
        gap="xs"
        wrap="nowrap"
        style={{ flex: 1, justifyContent: 'center' }}
      >
        {center}
      </Group>
      <Group gap="sm" wrap="nowrap">
        {right}
      </Group>
    </Group>
  )
}
