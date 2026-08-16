import { MantineProvider } from '@mantine/core'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '@/api/httpError'
import { PresetWorkflow } from './PresetWorkflow'

const fetchMock = vi.fn()
vi.mock('@/api/httpClient', () => ({ httpJson: (...args: unknown[]) => fetchMock(...args) }))
Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })
Object.defineProperty(window, 'ResizeObserver', { writable: true, value: class { observe() {} unobserve() {} disconnect() {} } })

describe('PresetWorkflow', () => {
  beforeEach(() => fetchMock.mockReset())
  afterEach(cleanup)

  it('creates presets with resolved scope ids and suppresses duplicate mutations', async () => {
    fetchMock.mockResolvedValueOnce({ items: [{ scope_id: 'scope-1', scope_code: 'warehouse', is_active: true }], total: 1 })
    fetchMock.mockResolvedValueOnce([{ scope_code: 'warehouse', supported_actions: ['read'] }])
    fetchMock.mockResolvedValueOnce({ preset_id: 'preset-1' })
    render(<MantineProvider><PresetWorkflow onDirtyChange={vi.fn()} /></MantineProvider>)
    fireEvent.change(await screen.findByLabelText('Preset code'), { target: { value: 'operator' } })
    fireEvent.change(screen.getByLabelText('Preset name'), { target: { value: 'Operator' } })
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: 'Create preset' } })
    fireEvent.change(screen.getByLabelText('Action'), { target: { value: 'read' } })
    fireEvent.change(screen.getByLabelText('Scope'), { target: { value: 'warehouse' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add permission' }))
    fireEvent.click(screen.getByRole('button', { name: 'Create preset' }))
    fireEvent.click(screen.getByRole('button', { name: 'Create preset' }))
    await waitFor(() => expect(fetchMock).toHaveBeenLastCalledWith('/access/role-presets', expect.objectContaining({ method: 'POST', body: expect.objectContaining({ permissions: [{ action: 'read', scope_id: 'scope-1' }] }) })))
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('rejects an unsupported action for a recognized active scope', async () => {
    fetchMock.mockResolvedValueOnce({ items: [{ scope_id: 'scope-1', scope_code: 'warehouse', is_active: true }], total: 1 })
    fetchMock.mockResolvedValueOnce([{ scope_code: 'warehouse', supported_actions: ['read'] }])
    render(<MantineProvider><PresetWorkflow onDirtyChange={vi.fn()} /></MantineProvider>)
    fireEvent.change(await screen.findByLabelText('Preset name'), { target: { value: 'Operator' } })
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: 'Create preset' } })
    fireEvent.change(screen.getByLabelText('Action'), { target: { value: 'write' } })
    fireEvent.change(screen.getByLabelText('Scope'), { target: { value: 'warehouse' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add permission' }))
    fireEvent.click(screen.getByRole('button', { name: 'Create preset' }))
    await waitFor(() => expect(fetchMock).toHaveBeenLastCalledWith('/access/role-presets', expect.objectContaining({ body: expect.objectContaining({ permissions: [] }) })))
    expect(screen.queryByText('write:warehouse')).toBeNull()
  })

  it('rejects a System Administrator-reserved action for an ordinary preset', async () => {
    fetchMock.mockResolvedValueOnce({ items: [{ scope_id: 'scope-1', scope_code: 'access-control', is_active: true }], total: 1 })
    fetchMock.mockResolvedValueOnce([{ scope_code: 'access-control', supported_actions: ['read'] }])
    render(<MantineProvider><PresetWorkflow onDirtyChange={vi.fn()} /></MantineProvider>)
    fireEvent.change(await screen.findByLabelText('Preset name'), { target: { value: 'Operator' } })
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: 'Create preset' } })
    fireEvent.change(screen.getByLabelText('Action'), { target: { value: 'manage_access' } })
    fireEvent.change(screen.getByLabelText('Scope'), { target: { value: 'access-control' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add permission' }))
    fireEvent.click(screen.getByRole('button', { name: 'Create preset' }))
    await waitFor(() => expect(fetchMock).toHaveBeenLastCalledWith('/access/role-presets', expect.objectContaining({ body: expect.objectContaining({ permissions: [] }) })))
    expect(screen.queryByText('manage_access:access-control')).toBeNull()
  })

  it('retains rejected inactive references until they are removed', async () => {
    fetchMock.mockResolvedValueOnce({ items: [{ scope_id: 'scope-1', scope_code: 'warehouse', is_active: false }], total: 1 })
    fetchMock.mockResolvedValueOnce([{ scope_code: 'warehouse', supported_actions: ['read'] }])
    fetchMock.mockRejectedValueOnce(new ApiError({ kind: 'http', status: 409, code: 'inactive_access_scope', message: 'Inactive scope rejected' }))
    render(<MantineProvider><PresetWorkflow preset={{ presetId: 'preset-1', presetCode: 'operator', presetName: 'Operator', description: null, isActive: true, version: 2, permissions: [{ action: 'read', scopeCode: 'warehouse' }] }} onDirtyChange={vi.fn()} /></MantineProvider>)
    expect(await screen.findByText('Inactive historical reference')).toBeTruthy()
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: 'Edit preset' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save preset' }))
    expect(await screen.findByText('Inactive scope rejected')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Save preset' }).hasAttribute('disabled')).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: 'Remove read:warehouse' }))
    expect(screen.getByRole('button', { name: 'Save preset' }).hasAttribute('disabled')).toBe(false)
  })

  it('keeps save and lifecycle retryable after unrelated failures', async () => {
    fetchMock.mockResolvedValueOnce({ items: [{ scope_id: 'scope-1', scope_code: 'warehouse', is_active: false }], total: 1 })
    fetchMock.mockResolvedValueOnce([{ scope_code: 'warehouse', supported_actions: ['read'] }])
    fetchMock.mockRejectedValueOnce(new ApiError({ kind: 'network', message: 'Service unavailable' }))
    fetchMock.mockResolvedValueOnce(undefined)
    render(<MantineProvider><PresetWorkflow preset={{ presetId: 'preset-1', presetCode: 'operator', presetName: 'Operator', description: null, isActive: true, version: 2, permissions: [{ action: 'read', scopeCode: 'warehouse' }] }} onDirtyChange={vi.fn()} /></MantineProvider>)
    fireEvent.change(await screen.findByLabelText(/Reason/), { target: { value: 'Retryable change' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save preset' }))
    expect(await screen.findByText('Service unavailable')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Save preset' }).hasAttribute('disabled')).toBe(false)
    fireEvent.click(screen.getByRole('button', { name: 'Deactivate preset' }))
    await waitFor(() => expect(fetchMock).toHaveBeenLastCalledWith('/access/role-presets/preset-1/status', expect.objectContaining({ method: 'PATCH' })))
  })

  it('updates lifecycle and reports drafts as dirty', async () => {
    const onDirtyChange = vi.fn()
    fetchMock.mockResolvedValueOnce({ items: [], total: 0 })
    fetchMock.mockResolvedValueOnce([])
    fetchMock.mockResolvedValueOnce(undefined)
    render(<MantineProvider><PresetWorkflow preset={{ presetId: 'preset-1', presetCode: 'operator', presetName: 'Operator', description: null, isActive: true, version: 2, permissions: [] }} onDirtyChange={onDirtyChange} /></MantineProvider>)
    fireEvent.change(await screen.findByLabelText(/Reason/), { target: { value: 'Retire preset' } })
    await waitFor(() => expect(onDirtyChange).toHaveBeenLastCalledWith(true))
    fireEvent.click(screen.getByRole('button', { name: 'Deactivate preset' }))
    await waitFor(() => expect(fetchMock).toHaveBeenLastCalledWith('/access/role-presets/preset-1/status', expect.objectContaining({ method: 'PATCH', body: { is_active: false, expected_version: 2, reason: 'Retire preset' } })))
    expect(await screen.findByRole('button', { name: 'Activate preset' })).toBeTruthy()
  })
})
