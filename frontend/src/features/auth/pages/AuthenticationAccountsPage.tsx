import { Alert, Anchor, Button, Card, Group, Loader, PasswordInput, Stack, Table, Text, TextInput, Textarea, Title } from '@mantine/core'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { isApiError } from '@/api/httpError'
import { disableAuthenticationAccount, fetchAuthenticationAccount, fetchAuthenticationAccounts, resetAuthenticationAccountPassword } from '../api/authApi'
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
  const [message, setMessage] = useState<string | null>(null)
  const [resetPassword, setResetPassword] = useState('')
  const [resetConfirmation, setResetConfirmation] = useState('')
  const [resetReason, setResetReason] = useState('')
  const [disableReason, setDisableReason] = useState('')
  const [disableConfirmation, setDisableConfirmation] = useState('')
  const [disableConfirmed, setDisableConfirmed] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [pending, setPending] = useState(false)
  const generation = useRef(0)
  const inFlight = useRef(false)
  const messageRef = useRef<HTMLDivElement>(null)

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

  useEffect(() => { if (message) messageRef.current?.focus() }, [message])

  const refreshAuthoritativeDetail = async (): Promise<boolean> => {
    setState({ status: 'loading' })
    try {
      const account = await fetchAuthenticationAccount(accountId)
      setState({ status: 'ready', value: account })
      return true
    } catch (error) {
      setState(isApiError(error) && error.status === 404 ? { status: 'missing' } : { status: 'failed' })
      return false
    }
  }

  const clearResetSecrets = () => { setResetPassword(''); setResetConfirmation('') }

  const handleReset = async () => {
    if (state.status !== 'ready' || state.value.status !== 'active' || inFlight.current) return
    const nextErrors: Record<string, string> = {}
    if (!resetPassword) nextErrors.resetPassword = 'A provisional password is required.'
    if (resetPassword !== resetConfirmation) nextErrors.resetConfirmation = 'Passwords must match.'
    if (!resetReason.trim()) nextErrors.resetReason = 'A reason is required.'
    if (Object.keys(nextErrors).length) { setErrors(nextErrors); clearResetSecrets(); return }
    inFlight.current = true; setPending(true); setErrors({}); setMessage(null)
    try {
      await resetAuthenticationAccountPassword(accountId, { provisional_password: resetPassword, reason: resetReason.trim(), expected_version: state.value.version })
      const refreshed = await refreshAuthoritativeDetail()
      setMessage(refreshed ? 'Password reset completed. The account detail has been refreshed.' : 'Password reset was accepted, but the current account state could not be verified. Refresh the detail before another action.')
      setResetReason('')
    } catch (error) {
      if (isApiError(error) && [404, 409, 503].includes(error.status ?? 0)) {
        await refreshAuthoritativeDetail()
        setMessage(error.status === 503
          ? 'Password reset verification is pending. The provider outcome is unknown; refresh the detail before taking another action.'
          : 'Password reset was not completed with the submitted version or account state. The account detail has been refreshed.')
      } else {
        setMessage('Password reset could not be confirmed. The account state may have changed; refresh the detail before retrying.')
      }
    } finally {
      clearResetSecrets(); inFlight.current = false; setPending(false)
    }
  }

  const handleDisable = async () => {
    if (state.status !== 'ready' || state.value.status === 'disabled' || inFlight.current) return
    const nextErrors: Record<string, string> = {}
    if (!disableReason.trim()) nextErrors.disableReason = 'A reason is required.'
    if (!disableConfirmed) nextErrors.disableConfirmed = 'Confirm that this reversible action should be submitted.'
    if (Object.keys(nextErrors).length) { setErrors(nextErrors); return }
    inFlight.current = true; setPending(true); setErrors({}); setMessage(null)
    try {
      await disableAuthenticationAccount(accountId, { reason: disableReason.trim(), expected_version: state.value.version })
      const refreshed = await refreshAuthoritativeDetail()
      setMessage(refreshed ? 'Account disabled. The account detail has been refreshed.' : 'Disablement was accepted, but the current account state could not be verified. Refresh the detail before another action.')
      setDisableReason(''); setDisableConfirmed(false)
    } catch (error) {
      if (isApiError(error) && [404, 409, 503].includes(error.status ?? 0)) {
        setDisableConfirmation(''); setDisableConfirmed(false)
        await refreshAuthoritativeDetail()
        setMessage(error.status === 503
          ? 'Disablement verification is pending. The provider outcome is unknown; refresh the detail before taking another action.'
          : 'Disablement was not completed with the submitted version or account state. The account detail has been refreshed.')
      } else {
        setMessage('Disablement could not be confirmed. The account state may have changed; refresh the detail before retrying.')
      }
    } finally {
      inFlight.current = false; setPending(false)
    }
  }

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
    {message ? <Alert ref={messageRef} tabIndex={-1} role="status">{message}</Alert> : null}
    <Card withBorder>
      <Stack gap="sm">
        <Title order={2}>Reset password</Title>
        {account.status === 'active' ? <>
          <PasswordInput label="New provisional password" value={resetPassword} error={errors.resetPassword} disabled={pending} onChange={(event) => setResetPassword(event.currentTarget.value)} />
          <PasswordInput label="Confirm provisional password" value={resetConfirmation} error={errors.resetConfirmation} disabled={pending} onChange={(event) => setResetConfirmation(event.currentTarget.value)} />
          <Textarea label="Reason for password reset" value={resetReason} error={errors.resetReason} required disabled={pending} onChange={(event) => setResetReason(event.currentTarget.value)} />
          <Button onClick={() => void handleReset()} disabled={pending}>Reset password</Button>
        </> : <Text c="dimmed">Password reset is available only while this account is active.</Text>}
      </Stack>
    </Card>
    <Card withBorder>
      <Stack gap="sm">
        <Title order={2}>Disable account</Title>
        {account.status !== 'disabled' ? <>
          <Textarea label="Reason for disabling account" value={disableReason} error={errors.disableReason} required disabled={pending} onChange={(event) => setDisableReason(event.currentTarget.value)} />
          <TextInput label="Confirmation" description="Type DISABLE to confirm this reversible action." value={disableConfirmation} error={errors.disableConfirmed} disabled={pending} onChange={(event) => { setDisableConfirmation(event.currentTarget.value); setDisableConfirmed(event.currentTarget.value === 'DISABLE') }} />
          <Button color="red" onClick={() => void handleDisable()} disabled={pending}>Disable account</Button>
        </> : <Text c="dimmed">This account is already disabled.</Text>}
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
