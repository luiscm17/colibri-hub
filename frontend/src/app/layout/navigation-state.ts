import type { NavItem } from '../navigation-data'

export function deriveNavigation(items: NavItem[], isAllowed: (item: NavItem) => boolean): NavItem[] {
  return items.flatMap((item) => {
    if (item.children) {
      const children = item.children.filter(isAllowed)
      return children.length === 0 ? [] : [{ ...item, children }]
    }
    return isAllowed(item) ? [item] : []
  })
}
