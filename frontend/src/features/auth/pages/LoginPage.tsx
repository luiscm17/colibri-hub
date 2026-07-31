import { useState } from 'react'
import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import {
  Paper,
  TextInput,
  PasswordInput,
  Button,
  Text,
  Alert,
} from '@mantine/core'
import { IconAlertCircle } from '@tabler/icons-react'
import { useAuth } from '../context/auth-context'
import { ProductLogo } from '@/common/components/ProductLogo'
import classes from '@/styles/components/LoginPage.module.css'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, isAuthenticated } = useAuth()

  const from = (location.state as { from?: { pathname: string } })?.from
    ?.pathname || '/warehouse/bales'

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (isAuthenticated) {
    return <Navigate to={from} replace />
  }

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)

    if (!username.trim() || !password.trim()) {
      setError('Completá ambos campos para iniciar sesión')
      return
    }

    setLoading(true)
    try {
      await login(username.trim(), password)
      navigate(from, { replace: true })
    } catch {
      setError('Credenciales inválidas. Intentalo de nuevo.')
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
          Ingresá a tu cuenta
        </Text>

        <form onSubmit={handleSubmit}>
          {error && (
            <Alert
              icon={<IconAlertCircle size={16} />}
              color="red"
              variant="light"
              mb="md"
              styles={{ body: { fontSize: 'var(--mantine-font-size-sm)' } }}
            >
              {error}
            </Alert>
          )}

          <TextInput
            label="Usuario"
            placeholder="Tu nombre de usuario"
            value={username}
            onChange={(e) => setUsername(e.currentTarget.value)}
            autoFocus
            mb="sm"
          />

          <PasswordInput
            label="Contraseña"
            placeholder="Tu contraseña"
            value={password}
            onChange={(e) => setPassword(e.currentTarget.value)}
            mb="lg"
          />

          <Button type="submit" fullWidth loading={loading}>
            Ingresar
          </Button>
        </form>
      </Paper>
    </div>
  )
}
