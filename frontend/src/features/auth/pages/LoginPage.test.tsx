import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MantineProvider } from '@mantine/core'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import LoginPage from './LoginPage'
import { getSafeReturnIntent } from './returnIntent'

const login = vi.fn()
const navigate = vi.fn()
let search = ''

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })
Object.defineProperty(window, 'ResizeObserver', { writable: true, value: class { observe() {} unobserve() {} disconnect() {} } })

vi.mock('../context/auth-context', () => ({ useAuth: () => ({ login }) }))
vi.mock('react-router', () => ({ useLocation: () => ({ search }), useNavigate: () => navigate }))

describe('LoginPage', () => {
  beforeEach(() => { login.mockReset(); navigate.mockReset(); search = '' })
  afterEach(cleanup)

  it.each([
    ['/warehouse/bales?tab=open', '/warehouse/bales?tab=open'],
    ['https://evil.test', null], ['//evil.test', null], ['/login', null], ['/%', null], ['warehouse/bales', null],
  ])('accepts only a normalized same-app return intent: %s', (value, expected) => {
    expect(getSafeReturnIntent(value)).toBe(expected)
  })

  it('keeps only the latest submission and focuses generic denial feedback', async () => {
    let rejectFirst!: () => void
    login.mockImplementationOnce(() => new Promise<void>((_, reject) => { rejectFirst = () => reject(new Error()) }))
      .mockResolvedValueOnce(undefined)
    render(<MantineProvider><LoginPage /></MantineProvider>)
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'user@example.test' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'first-secret' } })
    fireEvent.submit(screen.getByRole('button', { name: 'Sign in' }).closest('form')!)
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'second-secret' } })
    fireEvent.submit(screen.getByRole('button', { name: 'Sign in' }).closest('form')!)
    rejectFirst()
    await waitFor(() => expect(login).toHaveBeenCalledTimes(2))
    expect(screen.queryByRole('alert')).toBeNull()
  })
})
