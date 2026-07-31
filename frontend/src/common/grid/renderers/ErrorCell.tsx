import type { ReactNode } from 'react'
import { Tooltip } from '@mantine/core'

interface ErrorCellProps {
  children: ReactNode
  error?: string
}

export function ErrorCell({ children, error }: ErrorCellProps) {
  if (!error) {
    return <>{children}</>
  }

  return (
    <Tooltip label={error}>
      <div
        aria-invalid="true"
        style={{
          outline: '2px solid var(--mantine-color-red-6)',
          outlineOffset: -2,
          borderRadius: 'var(--mantine-radius-sm)',
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        {children}
      </div>
    </Tooltip>
  )
}
