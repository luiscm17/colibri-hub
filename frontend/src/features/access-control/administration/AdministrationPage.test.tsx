import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MantineProvider } from '@mantine/core'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '@/api/httpError'
import AdministrationPage from './AdministrationPage'
import { AccessAdministrationCollectionRecovery } from '../administration-route'

const fetchMock = vi.fn()
const USER_ID = '11111111-1111-4111-8111-111111111111'
const ROLE_ID = '22222222-2222-4222-8222-222222222222'
const PRESET_ID = '33333333-3333-4333-8333-333333333333'

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })
Object.defineProperty(window, 'ResizeObserver', { writable: true, value: class { observe() {} unobserve() {} disconnect() {} } })

vi.mock('@/api/httpClient', () => ({ httpJson: (...args: unknown[]) => fetchMock(...args) }))
vi.mock('@/features/access-control', () => ({ useAccess: () => ({ snapshot: { authorizationVersion: 1 } }) }))

function renderPage(path = '/access/users') {
  const router = createMemoryRouter([
    { path: '/access/scopes/:subjectId', element: <AccessAdministrationCollectionRecovery family="scopes" /> },
    { path: '/access/history/:subjectId', element: <AccessAdministrationCollectionRecovery family="history" /> },
    { path: '/access/:family/:subjectId/edit', element: <AdministrationPage mode="edit" /> },
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
    renderPage(`/access/users/${USER_ID}`)
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(`/access/users/${USER_ID}`, expect.anything()))
    expect(await screen.findByRole('heading', { name: 'Users' })).toBeTruthy()
  })

  it('captures and restores collection search, page, family, and selected subject', async () => {
    fetchMock
      .mockResolvedValueOnce({ items: [{ user_id: USER_ID, display_name: 'Ada', is_active: true }], page: 2, page_size: 50, total: 51 })
      .mockResolvedValueOnce({ user_id: USER_ID, display_name: 'Ada', is_active: true })
      .mockResolvedValueOnce({ items: [{ user_id: USER_ID, display_name: 'Ada', is_active: true }], page: 2, page_size: 50, total: 51 })
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

  it('restores preset create focus after Keep editing and focuses the collection after Discard', async () => {
    fetchMock.mockImplementation((path: string) => path === '/access/scope-definitions'
      ? Promise.resolve([])
      : Promise.resolve({ items: [], page: 1, page_size: 50, total: 0 }))
    const { router } = renderPage('/access/presets/new')
    fireEvent.change(await screen.findByLabelText('Preset name'), { target: { value: 'Draft preset' } })

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Keep editing' }))
    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Cancel' })))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect((screen.getByLabelText('Preset name') as HTMLInputElement).value).toBe('Draft preset')

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Discard changes' }))
    await waitFor(() => expect(router.state.location.pathname).toBe('/access/presets'))
    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole('heading', { name: 'Role presets' })))
  })

  it('opens collection create with complete origin and restores it on Cancel', async () => {
    fetchMock.mockResolvedValue({ items: [{ role_id: ROLE_ID, role_name: 'Operator', is_active: true }], page: 2, page_size: 50, total: 51 })
    const { router } = renderPage('/access/roles?q=Operator&page=2')
    fireEvent.click(await screen.findByRole('button', { name: 'Create role' }))
    expect(router.state.location.pathname).toBe('/access/roles/new')
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    await waitFor(() => expect(router.state.location.pathname + router.state.location.search).toBe('/access/roles?q=Operator&page=2'))
  })

  it('separates preset detail from edit and reconstructs adjustable role create', async () => {
    const preset = { preset_id: PRESET_ID, preset_code: 'operator', preset_name: 'Operator', description: 'Template', is_active: true, version: 1, permissions: [{ action: 'read', scope_code: 'warehouse' }] }
    fetchMock.mockImplementation((path: string) => path === `/access/role-presets/${PRESET_ID}` ? Promise.resolve(preset) : path === '/access/scopes?page=1&page_size=100' ? Promise.resolve({ items: [], total: 0 }) : Promise.resolve([]))
    const { router } = renderPage(`/access/presets/${PRESET_ID}`)
    expect(await screen.findByRole('button', { name: 'Edit preset' })).toBeTruthy()
    expect(screen.queryByLabelText('Preset name')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Start adjustable draft' }))
    expect(await screen.findByRole('heading', { name: 'Create role' })).toBeTruthy()
    expect((screen.getByLabelText('Role code') as HTMLInputElement).value).toBe('operator-copy')
    expect(router.state.location.pathname).toBe('/access/roles/new')
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    await waitFor(() => expect(router.state.location.pathname).toBe(`/access/presets/${PRESET_ID}`))
  })

  it('jumps from an empty page directly to the computed last page without cascading', async () => {
    fetchMock
      .mockResolvedValueOnce({ items: [], page: 999, page_size: 50, total: 101 })
      .mockResolvedValueOnce({ items: [{ role_id: ROLE_ID, role_name: 'Last role', is_active: true }], page: 3, page_size: 50, total: 101 })
    const { router } = renderPage('/access/roles?q=Last&page=999')

    expect(await screen.findByText('Last role')).toBeTruthy()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(fetchMock.mock.calls.map(([path]) => path)).toEqual([
      '/access/roles?page=999&page_size=50',
      '/access/roles?page=3&page_size=50',
    ])
    expect(router.state.location.search).toBe('?q=Last&page=3')
  })

  it.each([
    ['/access/roles/not-a-uuid', '/access/roles'],
    ['/access/presets/not-a-uuid/edit', '/access/presets'],
  ])('recovers malformed detail route %s before requesting protected data', async (path, collection) => {
    fetchMock.mockResolvedValue({ items: [], page: 1, page_size: 50, total: 0 })
    const { router } = renderPage(path)

    await waitFor(() => expect(router.state.location.pathname).toBe(collection))
    expect(fetchMock.mock.calls.some(([requestPath]) => String(requestPath).includes('not-a-uuid'))).toBe(false)
  })

  it('preserves a mounted role draft after declined navigation and leaves after confirmed departure', async () => {
    fetchMock.mockImplementation((path: string) => {
      if (path === `/access/roles/${ROLE_ID}`) return Promise.resolve({
        role_id: ROLE_ID,
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
      { path: '/access/roles', element: <AdministrationPage family="roles" /> },
    ], { initialEntries: [`/access/roles/${ROLE_ID}/edit`] })
    render(<MantineProvider><RouterProvider router={router} /></MantineProvider>)

    fireEvent.change(await screen.findByLabelText('Description'), { target: { value: 'Draft change' } })
    fireEvent.click(screen.getByRole('button', { name: 'Back to Roles' }))
    expect(await screen.findByText(/unsaved changes in role Operators/)).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Keep editing' }))
    expect(router.state.location.pathname).toBe(`/access/roles/${ROLE_ID}/edit`)
    expect((screen.getByLabelText('Description') as HTMLInputElement).value).toBe('Draft change')
    await waitFor(() => expect(screen.queryByText(/unsaved changes in role Operators/)).toBeNull())
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Back to Roles' })))

    fireEvent.click(screen.getByRole('button', { name: 'Back to Roles' }))
    expect(await screen.findByText(/unsaved changes in role Operators/)).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Discard changes' }))
    expect(await screen.findByRole('heading', { name: 'Roles' })).toBeTruthy()
    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole('heading', { name: 'Roles' })))
  })

  it('allows only RoleWorkflow to emit a confirmed shared-role PUT and reconciles the detail', async () => {
    const role = { role_id: ROLE_ID, role_code: 'operators', role_name: 'Operators', description: null, is_active: true, version: 1, permissions: [] }
    fetchMock.mockImplementation((path: string, options?: { method?: string }) => {
      if (path === `/access/roles/${ROLE_ID}` && options?.method === 'PUT') return Promise.resolve(role)
      if (path === `/access/roles/${ROLE_ID}/preview`) return Promise.resolve({ subject_version: 1, affected_user_count: 1, affected_users: [{ user_id: USER_ID, user_code: 'USR-1', display_name: 'Ada' }] })
      if (path === `/access/roles/${ROLE_ID}`) return Promise.resolve(role)
      if (path === '/access/scopes?page=1&page_size=100') return Promise.resolve({ items: [], page: 1, page_size: 50, total: 0 })
      if (path === '/access/scope-definitions') return Promise.resolve([])
      return Promise.resolve({ items: [], page: 1, page_size: 50, total: 0 })
    })
    renderPage(`/access/roles/${ROLE_ID}/edit`)

    fireEvent.change(await screen.findByLabelText('Description'), { target: { value: 'Updated responsibility' } })
    expect(screen.queryByText('Replace shared role permissions')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Preview role update' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Review role update' }))
    await screen.findByRole('dialog', { name: 'Confirm role update' })
    fireEvent.click(await screen.findByRole('button', { name: 'Confirm role update' }))

    await waitFor(() => expect(fetchMock.mock.calls.filter(([path, options]) => path === `/access/roles/${ROLE_ID}` && (options as { method?: string }).method === 'PUT')).toHaveLength(1))
    await waitFor(() => expect(screen.getByRole('status').textContent).toBe('Role saved.'))
    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole('status')))
  })

  it('retains and focuses the user-role success result after the reconciled version remounts', async () => {
    let version = 1
    fetchMock.mockImplementation((path: string, options?: { method?: string }) => {
      if (path === `/access/users/${USER_ID}`) return Promise.resolve({ user_id: USER_ID, display_name: 'Ada', roles: [{ role_id: 'role-a' }], version })
      if (path === `/access/users/${USER_ID}/roles/preview`) return Promise.resolve({ subject_version: 1, affected_user_count: 0, affected_users: [] })
      if (path === `/access/users/${USER_ID}/roles` && options?.method === 'PUT') { version = 2; return Promise.resolve(undefined) }
      return Promise.resolve({ items: [], page: 1, page_size: 50, total: 0 })
    })
    renderPage(`/access/users/${USER_ID}`)

    fireEvent.change(await screen.findByLabelText('Role IDs'), { target: { value: 'role-b' } })
    fireEvent.click(screen.getByRole('button', { name: 'Preview replacement' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Review replacement' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Confirm replacement' }))

    const result = (await screen.findByText('User roles replaced.')).closest('[role="status"]') as HTMLElement
    await waitFor(() => expect(document.activeElement).toBe(result))
    expect(fetchMock.mock.calls.filter(([path, options]) => path === `/access/users/${USER_ID}/roles` && (options as { method?: string }).method === 'PUT')).toHaveLength(1)
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
    const { router } = renderPage(`/access/users/${USER_ID}`)
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
