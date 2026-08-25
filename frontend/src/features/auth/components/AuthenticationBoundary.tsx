import { Navigate, useLocation } from 'react-router'
import { Center, Loader, Stack, Text, Button } from '@mantine/core'
import { useAuth } from '../context/auth-context'

interface AuthenticationBoundaryProps {
  children: React.ReactNode
}

export function AuthenticationBoundary({ children }: AuthenticationBoundaryProps) {
  const { authState, revalidate } = useAuth()
  const location = useLocation()

  switch (authState.status) {
    case 'initializing':
      return (
        <Center h="100vh">
          <Loader />
        </Center>
      )

    case 'unauthenticated': {
      const returnTo = `${location.pathname}${location.search}${location.hash}`
      return <Navigate to={`/login?returnTo=${encodeURIComponent(returnTo)}`} replace />
    }

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
