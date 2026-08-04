import { Navigate } from 'react-router'
import { useAuth } from '../context/auth-context'

interface UnauthenticatedOnlyProps {
  children: React.ReactNode
}

export function UnauthenticatedOnly({ children }: UnauthenticatedOnlyProps) {
  const { authState } = useAuth()

  if (authState.status === 'authenticated') {
    return <Navigate to="/" replace />
  }

  if (authState.status === 'password-change-required') {
    return <Navigate to="/password-change" replace />
  }

  return <>{children}</>
}
