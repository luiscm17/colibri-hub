import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MantineProvider } from '@mantine/core'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '@/api/httpError'
import { ScopeRegistrationPanel, ScopeStatusControl } from './ScopeGovernance'

const fetchMock = vi.fn()
vi.mock('@/api/httpClient', () => ({ httpJson: (...args: unknown[]) => fetchMock(...args) }))
Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })

describe('scope governance', () => {
  beforeEach(() => fetchMock.mockReset())
  afterEach(cleanup)

  it('registers once with a reason and refreshes authoritative collections', async () => {
    fetchMock.mockResolvedValueOnce([{ definition_key: 'warehouse.raw', is_registered: false }]).mockResolvedValueOnce({}).mockResolvedValueOnce([{ definition_key: 'warehouse.raw', is_registered: true }])
    const refreshScopes = vi.fn().mockResolvedValue(undefined)
    render(<MantineProvider><ScopeRegistrationPanel refreshScopes={refreshScopes} /></MantineProvider>)

    fireEvent.change(await screen.findByLabelText(/Registration reason/), { target: { value: 'Initial registration' } })
    const register = screen.getByRole('button', { name: 'Register warehouse.raw' })
    fireEvent.click(register)
    fireEvent.click(register)

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith('/access/scopes', expect.objectContaining({ method: 'POST', body: { definition_key: 'warehouse.raw', reason: 'Initial registration' } })))
    expect(fetchMock.mock.calls.filter(([path]) => path === '/access/scopes')).toHaveLength(1)
    expect(refreshScopes).toHaveBeenCalledOnce()
  })

  it('retains the reason and refreshes authoritative scope data after a stale mutation', async () => {
    fetchMock.mockRejectedValueOnce(new ApiError({ kind: 'http', status: 409, code: 'access_version_conflict', message: 'Scope changed' }))
    const refreshScopes = vi.fn().mockResolvedValue(undefined)
    render(<MantineProvider><ScopeStatusControl scopeId="scope-1" version={7} isActive refreshScopes={refreshScopes} /></MantineProvider>)

    fireEvent.change(screen.getByLabelText('Reason for Deactivate'), { target: { value: 'Scheduled review' } })
    fireEvent.click(screen.getByRole('button', { name: 'Deactivate' }))

    expect(await screen.findByText('Scope changed')).toBeTruthy()
    expect((screen.getByLabelText('Reason for Deactivate') as HTMLInputElement).value).toBe('Scheduled review')
    expect(fetchMock).toHaveBeenCalledWith('/access/scopes/scope-1/status', expect.objectContaining({ body: { is_active: false, expected_version: 7, reason: 'Scheduled review' } }))
    expect(refreshScopes).toHaveBeenCalledOnce()
  })
})
