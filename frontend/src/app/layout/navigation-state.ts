import type { NavItem } from '../navigation-data'
import { ACCESS_CATALOG } from '@/features/access-control'

export function canDisplayNavigationItem(item: NavItem, allows: (path: keyof typeof ACCESS_CATALOG) => boolean): boolean {
  if (!item.path || item.displayWithoutAccess) return true
  return allows(item.path)
}

export function deriveNavigation(items: NavItem[], isAllowed: (item: NavItem) => boolean): NavItem[] {
  return items.flatMap((item) => {
    if (item.children) {
      const children = item.children.filter(isAllowed)
      return children.length === 0 ? [] : [{ ...item, children }]
    }
    return isAllowed(item) ? [item] : []
  })
}
