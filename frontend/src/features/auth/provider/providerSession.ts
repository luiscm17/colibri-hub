import { identityClient } from './identityClient'

export type AuthStateChangeCallback = (
  event: string,
  session: unknown,
) => void

export async function signIn(
  email: string,
  password: string,
): Promise<{ success: boolean; error: string | null }> {
  const { error } = await identityClient.auth.signInWithPassword({ email, password })
  if (error) {
    return { success: false, error: error.message }
  }
  return { success: true, error: null }
}

export async function signOut(): Promise<void> {
  await identityClient.auth.signOut({ scope: 'local' })
}

export async function hasSession(): Promise<boolean> {
  const { data } = await identityClient.auth.getSession()
  return data.session !== null
}

export async function getAccessToken(): Promise<string | null> {
  const { data } = await identityClient.auth.getSession()
  return data.session?.access_token ?? null
}

export function onAuthStateChange(callback: AuthStateChangeCallback) {
  const { data } = identityClient.auth.onAuthStateChange(callback)
  return data.subscription
}
