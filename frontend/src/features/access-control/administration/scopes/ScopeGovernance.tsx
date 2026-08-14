import { Alert, Button, Group, Stack, Text, TextInput } from '@mantine/core'
import { useEffect, useRef, useState } from 'react'
import { httpJson } from '@/api/httpClient'
import { isApiError } from '@/api/httpError'
import { scopeRegistrationRequest, scopeStatusRequest, unregisteredDefinitions } from './history'

type RefreshScopes = () => Promise<void> | void

export function ScopeRegistrationPanel({ refreshScopes }: { refreshScopes: RefreshScopes }) {
  const [definitions, setDefinitions] = useState<Array<{ definitionKey: string; isRegistered: boolean }>>([])
  const [reason, setReason] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const mounted = useRef(true)
  const mutationInFlight = useRef(false)

  useEffect(() => {
    mounted.current = true
    void httpJson<Array<{ definition_key: string; is_registered: boolean }>>('/access/scope-definitions', { recoverAccessDenied: true })
      .then((result) => { if (mounted.current) setDefinitions(result.map(({ definition_key, is_registered }) => ({ definitionKey: definition_key, isRegistered: is_registered }))) })
      .catch((error: unknown) => { if (mounted.current && (!isApiError(error) || error.kind !== 'aborted')) { setDefinitions([]); setMessage(isApiError(error) ? error.message : 'Scope definitions are unavailable.') } })
    return () => { mounted.current = false }
  }, [])

  async function register(definitionKey: string) {
    const normalizedReason = reason.trim()
    if (!normalizedReason || mutationInFlight.current) return
    mutationInFlight.current = true
    setPending(true)
    setMessage(null)
    try {
      const request = scopeRegistrationRequest(definitionKey, normalizedReason)
      await httpJson(request.path, { method: request.method, body: request.body, recoverAccessDenied: true })
      if (!mounted.current) return
      setDefinitions((current) => current.map((definition) => definition.definitionKey === definitionKey ? { ...definition, isRegistered: true } : definition))
      setReason('')
      setMessage('Recognized scope registered.')
      await refreshScopes()
      try {
        const result = await httpJson<Array<{ definition_key: string; is_registered: boolean }>>('/access/scope-definitions', { recoverAccessDenied: true })
        if (mounted.current) setDefinitions(result.map(({ definition_key, is_registered }) => ({ definitionKey: definition_key, isRegistered: is_registered })))
      } catch (error) {
        if (mounted.current && (!isApiError(error) || error.kind !== 'aborted')) setMessage('Scope registered; recognized definitions could not be refreshed.')
      }
    } catch (error) {
      if (mounted.current && (!isApiError(error) || error.kind !== 'aborted')) setMessage(isApiError(error) ? error.message : 'The scope could not be registered.')
      await refreshScopes()
    } finally {
      mutationInFlight.current = false
      if (mounted.current) setPending(false)
    }
  }

  const available = unregisteredDefinitions(definitions)
  return <Stack gap="xs"><Text fw={500}>Recognized scope definitions</Text><TextInput label="Registration reason" value={reason} onChange={(event) => setReason(event.currentTarget.value)} required />{available.length ? <Group>{available.map(({ definitionKey }) => <Button key={definitionKey} variant="default" disabled={!reason.trim()} loading={pending} onClick={() => void register(definitionKey)}>Register {definitionKey}</Button>)}</Group> : <Text size="sm">No unregistered recognized definitions.</Text>}{message ? <Alert role="status">{message}</Alert> : null}</Stack>
}

export function ScopeStatusControl({ scopeId, version, isActive, refreshScopes }: { scopeId: string; version: number; isActive: boolean; refreshScopes: RefreshScopes }) {
  const [reason, setReason] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const mutationInFlight = useRef(false)

  async function changeStatus() {
    const normalizedReason = reason.trim()
    if (!normalizedReason || mutationInFlight.current) return
    mutationInFlight.current = true
    setPending(true)
    setMessage(null)
    try {
      const request = scopeStatusRequest({ scopeId, version }, !isActive, normalizedReason)
      await httpJson(request.path, { method: request.method, body: request.body, recoverAccessDenied: true })
      setReason('')
      await refreshScopes()
    } catch (error) {
      if (!isApiError(error) || error.kind !== 'aborted') setMessage(isApiError(error) ? error.message : 'The scope status could not be changed.')
      await refreshScopes()
    } finally {
      mutationInFlight.current = false
      setPending(false)
    }
  }

  const action = isActive ? 'Deactivate' : 'Activate'
  return <Stack gap={4}><TextInput aria-label={`Reason for ${action}`} placeholder="Reason" size="xs" value={reason} onChange={(event) => setReason(event.currentTarget.value)} required /><Button size="compact-sm" variant="subtle" disabled={!reason.trim()} loading={pending} onClick={() => void changeStatus()}>{action}</Button>{message ? <Alert role="status">{message}</Alert> : null}</Stack>
}
