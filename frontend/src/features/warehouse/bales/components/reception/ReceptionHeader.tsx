import { Paper, SimpleGrid, TextInput } from '@mantine/core'
import { useEffect, useRef } from 'react'
import type { ReceptionHeader as ReceptionHeaderModel } from '../../model/reception'

interface ReceptionHeaderProps {
  readonly header: ReceptionHeaderModel
  readonly errors?: Readonly<Record<string, string>>
  readonly onChange: (field: keyof ReceptionHeaderModel, value: string) => void
  readonly disabled?: boolean
  readonly focusField?: keyof ReceptionHeaderModel
}

export function ReceptionHeader({ header, errors = {}, onChange, disabled = false, focusField }: ReceptionHeaderProps) {
  const inputs = useRef<Partial<Record<keyof ReceptionHeaderModel, HTMLInputElement>>>({})

  useEffect(() => {
    if (focusField) inputs.current[focusField]?.focus()
  }, [focusField])

  return (
    <Paper component="section" withBorder p="md" aria-label="Datos de la recepción">
      <SimpleGrid cols={{ base: 1, sm: 3 }}>
        <TextInput
          label="Número de remito"
          name="shipmentNumber"
          ref={element => { inputs.current.shipmentNumber = element ?? undefined }}
          value={header.shipmentNumber}
          onChange={event => onChange('shipmentNumber', event.currentTarget.value)}
          error={headerError(errors.shipmentNumber, 'Ingresá el número de remito.')}
          required
          disabled={disabled}
        />
        <TextInput
          label="Fecha de recepción"
          name="receptionDate"
          ref={element => { inputs.current.receptionDate = element ?? undefined }}
          type="date"
          value={header.receptionDate}
          onChange={event => onChange('receptionDate', event.currentTarget.value)}
          error={headerError(errors.receptionDate, 'Ingresá la fecha de recepción.')}
          required
          disabled={disabled}
        />
        <TextInput
          label="Proveedor"
          name="providerName"
          ref={element => { inputs.current.providerName = element ?? undefined }}
          value={header.providerName}
          onChange={event => onChange('providerName', event.currentTarget.value)}
          error={headerError(errors.providerName, 'Ingresá el proveedor.')}
          required
          disabled={disabled}
        />
      </SimpleGrid>
    </Paper>
  )
}

function headerError(error: string | undefined, localMessage: string) {
  return error === 'This field is required.' ? localMessage : error
}
