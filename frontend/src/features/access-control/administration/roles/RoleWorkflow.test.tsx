import { MantineProvider } from '@mantine/core'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { RoleWorkflow } from './RoleWorkflow'

const fetchMock = vi.fn()
vi.mock('@/api/httpClient', () => ({ httpJson: (...args: unknown[]) => fetchMock(...args) }))
vi.mock('@/features/access-control', () => ({ useAccess: () => ({ snapshot: { authorizationVersion: 1 } }) }))
Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })
Object.defineProperty(window, 'ResizeObserver', { writable: true, value: class { observe() {} unobserve() {} disconnect() {} } })

describe('RoleWorkflow', () => {
  beforeEach(() => fetchMock.mockReset())
  afterEach(() => { cleanup(); vi.restoreAllMocks() })

  it('submits a new role using scope ids resolved from scope codes', async () => {
    fetchMock.mockResolvedValueOnce({ items: [{ scope_id: 'scope-1', scope_code: 'warehouse', is_active: true }], page: 1, page_size: 50, total: 1 })
    fetchMock.mockResolvedValueOnce([{ scope_code: 'warehouse', supported_actions: ['read'] }])
    fetchMock.mockResolvedValueOnce({ role_id: 'role-1' })
    render(<MantineProvider><RoleWorkflow onDirtyChange={vi.fn()} /></MantineProvider>)
    fireEvent.change(await screen.findByLabelText('Role code'), { target: { value: 'operator' } })
    fireEvent.change(screen.getByLabelText('Role name'), { target: { value: 'Operator' } })
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: 'Initial governance role' } })
    fireEvent.change(screen.getByLabelText('Action'), { target: { value: 'read' } })
    fireEvent.change(screen.getByLabelText('Scope'), { target: { value: 'warehouse' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add permission' }))
    fireEvent.click(screen.getByRole('button', { name: 'Create role' }))
    fireEvent.click(screen.getByRole('button', { name: 'Create role' }))
    await waitFor(() => expect(fetchMock).toHaveBeenLastCalledWith('/access/roles', expect.objectContaining({ method: 'POST', body: expect.objectContaining({ permissions: [{ action: 'read', scope_id: 'scope-1' }] }) })))
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('rejects an action that is recognized globally but unsupported for the selected scope', async () => {
    fetchMock.mockResolvedValueOnce({ items: [
      { scope_id: 'scope-warehouse', scope_code: 'warehouse', is_active: true },
      { scope_id: 'scope-yarn', scope_code: 'yarn', is_active: true },
    ], page: 1, page_size: 50, total: 2 })
    fetchMock.mockResolvedValueOnce([
      { scope_code: 'warehouse', supported_actions: ['read'] },
      { scope_code: 'yarn', supported_actions: ['write'] },
    ])
    render(<MantineProvider><RoleWorkflow onDirtyChange={vi.fn()} /></MantineProvider>)

    fireEvent.change(await screen.findByLabelText('Action'), { target: { value: 'write' } })
    fireEvent.change(screen.getByLabelText('Scope'), { target: { value: 'warehouse' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add permission' }))

    expect(screen.queryByText('write:warehouse')).toBeNull()
  })

  it('keeps inactive historical permissions visible until the administrator removes them', async () => {
    fetchMock.mockResolvedValueOnce({ items: [{ scope_id: 'scope-1', scope_code: 'warehouse', is_active: false }], page: 1, page_size: 50, total: 1 })
    fetchMock.mockResolvedValueOnce([{ scope_code: 'warehouse', supported_actions: ['read'] }])
    render(<MantineProvider><RoleWorkflow role={{ roleId: 'role-1', roleCode: 'operator', roleName: 'Operator', description: null, isActive: true, version: 1, permissions: [{ action: 'read', scopeCode: 'warehouse' }] }} onDirtyChange={vi.fn()} /></MantineProvider>)
    expect(await screen.findByText('Inactive historical reference')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Remove read:warehouse' }))
    expect(screen.queryByText('Inactive historical reference')).toBeNull()
  })

  it('reports edits as dirty for AdministrationShell departure protection', async () => {
    const onDirtyChange = vi.fn()
    fetchMock.mockResolvedValueOnce({ items: [], page: 1, page_size: 50, total: 0 })
    fetchMock.mockResolvedValueOnce([])
    render(<MantineProvider><RoleWorkflow role={{ roleId: 'role-1', roleCode: 'operator', roleName: 'Operator', description: null, isActive: true, version: 1, permissions: [] }} onDirtyChange={onDirtyChange} /></MantineProvider>)
    fireEvent.change(await screen.findByLabelText('Role name'), { target: { value: 'Operator revised' } })
    await waitFor(() => expect(onDirtyChange).toHaveBeenLastCalledWith(true))
  })

  it('requires a fresh confirmation for a metadata-only shared-role update and emits one PUT', async () => {
    fetchMock
      .mockResolvedValueOnce({ items: [{ scope_id: 'scope-1', scope_code: 'warehouse', is_active: true }], page: 1, page_size: 50, total: 1 })
      .mockResolvedValueOnce([{ scope_code: 'warehouse', supported_actions: ['read'] }])
      .mockResolvedValueOnce({ subject_version: 1, affected_user_count: 1, affected_users: [{ user_id: 'user-1', user_code: 'USR-1', display_name: 'Ada' }] })
      .mockResolvedValueOnce({ role_id: 'role-1' })
    render(<MantineProvider><RoleWorkflow role={{ roleId: 'role-1', roleCode: 'operator', roleName: 'Operator', description: null, isActive: true, version: 1, permissions: [{ action: 'read', scopeCode: 'warehouse' }] }} onDirtyChange={vi.fn()} /></MantineProvider>)

    fireEvent.change(await screen.findByLabelText('Description'), { target: { value: 'Updated responsibility' } })
    fireEvent.click(screen.getByRole('button', { name: 'Preview role update' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Review role update' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Confirm role update' }))
    fireEvent.click(screen.getByRole('button', { name: 'Confirm role update' }))

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith('/access/roles/role-1', expect.objectContaining({ method: 'PUT', body: expect.objectContaining({ description: 'Updated responsibility', expected_version: 1, reason: '' }) })))
    expect(fetchMock.mock.calls.filter(([path, options]) => path === '/access/roles/role-1' && (options as { method?: string }).method === 'PUT')).toHaveLength(1)
  })

  it('blocks a full semantic no-op and invalidates a preview after a reason edit', async () => {
    fetchMock
      .mockResolvedValueOnce({ items: [], page: 1, page_size: 50, total: 0 })
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce({ subject_version: 1, affected_user_count: 0, affected_users: [] })
    render(<MantineProvider><RoleWorkflow role={{ roleId: 'role-1', roleCode: 'operator', roleName: 'Operator', description: null, isActive: true, version: 1, permissions: [] }} onDirtyChange={vi.fn()} /></MantineProvider>)

    await screen.findByLabelText('Role name')
    fireEvent.click(screen.getByRole('button', { name: 'Preview role update' }))
    expect(await screen.findByText('Change the role name, description, or permissions before previewing.')).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Description'), { target: { value: 'Updated' } })
    fireEvent.click(screen.getByRole('button', { name: 'Preview role update' }))
    expect(await screen.findByRole('button', { name: 'Review role update' })).toBeTruthy()
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: 'Clarify change' } })
    expect(screen.queryByRole('button', { name: 'Review role update' })).toBeNull()
    expect(fetchMock.mock.calls.some(([path, options]) => path === '/access/roles/role-1' && (options as { method?: string }).method === 'PUT')).toBe(false)
  })
})
