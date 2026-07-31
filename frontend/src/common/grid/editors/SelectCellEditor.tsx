import { Select } from '@mantine/core'
import { useEffect, useRef } from 'react'
import type { RenderEditCellProps } from 'react-data-grid'

interface SelectCellEditorProps<TRow extends object> extends RenderEditCellProps<TRow> {
  data: Array<string | { value: string; label: string }>
}

export function SelectCellEditor<TRow extends object>({
  row,
  column,
  onClose,
  onRowChange,
  data,
}: SelectCellEditorProps<TRow>) {
  const ref = useRef<HTMLInputElement>(null)
  const key = column.key as keyof TRow

  useEffect(() => {
    ref.current?.focus()
    // Programmatically open the dropdown by dispatching a click
    ref.current?.click()
  }, [])

  return (
    <Select
      ref={ref}
      aria-label={String(column.name)}
      data={data}
      value={String(row[key] ?? '')}
      onChange={(value) => {
        if (value !== null) {
          onRowChange({ ...row, [key]: value as TRow[keyof TRow] }, true)
        }
      }}
      onKeyDown={(event) => {
        if (event.key === 'Escape') {
          onClose(false)
        }
      }}
      styles={{ input: { border: 0, borderRadius: 0, height: '100%', padding: '0 8px' } }}
    />
  )
}
