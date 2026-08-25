import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MantineProvider } from '@mantine/core'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import AuthenticationHistoryPage from './AuthenticationHistoryPage'

const listAudits = vi.fn()

vi.mock('../api/authApi', () => ({ fetchAuthenticationAudits: (cursor?: string) => listAudits(cursor) }))

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })
Object.defineProperty(window, 'ResizeObserver', { writable: true, value: class { observe() {} unobserve() {} disconnect() {} } })

const entry = (auditId: string) => ({
  audit_id: auditId, operation_id: null, event_type: 'account_disabled', outcome: 'succeeded',
  affected_account_id: 'account-1', occurred_at: '2026-08-24T12:00:00Z', source: 'unrecognized-source',
})

function renderPage() {
  render(<MantineProvider><AuthenticationHistoryPage /></MantineProvider>)
}

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((resolvePromise, rejectPromise) => { resolve = resolvePromise; reject = rejectPromise })
  return { promise, resolve, reject }
}

describe('AuthenticationHistoryPage', () => {
  beforeEach(() => listAudits.mockReset())
  afterEach(cleanup)

  it('shows the empty state and end after an empty terminal page', async () => {
    listAudits.mockResolvedValue({ entries: [], cursor: null })
    renderPage()

    expect(await screen.findByText('No authentication history is available.')).toBeTruthy()
    expect(screen.getByText('End of authentication history.')).toBeTruthy()
  })

  it('appends the next cursor page and preserves unknown sources', async () => {
    listAudits.mockResolvedValueOnce({ entries: [entry('audit-1')], cursor: 'cursor-2' }).mockResolvedValueOnce({ entries: [entry('audit-2')], cursor: null })
    renderPage()

    expect(await screen.findByText('audit-1')).toBeTruthy()
    expect(screen.getByText('unrecognized-source')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Load more' }))
    expect(await screen.findByText('audit-2')).toBeTruthy()
    expect(listAudits).toHaveBeenNthCalledWith(2, 'cursor-2')
    expect(screen.getByText('End of authentication history.')).toBeTruthy()
  })

  it('keeps one row per audit when an opaque cursor continuation overlaps the current page', async () => {
    listAudits.mockResolvedValueOnce({ entries: [entry('audit-1')], cursor: 'opaque-cursor' }).mockResolvedValueOnce({ entries: [entry('audit-1'), entry('audit-2')], cursor: null })
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Load more' }))
    expect(await screen.findByText('audit-2')).toBeTruthy()
    expect(screen.getAllByText('audit-1')).toHaveLength(1)
    expect(listAudits).toHaveBeenNthCalledWith(2, 'opaque-cursor')
  })

  it('prevents repeated load-more clicks while a continuation is pending', async () => {
    const next = deferred<{ entries: ReturnType<typeof entry>[]; cursor: string | null }>()
    listAudits.mockResolvedValueOnce({ entries: [entry('audit-1')], cursor: 'cursor-2' }).mockReturnValueOnce(next.promise)
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Load more' }))
    fireEvent.click(screen.getByRole('button', { name: 'Loading more' }))
    expect(listAudits).toHaveBeenCalledTimes(2)
    next.resolve({ entries: [entry('audit-2')], cursor: null })
    expect(await screen.findByText('audit-2')).toBeTruthy()
  })

  it('retries an initial failure', async () => {
    listAudits.mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({ entries: [entry('audit-1')], cursor: null })
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Retry' }))
    expect(await screen.findByText('audit-1')).toBeTruthy()
    expect(listAudits).toHaveBeenCalledTimes(2)
  })

  it('retries a continuation while keeping the visible page', async () => {
    listAudits.mockResolvedValueOnce({ entries: [entry('audit-1')], cursor: 'cursor-2' }).mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({ entries: [entry('audit-2')], cursor: null })
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Load more' }))
    expect(await screen.findByRole('alert')).toBeTruthy()
    expect(screen.getByText('audit-1')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Retry loading more' }))
    expect(await screen.findByText('audit-2')).toBeTruthy()
  })

  it('rejects a stale continuation after refresh starts a new chain', async () => {
    const first = deferred<{ entries: ReturnType<typeof entry>[]; cursor: string | null }>()
    const second = deferred<{ entries: ReturnType<typeof entry>[]; cursor: string | null }>()
    const continuation = deferred<{ entries: ReturnType<typeof entry>[]; cursor: string | null }>()
    listAudits.mockReturnValueOnce(first.promise).mockReturnValueOnce(continuation.promise).mockReturnValueOnce(second.promise)
    renderPage()

    first.resolve({ entries: [entry('old')], cursor: 'old-cursor' })
    expect(await screen.findByText('old')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Load more' }))
    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }))
    second.resolve({ entries: [entry('fresh')], cursor: null })
    expect(await screen.findByText('fresh')).toBeTruthy()
    continuation.resolve({ entries: [entry('next')], cursor: null })
    await Promise.resolve()
    expect(screen.queryByText('next')).toBeNull()
    expect(screen.queryByText('old')).toBeNull()
  })
})
