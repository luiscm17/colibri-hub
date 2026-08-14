import { MantineProvider } from '@mantine/core'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { AdministrationShell } from './AdministrationShell'

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })

describe('AdministrationShell', () => {
  afterEach(cleanup)

  it('preserves a dirty draft on decline and restores the exact origin on confirmation', async () => {
    const navigate = vi.fn()
    const origin = { family: 'roles' as const, criteria: { q: 'spinner' }, page: 3, subjectId: 'selected-role' }
    const router = createMemoryRouter([{ path: '*', element: <AdministrationShell route={{ family: 'roles', criteria: {}, page: 1, subjectId: 'edited-role', mode: 'edit' }} origin={origin} navigate={navigate}>
      {({ requestDeparture, setDraftState }) => <><button onClick={() => setDraftState('role Operators', true)}>Change draft</button><button onClick={() => requestDeparture()}>Cancel edit</button></>}
    </AdministrationShell> }], { initialEntries: ['/access/roles/edited-role/edit'] })
    render(<MantineProvider><RouterProvider router={router} /></MantineProvider>)

    fireEvent.click(screen.getByText('Change draft'))
    fireEvent.click(screen.getByText('Cancel edit'))
    expect(await screen.findByText(/unsaved changes in role Operators/)).toBeTruthy()
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Keep editing' }))
    fireEvent.click(screen.getByRole('button', { name: 'Keep editing' }))
    expect(navigate).not.toHaveBeenCalled()

    fireEvent.click(screen.getByText('Cancel edit'))
    fireEvent.click(await screen.findByRole('button', { name: 'Discard changes' }))
    expect(navigate).toHaveBeenCalledWith(origin)
  })
})
