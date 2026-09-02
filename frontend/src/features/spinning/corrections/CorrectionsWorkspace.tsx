import { Alert, Button, Group, NativeSelect, Stack, Table, Text, TextInput, Textarea, Title } from '@mantine/core'
import { useForm } from '@mantine/form'
import { useState } from 'react'
import type { CorrectionContextData, CorrectionHistoricalRecord, RemoteState, SpinningGateway } from '../integration/contracts'

type Values = { section: string; businessDate: string; shift: string; reason: string }
type Column = readonly [string, string, boolean]
const schemas: Record<CorrectionHistoricalRecord['family'], readonly Column[]> = {
  production_discharge: [['Sección', 'section', false], ['Máquina', 'machine', false], ['Descarga', 'dischargedKg', true]],
  skeining_production: [['Sección', 'section', false], ['Madejera', 'skeinMachine', false], ['Madejas', 'skeins', true]],
  progress: [['Sección', 'section', false], ['Máquina', 'machine', false], ['Salida', 'outputKg', true]],
  process_quality: [['Perfil', 'profile', false], ['Muestra', 'sample', false], ['Resultado', 'result', true]],
  waste: [['Área', 'area', false], ['Desperdicio', 'wasteKg', true]],
}
const titles: Record<CorrectionHistoricalRecord['family'], string> = { production_discharge: 'Descarga de producción', skeining_production: 'Producción de madejeras', progress: 'Progreso', process_quality: 'Calidad', waste: 'Desperdicio' }
const cellKey = (record: CorrectionHistoricalRecord, key: string) => `${record.family}:${record.recordId}:${key}`

export function CorrectionsWorkspace({ gateway }: { gateway: SpinningGateway }) {
  const form = useForm<Values>({ mode: 'controlled', initialValues: { section: '', businessDate: '', shift: '', reason: '' }, validate: { reason: value => value.trim() ? null : 'Ingrese el motivo de la corrección.' } })
  const [data, setData] = useState<CorrectionContextData | null>(null)
  const [drafts, setDrafts] = useState<Readonly<Record<string, string>>>({})
  const [state, setState] = useState<RemoteState<CorrectionContextData> | null>(null)
  const [mustReread, setMustReread] = useState(false)
  const ready = Boolean(form.values.section && form.values.businessDate && form.values.shift)
  const context = () => ({ section: form.values.section, businessDate: form.values.businessDate, shift: form.values.shift })
  const read = async () => {
    if (!ready) return
    if (!gateway.corrections) return setState({ status: 'unavailable', message: 'La búsqueda no está disponible.', retryable: false })
    setState({ status: 'loading' }); const result = await gateway.corrections.readCorrectionContext(context()); setState(result)
    if (result.status === 'populated') { setData(result.data); setMustReread(false) }
  }
  const save = async () => {
    if (!data || !gateway.corrections || mustReread || form.validate().hasErrors) return
    setState({ status: 'loading' }); const result = await gateway.corrections.saveCorrectionContext({ context: data.context, reason: form.values.reason.trim(), values: drafts }); setState(result)
    if (result.status === 'conflict') setMustReread(true)
  }
  const groups = data?.records.reduce<Record<string, CorrectionHistoricalRecord[]>>((all, record) => ({ ...all, [record.family]: [...(all[record.family] ?? []), record] }), {}) ?? {}
  return <Stack gap="lg"><div><Title order={1}>Correcciones</Title><Text>Busque el contexto histórico para corregir sus valores persistidos.</Text></div>
    <Group grow align="end"><NativeSelect label="Sección" data={[{ value: 'Preparación', label: 'Preparación' }, { value: 'Continuas', label: 'Continuas' }, { value: 'Bobinados', label: 'Bobinados' }, { value: 'Retorcedoras', label: 'Retorcedoras' }, { value: 'Madejeras', label: 'Madejeras' }, { value: 'Calidad', label: 'Calidad' }, { value: 'Desperdicio', label: 'Desperdicio' }]} {...form.getInputProps('section')} /><TextInput label="Fecha" type="date" {...form.getInputProps('businessDate')} /><NativeSelect label="Turno" data={[{ value: '', label: 'Seleccione un turno' }, { value: 'A', label: 'Turno A' }, { value: 'B', label: 'Turno B' }, { value: 'C', label: 'Turno C' }]} {...form.getInputProps('shift')} /><Button onClick={() => void read()} disabled={!ready}>Buscar</Button></Group>
    {state?.status === 'loading' ? <Text role="status">Consultando contexto histórico…</Text> : null}{(state?.status === 'unavailable' || state?.status === 'failure') ? <Alert role="status" title="Contexto no disponible">{state.message} El borrador se conservará.</Alert> : null}
    {state?.status === 'conflict' ? <Alert role="status" title="Conflicto de corrección">{state.message}<Button mt="sm" onClick={() => void read()}>Releer contexto</Button></Alert> : null}
    {Object.entries(groups).map(([family, records]) => <CorrectionGrid key={family} family={family as CorrectionHistoricalRecord['family']} records={records} drafts={drafts} locked={mustReread} onChange={(key, value) => setDrafts(current => ({ ...current, [key]: value }))} />)}
    {data ? <><Textarea label="Motivo de la corrección" required {...form.getInputProps('reason')} disabled={mustReread} /><Button onClick={() => void save()} disabled={mustReread || !form.values.reason.trim()}>Guardar</Button>{data.progressContinuityWarning ? <Alert title="Continuidad de progreso">{data.progressContinuityWarning} Los registros posteriores no se modificarán automáticamente.</Alert> : null}</> : null}
  </Stack>
}

function CorrectionGrid({ family, records, drafts, locked, onChange }: { family: CorrectionHistoricalRecord['family']; records: readonly CorrectionHistoricalRecord[]; drafts: Readonly<Record<string, string>>; locked: boolean; onChange: (key: string, value: string) => void }) {
  const columns = schemas[family]
  return <Stack gap="xs"><Title order={2}>{titles[family]}</Title><Table aria-label={titles[family]}><Table.Thead><Table.Tr>{columns.map(([label]) => <Table.Th key={label}>{label}</Table.Th>)}</Table.Tr></Table.Thead><Table.Tbody>{records.map(record => <Table.Tr key={`${record.family}:${record.recordId}`}>{columns.map(([label, key, editable]) => { const value = String((record as Record<string, unknown>)[key] ?? ''); const draftKey = cellKey(record, key); return <Table.Td key={key}>{editable ? <TextInput aria-label={`${titles[family]} ${label}`} value={drafts[draftKey] ?? value} onChange={event => onChange(draftKey, event.currentTarget.value)} disabled={locked} /> : value}</Table.Td> })}</Table.Tr>)}</Table.Tbody></Table></Stack>
}
