import { describe, expect, it } from 'vitest'
import { deriveNavigation } from './navigation-state'
import type { NavItem } from '../navigation-data'

describe('deriveNavigation', () => {
  it('omits denied leaves and their empty groups without inferring authority', () => {
    const items: NavItem[] = [{ label: 'Group', children: [
      { label: 'Allowed', path: '/warehouse/bales' },
      { label: 'Denied', path: '/warehouse/supplies' },
    ] }]

    expect(deriveNavigation(items, (item) => item.path === '/warehouse/bales')).toEqual([
      { label: 'Group', children: [{ label: 'Allowed', path: '/warehouse/bales' }] },
    ])
    expect(deriveNavigation(items, () => false)).toEqual([])
  })
})
