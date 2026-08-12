import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { useAccess } from './access-context'
import { AccessProvider } from './AccessProvider'

vi.mock('@/api/httpClient', () => ({
  clearAccessDeniedRecoveryHandler: vi.fn(),
  httpJson: vi.fn(),
  setAccessDeniedRecoveryHandler: vi.fn(),
}))
const accessHandoff = { condition: 'unresolved' } as const
vi.mock('@/features/auth', () => ({
  useAuth: () => ({ accessHandoff }),
}))

function StateProbe() {
  const { state } = useAccess()
  return <output>{state.status}</output>
}

describe('AccessProvider', () => {
  it('reads the controller state with its receiver bound during initialization', () => {
    render(<AccessProvider><StateProbe /></AccessProvider>)

    expect(screen.getByText('waiting-for-authentication')).toBeTruthy()
  })
})
