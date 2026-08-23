import { useState } from 'react'
import { Paper, PasswordInput, Button, Text, Alert, Stack } from '@mantine/core'
import { IconAlertCircle } from '@tabler/icons-react'
import { useAuth } from '../context/auth-context'
import { submitPasswordChange } from '../api/authApi'
import { isApiError } from '@/api/httpError'
import { ProductLogo } from '@/common/components/ProductLogo'
import classes from './AuthPages.module.css'

export default function MandatoryPasswordChangePage() {
  const { logout } = useAuth()

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)

  const clearPasswords = () => {
    setCurrentPassword('')
    setNewPassword('')
    setConfirmPassword('')
  }

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)
    setFieldErrors({})

    if (!currentPassword || !newPassword || !confirmPassword) {
      setError('All fields are required.')
      return
    }

    if (newPassword !== confirmPassword) {
      setFieldErrors({ confirmPassword: 'Passwords do not match.' })
      return
    }

    setLoading(true)
    try {
      await submitPasswordChange(currentPassword, newPassword)
      clearPasswords()
      await logout()
    } catch (err) {
      clearPasswords()

      if (isApiError(err)) {
        if (err.code === 'replacement_password_must_differ') {
          setFieldErrors({ newPassword: 'The new password must be different from the current one.' })
          return
        }
        if (err.code === 'weak_password') {
          setFieldErrors({ newPassword: 'The password does not meet security requirements.' })
          return
        }
        if (err.status === 401) {
          setError('Current password is incorrect.')
          return
        }
        setError(err.message)
        return
      }
      setError('An unexpected error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={classes.wrapper}>
      <Paper className={classes.card} p="xl" radius="md" withBorder>
        <div className={classes.brand}>
          <ProductLogo variant="full" size="lg" />
        </div>
        <Text c="dimmed" size="sm" ta="center" mb="lg">
          You must change your provisional password before continuing.
        </Text>

        <form onSubmit={handleSubmit}>
          {error && (
            <Alert
              icon={<IconAlertCircle size={16} />}
              color="red"
              variant="light"
              mb="md"
              role="alert"
              styles={{ body: { fontSize: 'var(--mantine-font-size-sm)' } }}
            >
              {error}
            </Alert>
          )}

          <Stack gap="sm">
            <PasswordInput
              label="Current password"
              placeholder="Your provisional password"
              autoComplete="current-password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.currentTarget.value)}
              error={fieldErrors.currentPassword}
              autoFocus
            />

            <PasswordInput
              label="New password"
              placeholder="Choose a new password"
              autoComplete="new-password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.currentTarget.value)}
              error={fieldErrors.newPassword}
            />

            <PasswordInput
              label="Confirm new password"
              placeholder="Repeat the new password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.currentTarget.value)}
              error={fieldErrors.confirmPassword}
            />
          </Stack>

          <Button type="submit" fullWidth loading={loading} mt="lg">
            Change password
          </Button>

          <Button
            variant="subtle"
            color="gray"
            fullWidth
            mt="xs"
            onClick={() => void logout()}
            disabled={loading}
          >
            Sign out instead
          </Button>
        </form>
      </Paper>
    </div>
  )
}
