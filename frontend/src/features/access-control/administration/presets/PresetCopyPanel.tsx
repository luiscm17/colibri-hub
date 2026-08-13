import { Alert, Button, Group, Stack, Text, TextInput } from '@mantine/core'
import { useState } from 'react'
import { httpJson } from '@/api/httpClient'
import { createAdjustableRoleDraft, createExactPresetCopy, type PresetSnapshot } from './presets'

export function PresetCopyPanel({ preset }: { preset: PresetSnapshot }) {
  const [roleCode, setRoleCode] = useState(`${preset.presetCode}-copy`)
  const [roleName, setRoleName] = useState(`${preset.presetName} copy`)
  const [message, setMessage] = useState<string | null>(null)
  const [draft, setDraft] = useState<ReturnType<typeof createAdjustableRoleDraft> | null>(null)

  async function createExactCopy() {
    const request = createExactPresetCopy(preset, { roleCode, roleName, description: preset.description, reason: '' })
    await httpJson(request.path, { method: request.method, body: request.body, recoverAccessDenied: true })
    setMessage('Exact role copy created. Later preset changes do not synchronize.')
  }

  return <Stack mt="md">
    <Text fw={500}>Create role from preset</Text>
    <Text size="sm">Each flow copies once; later preset changes do not synchronize.</Text>
    <TextInput label="Role code" value={roleCode} onChange={(event) => setRoleCode(event.currentTarget.value)} />
    <TextInput label="Role name" value={roleName} onChange={(event) => setRoleName(event.currentTarget.value)} />
    <Group><Button onClick={() => void createExactCopy()}>Create exact copy</Button><Button variant="default" onClick={() => setDraft(createAdjustableRoleDraft(preset, { roleCode, roleName }))}>Start adjustable draft</Button></Group>
    {message ? <Alert>{message}</Alert> : null}
    {draft ? <Alert>Adjustable draft is independent and contains {draft.permissions.length} copied permissions.</Alert> : null}
  </Stack>
}
