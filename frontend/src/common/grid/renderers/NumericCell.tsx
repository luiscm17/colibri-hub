interface NumericCellProps {
  value: number | null | undefined
  decimals?: number
}

export function NumericCell({ value, decimals }: NumericCellProps) {
  const isNullish = value === null || value === undefined || Number.isNaN(value)

  const display = isNullish
    ? '\u2014'
    : decimals !== undefined
      ? value.toFixed(decimals)
      : String(value)

  return (
    <span
      style={{
        display: 'block',
        textAlign: 'right',
        fontVariantNumeric: 'tabular-nums',
      }}
    >
      {display}
    </span>
  )
}
