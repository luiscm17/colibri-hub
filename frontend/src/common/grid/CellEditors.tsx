import { TextInput } from '@mantine/core'
import type { RenderEditCellProps } from 'react-data-grid'

type GridEditorProps<TRow extends object> = RenderEditCellProps<TRow>

export function TextCellEditor<TRow extends object>(props: GridEditorProps<TRow>) {
  return <GridTextInput {...props} inputMode="text" />
}

export function DecimalCellEditor<TRow extends object>(props: GridEditorProps<TRow>) {
  return <GridTextInput {...props} inputMode="decimal" />
}

function GridTextInput<TRow extends object>({
  row,
  column,
  onClose,
  onRowChange,
  inputMode,
}: GridEditorProps<TRow> & { inputMode: 'decimal' | 'text' }) {
  const key = column.key as keyof TRow
  return (
    <TextInput
      aria-label={String(column.name)}
      autoFocus
      inputMode={inputMode}
      value={String(row[key] ?? '')}
      onBlur={() => onClose(true)}
      onChange={(event) => onRowChange({ ...row, [key]: event.currentTarget.value })}
      onKeyDown={(event) => {
        if (event.key === 'Escape') onClose(false)
        if (event.key === 'Enter') onClose(true)
      }}
      styles={{ input: { border: 0, borderRadius: 0, height: '100%', padding: '0 8px' } }}
    />
  )
}
