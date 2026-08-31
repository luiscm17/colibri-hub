import { MantineProvider } from '@mantine/core'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { SpinningRoutePage } from './routes'

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: () => {}, removeEventListener: () => {} }) })

describe('SpinningRoutePage', () => {
  it('identifies the selected Yarn Spinning workspace and its unavailable integration', () => {
    render(<MantineProvider><SpinningRoutePage workspace="skeining" /></MantineProvider>)

    expect(screen.getByRole('heading', { name: 'Skeining' })).toBeTruthy()
    expect(screen.getByRole('status').textContent).toContain('integration is unavailable')
    expect(screen.queryByText('Lot Processing')).toBeNull()
    expect(screen.queryByText(/confirmed|calculated/i)).toBeNull()
  })
})
