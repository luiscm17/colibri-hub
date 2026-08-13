export type AdministrationFamily = 'users' | 'roles' | 'presets' | 'scopes' | 'history'

export type AdministrationOperation = Readonly<{
  family: AdministrationFamily
  title: string
  endpoint?: string
  id?: string
  label?: string
  request: 'collection' | 'detail' | 'none'
}>

const families = {
  users: { title: 'Users', endpoint: '/access/users', id: 'user_id', label: 'display_name' },
  roles: { title: 'Roles', endpoint: '/access/roles', id: 'role_id', label: 'role_name' },
  presets: { title: 'Role presets', endpoint: '/access/role-presets', id: 'preset_id', label: 'preset_name' },
  scopes: { title: 'Scopes', endpoint: '/access/scopes', id: 'scope_id', label: 'scope_name' },
  history: { title: 'Access history', endpoint: '/access/audits', label: 'change_kind' },
} as const

export function resolveAdministrationOperation(
  family: string | undefined,
  subjectId?: string,
  mode?: 'edit',
): AdministrationOperation | null {
  if (!family || !(family in families)) return null
  const key = family as AdministrationFamily
  const config = families[key]

  if (subjectId === 'new') {
    if (key !== 'roles' && key !== 'presets') return null
    return { family: key, title: config.title, request: 'none' }
  }
  if (mode === 'edit') {
    if (!subjectId || (key !== 'roles' && key !== 'presets')) return null
    return { family: key, title: config.title, request: 'none' }
  }
  if (subjectId && (key === 'scopes' || key === 'history')) return null
  return { family: key, ...config, request: subjectId ? 'detail' : 'collection' }
}
