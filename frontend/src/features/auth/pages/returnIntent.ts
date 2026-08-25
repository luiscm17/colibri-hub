export function getSafeReturnIntent(value: string | null): string | null {
  if (!value || !value.startsWith('/') || value.startsWith('//')) return null
  if (/%(?![0-9a-fA-F]{2})/.test(value)) return null
  try {
    const url = new URL(value, window.location.origin)
    if (url.origin !== window.location.origin || ['/login', '/password-change'].includes(url.pathname)) return null
    return `${url.pathname}${url.search}${url.hash}`
  } catch { return null }
}
