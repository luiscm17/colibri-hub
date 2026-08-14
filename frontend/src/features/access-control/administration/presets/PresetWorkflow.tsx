import { Alert, Button, Group, NativeSelect, Stack, Text, TextInput } from '@mantine/core'
import { useEffect, useEffectEvent, useMemo, useRef, useState } from 'react'
import { httpJson } from '@/api/httpClient'
import { isApiError } from '@/api/httpError'
import { isSelectablePermission, permissionReferenceState, type PermissionScope } from '../forms/matrix'
import { toPermissionInputs, type PermissionDraft, type RegisteredScope } from '../forms/permission-adapter'

export type PresetWorkflowPreset = Readonly<{ presetId: string; presetCode: string; presetName: string; description: string | null; isActive: boolean; version: number; permissions: readonly PermissionDraft[] }>
type ScopeResponse = { scope_id: string; scope_code: string; is_active: boolean }
type DefinitionResponse = { scope_code: string; supported_actions: string[] }
type Page<T> = { items: T[] }
const errorMessage = (error: unknown) => isApiError(error) || error instanceof Error ? error.message : 'The preset was not saved.'

export function PresetWorkflow({ preset, onDirtyChange }: { preset?: PresetWorkflowPreset; onDirtyChange(dirty: boolean): void }) {
  const reportDirty = useEffectEvent(onDirtyChange)
  const [presetCode, setPresetCode] = useState(preset?.presetCode ?? '')
  const [presetName, setPresetName] = useState(preset?.presetName ?? '')
  const [description, setDescription] = useState(preset?.description ?? '')
  const [reason, setReason] = useState('')
  const [drafts, setDrafts] = useState<PermissionDraft[]>([...(preset?.permissions ?? [])])
  const [action, setAction] = useState('')
  const [scopeCode, setScopeCode] = useState('')
  const [scopes, setScopes] = useState<RegisteredScope[]>([])
  const [permissionScopes, setPermissionScopes] = useState<PermissionScope[]>([])
  const [message, setMessage] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [blocked, setBlocked] = useState(false)
  const [isActive, setIsActive] = useState(preset?.isActive ?? true)
  const [version, setVersion] = useState(preset?.version ?? 0)
  const inFlight = useRef(false)

  useEffect(() => {
    const controller = new AbortController()
    void Promise.all([
      httpJson<Page<ScopeResponse>>('/access/scopes?page=1&page_size=100', { signal: controller.signal, recoverAccessDenied: true }),
      httpJson<DefinitionResponse[]>('/access/scope-definitions', { signal: controller.signal, recoverAccessDenied: true }),
    ]).then(([registered, definitions]) => {
      const definitionsByCode = new Map(definitions.map((definition) => [definition.scope_code, definition]))
      const nextScopes = registered.items.map((scope) => ({ scopeId: scope.scope_id, scopeCode: scope.scope_code, isActive: scope.is_active }))
      setScopes(nextScopes)
      setPermissionScopes(nextScopes.map((scope) => ({ ...scope, supportedActions: definitionsByCode.get(scope.scopeCode)?.supported_actions ?? [] })))
    }).catch((error: unknown) => { if (!isApiError(error) || error.kind !== 'aborted') setMessage('Permission choices are unavailable.') })
    return () => controller.abort()
  }, [])
  const inactive = useMemo(() => drafts.filter((draft) => permissionReferenceState(draft, permissionScopes) === 'inactive'), [drafts, permissionScopes])
  const unsupported = useMemo(() => drafts.filter((draft) => permissionReferenceState(draft, permissionScopes) === 'unsupported'), [drafts, permissionScopes])
  const dirty = presetCode !== (preset?.presetCode ?? '') || presetName !== (preset?.presetName ?? '') || description !== (preset?.description ?? '') || reason !== '' || JSON.stringify(drafts) !== JSON.stringify(preset?.permissions ?? [])
  useEffect(() => () => reportDirty(false), [])
  useEffect(() => { reportDirty(dirty) }, [dirty])

  const mutate = async (status?: boolean) => {
    if (inFlight.current || !reason.trim() || (status === undefined && (!presetName.trim() || unsupported.length > 0 || (blocked && inactive.length)))) return
    inFlight.current = true; setPending(true); setMessage(null)
    const path = status === undefined ? preset ? `/access/role-presets/${preset.presetId}` : '/access/role-presets' : `/access/role-presets/${preset!.presetId}/status`
    const body = status === undefined ? { ...(preset ? {} : { preset_code: presetCode.trim() }), preset_name: presetName.trim(), description: description.trim() || null, permissions: toPermissionInputs(drafts, scopes), ...(preset ? { expected_version: version } : {}), reason: reason.trim() } : { is_active: status, expected_version: version, reason: reason.trim() }
    try {
      await httpJson(path, { method: status === undefined ? preset ? 'PUT' : 'POST' : 'PATCH', body, recoverAccessDenied: true })
      if (status !== undefined) { setIsActive(status); setVersion((current) => current + 1) }
      setReason(''); setBlocked(false); setMessage(status === undefined ? preset ? 'Preset saved.' : 'Preset created.' : `Preset ${status ? 'activated' : 'deactivated'}.`)
    } catch (error) { setMessage(errorMessage(error)); if (status === undefined && inactive.length && isApiError(error) && error.code === 'inactive_access_scope') setBlocked(true) } finally { inFlight.current = false; setPending(false) }
  }
  const remove = (draft: PermissionDraft) => { setDrafts((current) => current.filter((item) => item.action !== draft.action || item.scopeCode !== draft.scopeCode)); setMessage(null) }
  const add = () => {
    const draft = { action: action.trim(), scopeCode }
    if (!draft.action || !draft.scopeCode || !isSelectablePermission(draft, permissionScopes)) return
    if (!drafts.some((candidate) => candidate.action === draft.action && candidate.scopeCode === draft.scopeCode)) setDrafts((current) => [...current, draft])
  }
  const scopeOptions = permissionScopes.filter((scope) => scope.isActive).map((scope) => scope.scopeCode)
  const selectedScopeActions = permissionScopes.find((scope) => scope.scopeCode === scopeCode)?.supportedActions ?? []

  return <Stack mt="md">
    <Text fw={500}>{preset ? 'Edit preset' : 'Create preset'}</Text>
    {!preset ? <TextInput label="Preset code" value={presetCode} onChange={(event) => setPresetCode(event.currentTarget.value)} /> : null}
    <TextInput label="Preset name" value={presetName} onChange={(event) => setPresetName(event.currentTarget.value)} />
    <TextInput label="Description" value={description} onChange={(event) => setDescription(event.currentTarget.value)} />
    <TextInput label="Reason" value={reason} required onChange={(event) => setReason(event.currentTarget.value)} />
    <Group align="end"><TextInput label="Action" value={action} onChange={(event) => setAction(event.currentTarget.value)} description={selectedScopeActions.length ? `Supported for selected scope: ${selectedScopeActions.join(', ')}` : undefined} /><NativeSelect label="Scope" data={[{ value: '', label: 'Choose a scope' }, ...scopeOptions]} value={scopeCode} onChange={(event) => setScopeCode(event.currentTarget.value)} /><Button onClick={add}>Add permission</Button></Group>
    {drafts.map((draft) => { const state = permissionReferenceState(draft, permissionScopes); return <Group key={`${draft.action}:${draft.scopeCode}`}><Text>{draft.action}:{draft.scopeCode}</Text>{state === 'inactive' ? <Text c="dimmed">Inactive historical reference</Text> : state === 'unsupported' ? <Text c="dimmed">Unsupported historical reference</Text> : <Text c="green">Effective</Text>}<Button variant="subtle" color="red" aria-label={`Remove ${draft.action}:${draft.scopeCode}`} onClick={() => remove(draft)}>Remove</Button></Group> })}
    {blocked && inactive.length ? <Alert color="red">Remove inactive references before retrying.</Alert> : null}
    {message ? <Alert role="status">{message}</Alert> : null}
    <Group><Button disabled={pending || !presetName.trim() || !reason.trim() || unsupported.length > 0 || (blocked && inactive.length > 0)} onClick={() => void mutate()}>{preset ? 'Save preset' : 'Create preset'}</Button>{preset ? <Button variant="default" disabled={pending || !reason.trim()} onClick={() => void mutate(!isActive)}>{isActive ? 'Deactivate preset' : 'Activate preset'}</Button> : null}</Group>
  </Stack>
}
