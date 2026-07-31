import { Center, Stack, Text, ThemeIcon } from '@mantine/core'
import { IconHammer } from '@tabler/icons-react'

interface ComingSoonProps {
  /** Optional feature name shown as heading */
  feature?: string
}

/**
 * Placeholder for routes whose feature has not been implemented yet.
 */
export function ComingSoon({ feature }: ComingSoonProps) {
  return (
    <Center h={400}>
      <Stack align="center" gap="xs">
        <ThemeIcon variant="light" size="xl" radius="xl" color="brand-cyan">
          <IconHammer size={24} />
        </ThemeIcon>
        {feature && (
          <Text fw={600} size="lg">
            {feature}
          </Text>
        )}
        <Text c="dimmed" size="sm" ta="center" maw={320}>
          Esta sección se encuentra en desarrollo.
        </Text>
      </Stack>
    </Center>
  )
}
