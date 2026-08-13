import { Alert, Button, Group, Stack, Text } from '@mantine/core'
import { useEffect, useState } from 'react'
import { httpJson } from '@/api/httpClient'
import { scopeRegistrationRequest, scopeStatusRequest, unregisteredDefinitions } from './history'

export function ScopeRegistrationPanel() {
  const [definitions, setDefinitions] = useState<Array<{ definitionKey: string; isRegistered: boolean }>>([])
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    void httpJson<Array<{ definition_key: string; is_registered: boolean }>>('/access/scope-definitions', { recoverAccessDenied: true })
      .then((result) => setDefinitions(result.map(({ definition_key, is_registered }) => ({ definitionKey: definition_key, isRegistered: is_registered }))))
  }, [])

  async function register(definitionKey: string) {
    const request = scopeRegistrationRequest(definitionKey)
    await httpJson(request.path, { method: request.method, body: request.body, recoverAccessDenied: true })
    setDefinitions((current) => current.map((definition) => definition.definitionKey === definitionKey ? { ...definition, isRegistered: true } : definition))
    setMessage('Recognized scope registered.')
  }

  const available = unregisteredDefinitions(definitions)
  return <Stack gap="xs"><Text fw={500}>Recognized scope definitions</Text>{available.length ? <Group>{available.map(({ definitionKey }) => <Button key={definitionKey} variant="default" onClick={() => void register(definitionKey)}>Register {definitionKey}</Button>)}</Group> : <Text size="sm">No unregistered recognized definitions.</Text>}{message ? <Alert>{message}</Alert> : null}</Stack>
}

export function ScopeStatusControl({ scopeId, version, isActive }: { scopeId: string; version: number; isActive: boolean }) {
  const [active, setActive] = useState(isActive)

  async function changeStatus() {
    const request = scopeStatusRequest({ scopeId, version }, !active)
    await httpJson(request.path, { method: request.method, body: request.body, recoverAccessDenied: true })
    setActive(!active)
  }

  return <Button size="compact-sm" variant="subtle" onClick={() => void changeStatus()}>{active ? 'Deactivate' : 'Activate'}</Button>
}
