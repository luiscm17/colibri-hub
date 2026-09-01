import { Alert, Select, Stack, Text, TextInput, Title } from '@mantine/core'
import { useEffect, useState } from 'react'
import type { QualityProfile, RemoteState, SpinningGateway } from '../integration/contracts'
import { unavailableSpinningGateway } from '../integration/unavailableGateway'
import { createQualityDraft, selectQualityProfile, selectedQualityProfile, updateQualityDraft } from './qualityModel'

export function QualityWorkspace({ gateway = unavailableSpinningGateway }: { gateway?: SpinningGateway }) {
  const [draft, setDraft] = useState(createQualityDraft)
  const [profiles, setProfiles] = useState<RemoteState<readonly QualityProfile[]>>({ status: 'loading' })

  useEffect(() => {
    const controller = new AbortController()
    void gateway.getQualityProfiles(controller.signal).then(result => {
      if (!controller.signal.aborted) setProfiles(result)
    })
    return () => controller.abort()
  }, [gateway])

  const availableProfiles = profiles.status === 'populated' ? profiles.data : []
  const profile = selectedQualityProfile(availableProfiles, draft)

  return <Stack gap="lg">
    <div><Title order={1}>Control de Calidad</Title><Text>Configuración y captura por perfil autorizado</Text></div>
    <Select
      label="Perfil de calidad"
      placeholder="Seleccione un perfil autorizado"
      data={availableProfiles.map(item => ({ value: item.id, label: item.label }))}
      value={profile?.id ?? null}
      onChange={profileId => setDraft(current => selectQualityProfile(current, profileId ?? ''))}
      disabled={profiles.status !== 'populated'}
    />
    {profiles.status === 'unavailable' ? <UnavailableQualityState /> : null}
    {profile ? <QualityCapture profile={profile} draft={draft} onValueChange={(fieldId, value) => setDraft(current => updateQualityDraft(current, fieldId, value))} /> : null}
  </Stack>
}

function QualityCapture({ profile, draft, onValueChange }: { profile: QualityProfile; draft: ReturnType<typeof createQualityDraft>; onValueChange: (fieldId: string, value: string) => void }) {
  if (profile.method === 'sample') return <Alert role="status" title="Perfil de muestra configurado">Las mediciones y los resultados se mostrarán en su captura ordenada cuando el contrato del servidor los proporcione.</Alert>

  return <Stack gap="sm" aria-label="Captura de calidad">
    <Text fw={600}>Captura: {profile.label}</Text>
    {profile.captureFields.map(field => <TextInput key={field.id} label={field.label} required={field.required} value={draft.values[field.id] ?? ''} onChange={event => onValueChange(field.id, event.currentTarget.value)} />)}
    <Text size="sm">Los resultados y las tolerancias dependen de la confirmación del servidor.</Text>
  </Stack>
}

function UnavailableQualityState() {
  return <Alert title="Perfiles no disponibles" role="status" aria-live="polite">
    No hay perfiles, campos de captura ni resultados disponibles hasta que el servicio autorice la configuración. Los borradores locales se conservarán.
  </Alert>
}
