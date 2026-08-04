import { Center, Stack, Title, Text, Button } from '@mantine/core'
import { useNavigate } from 'react-router'

export default function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <Center h="100%">
      <Stack align="center" gap="xs">
        <Title order={1} size="48px" c="dimmed" style={{ fontWeight: 300 }}>
          404
        </Title>
        <Text c="dimmed" mb="md">
          Esta página no existe
        </Text>
        <Button variant="light" onClick={() => navigate('/')}>
          Volver al inicio
        </Button>
      </Stack>
    </Center>
  )
}
