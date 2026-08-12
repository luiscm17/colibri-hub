import { Alert, Button, Group, Stack, Text, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { useState } from 'react'
import { mutate, MutationGate } from './governance'

type Family = 'users' | 'roles' | 'presets'
type Item = Record<string, unknown>
const asText = (value: unknown) => typeof value === 'string' ? value : ''
const asNumber = (value: unknown) => typeof value === 'number' ? value : 0

export function GovernancePanel({ family, item, onReconcile }: { family: Family; item: Item; onReconcile: () => void }) {
  const [gate] = useState(() => new MutationGate())
  const [message, setMessage] = useState<string | null>(null)
  const id = asText(item[family === 'users' ? 'user_id' : family === 'roles' ? 'role_id' : 'preset_id'])
  const version = asNumber(item.version)
  const form = useForm({ mode: 'controlled', initialValues: { reason: '', roleIds: '' }, validate: { reason: (value) => value.trim() ? null : 'A reason is required.' } })
  const endpoint = family === 'users' ? `/access/users/${id}/roles` : family === 'roles' ? `/access/roles/${id}/status` : `/access/role-presets/${id}/status`

  async function submit(values: typeof form.values) {
    const body = family === 'users'
      ? { role_ids: values.roleIds.split(',').map((id) => id.trim()).filter(Boolean), expected_version: version, reason: values.reason }
      : { is_active: item.is_active !== true, expected_version: version, reason: values.reason }
    const outcome = await mutate(gate, `${family}:${id}:${version}:${JSON.stringify(body)}`, endpoint, family === 'users' ? 'PUT' : 'PATCH', body)
    if (outcome.recovery === 'preserve') { form.reset(); onReconcile(); return }
    setMessage(outcome.recovery === 'reload' ? 'This record changed. Reloaded data requires a fresh preview and submission.' : outcome.recovery === 'last-administrator' ? 'The backend rejected removal of the last system administrator.' : 'Authorization changed. This mutation was not replayed and its draft was cleared.')
    if (outcome.recovery === 'clear') form.reset()
  }

  return <form onSubmit={form.onSubmit(submit)}><Stack mt="md">
    <Text fw={500}>{family === 'users' ? 'Replace assigned roles' : item.is_active === true ? 'Deactivate record' : 'Activate record'}</Text>
    {family === 'users' ? <TextInput label="Role IDs" description="Comma-separated IDs. Profile creation remains owned by Authentication." {...form.getInputProps('roleIds')} /> : null}
    <TextInput label="Reason" withAsterisk {...form.getInputProps('reason')} onChange={(event) => { gate.invalidatePreview(); form.getInputProps('reason').onChange(event) }} />
    {message ? <Alert>{message}</Alert> : null}
    <Group><Button type="submit">{family === 'users' ? 'Replace roles' : 'Save lifecycle change'}</Button><Text size="sm">Loaded version {version}</Text></Group>
  </Stack></form>
}
