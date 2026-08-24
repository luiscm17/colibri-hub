import { Alert, Button, Group, Loader, Stack, Table, Text, Title } from '@mantine/core'
import { useEffect, useRef, useState } from 'react'
import { fetchAuthenticationAudits } from '../api/authApi'
import type { AuthenticationAuditEntry, AuthenticationAuditPage } from '../api/authApi.types'

type HistoryState =
  | { status: 'loading-initial' }
  | { status: 'failed-initial' }
  | { status: 'ready'; entries: readonly AuthenticationAuditEntry[]; cursor: string | null; loadingMore: boolean; continuationFailed: boolean }

const unavailableMessage = 'Authentication history is unavailable.'

export default function AuthenticationHistoryPage() {
  const [state, setState] = useState<HistoryState>({ status: 'loading-initial' })
  const generation = useRef(0)
  const page = useRef<AuthenticationAuditPage | null>(null)
  const continuation = useRef<symbol | null>(null)

  const loadInitial = () => {
    const requestGeneration = ++generation.current
    continuation.current = null
    page.current = null
    setState({ status: 'loading-initial' })
    void fetchAuthenticationAudits().then((response) => {
      if (requestGeneration !== generation.current) return
      page.current = response
      setState({ status: 'ready', entries: response.entries, cursor: response.cursor, loadingMore: false, continuationFailed: false })
    }).catch(() => {
      if (requestGeneration === generation.current) setState({ status: 'failed-initial' })
    })
  }

  useEffect(() => {
    let active = true
    const requestGeneration = ++generation.current
    void fetchAuthenticationAudits().then((response) => {
      if (!active || requestGeneration !== generation.current) return
      page.current = response
      setState({ status: 'ready', entries: response.entries, cursor: response.cursor, loadingMore: false, continuationFailed: false })
    }).catch(() => {
      if (active && requestGeneration === generation.current) setState({ status: 'failed-initial' })
    })
    return () => { active = false }
  }, [])

  const loadMore = () => {
    const current = page.current
    if (!current?.cursor || continuation.current) return
    const requestGeneration = generation.current
    const cursor = current.cursor
    const request = Symbol('continuation')
    continuation.current = request
    setState((previous) => previous.status === 'ready' ? { ...previous, loadingMore: true, continuationFailed: false } : previous)
    void fetchAuthenticationAudits(cursor).then((response) => {
      if (generation.current !== requestGeneration || continuation.current !== request || page.current?.cursor !== cursor) return
      page.current = { entries: [...page.current.entries, ...response.entries], cursor: response.cursor }
      setState({ status: 'ready', entries: page.current.entries, cursor: response.cursor, loadingMore: false, continuationFailed: false })
    }).catch(() => {
      if (generation.current === requestGeneration && continuation.current === request && page.current?.cursor === cursor) {
        setState((previous) => previous.status === 'ready' ? { ...previous, loadingMore: false, continuationFailed: true } : previous)
      }
    }).finally(() => {
      if (continuation.current === request) continuation.current = null
    })
  }

  if (state.status === 'loading-initial') return <Stack align="center" py="xl"><Loader aria-label="Loading authentication history" /></Stack>
  if (state.status === 'failed-initial') return <Stack gap="md"><Alert role="alert">{unavailableMessage}</Alert><Button onClick={loadInitial}>Retry</Button></Stack>

  return <Stack gap="lg">
    <Group justify="space-between"><Title order={1}>Authentication history</Title><Button variant="subtle" onClick={loadInitial}>Refresh</Button></Group>
    {state.entries.length === 0 ? <Text c="dimmed">No authentication history is available.</Text> : <Table.ScrollContainer minWidth={900}>
      <Table highlightOnHover>
        <Table.Thead><Table.Tr><Table.Th>Audit ID</Table.Th><Table.Th>Operation ID</Table.Th><Table.Th>Event type</Table.Th><Table.Th>Outcome</Table.Th><Table.Th>Affected account ID</Table.Th><Table.Th>Occurred at</Table.Th><Table.Th>Source</Table.Th></Table.Tr></Table.Thead>
        <Table.Tbody>{state.entries.map((entry) => <Table.Tr key={entry.audit_id}>
          <Table.Td>{entry.audit_id}</Table.Td><Table.Td>{entry.operation_id ?? '—'}</Table.Td><Table.Td>{entry.event_type}</Table.Td><Table.Td>{entry.outcome}</Table.Td><Table.Td>{entry.affected_account_id ?? '—'}</Table.Td><Table.Td>{entry.occurred_at}</Table.Td><Table.Td>{entry.source}</Table.Td>
        </Table.Tr>)}</Table.Tbody>
      </Table>
    </Table.ScrollContainer>}
    {state.continuationFailed ? <Alert role="alert">{unavailableMessage}</Alert> : null}
    {state.cursor ? <Group><Button onClick={loadMore} disabled={state.loadingMore}>{state.loadingMore ? 'Loading more' : state.continuationFailed ? 'Retry loading more' : 'Load more'}</Button></Group> : <Text c="dimmed">End of authentication history.</Text>}
  </Stack>
}
