import { Alert } from '@mantine/core'

const colorMap = {
  error: 'red',
  success: 'green',
  info: 'blue',
} as const

interface DataGridStatusBarProps {
  /** Feedback message */
  message: string
  /** Semantic type controlling color and ARIA role */
  type: 'error' | 'success' | 'info'
  /** Optional count to include in message (e.g., "3 filas requieren corrección") */
  count?: number
}

export function DataGridStatusBar({ message, type, count }: DataGridStatusBarProps) {
  const displayMessage =
    type === 'error' && count != null && count > 0 ? `${count} ${message}` : message

  return (
    <Alert
      color={colorMap[type]}
      role={type === 'error' ? 'alert' : 'status'}
      aria-live={type === 'error' ? undefined : 'polite'}
      mt="sm"
    >
      {displayMessage}
    </Alert>
  )
}
