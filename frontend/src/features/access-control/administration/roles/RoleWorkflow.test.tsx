import { MantineProvider } from '@mantine/core'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { RoleWorkflow } from './RoleWorkflow'

const fetchMock = vi.fn()
vi.mock('@/api/httpClient', () => ({ httpJson: (...args: unknown[]) => fetchMock(...args) }))
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

  it('keeps inactive historical permissions visible and requires removal after authoritative rejection', async () => {
    fetchMock.mockResolvedValueOnce({ items: [{ scope_id: 'scope-1', scope_code: 'warehouse', is_active: false }], page: 1, page_size: 50, total: 1 })
    fetchMock.mockResolvedValueOnce([{ scope_code: 'warehouse', supported_actions: ['read'] }])
    fetchMock.mockRejectedValueOnce(new Error('Inactive scope is no longer valid'))
    render(<MantineProvider><RoleWorkflow role={{ roleId: 'role-1', roleCode: 'operator', roleName: 'Operator', description: null, isActive: true, version: 1, permissions: [{ action: 'read', scopeCode: 'warehouse' }] }} onDirtyChange={vi.fn()} /></MantineProvider>)
    expect(await screen.findByText('Inactive historical reference')).toBeTruthy()
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: 'Update role' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save role' }))
    expect(await screen.findByText(/Remove inactive references before retrying/)).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Save role' }).hasAttribute('disabled')).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: 'Remove read:warehouse' }))
    expect(screen.getByRole('button', { name: 'Save role' }).hasAttribute('disabled')).toBe(false)
  })

  it('reports edits as dirty for AdministrationShell departure protection', async () => {
    const onDirtyChange = vi.fn()
    fetchMock.mockResolvedValueOnce({ items: [], page: 1, page_size: 50, total: 0 })
    fetchMock.mockResolvedValueOnce([])
    render(<MantineProvider><RoleWorkflow role={{ roleId: 'role-1', roleCode: 'operator', roleName: 'Operator', description: null, isActive: true, version: 1, permissions: [] }} onDirtyChange={onDirtyChange} /></MantineProvider>)
    fireEvent.change(await screen.findByLabelText('Role name'), { target: { value: 'Operator revised' } })
    await waitFor(() => expect(onDirtyChange).toHaveBeenLastCalledWith(true))
  })
})
