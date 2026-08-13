export type PresetSnapshot = Readonly<{
  presetId: string
  presetCode: string
  presetName: string
  description: string | null
  permissions: readonly Readonly<{ action: string; scopeCode: string }>[]
}>

type RoleDetails = Readonly<{ roleCode: string; roleName: string; description: string | null }>

export function createExactPresetCopy(preset: PresetSnapshot, role: RoleDetails & { reason: string }) {
  return {
    path: `/access/role-presets/${preset.presetId}/roles`,
    method: 'POST' as const,
    body: { role_code: role.roleCode, role_name: role.roleName, description: role.description, reason: role.reason },
  }
}

export function createAdjustableRoleDraft(preset: PresetSnapshot, role: Omit<RoleDetails, 'description'> & Partial<Pick<RoleDetails, 'description'>>) {
  return {
    sourcePresetId: preset.presetId,
    roleCode: role.roleCode,
    roleName: role.roleName,
    description: role.description ?? preset.description,
    permissions: preset.permissions.map((permission) => ({ ...permission })),
  }
}
