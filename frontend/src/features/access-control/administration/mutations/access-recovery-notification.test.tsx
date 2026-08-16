import { MantineProvider } from '@mantine/core'
import { Notifications, notifications } from '@mantine/notifications'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ProtectedRoute } from '@/app/routes/protected-route'
import { AccessProvider } from '@/features/access-control'
import { RoleWorkflow } from '../roles/RoleWorkflow'
import { UserRoleReplacementPanel } from './UserRoleReplacementPanel'

const accessHandoff = { condition: 'eligible', accountId: 'account-1', handoffId: 'handoff-1' } as const
const USER_ID = '11111111-1111-4111-8111-111111111111'
const ROLE_ID = '22222222-2222-4222-8222-222222222222'
const RECOVERY_MESSAGE = 'Your access changed. Review the current access and preview again.'

vi.mock('@/features/auth', () => ({ useAuth: () => ({ accessHandoff }) }))

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })
Object.defineProperty(window, 'ResizeObserver', { writable: true, value: class { observe() {} unobserve() {} disconnect() {} } })

const accessResponse = (allowed: boolean) => ({
  user_id: 'admin-1', user_code: 'ADMIN-1', display_name: 'Administrator', is_active: true,
  authorization: { version: 1, is_global: true, actions: allowed ? ['manage_access'] : [], permissions: [] },
})
const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

function RecoveryHarness({ owner }: { owner: 'user' | 'role' }) {
  const content = owner === 'user'
    ? <UserRoleReplacementPanel userId={USER_ID} version={1} roleIds={['role-a']} />
    : <RoleWorkflow role={{ roleId: ROLE_ID, roleCode: 'operators', roleName: 'Operators', description: null, isActive: true, version: 1, permissions: [] }} onDirtyChange={vi.fn()} />
  return <MantineProvider><Notifications position="top-right" /><MemoryRouter><AccessProvider><ProtectedRoute requirement={{ action: 'manage_access', scope: 'access' }}>{content}</ProtectedRoute></AccessProvider></MemoryRouter></MantineProvider>
}

describe('Access administration recovery notifications', () => {
  afterEach(() => { cleanup(); notifications.clean(); vi.unstubAllGlobals() })

  it.each([
    ['user', true], ['user', false], ['role', true], ['role', false],
  ] as const)('preserves generic recovery notification when %s mutation refreshes to %s authority', async (owner, allowedAfterRefresh) => {
    let accessRequests = 0
    let resolveRefresh!: (value: Response) => void
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith('/access/me')) {
        accessRequests += 1
        return accessRequests === 1 ? Promise.resolve(response(accessResponse(true))) : new Promise<Response>((resolve) => { resolveRefresh = resolve })
      }
      if (url.endsWith('/access/scopes?page=1&page_size=100')) return Promise.resolve(response({ items: [], page: 1, page_size: 50, total: 0 }))
      if (url.endsWith('/access/scope-definitions')) return Promise.resolve(response([]))
      if (url.endsWith('/preview')) return Promise.resolve(response({ subject_version: 1, affected_user_count: 1, affected_users: [{ user_id: USER_ID, user_code: 'USR-1', display_name: 'Ada' }] }))
      if (init?.method === 'PUT') return Promise.resolve(response({ error: { code: 'access_denied', message: 'Denied' } }, 403))
      throw new Error(`Unexpected request: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<RecoveryHarness owner={owner} />)

    if (owner === 'user') fireEvent.change(await screen.findByLabelText('Role IDs'), { target: { value: 'role-b' } })
    else fireEvent.change(await screen.findByLabelText('Description'), { target: { value: 'Updated responsibility' } })
    fireEvent.click(screen.getByRole('button', { name: owner === 'user' ? 'Preview replacement' : 'Preview role update' }))
    fireEvent.click(await screen.findByRole('button', { name: owner === 'user' ? 'Review replacement' : 'Review role update' }))
    fireEvent.click(await screen.findByRole('button', { name: owner === 'user' ? 'Confirm replacement' : 'Confirm role update' }))

    await screen.findByLabelText('Loading access')
    expect(screen.queryByLabelText(owner === 'user' ? 'Role IDs' : 'Description')).toBeNull()
    resolveRefresh(response(accessResponse(allowedAfterRefresh)))

    expect(await screen.findByText(RECOVERY_MESSAGE)).toBeTruthy()
    expect(fetchMock.mock.calls.filter(([input, init]) => String(input).endsWith(owner === 'user' ? `/access/users/${USER_ID}/roles` : `/access/roles/${ROLE_ID}`) && (init as RequestInit | undefined)?.method === 'PUT')).toHaveLength(1)
    expect(fetchMock.mock.calls.filter(([input]) => String(input).endsWith('/preview'))).toHaveLength(1)
    expect(accessRequests).toBe(2)
    expect(screen.queryByText('Ada (USR-1)')).toBeNull()
    if (allowedAfterRefresh) await waitFor(() => expect(screen.getByLabelText(owner === 'user' ? 'Role IDs' : 'Description')).toBeTruthy())
    else await waitFor(() => expect(screen.queryByLabelText(owner === 'user' ? 'Role IDs' : 'Description')).toBeNull())
  })
})
