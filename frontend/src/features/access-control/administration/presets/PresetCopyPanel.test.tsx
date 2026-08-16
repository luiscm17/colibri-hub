import { MantineProvider } from '@mantine/core'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
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
    render(<MantineProvider><PresetCopyPanel preset={preset} onDirtyChange={vi.fn()} onStartAdjustable={vi.fn()} /></MantineProvider>)
    fireEvent.change(screen.getByLabelText('Role code'), { target: { value: 'custom-copy' } })
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: 'Exact copy' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create exact copy' }))
    expect(await screen.findByText('Role code already exists')).toBeTruthy()
    expect((screen.getByLabelText('Role code') as HTMLInputElement).value).toBe('custom-copy')
    expect(fetchMock).toHaveBeenCalledWith('/access/role-presets/preset-1/roles', expect.objectContaining({ body: expect.not.objectContaining({ permissions: expect.anything() }) }))
  })

  it('delegates adjustable copies to the addressable role draft transition', () => {
    const onStartAdjustable = vi.fn()
    render(<MantineProvider><PresetCopyPanel preset={preset} onDirtyChange={vi.fn()} onStartAdjustable={onStartAdjustable} /></MantineProvider>)
    fireEvent.click(screen.getByRole('button', { name: 'Start adjustable draft' }))
    expect(onStartAdjustable).toHaveBeenCalledOnce()
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
