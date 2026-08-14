import { MantineProvider } from '@mantine/core'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '@/api/httpError'
import { PresetCopyPanel } from './PresetCopyPanel'

const fetchMock = vi.fn()
vi.mock('@/api/httpClient', () => ({ httpJson: (...args: unknown[]) => fetchMock(...args) }))
Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })

const preset = { presetId: 'preset-1', presetCode: 'operator', presetName: 'Operator', description: 'Template', permissions: [{ action: 'read', scopeCode: 'warehouse' }] }

describe('PresetCopyPanel', () => {
  beforeEach(() => fetchMock.mockReset())
  afterEach(cleanup)

  it('submits exact copies without permissions and preserves errors and draft fields', async () => {
    fetchMock.mockRejectedValueOnce(new ApiError({ kind: 'http', status: 409, message: 'Role code already exists' }))
    render(<MantineProvider><PresetCopyPanel preset={preset} onDirtyChange={vi.fn()} /></MantineProvider>)
    fireEvent.change(screen.getByLabelText('Role code'), { target: { value: 'custom-copy' } })
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: 'Exact copy' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create exact copy' }))
    expect(await screen.findByText('Role code already exists')).toBeTruthy()
    expect((screen.getByLabelText('Role code') as HTMLInputElement).value).toBe('custom-copy')
    expect(fetchMock).toHaveBeenCalledWith('/access/role-presets/preset-1/roles', expect.objectContaining({ body: expect.not.objectContaining({ permissions: expect.anything() }) }))
  })

  it('submits an independent adjustable snapshot as an ordinary role once', async () => {
    fetchMock.mockResolvedValueOnce({ items: [{ scope_id: 'scope-1', scope_code: 'warehouse', is_active: true }], total: 1 })
    fetchMock.mockResolvedValueOnce([{ scope_code: 'warehouse', supported_actions: ['read', 'write'] }])
    let resolveRole!: (value: unknown) => void
    fetchMock.mockReturnValueOnce(new Promise((resolve) => { resolveRole = resolve }))
    const { rerender } = render(<MantineProvider><PresetCopyPanel preset={preset} onDirtyChange={vi.fn()} /></MantineProvider>)
    fireEvent.click(screen.getByRole('button', { name: 'Start adjustable draft' }))
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: 'Adjust copy' } })
    await waitFor(() => expect(screen.getByRole('button', { name: 'Create adjustable copy' }).hasAttribute('disabled')).toBe(false))
    rerender(<MantineProvider><PresetCopyPanel preset={{ ...preset, permissions: [{ action: 'write', scopeCode: 'warehouse' }] }} onDirtyChange={vi.fn()} /></MantineProvider>)
    fireEvent.click(screen.getByRole('button', { name: 'Remove adjustable read:warehouse' }))
    fireEvent.change(screen.getByLabelText('Adjustable scope'), { target: { value: 'warehouse' } })
    fireEvent.change(screen.getByLabelText('Adjustable action'), { target: { value: 'write' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add adjustable permission' }))
    fireEvent.click(screen.getByRole('button', { name: 'Create adjustable copy' }))
    fireEvent.click(screen.getByRole('button', { name: 'Create adjustable copy' }))
    await waitFor(() => expect(fetchMock).toHaveBeenLastCalledWith('/access/roles', expect.objectContaining({ method: 'POST', body: expect.objectContaining({ permissions: [{ action: 'write', scope_id: 'scope-1' }] }) })))
    expect(fetchMock).toHaveBeenCalledTimes(3)
    resolveRole({ role_id: 'role-1' })
  })
})
