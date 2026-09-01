import { Alert, Select, Stack, Text, TextInput, Title } from '@mantine/core'
import { useEffect, useState } from 'react'
import type { QualityCaptureCatalog, QualityCaptureContext, QualityProfile, RemoteState, SpinningGateway } from '../integration/contracts'
import { developmentSpinningGateway } from '../integration/developmentGateway'
import { createQualityDraft, selectQualityProfile, selectedQualityProfile, updateQualityDraft } from './qualityModel'
import { SampleQualityGrid } from './SampleQualityGrid'

export function QualityWorkspace({ gateway = developmentSpinningGateway }: { gateway?: SpinningGateway }) {
  const [draft, setDraft] = useState(createQualityDraft)
  const [context, setContext] = useState<QualityCaptureContext>({ sectionId: '', businessDate: '', shiftId: '', inspectorId: '', machineId: '', yarnCountId: '' })
  const [catalog, setCatalog] = useState<RemoteState<QualityCaptureCatalog>>({ status: 'loading' })
  const [profiles, setProfiles] = useState<RemoteState<readonly QualityProfile[]>>({ status: 'loading' })
  const hasProfileContext = Boolean(context.sectionId && context.businessDate && context.shiftId && context.inspectorId)

  useEffect(() => {
    const controller = new AbortController()
    void gateway.getQualityCaptureCatalog(controller.signal).then(result => {
      if (!controller.signal.aborted) setCatalog(result)
    })
    return () => controller.abort()
  }, [gateway])

  useEffect(() => {
    if (!hasProfileContext) return
    const controller = new AbortController()
    void gateway.getQualityProfiles(context, controller.signal).then(result => {
      if (!controller.signal.aborted) setProfiles(result)
    })
    return () => controller.abort()
  }, [context, gateway, hasProfileContext])

  const availableProfiles = hasProfileContext && profiles.status === 'populated' ? profiles.data : []
  const profile = selectedQualityProfile(availableProfiles, draft) ?? availableProfiles[0]
  const updateContext = (field: keyof QualityCaptureContext, value: string) => {
    setContext(current => ({ ...current, [field]: value }))
    if (field === 'sectionId' || field === 'businessDate' || field === 'shiftId' || field === 'inspectorId') setDraft(createQualityDraft())
  }

  return <Stack gap="lg">
    <div><Title order={1}>Control de Calidad</Title><Text>Configuración y captura por perfil autorizado</Text></div>
    <QualityCaptureContextFields catalog={catalog} context={context} onChange={updateContext} />
    <Select
      label="Perfil de calidad"
      placeholder="Seleccione un perfil autorizado"
      data={availableProfiles.map(item => ({ value: item.id, label: item.label }))}
      value={profile?.id ?? null}
      onChange={profileId => setDraft(current => selectQualityProfile(current, profileId ?? ''))}
      disabled={!hasProfileContext || profiles.status !== 'populated'}
    />
    {catalog.status === 'unavailable' || profiles.status === 'unavailable' ? <UnavailableQualityState /> : null}
    {profile ? <QualityProfileContextFields catalog={catalog} profile={profile} context={context} onChange={updateContext} /> : null}
    {profile ? <QualityCapture profile={profile} draft={draft} onValueChange={(fieldId, value) => setDraft(current => updateQualityDraft(current, fieldId, value))} /> : null}
  </Stack>
}

function QualityCaptureContextFields({ catalog, context, onChange }: { catalog: RemoteState<QualityCaptureCatalog>; context: QualityCaptureContext; onChange: (field: keyof QualityCaptureContext, value: string) => void }) {
  const options = catalog.status === 'populated' ? catalog.data : undefined
  const selectData = (items: readonly { id: string; label: string }[]) => items.map(item => ({ value: item.id, label: item.label }))
  return <Stack gap="sm" aria-label="Contexto de captura de calidad">
    <Select label="Sección" data={selectData(options?.sections ?? [])} value={context.sectionId || null} onChange={value => onChange('sectionId', value ?? '')} disabled={!options} />
    <TextInput label="Fecha operativa" type="date" value={context.businessDate} onChange={event => onChange('businessDate', event.currentTarget.value)} disabled={!options} />
    <Select label="Turno" data={selectData(options?.shifts ?? [])} value={context.shiftId || null} onChange={value => onChange('shiftId', value ?? '')} disabled={!options} />
    <Select label="Inspector" data={selectData(options?.inspectors ?? [])} value={context.inspectorId || null} onChange={value => onChange('inspectorId', value ?? '')} disabled={!options} />
  </Stack>
}

function QualityProfileContextFields({ catalog, profile, context, onChange }: { catalog: RemoteState<QualityCaptureCatalog>; profile: QualityProfile; context: QualityCaptureContext; onChange: (field: keyof QualityCaptureContext, value: string) => void }) {
  if (catalog.status !== 'populated') return null
  const selectOptions = (options: readonly { id: string; label: string }[], allowedIds: readonly string[]) => options.filter(option => allowedIds.includes(option.id)).map(option => ({ value: option.id, label: option.label }))
  return <Stack gap="sm" aria-label="Contexto de perfil de calidad">
    {profile.captureContext.machine === 'hidden' ? null : <Select label="Máquina" required={profile.captureContext.machine === 'required'} data={selectOptions(catalog.data.machines, profile.captureContext.applicableMachineIds)} value={context.machineId || null} onChange={value => onChange('machineId', value ?? '')} />}
    {profile.captureContext.yarnCount === 'hidden' ? null : <Select label="Título de hilo" required={profile.captureContext.yarnCount === 'required'} data={selectOptions(catalog.data.yarnCounts, profile.captureContext.applicableYarnCountIds)} value={context.yarnCountId || null} onChange={value => onChange('yarnCountId', value ?? '')} />}
  </Stack>
}

function QualityCapture({ profile, draft, onValueChange }: { profile: QualityProfile; draft: ReturnType<typeof createQualityDraft>; onValueChange: (fieldId: string, value: string) => void }) {
  if (profile.method === 'sample') return <SampleQualityGrid measurements={profile.measurements} values={draft.values} onValueChange={onValueChange} />

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
