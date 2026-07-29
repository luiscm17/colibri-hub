import { Alert, Button, Group, Modal, Stack, Text, TextInput } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import { IconAlertCircle } from '@tabler/icons-react'
import { useRef, useState } from 'react'
import { PageHeader } from '@/common/components/PageHeader'
import { deliverBales } from '../api/baleApi'
import { BaleApiError } from '../api/baleApi.errors'
import { DeliveryGrid } from '../components/delivery/DeliveryGrid'
import { useBaleDelivery } from '../hooks/useBaleDelivery'

export default function BaleDeliveryPage() {
  const delivery = useBaleDelivery()
  const [confirmOpened, confirm] = useDisclosure(false)
  const [clearOpened, clear] = useDisclosure(false)
  const [submitting, setSubmitting] = useState(false)
  const [attempted, setAttempted] = useState(false)
  const [message, setMessage] = useState<string>()
  const [outcomeSummary, setOutcomeSummary] = useState<string>()
  const submitRef = useRef<HTMLButtonElement>(null)
  const activeRows = delivery.rows.filter(row => row.shipmentNumber.trim() || row.baleNumber.trim())
  const hasDraft = activeRows.length > 0

  function requestDelivery() {
    setAttempted(true)
    setMessage(undefined)
    if (!delivery.isReady) return
    confirm.open()
  }

  async function submit() {
    const snapshot = delivery.snapshot()
    confirm.close()
    setSubmitting(true)
    try {
      const response = await deliverBales(snapshot)
      delivery.applyOutcomes(response.results)
      const summary = `${response.deliveredCount} entregado${response.deliveredCount === 1 ? '' : 's'} · ${response.failedCount} con error`
      setOutcomeSummary(summary)
      setMessage(undefined)
      notifications.show({ color: response.failedCount ? 'yellow' : 'green', title: 'Entrega procesada', message: summary })
    } catch (error) {
      const nextMessage = deliveryErrorMessage(error)
      setMessage(nextMessage)
      notifications.show({ color: 'red', title: 'No se pudo registrar la entrega', message: nextMessage })
    } finally { setSubmitting(false) }
  }

  function clearDraft() { delivery.reset(); setAttempted(false); setMessage(undefined); setOutcomeSummary(undefined); clear.close(); submitRef.current?.focus() }

  return <Stack gap="lg">
    <PageHeader title="Entrega de fardos a Producción" />
    {message ? <Alert color="red" icon={<IconAlertCircle size={16} />} role="alert">{message}</Alert> : null}
    <TextInput label="Fecha de entrega" type="date" required value={delivery.deliveryDate} onChange={event => delivery.setDeliveryDate(event.currentTarget.value)} error={attempted && !delivery.deliveryDate ? 'Ingresá la fecha de entrega.' : undefined} disabled={submitting} />
    <DeliveryGrid rows={delivery.rows} feedback={delivery.feedback} disabled={submitting} onRowsChange={delivery.updateRows} onPaste={delivery.paste} />
    {outcomeSummary ? <Alert color="blue" role="status">{outcomeSummary}</Alert> : null}
    {attempted && !delivery.isReady && activeRows.some(row => row.result !== 'delivered') ? <Alert color="red" role="alert">Completá la fecha y al menos una identidad sin errores antes de confirmar.</Alert> : null}
    <Group><Button ref={submitRef} onClick={requestDelivery} loading={submitting} disabled={submitting || !hasDraft}>Entregar</Button><Button variant="default" onClick={() => hasDraft ? clear.open() : clearDraft()} disabled={submitting}>Limpiar</Button></Group>
    <Modal opened={confirmOpened} onClose={confirm.close} title="Confirmar entrega irreversible" centered><Stack><Text>Vas a registrar la entrega irreversible de {delivery.snapshot().bales.length} fardo{delivery.snapshot().bales.length === 1 ? '' : 's'} con fecha {delivery.deliveryDate}.</Text><Text size="sm" c="dimmed">Los fardos entregados no podrán volver a entregarse.</Text><Group justify="flex-end"><Button variant="default" onClick={confirm.close}>Cancelar</Button><Button color="red" onClick={() => void submit()}>Confirmar entrega</Button></Group></Stack></Modal>
    <Modal opened={clearOpened} onClose={clear.close} title="Limpiar entrega" centered><Stack><Text>Se perderán los datos cargados en esta página.</Text><Group justify="flex-end"><Button variant="default" onClick={clear.close}>Cancelar</Button><Button color="red" onClick={clearDraft}>Limpiar</Button></Group></Stack></Modal>
  </Stack>
}

function deliveryErrorMessage(error: unknown) {
  if (error instanceof BaleApiError && error.kind === 'validation') return 'Corregí los datos indicados y volvé a intentar.'
  if (error instanceof BaleApiError && error.kind === 'conflict') return 'La entrega cambió mientras se procesaba. Revisá los resultados e intentá nuevamente.'
  if (error instanceof BaleApiError && error.kind === 'unavailable') return 'No se pudo conectar con el servicio. Intentá nuevamente.'
  return 'Ocurrió un error inesperado. Intentá nuevamente.'
}
