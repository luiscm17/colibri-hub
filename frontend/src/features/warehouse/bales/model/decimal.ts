const DECIMAL_PATTERN = /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/

type ScaledDecimal = Readonly<{ value: bigint; scale: number }>

export function isDecimal(value: string): boolean {
  return DECIMAL_PATTERN.test(value)
}

export function addDecimals(left: string, right: string): string {
  return formatScaled(add(toScaled(left), toScaled(right)))
}

export function subtractDecimals(left: string, right: string): string {
  const rightDecimal = toScaled(right)
  return formatScaled(add(toScaled(left), { ...rightDecimal, value: -rightDecimal.value }))
}

export function compareDecimals(left: string, right: string): number {
  const [normalizedLeft, normalizedRight] = align(toScaled(left), toScaled(right))
  return normalizedLeft.value === normalizedRight.value ? 0 : normalizedLeft.value > normalizedRight.value ? 1 : -1
}

function toScaled(input: string): ScaledDecimal {
  if (!isDecimal(input)) throw new Error(`Invalid decimal: ${input}`)

  const negative = input.startsWith('-')
  const unsigned = negative ? input.slice(1) : input
  const [whole, fraction = ''] = unsigned.split('.')
  const scale = fraction.length
  const value = BigInt(`${whole}${fraction}`) * (negative ? -1n : 1n)
  return { value, scale }
}

function add(left: ScaledDecimal, right: ScaledDecimal): ScaledDecimal {
  const [normalizedLeft, normalizedRight] = align(left, right)
  return { value: normalizedLeft.value + normalizedRight.value, scale: normalizedLeft.scale }
}

function align(left: ScaledDecimal, right: ScaledDecimal): [ScaledDecimal, ScaledDecimal] {
  const scale = Math.max(left.scale, right.scale)
  return [
    { value: left.value * 10n ** BigInt(scale - left.scale), scale },
    { value: right.value * 10n ** BigInt(scale - right.scale), scale },
  ]
}

function formatScaled({ value, scale }: ScaledDecimal): string {
  const sign = value < 0n ? '-' : ''
  const digits = (value < 0n ? -value : value).toString().padStart(scale + 1, '0')
  const whole = scale === 0 ? digits : digits.slice(0, -scale)
  const fraction = scale === 0 ? '' : digits.slice(-scale).replace(/0+$/, '')
  return `${sign}${whole}${fraction ? `.${fraction}` : ''}`
}
