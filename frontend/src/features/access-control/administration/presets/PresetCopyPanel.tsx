import { Alert, Button, Group, Stack, Text, TextInput } from '@mantine/core'
import { useEffect, useEffectEvent, useRef, useState } from 'react'
import { httpJson } from '@/api/httpClient'
import { isApiError } from '@/api/httpError'
import { createExactPresetCopy, type PresetSnapshot } from './presets'

export function PresetCopyPanel({ preset, onDirtyChange, onStartAdjustable }: { preset: PresetSnapshot; onDirtyChange(dirty: boolean): void; onStartAdjustable(): void }) {
  const reportDirty = useEffectEvent(onDirtyChange)
  const [roleCode, setRoleCode] = useState(`${preset.presetCode}-copy`)
  const [roleName, setRoleName] = useState(`${preset.presetName} copy`)
  const [message, setMessage] = useState<string | null>(null)
  const [reason, setReason] = useState('')
  const [pending, setPending] = useState(false)
  const inFlight = useRef(false)

  useEffect(() => () => reportDirty(false), [])
  useEffect(() => { reportDirty(roleCode !== `${preset.presetCode}-copy` || roleName !== `${preset.presetName} copy` || reason !== '') }, [reason, roleCode, roleName, preset.presetCode, preset.presetName])

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

  return <Stack mt="md">
    <Text fw={500}>Create role from preset</Text>
    <Text size="sm">Each flow copies once; later preset changes do not synchronize.</Text>
    <TextInput label="Role code" value={roleCode} onChange={(event) => setRoleCode(event.currentTarget.value)} />
    <TextInput label="Role name" value={roleName} onChange={(event) => setRoleName(event.currentTarget.value)} />
    <TextInput label="Reason" value={reason} required onChange={(event) => setReason(event.currentTarget.value)} />
    <Group><Button disabled={pending || !reason.trim()} onClick={() => void createExactCopy()}>Create exact copy</Button><Button variant="default" onClick={onStartAdjustable}>Start adjustable draft</Button></Group>
    {message ? <Alert role="status">{message}</Alert> : null}
  </Stack>
}
