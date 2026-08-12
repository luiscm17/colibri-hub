import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MantineProvider } from '@mantine/core'
import { MemoryRouter, Route, Routes } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '@/api/httpError'
import AdministrationPage from './AdministrationPage'

const fetchMock = vi.fn()

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })

vi.mock('@/api/httpClient', () => ({ httpJson: (...args: unknown[]) => fetchMock(...args) }))

function renderPage(path = '/access/users') {
  return render(<MantineProvider><MemoryRouter initialEntries={[path]}><Routes><Route path="/access/:family/:subjectId?" element={<AdministrationPage />} /></Routes></MemoryRouter></MantineProvider>)
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

  it('sends only supported history filters', async () => {
    fetchMock.mockResolvedValue({ items: [], page: 1, page_size: 50, total: 0 })
    renderPage('/access/history')
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith('/access/audits?page=1&page_size=50', expect.anything()))
    await screen.findByLabelText('Subject Type')
    fireEvent.change(screen.getByLabelText('Subject Type'), { target: { value: 'user' } })
    await waitFor(() => expect(fetchMock).toHaveBeenLastCalledWith('/access/audits?page=1&page_size=50&subject_type=user', expect.anything()))
  })

  it('silently handles an aborted collection request during filter navigation', async () => {
    fetchMock.mockRejectedValueOnce(new ApiError({ kind: 'aborted', message: 'cancelled' }))
    renderPage('/access/history')
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(await screen.findByLabelText('Loading administration')).toBeTruthy()
  })

  it('presents non-abort collection failures instead of treating them as cancellation', async () => {
    fetchMock.mockRejectedValueOnce(new ApiError({ kind: 'network', message: 'offline' }))
    renderPage()
    expect(await screen.findByText('The administration data is unavailable.')).toBeTruthy()
  })
})
