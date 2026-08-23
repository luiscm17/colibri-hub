import { describe, expect, it } from 'vitest'
import { deriveNavigation } from './navigation-state'
import { navData, type NavItem } from '../navigation-data'
import { ACCESS_CATALOG } from '@/features/access-control'

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

  it('shows Accounts only for the canonical Access catalog requirement', () => {
    const accounts = navData.find((item) => item.label === 'Acceso')?.children?.find((item) => item.path === '/auth/accounts')
    expect(accounts).toBeDefined()
    expect(ACCESS_CATALOG['/auth/accounts']).toEqual({ action: 'manage_access', scope: 'access_control' })
    expect(deriveNavigation([accounts!], (item) => item.path === '/auth/accounts')).toHaveLength(1)
    expect(deriveNavigation([accounts!], () => false)).toEqual([])
  })
})
