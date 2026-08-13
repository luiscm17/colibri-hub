import { Alert, Button, Group, Stack, Text, TextInput } from '@mantine/core'
import { useMemo, useState } from 'react'
import { httpJson } from '@/api/httpClient'
import { useAccess } from '@/features/access-control'
import { UserRoleReplacementGate } from './user-role-gate'

export function UserRoleReplacementPanel({ userId, version, roleIds }: { userId: string; version: number; roleIds: string[] }) {
  const { snapshot } = useAccess()
  const authorityGeneration = String(snapshot?.authorizationVersion ?? '')
  return <UserRoleReplacementContent key={`${userId}:${version}:${authorityGeneration}`} userId={userId} version={version} roleIds={roleIds} authorityGeneration={authorityGeneration} />
}

function UserRoleReplacementContent({ userId, version, roleIds, authorityGeneration }: { userId: string; version: number; roleIds: string[]; authorityGeneration: string }) {
  const gate = useMemo(() => new UserRoleReplacementGate({ subjectId: userId, subjectVersion: version, authorityGeneration }, roleIds), [authorityGeneration, roleIds, userId, version])
  const [draft, setDraft] = useState(roleIds.join(', '))
  const [preview, setPreview] = useState<{ subjectVersion: number; affectedUserCount: number } | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  async function previewChange() { const request = gate.previewRequest(draft.split(',')); const generation = gate.currentRequestGeneration(); if (!request) { setPreview(null); setMessage('Choose a different role set before previewing.'); return }; try { const result = await httpJson<{ subject_version: number; affected_user_count: number }>(request.path, { method: request.method, body: request.body, recoverAccessDenied: true }); if (gate.acceptPreview({ subjectVersion: result.subject_version, affectedUserCount: result.affected_user_count }, draft.split(','), generation)) setPreview({ subjectVersion: result.subject_version, affectedUserCount: result.affected_user_count }) } catch { gate.invalidate(); setPreview(null); setMessage('Preview is no longer current. Review the roles and preview again.') } }
  async function applyChange() { const request = gate.applyRequest(); if (!request) return; try { await httpJson(request.path, { method: request.method, body: request.body, recoverAccessDenied: true }); setMessage('User roles replaced.') } catch { gate.invalidate(); setPreview(null); setMessage('The replacement was not applied. Preview a fresh change before retrying.') } }
  return <Stack mt="md"><Text fw={500}>Replace user roles</Text><TextInput label="Role IDs" value={draft} onChange={(event) => { gate.invalidate(); setPreview(null); setDraft(event.currentTarget.value) }} description="Comma-separated role IDs. Changes require a fresh preview." /><Group><Button onClick={() => void previewChange()}>Preview replacement</Button>{preview ? <Button color="red" onClick={() => void applyChange()}>Confirm replacement</Button> : null}</Group>{preview ? <Alert>Users affected by this proposed change: {preview.affectedUserCount}.</Alert> : null}{message ? <Alert>{message}</Alert> : null}</Stack>
}
