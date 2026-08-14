export type AdministrationFamily = 'users' | 'roles' | 'presets' | 'scopes' | 'history'

export type AdministrationOperation = Readonly<{
  family: AdministrationFamily
  title: string
  endpoint?: string
  id?: string
  label?: string
  request: 'collection' | 'detail' | 'none'
  renderer?: 'role-create' | 'role-edit' | 'preset-create' | 'preset-edit'
}>

export const ADMINISTRATION_OPERATION_MATRIX = {
  users: { collection: true, detail: true, create: false, edit: false },
  roles: { collection: true, detail: true, create: true, edit: true },
  presets: { collection: true, detail: true, create: true, edit: true },
  scopes: { collection: true, detail: false, create: false, edit: false },
  history: { collection: true, detail: false, create: false, edit: false },
} as const

export function collectionOnlyFamily(family: string): family is AdministrationFamily {
  return family in ADMINISTRATION_OPERATION_MATRIX && !ADMINISTRATION_OPERATION_MATRIX[family as AdministrationFamily].detail
}

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
    if (!ADMINISTRATION_OPERATION_MATRIX[key].create) {
      return key === 'presets' ? { family: key, title: config.title, request: 'none' } : null
    }
    return { family: key, title: config.title, request: 'none', renderer: key === 'presets' ? 'preset-create' : 'role-create' }
  }
  if (mode === 'edit') {
    if (!subjectId || (key !== 'roles' && key !== 'presets')) return null
    return { family: key, ...config, request: 'detail', renderer: key === 'presets' ? 'preset-edit' : 'role-edit' }
  }
  if (subjectId && (key === 'scopes' || key === 'history')) return null
  return { family: key, ...config, request: subjectId ? 'detail' : 'collection' }
}
