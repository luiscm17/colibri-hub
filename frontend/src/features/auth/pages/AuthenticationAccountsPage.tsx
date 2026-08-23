import { Alert, Anchor, Button, Card, Group, Loader, Stack, Table, Text, Title } from '@mantine/core'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { isApiError } from '@/api/httpError'
import { fetchAuthenticationAccount, fetchAuthenticationAccounts } from '../api/authApi'
import type { AuthenticationAccountResponse } from '../api/authApi.types'

type LoadState<T> =
  | { status: 'loading' }
  | { status: 'ready'; value: T }
  | { status: 'missing' }
  | { status: 'failed' }

const unavailableMessage = 'Authentication account data is unavailable.'

export default function AuthenticationAccountsPage() {
  const { accountId } = useParams()
  return accountId ? <AuthenticationAccountDetail key={accountId} accountId={accountId} /> : <AuthenticationAccountsCollection />
}

function AuthenticationAccountsCollection() {
  const [state, setState] = useState<LoadState<readonly AuthenticationAccountResponse[]>>({ status: 'loading' })
  const [reload, setReload] = useState(0)
  const generation = useRef(0)

  useEffect(() => {
    let active = true
    const request = ++generation.current
    void fetchAuthenticationAccounts()
      .then((accounts) => {
        if (active && request === generation.current) setState({ status: 'ready', value: accounts })
      })
      .catch(() => {
        if (active && request === generation.current) setState({ status: 'failed' })
      })
    return () => { active = false }
  }, [reload])

  if (state.status === 'loading') return <LoadingAccounts />
  if (state.status !== 'ready') return <RetryState message={unavailableMessage} onRetry={() => { setState({ status: 'loading' }); setReload((value) => value + 1) }} />

  return <Stack gap="lg">
    <Title order={1}>Accounts</Title>
    <Table.ScrollContainer minWidth={700}>
      <Table highlightOnHover>
        <Table.Thead><Table.Tr><Table.Th>Display name</Table.Th><Table.Th>Email</Table.Th><Table.Th>User code</Table.Th><Table.Th>Status</Table.Th></Table.Tr></Table.Thead>
        <Table.Tbody>{state.value.map((account) => <Table.Tr key={account.account_id}>
          <Table.Td><Anchor component={Link} to={`/auth/accounts/${encodeURIComponent(account.account_id)}`}>{account.display_name}</Anchor></Table.Td>
          <Table.Td>{account.email}</Table.Td><Table.Td>{account.user_code}</Table.Td><Table.Td>{account.status}</Table.Td>
        </Table.Tr>)}</Table.Tbody>
      </Table>
    </Table.ScrollContainer>
    {state.value.length === 0 ? <Text c="dimmed">No authentication accounts are available.</Text> : null}
  </Stack>
}

function AuthenticationAccountDetail({ accountId }: { accountId: string }) {
  const navigate = useNavigate()
  const [state, setState] = useState<LoadState<AuthenticationAccountResponse>>({ status: 'loading' })
  const [reload, setReload] = useState(0)
  const generation = useRef(0)

  useEffect(() => {
    let active = true
    const request = ++generation.current
    void fetchAuthenticationAccount(accountId)
      .then((account) => {
        if (active && request === generation.current) setState({ status: 'ready', value: account })
      })
      .catch((error: unknown) => {
        if (!active || request !== generation.current) return
        setState(isApiError(error) && error.status === 404 ? { status: 'missing' } : { status: 'failed' })
      })
    return () => { active = false }
  }, [accountId, reload])

  if (state.status === 'loading') return <LoadingAccounts />
  if (state.status === 'missing') return <RetryState message="This authentication account no longer exists." onRetry={() => { setState({ status: 'loading' }); setReload((value) => value + 1) }} back={() => navigate('/auth/accounts')} />
  if (state.status === 'failed') return <RetryState message={unavailableMessage} onRetry={() => { setState({ status: 'loading' }); setReload((value) => value + 1) }} back={() => navigate('/auth/accounts')} />

  const account = state.value
  return <Stack gap="lg">
    <Group justify="space-between"><Title order={1}>Authentication account</Title><Button variant="subtle" onClick={() => navigate('/auth/accounts')}>Back to accounts</Button></Group>
    <Card withBorder>
      <Stack gap="sm">
        <AccountFact label="Account ID" value={account.account_id} />
        <AccountFact label="Email" value={account.email} />
        <AccountFact label="Display name" value={account.display_name} />
        <AccountFact label="User code" value={account.user_code} />
        <AccountFact label="Status" value={account.status} />
        <AccountFact label="Version" value={String(account.version)} />
      </Stack>
    </Card>
  </Stack>
}

function AccountFact({ label, value }: { label: string; value: string }) {
  return <Group gap="xs"><Text fw={500}>{label}:</Text><Text>{value}</Text></Group>
}

function LoadingAccounts() {
  return <Stack align="center" py="xl"><Loader aria-label="Loading authentication accounts" /></Stack>
}

function RetryState({ message, onRetry, back }: { message: string; onRetry(): void; back?: () => void }) {
  return <Stack gap="md"><Alert role="alert">{message}</Alert><Group><Button onClick={onRetry}>Retry</Button>{back ? <Button variant="subtle" onClick={back}>Back to accounts</Button> : null}</Group></Stack>
}
