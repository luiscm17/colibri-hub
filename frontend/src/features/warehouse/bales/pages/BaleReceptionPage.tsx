import { Alert, Button, Group, Modal, Stack, Text } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import { IconAlertCircle, IconCheck } from '@tabler/icons-react'
import { useMemo, useReducer, useRef } from 'react'
import { PageHeader } from '@/common/components/PageHeader'
import { registerBatch } from '../api/baleApi'
import { BaleApiError } from '../api/baleApi.errors'
import { ReceptionGrid } from '../components/reception/ReceptionGrid'
import { ReceptionHeader } from '../components/reception/ReceptionHeader'
import { ReceptionSummary } from '../components/reception/ReceptionSummary'
import { useBaleReception } from '../hooks/useBaleReception'
import type { ReceptionGridRow, ReceptionHeader as ReceptionHeaderModel, RegisteredBatch } from '../model/reception'

type FieldErrors = Readonly<Record<string, string>>

interface SubmissionState {
  submitting: boolean
  attempted: boolean
  headerErrors: FieldErrors
  cellErrors: FieldErrors
  result: RegisteredBatch | undefined
  message: string | undefined
}

type SubmissionAction =
  | { type: 'ATTEMPT' }
  | { type: 'SUBMIT_START' }
  | { type: 'SUBMIT_SUCCESS'; result: RegisteredBatch }
  | { type: 'SUBMIT_FAILURE'; headerErrors: FieldErrors; cellErrors: FieldErrors; message: string }
  | { type: 'RESET' }

const INITIAL_SUBMISSION: SubmissionState = {
  submitting: false,
  attempted: false,
  headerErrors: {},
  cellErrors: {},
  result: undefined,
  message: undefined,
}

function submissionReducer(state: SubmissionState, action: SubmissionAction): SubmissionState {
  switch (action.type) {
    case 'ATTEMPT':
      return { ...state, attempted: true, message: undefined, headerErrors: {}, cellErrors: {} }
    case 'SUBMIT_START':
      return { ...state, submitting: true }
    case 'SUBMIT_SUCCESS':
      return { ...state, submitting: false, result: action.result, message: undefined }
    case 'SUBMIT_FAILURE':
      return { ...state, submitting: false, headerErrors: action.headerErrors, cellErrors: action.cellErrors, message: action.message }
    case 'RESET':
      return INITIAL_SUBMISSION
  }
}

export default function BaleReceptionPage() {
  const reception = useBaleReception()
  const [confirmOpened, confirm] = useDisclosure(false)
  const [clearOpened, clear] = useDisclosure(false)
  const [state, dispatch] = useReducer(submissionReducer, INITIAL_SUBMISSION)
  const saveButtonRef = useRef<HTMLButtonElement>(null)
  const firstHeaderError = useMemo(() => Object.keys({ ...reception.headerErrors, ...state.headerErrors })[0], [state.headerErrors, reception.headerErrors])

  const hasDraft = reception.summary.contentCount > 0 || Object.values(reception.header).some(Boolean)
  const editingLocked = state.submitting || Boolean(state.result)

  function requestSave() {
    dispatch({ type: 'ATTEMPT' })
    if (!reception.isReadyForSubmission) return
    confirm.open()
  }

  async function submit() {
    const snapshot = reception.createSubmissionSnapshot()
    confirm.close()
    dispatch({ type: 'SUBMIT_START' })
    try {
      const registered = await registerBatch({ ...snapshot.header, bales: snapshot.bales.map(bale => ({ ...bale })) })
      dispatch({ type: 'SUBMIT_SUCCESS', result: registered })
      notifications.show({ color: 'green', title: 'Recepción guardada', message: 'La recepción se registró correctamente.' })
    } catch (error) {
      const mapped = mapRemoteErrors(error, snapshot)
      dispatch({ type: 'SUBMIT_FAILURE', headerErrors: mapped.header, cellErrors: mapped.cells, message: mapped.message })
      notifications.show({ color: 'red', title: 'No se pudo guardar', message: mapped.message })
    }
  }

  function clearDraft() {
    reception.reset()
    dispatch({ type: 'RESET' })
    clear.close()
    saveButtonRef.current?.focus()
  }

  return (
    <Stack gap="lg">
      <PageHeader title="Recepción de fardos" />
      {state.result ? (
        <Alert color="green" icon={<IconCheck size={16} />} role="status" title="Recepción guardada">
          Se registraron {state.result.baleCount} fardo{state.result.baleCount === 1 ? '' : 's'} del remito {state.result.shipmentNumber}.
        </Alert>
      ) : null}
      {state.message ? <Alert color="red" icon={<IconAlertCircle size={16} />} role="alert">{state.message}</Alert> : null}
      <ReceptionHeader
        header={reception.header}
        errors={state.attempted ? { ...reception.headerErrors, ...state.headerErrors } : state.headerErrors}
        onChange={reception.updateHeader}
        disabled={editingLocked}
        focusField={state.attempted ? firstHeaderError as keyof ReceptionHeaderModel : undefined}
      />
      <ReceptionGrid
        rows={reception.rows}
        feedback={reception.feedback}
        onRowsChange={reception.updateRows}
        onPaste={reception.paste}
        errors={state.cellErrors}
        disabled={editingLocked}
      />
      <ReceptionSummary summary={reception.summary} />
      <Group>
        <Button ref={saveButtonRef} onClick={requestSave} loading={state.submitting} disabled={editingLocked}>Guardar</Button>
        <Button variant="default" onClick={() => hasDraft ? clear.open() : clearDraft()} disabled={state.submitting}>Limpiar</Button>
      </Group>

      <Modal opened={confirmOpened} onClose={confirm.close} title="Confirmar recepción" centered>
        <Stack>
          <Text>Vas a registrar {reception.summary.contentCount} fardo{reception.summary.contentCount === 1 ? '' : 's'} del remito {reception.header.shipmentNumber}.</Text>
          <Group justify="flex-end"><Button variant="default" onClick={confirm.close}>Cancelar</Button><Button onClick={submit}>Confirmar</Button></Group>
        </Stack>
      </Modal>
      <Modal opened={clearOpened} onClose={clear.close} title="Limpiar recepción" centered>
        <Stack>
          <Text>Se perderán los datos cargados en esta página.</Text>
          <Group justify="flex-end"><Button variant="default" onClick={clear.close}>Cancelar</Button><Button color="red" onClick={clearDraft}>Limpiar</Button></Group>
        </Stack>
      </Modal>
    </Stack>
  )
}

function mapRemoteErrors(error: unknown, snapshot: { readonly header: Readonly<ReceptionHeaderModel>; readonly bales: readonly Pick<ReceptionGridRow, 'rowId' | 'baleNumber'>[] }) {
  const fallback = 'Ocurrió un error inesperado. Intentá nuevamente.'
  if (!(error instanceof BaleApiError)) return { header: {}, cells: {}, message: fallback }
  const header: Record<string, string> = {}
  const cells: Record<string, string> = {}
  for (const field of error.fields) {
    const path = field.path.replace(/^body\./, '')
    const headerField = ({ shipment_number: 'shipmentNumber', received_at: 'receptionDate', provider_name: 'providerName' } as const)[path]
    if (headerField) header[headerField] = field.message
    const match = /^bales(?:\.(\d+)|\[\])\.([a-z_]+)$/.exec(path)
    if (match && match[1] === undefined) {
      const column = toCamelCase(match[2])
      const matchingRows = column === 'baleNumber' ? duplicateBaleRows(snapshot) : snapshot.bales
      for (const bale of matchingRows) cells[`${bale.rowId}:${column}`] = field.message
    }
    if (match?.[1] !== undefined && snapshot.bales[Number(match[1])]) cells[`${snapshot.bales[Number(match[1])].rowId}:${toCamelCase(match[2])}`] = field.message
  }
  return { header, cells, message: remoteErrorMessage(error, fallback) }
}

function duplicateBaleRows(snapshot: { readonly bales: readonly Pick<ReceptionGridRow, 'rowId' | 'baleNumber'>[] }) {
  const counts = new Map<string, number>()
  for (const bale of snapshot.bales) {
    const value = bale.baleNumber.trim().toUpperCase()
    if (value) counts.set(value, (counts.get(value) ?? 0) + 1)
  }
  return snapshot.bales.filter(bale => (counts.get(bale.baleNumber.trim().toUpperCase()) ?? 0) > 1)
}

function remoteErrorMessage(error: BaleApiError, fallback: string) {
  if (error.kind === 'conflict') return 'El número de remito ya está registrado.'
  if (error.kind === 'validation') return 'Corregí los campos indicados para guardar.'
  if (error.source === 'network') return 'No se pudo conectar con el servicio. Intentá nuevamente.'
  if (error.status && error.status >= 500) return 'El servidor no pudo procesar la recepción. Intentá nuevamente.'
  return fallback
}

function toCamelCase(value: string) {
  return value.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase())
}
