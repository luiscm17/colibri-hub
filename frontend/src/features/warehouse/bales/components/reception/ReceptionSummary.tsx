import { Paper, SimpleGrid, Stack, Text, Title } from '@mantine/core'
import type { ReceptionSummary as ReceptionSummaryModel } from '../../model/receptionGrid'

interface ReceptionSummaryProps {
  readonly summary: ReceptionSummaryModel
}

export function ReceptionSummary({ summary }: ReceptionSummaryProps) {
  return (
    <Paper component="section" withBorder p="md" aria-labelledby="reception-summary-title">
      <Stack gap="sm">
        <Title order={2} size="h3" id="reception-summary-title">Resumen de recepción</Title>
        <SimpleGrid cols={{ base: 1, sm: 3 }}>
          <Metric label="Fardos con contenido" value={String(summary.contentCount)} />
          <Metric label="Filas válidas" value={String(summary.validCount)} />
          <Metric label="Filas con errores" value={String(summary.errorCount)} />
        </SimpleGrid>
        <SimpleGrid cols={{ base: 1, sm: 3 }}>
          <Metric label="Total bruto (kg)" value={summary.totalGrossWeightKg} />
          <Metric label="Total tara (kg)" value={summary.totalContainerWeightKg} />
          <Metric label="Total neto (kg)" value={summary.totalNetWeightKg} />
        </SimpleGrid>
      </Stack>
    </Paper>
  )
}

function Metric({ label, value }: { readonly label: string; readonly value: string }) {
  return (
    <div>
      <Text size="sm" c="dimmed">{label}</Text>
      <Text fw={700}>{value}</Text>
    </div>
  )
}
