import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MantineProvider } from '@mantine/core'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '@/api/httpError'
import AdministrationPage from './AdministrationPage'
import { AccessAdministrationCollectionRecovery } from '../administration-route'

const fetchMock = vi.fn()

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })
Object.defineProperty(window, 'ResizeObserver', { writable: true, value: class { observe() {} unobserve() {} disconnect() {} } })

vi.mock('@/api/httpClient', () => ({ httpJson: (...args: unknown[]) => fetchMock(...args) }))
vi.mock('@/features/access-control', () => ({ useAccess: () => ({ snapshot: { authorizationVersion: 1 } }) }))

function renderPage(path = '/access/users') {
  const router = createMemoryRouter([
    { path: '/access/scopes/:subjectId', element: <AccessAdministrationCollectionRecovery family="scopes" /> },
    { path: '/access/history/:subjectId', element: <AccessAdministrationCollectionRecovery family="history" /> },
    { path: '/access/:family/:subjectId?', element: <AdministrationPage /> },
  ], { initialEntries: [path] })
  return { ...render(<MantineProvider><RouterProvider router={router} /></MantineProvider>), router }
}

describe('AdministrationPage', () => {
  beforeEach(() => fetchMock.mockReset())
  afterEach(cleanup)

  it('loads only the latest collection page and labels local no-match results', async () => {
    fetchMock.mockResolvedValueOnce({ items: [{ user_id: 'first', display_name: 'First', user_code: 'F1', is_active: true }], page: 1, page_size: 50, total: 51 })
    fetchMock.mockResolvedValueOnce({ items: [{ user_id: 'second', display_name: 'Second', user_code: 'S2', is_active: true }], page: 2, page_size: 50, total: 51 })
    renderPage()
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    await screen.findByText('First')
    fireEvent.click(screen.getByRole('button', { name: 'Next page' }))
    expect(await screen.findByText('Second')).toBeTruthy()
    expect(screen.queryByText('First')).toBeNull()
    fireEvent.change(screen.getByLabelText('Filter loaded page'), { target: { value: 'missing' } })
    expect(screen.getByText('No matches on this loaded page.')).toBeTruthy()
  })

  it('loads an addressable user directly and returns to its collection when missing', async () => {
    fetchMock.mockRejectedValueOnce(new ApiError({ kind: 'http', status: 404, message: 'Not found' }))
    fetchMock.mockResolvedValueOnce({ items: [], page: 1, page_size: 50, total: 0 })
    renderPage('/access/users/missing')
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith('/access/users/missing', expect.anything()))
    expect(await screen.findByRole('heading', { name: 'Users' })).toBeTruthy()
  })

  it('captures and restores collection search, page, family, and selected subject', async () => {
    fetchMock
      .mockResolvedValueOnce({ items: [{ user_id: 'user-1', display_name: 'Ada', is_active: true }], page: 2, page_size: 50, total: 51 })
      .mockResolvedValueOnce({ user_id: 'user-1', display_name: 'Ada', is_active: true })
      .mockResolvedValueOnce({ items: [{ user_id: 'user-1', display_name: 'Ada', is_active: true }], page: 2, page_size: 50, total: 51 })
    renderPage('/access/users?q=Ada&page=2')

    fireEvent.click(await screen.findByRole('button', { name: 'Ada' }))
    expect(await screen.findByRole('button', { name: 'Back to Users' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Back to Users' }))

    expect((await screen.findByLabelText('Filter loaded page') as HTMLInputElement).value).toBe('Ada')
    expect(fetchMock).toHaveBeenLastCalledWith('/access/users?page=2&page_size=50', expect.anything())
  })

  it('renders the preset workflow for a direct create route', async () => {
    fetchMock.mockResolvedValueOnce({ items: [], page: 1, page_size: 50, total: 0 })
    renderPage('/access/presets/new')

    expect(await screen.findByRole('heading', { name: 'Create preset' })).toBeTruthy()
    expect(screen.queryByText('Create role')).toBeNull()
    expect(fetchMock).toHaveBeenCalledWith('/access/scopes?page=1&page_size=100', expect.anything())
  })

  it('preserves a mounted role draft after declined navigation and leaves after confirmed departure', async () => {
    fetchMock.mockImplementation((path: string) => {
      if (path === '/access/roles/role-1') return Promise.resolve({
        role_id: 'role-1',
        role_code: 'operators',
        role_name: 'Operators',
        description: null,
        is_active: true,
        version: 1,
        permissions: [],
      })
      if (path === '/access/scopes?page=1&page_size=100') return Promise.resolve({ items: [], page: 1, page_size: 50, total: 0 })
      if (path === '/access/scope-definitions') return Promise.resolve([])
      return Promise.resolve({ items: [], page: 1, page_size: 50, total: 0 })
    })
    const router = createMemoryRouter([
      { path: '/access/roles/:subjectId/edit', element: <AdministrationPage family="roles" mode="edit" /> },
      { path: '/elsewhere', element: <p>Elsewhere</p> },
    ], { initialEntries: ['/access/roles/role-1/edit'] })
    render(<MantineProvider><RouterProvider router={router} /></MantineProvider>)

    fireEvent.change(await screen.findByLabelText('Description'), { target: { value: 'Draft change' } })
    const declinedDeparture = router.navigate('/elsewhere')
    expect(await screen.findByText(/unsaved changes in role Operators/)).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Keep editing' }))
    await declinedDeparture
    expect(router.state.location.pathname).toBe('/access/roles/role-1/edit')
    expect((screen.getByLabelText('Description') as HTMLInputElement).value).toBe('Draft change')
    await waitFor(() => expect(screen.queryByText(/unsaved changes in role Operators/)).toBeNull())

    const confirmedDeparture = router.navigate('/elsewhere')
    expect(await screen.findByText(/unsaved changes in role Operators/)).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Discard changes' }))
    await confirmedDeparture
    expect(await screen.findByText('Elsewhere')).toBeTruthy()
  })

  it('sends only supported history filters', async () => {
    fetchMock.mockResolvedValue({ items: [], page: 1, page_size: 50, total: 0 })
    renderPage('/access/history')
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith('/access/audits?page=1&page_size=50', expect.anything()))
    await screen.findByLabelText('Subject Type')
    fireEvent.change(screen.getByLabelText('Subject Type'), { target: { value: 'user' } })
    await waitFor(() => expect(fetchMock).toHaveBeenLastCalledWith('/access/audits?page=1&page_size=50&subject_type=user', expect.anything()))
  })

  it.each(['/access/scopes/scope-1', '/access/history/audit-1'])('recovers unsupported detail %s to its collection without a detail request', async (path) => {
    fetchMock.mockResolvedValue({ items: [], page: 1, page_size: 50, total: 0 })
    const { container } = renderPage(path)

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(path.includes('/scopes/') ? 2 : 1))
    expect(fetchMock.mock.calls.some(([requestPath]) => requestPath === path.replace('/access', ''))).toBe(false)
    expect(fetchMock.mock.calls.some(([requestPath]) => String(requestPath).includes('preview') || String(requestPath).includes('before') || String(requestPath).includes('confirmation'))).toBe(false)
    expect(container.querySelector('a[href*="scope-1"], a[href*="audit-1"]')).toBeNull()
  })

  it('silently handles an aborted collection request during filter navigation', async () => {
    fetchMock.mockRejectedValueOnce(new ApiError({ kind: 'aborted', message: 'cancelled' }))
    renderPage('/access/history')
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(await screen.findByLabelText('Loading administration')).toBeTruthy()
  })

  it('ignores a stale denied response after a newer collection succeeds', async () => {
    let rejectStale!: (error: unknown) => void
    fetchMock
      .mockReturnValueOnce(new Promise((_, reject) => { rejectStale = reject }))
      .mockResolvedValueOnce({ items: [{ audit_id: 'audit-2', change_kind: 'newer' }], page: 1, page_size: 50, total: 1 })
    const { router } = renderPage('/access/history')
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))

    await router.navigate('/access/history?subject_type=user')
    expect(await screen.findByText('newer')).toBeTruthy()
    rejectStale(new ApiError({ kind: 'http', status: 403, message: 'Denied' }))

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2))
    expect(router.state.location.search).toBe('?subject_type=user')
    expect(screen.getByText('newer')).toBeTruthy()
  })

  it('ignores a stale missing detail response after its collection succeeds', async () => {
    let rejectStale!: (error: unknown) => void
    fetchMock
      .mockReturnValueOnce(new Promise((_, reject) => { rejectStale = reject }))
      .mockResolvedValueOnce({ items: [{ user_id: 'user-2', display_name: 'Newer user', is_active: true }], page: 1, page_size: 50, total: 1 })
    const { router } = renderPage('/access/users/missing')
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))

    await router.navigate('/access/users')
    expect(await screen.findByText('Newer user')).toBeTruthy()
    rejectStale(new ApiError({ kind: 'http', status: 404, message: 'Missing' }))

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2))
    expect(router.state.location.pathname).toBe('/access/users')
    expect(screen.getByText('Newer user')).toBeTruthy()
  })

  it('presents non-abort collection failures instead of treating them as cancellation', async () => {
    fetchMock.mockRejectedValueOnce(new ApiError({ kind: 'network', message: 'offline' }))
    renderPage()
    expect(await screen.findByText('The administration data is unavailable.')).toBeTruthy()
  })
})
