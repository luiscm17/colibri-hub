import { Alert, Select, SimpleGrid, Stack, Text, TextInput, Title } from '@mantine/core'
import { useEffect, useState } from 'react'
import type { QualityCaptureCatalog, QualityCaptureContext, QualityProfile, QualitySampleRecord, RemoteState, SpinningGateway } from '../integration/contracts'
import { developmentSpinningGateway } from '../integration/developmentGateway'
import { createQualityDraft, selectQualityProfile, selectedQualityProfile, updateQualityDraft } from './qualityModel'
import { SampleQualityGrid } from './SampleQualityGrid'

const emptyQualityCaptureContext: QualityCaptureContext = { businessDate: '', shiftId: '', supervisorId: '', analystId: '' }

export function QualityWorkspace({ gateway = developmentSpinningGateway }: { gateway?: SpinningGateway }) {
  const [draft, setDraft] = useState(createQualityDraft)
  const [context, setContext] = useState<QualityCaptureContext>(() => gateway.defaultQualityCaptureContext ?? emptyQualityCaptureContext)
  const [catalog, setCatalog] = useState<RemoteState<QualityCaptureCatalog>>({ status: 'loading' })
  const [profiles, setProfiles] = useState<RemoteState<readonly QualityProfile[]>>({ status: 'loading' })
  const [sampleRecords, setSampleRecords] = useState<RemoteState<readonly QualitySampleRecord[]>>({ status: 'loading' })
  const hasProfileContext = Boolean(context.businessDate && context.shiftId && context.supervisorId && context.analystId)

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

  useEffect(() => {
    if (!profile || profile.method !== 'sample') return
    const controller = new AbortController()
    void gateway.getQualitySampleRecords(profile.id, context, controller.signal).then(result => {
      if (!controller.signal.aborted) setSampleRecords(result)
    })
    return () => controller.abort()
  }, [context, gateway, profile])

  const updateContext = (field: keyof QualityCaptureContext, value: string) => {
    setContext(current => ({ ...current, [field]: value }))
    setDraft(createQualityDraft())
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
    {profile ? <QualityCapture profile={profile} draft={draft} sampleRecords={sampleRecords} onRecordsChange={records => setSampleRecords({ status: 'populated', data: records })} onValueChange={(fieldId, value) => setDraft(current => updateQualityDraft(current, fieldId, value))} /> : null}
  </Stack>
}

function QualityCaptureContextFields({ catalog, context, onChange }: { catalog: RemoteState<QualityCaptureCatalog>; context: QualityCaptureContext; onChange: (field: keyof QualityCaptureContext, value: string) => void }) {
  const options = catalog.status === 'populated' ? catalog.data : undefined
  const selectData = (items: readonly { id: string; label: string }[]) => items.map(item => ({ value: item.id, label: item.label }))
  return <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="sm" aria-label="Contexto de captura de calidad">
    <Select label="Turno" data={selectData(options?.shifts ?? [])} value={context.shiftId || null} onChange={value => onChange('shiftId', value ?? '')} disabled={!options} />
    <Select label="Supervisor" data={selectData(options?.supervisors ?? [])} value={context.supervisorId || null} onChange={value => onChange('supervisorId', value ?? '')} disabled={!options} />
    <TextInput label="Fecha" type="date" value={context.businessDate} onChange={event => onChange('businessDate', event.currentTarget.value)} disabled={!options} />
    <Select label="Analista" data={selectData(options?.analysts ?? [])} value={context.analystId || null} onChange={value => onChange('analystId', value ?? '')} disabled={!options} />
  </SimpleGrid>
}

function QualityCapture({ profile, draft, sampleRecords, onRecordsChange, onValueChange }: { profile: QualityProfile; draft: ReturnType<typeof createQualityDraft>; sampleRecords: RemoteState<readonly QualitySampleRecord[]>; onRecordsChange: (records: readonly QualitySampleRecord[]) => void; onValueChange: (fieldId: string, value: string) => void }) {
  if (profile.method === 'sample') {
    if (sampleRecords.status === 'populated') return <SampleQualityGrid profile={profile} records={sampleRecords.data} onRecordsChange={onRecordsChange} />
    if (sampleRecords.status === 'unavailable' || sampleRecords.status === 'failure') return <Alert role="status" title="Registros no disponibles">Los registros de muestra no están disponibles hasta que el servicio los autorice.</Alert>
    return <Text role="status">Cargando registros de muestra…</Text>
  }

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
