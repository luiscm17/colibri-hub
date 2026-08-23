import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MantineProvider } from '@mantine/core'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '@/api/httpError'
import AuthenticationAccountsPage from './AuthenticationAccountsPage'

const listAccounts = vi.fn()
const getAccount = vi.fn()
const account = { account_id: 'account-1', email: 'ada@example.com', display_name: 'Ada Lovelace', user_code: 'ADA-1', status: 'active', version: 3 }

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })
Object.defineProperty(window, 'ResizeObserver', { writable: true, value: class { observe() {} unobserve() {} disconnect() {} } })

vi.mock('../api/authApi', () => ({
  fetchAuthenticationAccounts: () => listAccounts(),
  fetchAuthenticationAccount: (accountId: string) => getAccount(accountId),
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
  beforeEach(() => { listAccounts.mockReset(); getAccount.mockReset() })
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
})
