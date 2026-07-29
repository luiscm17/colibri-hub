import { Paper, SimpleGrid, TextInput } from '@mantine/core'
import type { ReceptionHeader as ReceptionHeaderModel } from '../../model/reception'

interface ReceptionHeaderProps {
  readonly header: ReceptionHeaderModel
  readonly errors?: Readonly<Record<string, string>>
  readonly onChange: (field: keyof ReceptionHeaderModel, value: string) => void
}

export function ReceptionHeader({ header, errors = {}, onChange }: ReceptionHeaderProps) {
  return (
    <Paper component="section" withBorder p="md" aria-label="Datos de la recepción">
      <SimpleGrid cols={{ base: 1, sm: 3 }}>
        <TextInput
          label="Número de remito"
          value={header.shipmentNumber}
          onChange={event => onChange('shipmentNumber', event.currentTarget.value)}
          error={errors.shipmentNumber ? 'Ingresá el número de remito.' : undefined}
          required
        />
        <TextInput
          label="Fecha de recepción"
          type="date"
          value={header.receptionDate}
          onChange={event => onChange('receptionDate', event.currentTarget.value)}
          error={errors.receptionDate ? 'Ingresá la fecha de recepción.' : undefined}
          required
        />
        <TextInput
          label="Proveedor"
          value={header.providerName}
          onChange={event => onChange('providerName', event.currentTarget.value)}
          error={errors.providerName ? 'Ingresá el proveedor.' : undefined}
          required
        />
      </SimpleGrid>
    </Paper>
  )
}
