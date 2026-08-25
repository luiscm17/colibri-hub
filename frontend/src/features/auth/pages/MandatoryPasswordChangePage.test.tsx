import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MantineProvider } from '@mantine/core'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import MandatoryPasswordChangePage from './MandatoryPasswordChangePage'

const logout = vi.fn()
const revalidate = vi.fn()
const submitPasswordChange = vi.fn()

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })
Object.defineProperty(window, 'ResizeObserver', { writable: true, value: class { observe() {} unobserve() {} disconnect() {} } })

vi.mock('../context/auth-context', () => ({
  useAuth: () => ({ logout, revalidate }),
}))

vi.mock('../api/authApi', () => ({
  submitPasswordChange: (...args: unknown[]) => submitPasswordChange(...args),
}))

describe('MandatoryPasswordChangePage', () => {
  beforeEach(() => {
    logout.mockReset()
    revalidate.mockReset()
    submitPasswordChange.mockReset()
  })

  afterEach(cleanup)

  it('clears password fields and logs out after a successful replacement without revalidation', async () => {
    submitPasswordChange.mockResolvedValue(undefined)
    logout.mockResolvedValue(undefined)
    render(<MantineProvider><MandatoryPasswordChangePage /></MantineProvider>)

    fireEvent.change(screen.getByLabelText('Current password'), { target: { value: 'provisional-password' } })
    fireEvent.change(screen.getByLabelText('New password'), { target: { value: 'established-password' } })
    fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'established-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Change password' }))

    await waitFor(() => expect(logout).toHaveBeenCalledTimes(1))

    expect(submitPasswordChange).toHaveBeenCalledWith('provisional-password', 'established-password')
    expect((screen.getByLabelText('Current password') as HTMLInputElement).value).toBe('')
    expect((screen.getByLabelText('New password') as HTMLInputElement).value).toBe('')
    expect((screen.getByLabelText('Confirm new password') as HTMLInputElement).value).toBe('')
    expect(revalidate).not.toHaveBeenCalled()
  })

  it('rejects equal replacement passwords before calling the API', () => {
    render(<MantineProvider><MandatoryPasswordChangePage /></MantineProvider>)
    fireEvent.change(screen.getByLabelText('Current password'), { target: { value: 'same-secret' } })
    fireEvent.change(screen.getByLabelText('New password'), { target: { value: 'same-secret' } })
    fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'same-secret' } })
    fireEvent.click(screen.getByRole('button', { name: 'Change password' }))
    expect(screen.getByText('The new password must be different from the current one.')).toBeTruthy()
    expect(submitPasswordChange).not.toHaveBeenCalled()
  })

  it('confirms dirty sign-out and clears all secrets when discarded', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
    logout.mockResolvedValue(undefined)
    render(<MantineProvider><MandatoryPasswordChangePage /></MantineProvider>)
    fireEvent.change(screen.getByLabelText('Current password'), { target: { value: 'provisional-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign out instead' }))
    await waitFor(() => expect(logout).toHaveBeenCalledTimes(1))
    expect(confirm).toHaveBeenCalled()
    expect((screen.getByLabelText('Current password') as HTMLInputElement).value).toBe('')
    confirm.mockRestore()
  })
})
