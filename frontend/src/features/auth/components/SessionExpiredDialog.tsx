import { Modal, Text, Button, Stack } from '@mantine/core'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/auth-context'

export function SessionExpiredDialog() {
  const { authState } = useAuth()
  const navigate = useNavigate()

  const isExpired =
    authState.status === 'unauthenticated' && authState.reason === 'expired'

  return (
    <Modal
      opened={isExpired}
      onClose={() => navigate('/login', { replace: true })}
      title="Session expired"
      centered
      withCloseButton={false}
      closeOnClickOutside={false}
      closeOnEscape={false}
    >
      <Stack gap="md">
        <Text size="sm">
          Your session has ended. Please sign in again to continue.
        </Text>
        <Button
          fullWidth
          onClick={() => navigate('/login', { replace: true })}
        >
          Return to login
        </Button>
      </Stack>
    </Modal>
  )
}
