import { MantineProvider } from '@mantine/core'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { UserRoleReplacementPanel } from './UserRoleReplacementPanel'
import { SharedRolePermissionPanel } from './SharedRolePermissionPanel'

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })

const fetchMock = vi.fn()
vi.mock('@/api/httpClient', () => ({ httpJson: (...args: unknown[]) => fetchMock(...args) }))
vi.mock('@/features/access-control', () => ({ useAccess: () => ({ snapshot: { authorizationVersion: 1 } }) }))

describe('ReplacementConfirmationDialog', () => {
  const affectedUsers = Array.from({ length: 7 }, (_, index) => ({ user_id: `user-${index + 1}`, user_code: `USR-${index + 1}`, display_name: `User ${index + 1}` }))

  beforeEach(() => fetchMock.mockReset())
  afterEach(cleanup)

  it('announces proposed impact and requires a deliberate confirmation', async () => {
    fetchMock.mockResolvedValueOnce({ subject_version: 1, affected_user_count: 7, affected_users: affectedUsers })
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

  it('renders six user-role preview users and expands the remaining impact accessibly', async () => {
    fetchMock.mockResolvedValueOnce({ subject_version: 1, affected_user_count: 7, affected_users: affectedUsers })
    render(<MantineProvider><UserRoleReplacementPanel userId="user-1" version={1} roleIds={['role-a']} /></MantineProvider>)

    fireEvent.change(screen.getByLabelText('Role IDs'), { target: { value: 'role-b' } })
    fireEvent.click(screen.getByRole('button', { name: 'Preview replacement' }))

    expect(await screen.findByText('User 6 (USR-6)')).toBeTruthy()
    expect(screen.queryByText('User 7 (USR-7)')).toBeNull()
    const expansion = screen.getByRole('button', { name: 'Show 1 additional affected user' })
    expect(expansion.getAttribute('aria-expanded')).toBe('false')
    fireEvent.click(expansion)
    expect(screen.getByText('User 7 (USR-7)')).toBeTruthy()
    expect(expansion.getAttribute('aria-expanded')).toBe('true')
  })

  it('renders six shared-role preview users and expands the remaining impact accessibly', async () => {
    fetchMock.mockResolvedValueOnce({ subject_version: 1, affected_user_count: 7, affected_users: affectedUsers })
    render(<MantineProvider><SharedRolePermissionPanel roleId="role-1" version={1} roleName="Role" description={null} permissions={[{ action: 'read', scopeId: 'scope-a' }]} /></MantineProvider>)

    fireEvent.change(screen.getByLabelText('Permission pairs'), { target: { value: 'write:scope-a' } })
    fireEvent.click(screen.getByRole('button', { name: 'Preview replacement' }))

    expect(await screen.findByText('User 6 (USR-6)')).toBeTruthy()
    expect(screen.queryByText('User 7 (USR-7)')).toBeNull()
    const expansion = screen.getByRole('button', { name: 'Show 1 additional affected user' })
    expect(expansion.getAttribute('aria-expanded')).toBe('false')
    fireEvent.click(expansion)
    expect(screen.getByText('User 7 (USR-7)')).toBeTruthy()
    expect(expansion.getAttribute('aria-expanded')).toBe('true')
  })
})
