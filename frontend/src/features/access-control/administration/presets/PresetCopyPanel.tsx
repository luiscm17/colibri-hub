import { Alert, Button, Group, NativeSelect, Stack, Text, TextInput } from '@mantine/core'
import { useEffect, useEffectEvent, useRef, useState } from 'react'
import { httpJson } from '@/api/httpClient'
import { isApiError } from '@/api/httpError'
import { toPermissionInputs, type RegisteredScope } from '../forms/permission-adapter'
import { isSelectablePermission, type PermissionScope } from '../forms/matrix'
import { createAdjustableRoleDraft, createAdjustableRoleRequest, createExactPresetCopy, type PresetSnapshot } from './presets'

export function PresetCopyPanel({ preset, onDirtyChange }: { preset: PresetSnapshot; onDirtyChange(dirty: boolean): void }) {
  const reportDirty = useEffectEvent(onDirtyChange)
  const [roleCode, setRoleCode] = useState(`${preset.presetCode}-copy`)
  const [roleName, setRoleName] = useState(`${preset.presetName} copy`)
  const [message, setMessage] = useState<string | null>(null)
  const [draft, setDraft] = useState<ReturnType<typeof createAdjustableRoleDraft> | null>(null)
  const [reason, setReason] = useState('')
  const [scopes, setScopes] = useState<RegisteredScope[]>([])
  const [permissionScopes, setPermissionScopes] = useState<PermissionScope[]>([])
  const [action, setAction] = useState('')
  const [scopeCode, setScopeCode] = useState('')
  const [pending, setPending] = useState(false)
  const inFlight = useRef(false)

  useEffect(() => () => reportDirty(false), [])
  useEffect(() => { reportDirty(roleCode !== `${preset.presetCode}-copy` || roleName !== `${preset.presetName} copy` || reason !== '' || draft !== null) }, [draft, reason, roleCode, roleName, preset.presetCode, preset.presetName])

  async function startAdjustable() {
    setDraft(createAdjustableRoleDraft(preset, { roleCode, roleName }))
    try {
      const [page, definitions] = await Promise.all([
        httpJson<{ items: { scope_id: string; scope_code: string; is_active: boolean }[] }>('/access/scopes?page=1&page_size=100', { recoverAccessDenied: true }),
        httpJson<{ scope_code: string; supported_actions: string[] }[]>('/access/scope-definitions', { recoverAccessDenied: true }),
      ])
      setScopes(page.items.map((scope) => ({ scopeId: scope.scope_id, scopeCode: scope.scope_code, isActive: scope.is_active })))
      setPermissionScopes(page.items.map((scope) => ({ scopeId: scope.scope_id, scopeCode: scope.scope_code, isActive: scope.is_active, supportedActions: definitions.find((definition) => definition.scope_code === scope.scope_code)?.supported_actions ?? [] })))
    } catch (error) { setMessage(isApiError(error) ? error.message : 'Permission choices are unavailable.') }
  }

  async function submit(path: string, body: object, success: string) {
    if (inFlight.current || !reason.trim()) return
    inFlight.current = true; setPending(true); setMessage(null)
    try { await httpJson(path, { method: 'POST', body, recoverAccessDenied: true }); setReason(''); setMessage(success) }
    catch (error) { setMessage(isApiError(error) || error instanceof Error ? error.message : 'The role was not created.') }
    finally { inFlight.current = false; setPending(false) }
  }

  async function createExactCopy() {
    const request = createExactPresetCopy(preset, { roleCode, roleName, description: preset.description, reason: reason.trim() })
    await submit(request.path, request.body, 'Exact role copy created. Later preset changes do not synchronize.')
  }

  const removePermission = (removedAction: string, removedScope: string) => setDraft((current) => current ? { ...current, permissions: current.permissions.filter((permission) => permission.action !== removedAction || permission.scopeCode !== removedScope) } : null)
  const addPermission = () => {
    const permission = { action, scopeCode }
    if (!draft || !isSelectablePermission(permission, permissionScopes) || draft.permissions.some((item) => item.action === action && item.scopeCode === scopeCode)) return
    setDraft({ ...draft, permissions: [...draft.permissions, permission] })
  }

  return <Stack mt="md">
    <Text fw={500}>Create role from preset</Text>
    <Text size="sm">Each flow copies once; later preset changes do not synchronize.</Text>
    <TextInput label="Role code" value={roleCode} onChange={(event) => setRoleCode(event.currentTarget.value)} />
    <TextInput label="Role name" value={roleName} onChange={(event) => setRoleName(event.currentTarget.value)} />
    <TextInput label="Reason" value={reason} required onChange={(event) => setReason(event.currentTarget.value)} />
    <Group><Button disabled={pending || !reason.trim()} onClick={() => void createExactCopy()}>Create exact copy</Button><Button variant="default" onClick={() => void startAdjustable()}>Start adjustable draft</Button></Group>
    {message ? <Alert role="status">{message}</Alert> : null}
    {draft ? <><Alert>Adjustable draft is independent and contains {draft.permissions.length} copied permissions.</Alert><Group align="end"><NativeSelect label="Adjustable action" data={[{ value: '', label: 'Choose an action' }, ...(permissionScopes.find((scope) => scope.scopeCode === scopeCode)?.supportedActions ?? [])]} value={action} onChange={(event) => setAction(event.currentTarget.value)} /><NativeSelect label="Adjustable scope" data={[{ value: '', label: 'Choose a scope' }, ...permissionScopes.filter((scope) => scope.isActive).map((scope) => scope.scopeCode)]} value={scopeCode} onChange={(event) => { setScopeCode(event.currentTarget.value); setAction('') }} /><Button onClick={addPermission}>Add adjustable permission</Button></Group>{draft.permissions.map((permission) => <Group key={`${permission.action}:${permission.scopeCode}`}><Text>{permission.action}:{permission.scopeCode}</Text><Button variant="subtle" color="red" aria-label={`Remove adjustable ${permission.action}:${permission.scopeCode}`} onClick={() => removePermission(permission.action, permission.scopeCode)}>Remove</Button></Group>)}<Button disabled={pending || !reason.trim() || scopes.length === 0} onClick={() => { const request = createAdjustableRoleRequest(draft, toPermissionInputs(draft.permissions, scopes), reason.trim()); void submit(request.path, request.body, 'Adjustable role copy created.') }}>Create adjustable copy</Button></> : null}
  </Stack>
}
