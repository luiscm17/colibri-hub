import { Alert, Button, Group, NativeSelect, Stack, Text, TextInput } from '@mantine/core'
import { useEffect, useEffectEvent, useMemo, useRef, useState } from 'react'
import { httpJson } from '@/api/httpClient'
import { isApiError } from '@/api/httpError'
import { toPermissionInputs, type PermissionDraft, type RegisteredScope } from '../forms/permission-adapter'

export type PresetWorkflowPreset = Readonly<{ presetId: string; presetCode: string; presetName: string; description: string | null; isActive: boolean; version: number; permissions: readonly PermissionDraft[] }>
type Page = { items: { scope_id: string; scope_code: string; is_active: boolean }[] }
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
  const [message, setMessage] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [blocked, setBlocked] = useState(false)
  const [isActive, setIsActive] = useState(preset?.isActive ?? true)
  const [version, setVersion] = useState(preset?.version ?? 0)
  const inFlight = useRef(false)

  useEffect(() => {
    const controller = new AbortController()
    void httpJson<Page>('/access/scopes?page=1&page_size=100', { signal: controller.signal, recoverAccessDenied: true }).then((page) => setScopes(page.items.map((scope) => ({ scopeId: scope.scope_id, scopeCode: scope.scope_code, isActive: scope.is_active })))).catch((error: unknown) => { if (!isApiError(error) || error.kind !== 'aborted') setMessage('Permission choices are unavailable.') })
    return () => controller.abort()
  }, [])
  const inactive = useMemo(() => drafts.filter((draft) => scopes.some((scope) => scope.scopeCode === draft.scopeCode && !scope.isActive)), [drafts, scopes])
  const dirty = presetCode !== (preset?.presetCode ?? '') || presetName !== (preset?.presetName ?? '') || description !== (preset?.description ?? '') || reason !== '' || JSON.stringify(drafts) !== JSON.stringify(preset?.permissions ?? [])
  useEffect(() => () => reportDirty(false), [])
  useEffect(() => { reportDirty(dirty) }, [dirty])

  const mutate = async (status?: boolean) => {
    if (inFlight.current || !reason.trim() || (status === undefined && (!presetName.trim() || (blocked && inactive.length)))) return
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
  const add = () => { if (action.trim() && scopeCode && !drafts.some((draft) => draft.action === action.trim() && draft.scopeCode === scopeCode)) setDrafts((current) => [...current, { action: action.trim(), scopeCode }]) }

  return <Stack mt="md">
    <Text fw={500}>{preset ? 'Edit preset' : 'Create preset'}</Text>
    {!preset ? <TextInput label="Preset code" value={presetCode} onChange={(event) => setPresetCode(event.currentTarget.value)} /> : null}
    <TextInput label="Preset name" value={presetName} onChange={(event) => setPresetName(event.currentTarget.value)} />
    <TextInput label="Description" value={description} onChange={(event) => setDescription(event.currentTarget.value)} />
    <TextInput label="Reason" value={reason} required onChange={(event) => setReason(event.currentTarget.value)} />
    <Group align="end"><TextInput label="Action" value={action} onChange={(event) => setAction(event.currentTarget.value)} /><NativeSelect label="Scope" data={[{ value: '', label: 'Choose a scope' }, ...scopes.filter((scope) => scope.isActive).map((scope) => scope.scopeCode)]} value={scopeCode} onChange={(event) => setScopeCode(event.currentTarget.value)} /><Button onClick={add}>Add permission</Button></Group>
    {drafts.map((draft) => <Group key={`${draft.action}:${draft.scopeCode}`}><Text>{draft.action}:{draft.scopeCode}</Text><Text c={inactive.includes(draft) ? 'dimmed' : 'green'}>{inactive.includes(draft) ? 'Inactive historical reference' : 'Effective'}</Text><Button variant="subtle" color="red" aria-label={`Remove ${draft.action}:${draft.scopeCode}`} onClick={() => remove(draft)}>Remove</Button></Group>)}
    {blocked && inactive.length ? <Alert color="red">Remove inactive references before retrying.</Alert> : null}
    {message ? <Alert role="status">{message}</Alert> : null}
    <Group><Button disabled={pending || !presetName.trim() || !reason.trim() || (blocked && inactive.length > 0)} onClick={() => void mutate()}>{preset ? 'Save preset' : 'Create preset'}</Button>{preset ? <Button variant="default" disabled={pending || !reason.trim()} onClick={() => void mutate(!isActive)}>{isActive ? 'Deactivate preset' : 'Activate preset'}</Button> : null}</Group>
  </Stack>
}
