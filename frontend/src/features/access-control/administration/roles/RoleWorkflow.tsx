import { Alert, Button, Group, Modal, NativeSelect, Stack, Text, TextInput } from '@mantine/core'
import { useEffect, useEffectEvent, useMemo, useRef, useState } from 'react'
import { httpJson } from '@/api/httpClient'
import { isApiError } from '@/api/httpError'
import { useAccess } from '@/features/access-control'
import { isSelectablePermission, permissionReferenceState, type PermissionScope } from '../forms/matrix'
import { toPermissionInputs, type PermissionDraft, type RegisteredScope } from '../forms/permission-adapter'
import { ImpactPreview, type AffectedUser } from '../mutations/ImpactPreview'
import { announceAccessAdministrationRecovery } from '../mutations/access-recovery-notification'
import { SharedRolePermissionGate, type SharedRoleDraft } from '../mutations/shared-role-gate'

export type RoleWorkflowRole = Readonly<{
  roleId: string
  roleCode: string
  roleName: string
  description: string | null
  isActive: boolean
  version: number
  permissions: readonly PermissionDraft[]
}>

type ScopeResponse = { scope_id: string; scope_code: string; is_active: boolean }
type DefinitionResponse = { scope_code: string; supported_actions: string[] }
type Page<T> = { items: T[] }

const errorMessage = (error: unknown) => isApiError(error) ? error.message : error instanceof Error ? error.message : 'The role was not saved.'

type RoleWorkflowDraft = Pick<RoleWorkflowRole, 'roleCode' | 'roleName' | 'description' | 'permissions'>

export function RoleWorkflow({ role, initialDraft, onDirtyChange, onReconcile }: { role?: RoleWorkflowRole; initialDraft?: RoleWorkflowDraft; onDirtyChange(dirty: boolean): void; onReconcile?(): void | Promise<void> }) {
  const { snapshot } = useAccess()
  const reportDirty = useEffectEvent(onDirtyChange)
  const baseline = role ?? initialDraft
  const [roleCode, setRoleCode] = useState(baseline?.roleCode ?? '')
  const [roleName, setRoleName] = useState(baseline?.roleName ?? '')
  const [description, setDescription] = useState(baseline?.description ?? '')
  const [reason, setReason] = useState('')
  const [drafts, setDrafts] = useState<PermissionDraft[]>([...(baseline?.permissions ?? [])])
  const [action, setAction] = useState('')
  const [scopeCode, setScopeCode] = useState<string | null>(null)
  const [scopes, setScopes] = useState<RegisteredScope[]>([])
  const [permissionScopes, setPermissionScopes] = useState<PermissionScope[]>([])
  const [message, setMessage] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const mutationInFlight = useRef(false)
  const [requiresInactiveRemoval, setRequiresInactiveRemoval] = useState(false)
  const [isActive, setIsActive] = useState(role?.isActive ?? true)
  const [version, setVersion] = useState(role?.version ?? 0)
  const [preview, setPreview] = useState<{ affectedUserCount: number; affectedUsers: AffectedUser[] } | null>(null)
  const [confirming, setConfirming] = useState(false)
  const result = useRef<HTMLDivElement>(null)

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

  const inactiveDrafts = useMemo(() => drafts.filter((draft) => permissionReferenceState(draft, permissionScopes) === 'inactive'), [drafts, permissionScopes])
  const roleDraft = useMemo<SharedRoleDraft>(() => ({ roleName, description: description.trim() || null, permissions: toPermissionInputs(drafts, scopes).map((permission) => ({ action: permission.action, scopeId: permission.scope_id })) }), [description, drafts, roleName, scopes])
  const roleBaseline = useMemo<SharedRoleDraft | null>(() => role ? { roleName: role.roleName, description: role.description, permissions: toPermissionInputs(role.permissions, scopes).map((permission) => ({ action: permission.action, scopeId: permission.scope_id })) } : null, [role, scopes])
  const roleGate = useMemo(() => role && roleBaseline ? new SharedRolePermissionGate({ subjectId: role.roleId, subjectVersion: version, authorityGeneration: String(snapshot?.authorizationVersion ?? '') }, roleBaseline) : null, [role, roleBaseline, snapshot?.authorizationVersion, version])
  const metadataChanges = role ? [role.roleName.trim() !== roleName.trim() ? `Name: ${role.roleName} → ${roleName.trim()}` : null, (role.description?.trim() || null) !== (description.trim() || null) ? `Description: ${role.description?.trim() || 'None'} → ${description.trim() || 'None'}` : null].filter((change): change is string => Boolean(change)) : []
  const dirty = roleCode !== (baseline?.roleCode ?? '') || roleName !== (baseline?.roleName ?? '') || description !== (baseline?.description ?? '') || reason !== '' || JSON.stringify(drafts) !== JSON.stringify(baseline?.permissions ?? [])
  useEffect(() => () => reportDirty(false), [])
  useEffect(() => { reportDirty(dirty) }, [dirty])

  const remove = (draft: PermissionDraft) => {
    roleGate?.invalidate(); setPreview(null); setConfirming(false)
    setDrafts((current) => current.filter((candidate) => candidate.action !== draft.action || candidate.scopeCode !== draft.scopeCode))
    setMessage(null)
  }
  const add = () => {
    if (!action || !scopeCode) return
    const draft = { action, scopeCode }
    if (!isSelectablePermission(draft, permissionScopes)) return
    if (!drafts.some((candidate) => candidate.action === draft.action && candidate.scopeCode === draft.scopeCode)) { roleGate?.invalidate(); setPreview(null); setConfirming(false); setDrafts((current) => [...current, draft]) }
  }
  const submit = async () => {
    if (mutationInFlight.current || !roleName.trim() || !reason.trim() || (requiresInactiveRemoval && inactiveDrafts.length > 0)) return
    mutationInFlight.current = true
    setPending(true); setMessage(null)
    const body = role ? { role_name: roleName.trim(), description: description.trim() || null, permissions: toPermissionInputs(drafts, scopes), expected_version: version, reason: reason.trim() } : { role_code: roleCode.trim(), role_name: roleName.trim(), description: description.trim() || null, permissions: toPermissionInputs(drafts, scopes), reason: reason.trim() }
    try {
      await httpJson(role ? `/access/roles/${role.roleId}` : '/access/roles', { method: role ? 'PUT' : 'POST', body, recoverAccessDenied: true })
      setMessage(role ? 'Role saved.' : 'Role created.')
      setReason(''); setRequiresInactiveRemoval(false); onDirtyChange(false)
    } catch (error) {
      setMessage(errorMessage(error))
      if (inactiveDrafts.length > 0) setRequiresInactiveRemoval(true)
    } finally { mutationInFlight.current = false; setPending(false) }
  }
  const changeStatus = async () => {
    if (!role || mutationInFlight.current || !reason.trim()) return
    mutationInFlight.current = true
    setPending(true); setMessage(null)
    try {
      await httpJson(`/access/roles/${role.roleId}/status`, { method: 'PATCH', body: { is_active: !isActive, expected_version: version, reason: reason.trim() }, recoverAccessDenied: true })
      setIsActive((current) => !current); setVersion((current) => current + 1); setReason(''); setMessage(`Role ${isActive ? 'deactivated' : 'activated'}.`)
    } catch (error) { setMessage(errorMessage(error)) } finally { mutationInFlight.current = false; setPending(false) }
  }
  const invalidatePreview = () => { roleGate?.invalidate(); setPreview(null); setConfirming(false) }
  const previewUpdate = async () => {
    if (!roleGate) return
    const request = roleGate.previewRequest(roleDraft, reason)
    const generation = roleGate.currentRequestGeneration()
    if (!request) { setPreview(null); setMessage('Change the role name, description, or permissions before previewing.'); return }
    setMessage(null)
    try {
      const response = await httpJson<{ subject_version: number; affected_user_count: number; affected_users: AffectedUser[] }>(request.path, { method: request.method, body: request.body, signal: request.signal, recoverAccessDenied: true })
      if (roleGate.acceptPreview({ subjectVersion: response.subject_version }, roleDraft, reason, generation)) setPreview({ affectedUserCount: response.affected_user_count, affectedUsers: response.affected_users })
    } catch (error) { roleGate.handleOutcome(isApiError(error) && error.status === 401 ? '401' : isApiError(error) && error.status === 403 ? '403' : 'failure'); setPreview(null); setConfirming(false); setMessage('Preview is no longer current. Review the role and preview again.') }
  }
  const applyUpdate = async () => {
    const request = roleGate?.applyRequest()
    if (!request) return
    setPending(true); setMessage(null)
    try {
      await httpJson(request.path, { method: request.method, body: request.body, recoverAccessDenied: true })
      roleGate?.invalidate(); setPreview(null); setConfirming(false); setReason(''); setRequiresInactiveRemoval(false); onDirtyChange(false)
      await onReconcile?.()
      setMessage('Role saved.'); window.setTimeout(() => result.current?.focus(), 0)
    } catch (error) { const accessDenied = isApiError(error) && error.status === 403; roleGate?.handleOutcome(isApiError(error) && error.status === 401 ? '401' : accessDenied ? '403' : 'failure'); setPreview(null); setConfirming(false); if (accessDenied) announceAccessAdministrationRecovery(); else setMessage(errorMessage(error))
    } finally { setPending(false) }
  }
  const scopeOptions = permissionScopes.filter((scope) => scope.isActive).map((scope) => ({ value: scope.scopeCode, label: scope.scopeCode }))
  const selectedScopeActions = permissionScopes.find((scope) => scope.scopeCode === scopeCode)?.supportedActions ?? []

  return <Stack mt="md">
    <Text fw={500}>{role ? 'Edit role' : 'Create role'}</Text>
    {!role ? <TextInput label="Role code" value={roleCode} onChange={(event) => setRoleCode(event.currentTarget.value)} /> : null}
    <TextInput label="Role name" value={roleName} onChange={(event) => { invalidatePreview(); setRoleName(event.currentTarget.value) }} />
    <TextInput label="Description" value={description} onChange={(event) => { invalidatePreview(); setDescription(event.currentTarget.value) }} />
    <TextInput label="Reason (optional)" value={reason} onChange={(event) => { invalidatePreview(); setReason(event.currentTarget.value) }} />
    <Group align="end"><TextInput label="Action" value={action} onChange={(event) => setAction(event.currentTarget.value)} description={selectedScopeActions.length ? `Supported for selected scope: ${selectedScopeActions.join(', ')}` : undefined} /><NativeSelect label="Scope" data={[{ value: '', label: 'Choose a scope' }, ...scopeOptions]} value={scopeCode ?? ''} onChange={(event) => setScopeCode(event.currentTarget.value || null)} /><Button onClick={add}>Add permission</Button></Group>
    {drafts.map((draft) => { const state = permissionReferenceState(draft, permissionScopes); return <Group key={`${draft.action}:${draft.scopeCode}`}><Text>{draft.action}:{draft.scopeCode}</Text>{state === 'inactive' ? <Text c="dimmed">Inactive historical reference</Text> : state === 'unsupported' ? <Text c="dimmed">Unsupported historical reference</Text> : <Text c="green">Effective</Text>}<Button variant="subtle" color="red" onClick={() => remove(draft)} aria-label={`Remove ${draft.action}:${draft.scopeCode}`}>Remove</Button></Group> })}
    {requiresInactiveRemoval && inactiveDrafts.length > 0 ? <Alert color="red">Remove inactive references before retrying.</Alert> : null}
    {preview ? <Alert><ImpactPreview affectedUserCount={preview.affectedUserCount} affectedUsers={preview.affectedUsers} metadataChanges={metadataChanges} /></Alert> : null}
    {message ? <Alert ref={result} tabIndex={-1} role="status">{message}</Alert> : null}
    <Group>{role ? <><Button onClick={() => void previewUpdate()} disabled={pending || !roleName.trim() || (requiresInactiveRemoval && inactiveDrafts.length > 0)}>Preview role update</Button>{preview ? <Button color="red" onClick={() => { if (roleGate?.confirm()) setConfirming(true) }}>Review role update</Button> : null}</> : <Button onClick={() => void submit()} disabled={pending || !roleName.trim() || !reason.trim() || (requiresInactiveRemoval && inactiveDrafts.length > 0)}>Create role</Button>}{role ? <Button variant="default" onClick={() => void changeStatus()} disabled={pending || !reason.trim()}>{isActive ? 'Deactivate role' : 'Activate role'}</Button> : null}</Group>
    <Modal opened={confirming} onClose={() => setConfirming(false)} title="Confirm role update" closeOnClickOutside={false} returnFocus><Stack><Text>Update shared role</Text><Text role="status" aria-live="polite">Users affected by this proposed change: {preview?.affectedUserCount ?? 0}.</Text><Text>Confirming applies this preview once. A new preview is required after any edit or conflict.</Text><Group justify="flex-end"><Button variant="default" onClick={() => setConfirming(false)}>Cancel</Button><Button color="red" onClick={() => void applyUpdate()} disabled={pending}>Confirm role update</Button></Group></Stack></Modal>
  </Stack>
}
