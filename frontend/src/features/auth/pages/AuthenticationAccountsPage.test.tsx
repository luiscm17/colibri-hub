import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MantineProvider } from '@mantine/core'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '@/api/httpError'
import AuthenticationAccountsPage from './AuthenticationAccountsPage'

const listAccounts = vi.fn()
const getAccount = vi.fn()
const resetPassword = vi.fn()
const disableAccount = vi.fn()
const account = { account_id: 'account-1', email: 'ada@example.com', display_name: 'Ada Lovelace', user_code: 'ADA-1', status: 'active', version: 3 }

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })
Object.defineProperty(window, 'ResizeObserver', { writable: true, value: class { observe() {} unobserve() {} disconnect() {} } })

vi.mock('../api/authApi', () => ({
  fetchAuthenticationAccounts: () => listAccounts(),
  fetchAuthenticationAccount: (accountId: string) => getAccount(accountId),
  resetAuthenticationAccountPassword: (accountId: string, body: unknown) => resetPassword(accountId, body),
  disableAuthenticationAccount: (accountId: string, body: unknown) => disableAccount(accountId, body),
}))

function renderPage(path = '/auth/accounts') {
  const router = createMemoryRouter([
    { path: '/auth/accounts', element: <AuthenticationAccountsPage /> },
    { path: '/auth/accounts/:accountId', element: <AuthenticationAccountsPage /> },
  ], { initialEntries: [path] })
  render(<MantineProvider><RouterProvider router={router} /></MantineProvider>)
  return router
}

describe('AuthenticationAccountsPage', () => {
  beforeEach(() => { listAccounts.mockReset(); getAccount.mockReset(); resetPassword.mockReset(); disableAccount.mockReset() })
  afterEach(cleanup)

  it('links an account from the collection to its Authentication-owned detail', async () => {
    listAccounts.mockResolvedValue([account])
    getAccount.mockResolvedValue(account)
    const router = renderPage()

    fireEvent.click(await screen.findByRole('link', { name: 'Ada Lovelace' }))

    expect(await screen.findByRole('heading', { name: 'Authentication account' })).toBeTruthy()
    expect(getAccount).toHaveBeenCalledWith('account-1')
    expect(screen.getByText('Account ID:')).toBeTruthy()
    expect(screen.queryByText(/role/i)).toBeNull()
    expect(router.state.location.pathname).toBe('/auth/accounts/account-1')
  })

  it('loads an addressable detail directly', async () => {
    getAccount.mockResolvedValue(account)
    renderPage('/auth/accounts/account-1')

    expect(await screen.findByText('ada@example.com')).toBeTruthy()
    expect(getAccount).toHaveBeenCalledWith('account-1')
  })

  it('recovers a missing account with retry or a safe collection back route', async () => {
    getAccount
      .mockRejectedValueOnce(new ApiError({ kind: 'http', status: 404, message: 'Missing' }))
      .mockResolvedValueOnce(account)
    const router = renderPage('/auth/accounts/account-1')

    fireEvent.click(await screen.findByRole('button', { name: 'Retry' }))
    expect(await screen.findByText('ada@example.com')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Back to accounts' }))

    await waitFor(() => expect(router.state.location.pathname).toBe('/auth/accounts'))
  })

  it('submits an active account reset with its current version and clears secrets after success', async () => {
    getAccount.mockResolvedValueOnce(account).mockResolvedValueOnce({ ...account, status: 'awaiting_password_change', version: 4 })
    resetPassword.mockResolvedValue(undefined)
    renderPage('/auth/accounts/account-1')
    fireEvent.change(await screen.findByLabelText('New provisional password'), { target: { value: 'temporary-secret' } })
    fireEvent.change(await screen.findByLabelText('Confirm provisional password'), { target: { value: 'temporary-secret' } })
    fireEvent.change(await screen.findByLabelText(/Reason for password reset/), { target: { value: 'Support request' } })
    fireEvent.click(screen.getByRole('button', { name: 'Reset password' }))
    await waitFor(() => expect(resetPassword).toHaveBeenCalledWith('account-1', { provisional_password: 'temporary-secret', reason: 'Support request', expected_version: 3 }))
    expect(await screen.findByText(/Password reset completed/)).toBeTruthy()
    expect(getAccount).toHaveBeenCalledTimes(2)
    expect(screen.queryByLabelText('New provisional password')).toBeNull()
    expect(screen.queryByLabelText('Confirm provisional password')).toBeNull()
  })

  it('validates reset locally and clears secret inputs without submitting', async () => {
    getAccount.mockResolvedValue(account)
    renderPage('/auth/accounts/account-1')
    fireEvent.change(await screen.findByLabelText('New provisional password'), { target: { value: 'one' } })
    fireEvent.change(await screen.findByLabelText('Confirm provisional password'), { target: { value: 'two' } })
    fireEvent.click(screen.getByRole('button', { name: 'Reset password' }))
    expect(await screen.findByText('Passwords must match.')).toBeTruthy()
    expect(resetPassword).not.toHaveBeenCalled()
    expect((screen.getByLabelText('New provisional password') as HTMLInputElement).value).toBe('')
  })

  it('requires explicit disable confirmation, prevents duplicate submission, and refreshes after success', async () => {
    let resolveDisable: () => void
    getAccount.mockResolvedValueOnce(account).mockResolvedValueOnce({ ...account, status: 'disabled', version: 4 })
    disableAccount.mockImplementation(() => new Promise<void>((resolve) => { resolveDisable = resolve }))
    renderPage('/auth/accounts/account-1')
    fireEvent.change(await screen.findByLabelText(/Reason for disabling account/), { target: { value: 'Policy breach' } })
    fireEvent.click(screen.getByRole('button', { name: 'Disable account' }))
    expect(await screen.findByText(/Confirm that this reversible action/)).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Confirmation'), { target: { value: 'DISABLE' } })
    fireEvent.click(screen.getByRole('button', { name: 'Disable account' }))
    fireEvent.click(screen.getByRole('button', { name: 'Disable account' }))
    expect(disableAccount).toHaveBeenCalledTimes(1)
    resolveDisable!()
    expect(await screen.findByText(/Account disabled/)).toBeTruthy()
    expect(getAccount).toHaveBeenCalledTimes(2)
  })

  it.each([409, 404, 503])('refreshes authoritative detail before reporting reset error %s', async (status) => {
    getAccount.mockResolvedValueOnce(account).mockResolvedValueOnce(status === 404 ? account : { ...account, version: 4 })
    resetPassword.mockRejectedValue(new ApiError({ kind: 'http', status, message: 'Rejected' }))
    renderPage('/auth/accounts/account-1')
    fireEvent.change(await screen.findByLabelText('New provisional password'), { target: { value: 'temporary-secret' } })
    fireEvent.change(await screen.findByLabelText('Confirm provisional password'), { target: { value: 'temporary-secret' } })
    fireEvent.change(await screen.findByLabelText(/Reason for password reset/), { target: { value: 'Support request' } })
    fireEvent.click(screen.getByRole('button', { name: 'Reset password' }))
    await waitFor(() => expect(getAccount).toHaveBeenCalledTimes(2))
    expect(await screen.findByRole('status')).toBeTruthy()
    expect((screen.getByLabelText('New provisional password') as HTMLInputElement).value).toBe('')
  })

  it('does not expose incompatible actions', async () => {
    getAccount.mockResolvedValue({ ...account, status: 'disabled' })
    renderPage('/auth/accounts/account-1')
    expect(await screen.findByText('This account is already disabled.')).toBeTruthy()
    expect(screen.getByText(/Password reset is available only/)).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Reset password' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Disable account' })).toBeNull()
  })
})
