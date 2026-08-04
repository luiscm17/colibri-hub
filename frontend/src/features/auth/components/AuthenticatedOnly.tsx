import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/auth-context'

interface AuthenticatedOnlyProps {
  children: React.ReactNode
}

export function AuthenticatedOnly({ children }: AuthenticatedOnlyProps) {
  const { authState } = useAuth()

  if (authState.status === 'authenticated') {
    return <>{children}</>
  }

  if (authState.status === 'password-change-required') {
    return <Navigate to="/password-change" replace />
  }

  return <Navigate to="/login" replace />
}
