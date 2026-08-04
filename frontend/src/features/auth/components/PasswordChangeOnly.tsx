import { Navigate } from 'react-router'
import { useAuth } from '../context/auth-context'

interface PasswordChangeOnlyProps {
  children: React.ReactNode
}

export function PasswordChangeOnly({ children }: PasswordChangeOnlyProps) {
  const { authState } = useAuth()

  if (authState.status === 'password-change-required') {
    return <>{children}</>
  }

  if (authState.status === 'authenticated') {
    return <Navigate to="/" replace />
  }

  return <Navigate to="/login" replace />
}
