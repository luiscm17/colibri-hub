import { useEffect } from 'react'
import { useLocation } from 'react-router'
import { navData } from '@/app/navigation-data'

function resolveTitle(pathname: string): string {
  for (const section of navData) {
    for (const child of section.children ?? []) {
      if (child.path === pathname) return child.label
    }
  }

  const overrides: Record<string, string> = {
    '/profile': 'Mi perfil',
  }

  return overrides[pathname] ?? 'Yarn EPR'
}

export function usePageTitle() {
  const { pathname } = useLocation()

  useEffect(() => {
    const label = resolveTitle(pathname)
    document.title = `${label} — Yarn EPR`
  }, [pathname])
}
