import { Navigate } from 'react-router-dom'
import { Center, Loader, Stack, Text, Button } from '@mantine/core'
import { useAuth } from '../context/auth-context'

interface AuthenticationBoundaryProps {
  children: React.ReactNode
}

export function AuthenticationBoundary({ children }: AuthenticationBoundaryProps) {
  const { authState, revalidate } = useAuth()

  switch (authState.status) {
    case 'initializing':
      return (
        <Center h="100vh">
          <Loader />
        </Center>
      )

    case 'unauthenticated':
      return <Navigate to="/login" replace />

    case 'unavailable':
      return (
        <Center h="100vh">
          <Stack align="center" gap="md">
            <Text c="dimmed">The service is temporarily unavailable.</Text>
            {authState.retryable && (
              <Button variant="light" onClick={() => void revalidate()}>
                Retry
              </Button>
            )}
          </Stack>
        </Center>
      )

    case 'password-change-required':
    case 'authenticated':
      return <>{children}</>
  }
}
