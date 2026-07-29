import { useState, useCallback, useMemo, type ReactNode } from 'react'
import { AuthContext } from './auth-context'

export interface User {
  id: string
  username: string
  name: string
  initials: string
  /**
   * Resource types a los que el usuario tiene acceso `read`.
   * Vacío/indefinido = todos visibles (fallback mientras el backend
   * de RBAC no está conectado).
   */
  allowedResources: string[]
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)

  const isResourceAllowed = useCallback(
    (resourceType: string) => {
      if (!user || user.allowedResources.length === 0) return true
      return user.allowedResources.includes(resourceType)
    },
    [user],
  )

  const login = useCallback(async (username: string, _password: string) => {
    // Mock login — en producción reemplazar con llamada a API
    void _password
    await new Promise((r) => setTimeout(r, 400))

    // TODO: el backend devolverá allowedResources basado en roles + scopes
    setUser({
      id: '1',
      username,
      name: username.charAt(0).toUpperCase() + username.slice(1),
      initials: username.charAt(0).toUpperCase(),
      allowedResources: [], // vacío = acceso total (sin backend aún)
    })
  }, [])

  const logout = useCallback(() => {
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: user !== null,
      isResourceAllowed,
      login,
      logout,
    }),
    [user, isResourceAllowed, login, logout],
  )

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

