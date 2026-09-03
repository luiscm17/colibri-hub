import { MantineProvider } from '@mantine/core'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { afterEach, describe, expect, it } from 'vitest'
import { renderTextEditor, type Column } from 'react-data-grid'
import { DataGridShell } from './DataGridShell'
import { DataGridStatusBar } from './DataGridStatusBar'

interface TestRow {
  readonly id: string
  readonly value: string
  readonly next: string
}

const columns: readonly Column<TestRow>[] = [
  { key: 'value', name: 'Value', width: 240, editable: true, renderEditCell: renderTextEditor },
  { key: 'next', name: 'Next', width: 180 },
]
const rows: readonly TestRow[] = [{ id: 'first', value: 'before', next: 'Navigation target' }]

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: () => {}, removeEventListener: () => {} }) })
Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', { writable: true, value: () => {} })

afterEach(cleanup)

describe('DataGrid accessibility', () => {
  it('keeps the grid label and provides a named focusable horizontal scroll region', () => {
    renderGrid()

    const region = screen.getByRole('region', { name: 'Horizontal scroll region for Editable test grid' })
    expect(region.tabIndex).toBe(0)
    expect(region.style.overflowX).toBe('auto')
    expect(screen.getByRole('grid', { name: 'Editable test grid' })).toBeTruthy()
  })

  it('supports keyboard editing and navigation', async () => {
    const user = userEvent.setup()
    renderGrid()

    const cell = screen.getByRole('gridcell', { name: 'before' })
    await user.click(cell)
    await user.keyboard('{Enter}updated{Enter}{ArrowRight}')

    expect(screen.getByRole('gridcell', { name: 'updated' })).toBeTruthy()
    expect(screen.getByRole('gridcell', { name: 'Navigation target' }).getAttribute('aria-selected')).toBe('true')
  })

  it('announces non-errors politely and preserves alert semantics for errors', () => {
    render(<MantineProvider><><DataGridStatusBar type="info" message="Saved locally." /><DataGridStatusBar type="error" message="rows require correction" count={2} /></></MantineProvider>)

    expect(screen.getByRole('status').getAttribute('aria-live')).toBe('polite')
    expect(screen.getByRole('alert').getAttribute('aria-live')).toBeNull()
    expect(screen.getByRole('alert').textContent).toContain('2 rows require correction')
  })
})

function renderGrid() {
  return render(
    <MantineProvider>
      <TestGrid />
    </MantineProvider>,
  )
}

function TestGrid() {
  const [currentRows, setRows] = useState(rows)

  return <DataGridShell
    aria-label="Editable test grid"
    columns={columns}
    rows={currentRows}
    rowKeyGetter={row => row.id}
    onRowsChange={setRows}
    style={{ minWidth: 640 }}
  />
}
