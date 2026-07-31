import { Card, Group, SimpleGrid, Stack, Text, ThemeIcon, Title } from '@mantine/core'
import {
  IconArrowRight,
  IconPackageImport,
  IconPackages,
  IconTruckDelivery,
} from '@tabler/icons-react'
import { Link } from 'react-router-dom'
import classes from './BaleManagementPage.module.css'

const workflowCards = [
  {
    label: 'Recepción',
    description: 'Registrar la recepción de fardos de materia prima.',
    path: '/warehouse/bales/reception',
    icon: IconPackageImport,
  },
  {
    label: 'Stock',
    description: 'Consultar el stock y la trazabilidad de los fardos.',
    path: '/warehouse/bales/stock',
    icon: IconPackages,
  },
  {
    label: 'Entrega',
    description: 'Registrar la entrega de fardos a producción.',
    path: '/warehouse/bales/delivery',
    icon: IconTruckDelivery,
  },
] as const

export default function BaleManagementPage() {
  return (
    <Stack gap="xl">
      <Stack gap="xs">
        <Title order={1}>Gestión de fardos</Title>
        <Text c="dimmed">Seleccioná el flujo de trabajo que necesitás realizar.</Text>
      </Stack>

      <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }}>
        {workflowCards.map(({ label, description, path, icon: Icon }) => (
          <Card
            key={path}
            component={Link}
            to={path}
            withBorder
            padding="lg"
            radius="md"
            className={classes.card}
          >
            <Group justify="space-between" align="flex-start" wrap="nowrap">
              <ThemeIcon variant="light" size="lg" radius="md">
                <Icon aria-hidden size={20} />
              </ThemeIcon>
              <IconArrowRight aria-hidden size={20} />
            </Group>
            <Title order={2} size="h3" mt="md">
              {label}
            </Title>
            <Text c="dimmed" size="sm" mt="xs">
              {description}
            </Text>
          </Card>
        ))}
      </SimpleGrid>
    </Stack>
  )
}
