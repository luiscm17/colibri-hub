import { Button, Center, Stack, Text } from '@mantine/core'
import { IconInboxOff } from '@tabler/icons-react'

interface DataGridEmptyStateProps {
  /** Message shown when grid is empty */
  message?: string
  /** Optional action button */
  action?: { label: string; onClick: () => void }
}

export function DataGridEmptyState({
  message = 'Sin datos para mostrar',
  action,
}: DataGridEmptyStateProps) {
  return (
    <Center py="xl">
      <Stack align="center" gap="xs">
        <IconInboxOff
          size={40}
          style={{ color: 'var(--mantine-color-dimmed)' }}
        />
        <Text size="sm" c="dimmed">
          {message}
        </Text>
        {action && (
          <Button variant="light" size="xs" mt="sm" onClick={action.onClick}>
            {action.label}
          </Button>
        )}
      </Stack>
    </Center>
  )
}
