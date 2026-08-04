import { useState } from 'react'
import { Paper, TextInput, PasswordInput, Button, Text, Alert } from '@mantine/core'
import { IconAlertCircle } from '@tabler/icons-react'
import { useAuth } from '../context/auth-context'
import { ProductLogo } from '@/common/components/ProductLogo'
import classes from '@/styles/components/LoginPage.module.css'

export default function LoginPage() {
  const { login } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)

    if (!email.trim() || !password.trim()) {
      setError('Complete both fields to sign in.')
      return
    }

    setLoading(true)
    try {
      await login(email.trim(), password)
    } catch {
      setPassword('')
      setError('Invalid email or password. Please try again.')
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
          Sign in to your account
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

          <TextInput
            label="Email"
            placeholder="your@email.com"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.currentTarget.value)}
            autoFocus
            mb="sm"
          />

          <PasswordInput
            label="Password"
            placeholder="Your password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.currentTarget.value)}
            mb="lg"
          />

          <Button type="submit" fullWidth loading={loading}>
            Sign in
          </Button>
        </form>
      </Paper>
    </div>
  )
}
