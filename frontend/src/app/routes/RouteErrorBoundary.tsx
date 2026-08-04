import { useRouteError, isRouteErrorResponse, useNavigate } from 'react-router'
import { Center, Stack, Title, Text, Button } from '@mantine/core'
import { IconAlertTriangle } from '@tabler/icons-react'

/**
 * Root-level error boundary for React Router.
 * Catches errors thrown in loaders, actions, or during route rendering.
 * Uses React Router's `useRouteError` instead of class-based error boundaries.
 */
export function RouteErrorBoundary() {
  const error = useRouteError()
  const navigate = useNavigate()

  let message = 'Ocurrió un error inesperado.'

  if (isRouteErrorResponse(error)) {
    message = error.status === 404
      ? 'La página que buscás no existe.'
      : `Error ${error.status}: ${error.statusText}`
  } else if (error instanceof Error) {
    message = import.meta.env.DEV ? error.message : 'Ocurrió un error inesperado.'
  }

  return (
    <Center h="100vh">
      <Stack align="center" gap="xs" px="md">
        <IconAlertTriangle
          size={40}
          style={{ color: 'var(--mantine-color-red-6)' }}
        />
        <Title order={2} size="h3">
          Algo salió mal
        </Title>
        <Text c="dimmed" size="sm" ta="center" maw={400}>
          {message}
        </Text>
        <Button variant="light" onClick={() => navigate('/', { replace: true })} mt="sm">
          Volver al inicio
        </Button>
      </Stack>
    </Center>
  )
}
