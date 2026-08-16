import { MantineProvider } from '@mantine/core'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { PresetDetailWorkflows } from './PresetDetailWorkflows'

const fetchMock = vi.fn((...args: unknown[]) => { void args; return Promise.resolve({ items: [], total: 0 }) })
vi.mock('@/api/httpClient', () => ({ httpJson: (...args: unknown[]) => fetchMock(...args) }))
Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })
Object.defineProperty(window, 'ResizeObserver', { writable: true, value: class { observe() {} unobserve() {} disconnect() {} } })

afterEach(cleanup)

describe('PresetDetailWorkflows', () => {
  it('keeps detail read-only while reporting copy draft dirtiness', async () => {
    const onDirtyChange = vi.fn()
    render(<MantineProvider><PresetDetailWorkflows preset={{ presetId: 'preset-1', presetCode: 'operator', presetName: 'Operator', description: null, isActive: true, version: 1, permissions: [] }} onDirtyChange={onDirtyChange} onStartAdjustable={vi.fn()} /></MantineProvider>)
    expect(screen.queryByLabelText('Preset name')).toBeNull()
    fireEvent.change(screen.getByLabelText('Role code'), { target: { value: 'changed-copy' } })
    await waitFor(() => expect(onDirtyChange).toHaveBeenLastCalledWith(true))
  })
})
