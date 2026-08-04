import {
  Avatar,
  Card,
  Group,
  Stack,
  Text,
} from '@mantine/core'
import { useAuth } from '@/features/auth'
import { PageHeader } from '@/common/components/PageHeader'

export default function ProfilePage() {
  const { account } = useAuth()

  if (!account) return null

  return (
    <Stack gap="lg">
      <PageHeader title="Mi perfil" />

      {/* Avatar + name */}
      <Card withBorder radius="md" padding="lg">
        <Group gap="lg" wrap="nowrap">
          <Avatar
            size={80}
            color="brand-cyan"
            radius={100}
            name={account.displayName}
          >
            {account.initials}
          </Avatar>

          <Stack gap={4}>
            <Text size="xl" fw={600}>
              {account.displayName}
            </Text>
            <Text size="sm" c="dimmed">
              {account.email}
            </Text>
          </Stack>
        </Group>
      </Card>

      {/* Account details */}
      <Card withBorder radius="md" padding="lg">
        <Text fw={500} mb="md">
          Account details
        </Text>

        <Stack gap="xs">
          <div>
            <Text size="sm" c="dimmed">Email</Text>
            <Text>{account.email}</Text>
          </div>
          <div>
            <Text size="sm" c="dimmed">Display name</Text>
            <Text>{account.displayName}</Text>
          </div>
        </Stack>
      </Card>
    </Stack>
  )
}
