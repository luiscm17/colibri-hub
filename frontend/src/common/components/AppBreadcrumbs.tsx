import { Breadcrumbs as MantineBreadcrumbs, Anchor, Text } from '@mantine/core'
import { useLocation } from 'react-router'
import { navData } from '@/app/navigation-data'

type Crumb = { label: string; path?: string }

/**
 * Resuelve la jerarquía de navegación a partir del path actual
 * recorriendo la estructura navData (sección > página).
 */
function resolveBreadcrumbs(pathname: string): Crumb[] {
  for (const section of navData) {
    for (const child of section.children ?? []) {
      if (child.path === pathname) {
        return [
          { label: section.label },
          { label: child.label, path: child.path },
        ]
      }
    }
  }
  return []
}

export function AppBreadcrumbs() {
  const location = useLocation()
  const crumbs = resolveBreadcrumbs(location.pathname)

  if (crumbs.length === 0) return null

  return (
    <MantineBreadcrumbs
      separator="/"
      separatorMargin="xs"
      mb="md"
      style={{ fontSize: 'var(--mantine-font-size-sm)' }}
    >
      {crumbs.map((crumb, i) => {
        const isLast = i === crumbs.length - 1
        return isLast ? (
          <Text key={crumb.label} c="dimmed" size="sm">
            {crumb.label}
          </Text>
        ) : (
          <Anchor key={crumb.label} size="sm" c="dimmed">
            {crumb.label}
          </Anchor>
        )
      })}
    </MantineBreadcrumbs>
  )
}
