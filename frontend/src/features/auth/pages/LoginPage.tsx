import { useRef, useState } from 'react'
import { Paper, TextInput, PasswordInput, Button, Text, Alert } from '@mantine/core'
import { IconAlertCircle } from '@tabler/icons-react'
import { useAuth } from '../context/auth-context'
import { useLocation, useNavigate } from 'react-router'
import { getSafeReturnIntent } from './returnIntent'
import { ProductLogo } from '@/common/components/ProductLogo'
import classes from './AuthPages.module.css'

export default function LoginPage() {
  const { login } = useAuth()
  const { search } = useLocation()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const submissionRef = useRef(0)
  const errorRef = useRef<HTMLDivElement>(null)

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault()
    const submission = ++submissionRef.current
    setError(null)

    if (!email.trim() || !password.trim()) {
      setError('Complete both fields to sign in.')
      return
    }

    setLoading(true)
    try {
      await login(email.trim(), password)
      if (submission === submissionRef.current) navigate(getSafeReturnIntent(new URLSearchParams(search).get('returnTo')) ?? '/', { replace: true })
    } catch {
      if (submission !== submissionRef.current) return
      setPassword('')
      setError('Invalid email or password. Please try again.')
      queueMicrotask(() => errorRef.current?.focus())
    } finally {
      if (submission === submissionRef.current) setLoading(false)
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
            <Alert ref={errorRef} tabIndex={-1}
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
