import { describe, expect, it } from 'vitest'

const accessSource = Object.entries(import.meta.glob('../**/*.{ts,tsx}', {
  query: '?raw', import: 'default', eager: true,
})).filter(([path]) => !path.endsWith('.test.ts') && !path.endsWith('.test.tsx')).map(([, source]) => source).join('\n')

describe('Access compliance evidence ledger', () => {
  it('keeps the Access capability free of retired authorities', () => {
    expect(accessSource).not.toMatch(/\bMutationGate\b|\bGovernancePanel\b|from ['"].*\/governance['"]/);
  })
})
