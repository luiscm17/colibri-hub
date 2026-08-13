import { MantineProvider } from '@mantine/core'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { UserRoleReplacementPanel } from './UserRoleReplacementPanel'

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })

const fetchMock = vi.fn()
vi.mock('@/api/httpClient', () => ({ httpJson: (...args: unknown[]) => fetchMock(...args) }))
vi.mock('@/features/access-control', () => ({ useAccess: () => ({ snapshot: { authorizationVersion: 1 } }) }))

describe('ReplacementConfirmationDialog', () => {
  it('announces proposed impact and requires a deliberate confirmation', async () => {
    fetchMock.mockResolvedValueOnce({ subject_version: 1, affected_user_count: 7 })
    render(<MantineProvider><UserRoleReplacementPanel userId="user-1" version={1} roleIds={['role-a']} /></MantineProvider>)

    fireEvent.change(screen.getByLabelText('Role IDs'), { target: { value: 'role-b' } })
    fireEvent.click(screen.getByRole('button', { name: 'Preview replacement' }))
    expect(await screen.findByRole('button', { name: 'Review replacement' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Review replacement' }))

    expect(await screen.findByRole('dialog', { name: 'Confirm replacement' })).toBeTruthy()
    expect(screen.getByRole('status').textContent).toBe('Users affected by this proposed change: 7.')
    expect(fetchMock).toHaveBeenCalledOnce()
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Confirm replacement' })).toBeNull())
  })
})
