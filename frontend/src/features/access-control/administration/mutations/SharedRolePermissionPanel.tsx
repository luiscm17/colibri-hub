import { Alert, Button, Group, Modal, Stack, Text, TextInput } from '@mantine/core'
import { useMemo, useState } from 'react'
import { httpJson } from '@/api/httpClient'
import { useAccess } from '@/features/access-control'
import { SharedRolePermissionGate } from './shared-role-gate'
import type { PermissionInput } from './shared-role-gate'

const parse = (draft: string): PermissionInput[] => draft.split(',').flatMap((entry) => { const [action, scopeId] = entry.trim().split(':'); return action && scopeId ? [{ action, scopeId }] : [] })

export function SharedRolePermissionPanel({ roleId, version, roleName, description, permissions }: { roleId: string; version: number; roleName: string; description: string | null; permissions: PermissionInput[] }) {
  const { snapshot } = useAccess()
  const authorityGeneration = String(snapshot?.authorizationVersion ?? '')
  return <SharedRolePermissionContent key={`${roleId}:${version}:${authorityGeneration}`} roleId={roleId} version={version} roleName={roleName} description={description} permissions={permissions} authorityGeneration={authorityGeneration} />
}

function SharedRolePermissionContent({ roleId, version, roleName, description, permissions, authorityGeneration }: { roleId: string; version: number; roleName: string; description: string | null; permissions: PermissionInput[]; authorityGeneration: string }) {
  const gate = useMemo(() => new SharedRolePermissionGate({ subjectId: roleId, subjectVersion: version, authorityGeneration }, permissions, { roleName, description }), [authorityGeneration, description, permissions, roleId, roleName, version])
  const [draft, setDraft] = useState(permissions.map((permission) => `${permission.action}:${permission.scopeId}`).join(', '))
  const [reason, setReason] = useState('')
  const [preview, setPreview] = useState<number | null>(null)
  const [confirming, setConfirming] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  async function previewChange() { const request = gate.previewRequest(parse(draft)); const generation = gate.currentRequestGeneration(); if (!request) { setPreview(null); setMessage('Choose a different permission set before previewing.'); return }; try { const result = await httpJson<{ subject_version: number; affected_user_count: number }>(request.path, { method: request.method, body: request.body, recoverAccessDenied: true }); if (gate.acceptPreview({ subjectVersion: result.subject_version, affectedUserCount: result.affected_user_count }, parse(draft), generation)) setPreview(result.affected_user_count) } catch { gate.invalidate(); setPreview(null); setMessage('Preview is no longer current. Review permissions and preview again.') } }
  async function applyChange() { const request = gate.applyRequest(reason); if (!request) return; try { await httpJson(request.path, { method: request.method, body: request.body, recoverAccessDenied: true }); setConfirming(false); setMessage('Role permissions replaced.') } catch { gate.invalidate(); setConfirming(false); setPreview(null); setMessage('The replacement was not applied. Preview a fresh change before retrying.') } }
  return <Stack mt="md"><Text fw={500}>Replace shared role permissions</Text><TextInput label="Permission pairs" value={draft} onChange={(event) => { gate.invalidate(); setConfirming(false); setPreview(null); setDraft(event.currentTarget.value) }} description="Comma-separated action:scope ID pairs. Changes require a fresh preview." /><TextInput label="Reason (optional)" value={reason} onChange={(event) => setReason(event.currentTarget.value)} /><Group><Button onClick={() => void previewChange()}>Preview replacement</Button>{preview !== null ? <Button color="red" onClick={() => setConfirming(true)}>Review replacement</Button> : null}</Group>{preview !== null ? <Alert>Users affected by this proposed change: {preview}.</Alert> : null}{message ? <Alert>{message}</Alert> : null}<Modal opened={confirming} onClose={() => setConfirming(false)} title="Confirm replacement" closeOnClickOutside={false} returnFocus><Stack><Text>Replace shared role permissions</Text><Text role="status" aria-live="polite">Users affected by this proposed change: {preview ?? 0}.</Text><Text>Confirming applies this preview once. A new preview is required after any conflict or edit.</Text><Group justify="flex-end"><Button variant="default" onClick={() => setConfirming(false)}>Cancel</Button><Button color="red" onClick={() => void applyChange()}>Confirm replacement</Button></Group></Stack></Modal></Stack>
}
