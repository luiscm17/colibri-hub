import { Badge, Tooltip } from '@mantine/core'

interface CellFeedbackProps {
  message?: string
  status?: 'error' | 'success'
}

export function CellFeedback({ message, status = 'error' }: CellFeedbackProps) {
  if (!message) return null

  return (
    <Tooltip label={message}>
      <Badge color={status === 'error' ? 'red' : 'green'} variant="light" aria-label={message}>
        {status === 'error' ? 'Error' : 'Complete'}
      </Badge>
    </Tooltip>
  )
}
