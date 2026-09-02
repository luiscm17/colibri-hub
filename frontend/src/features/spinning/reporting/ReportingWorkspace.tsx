import { Alert, Button, Card, Group, SimpleGrid, Stack, Text, TextInput, Title } from '@mantine/core'
import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router'
import type { DashboardFilters, DashboardMetric, DashboardProjection, RemoteState, SpinningGateway } from '../integration/contracts'
import { unavailableIntegrationState } from '../integration/unavailableGateway'

const filterKeys = ['businessDateFrom', 'businessDateTo', 'shift', 'machine', 'machineGroup', 'yarnCount'] as const
function filtersFromSearchParams(searchParams: URLSearchParams): DashboardFilters {
  return Object.fromEntries(filterKeys.map(key => [key, searchParams.get(key) ?? ''])) as DashboardFilters
}

function writeFilters(searchParams: URLSearchParams, filters: DashboardFilters): URLSearchParams {
  const next = new URLSearchParams(searchParams)
  filterKeys.forEach(key => filters[key] ? next.set(key, filters[key]) : next.delete(key))
  return next
}

export function ReportingWorkspace({ gateway, section }: { gateway: SpinningGateway; section?: string }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const filterQuery = searchParams.toString()
  const filters = useMemo(() => filtersFromSearchParams(new URLSearchParams(filterQuery)), [filterQuery])
  const [state, setState] = useState<RemoteState<DashboardProjection>>({ status: 'loading' })
  const [reloadVersion, setReloadVersion] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    const getDashboard = gateway.getDashboard ?? (() => Promise.resolve(unavailableIntegrationState))
    void Promise.resolve().then(async () => {
      if (controller.signal.aborted) return
      setState(current => current.status === 'populated' || current.status === 'stale' ? { status: 'stale', data: current.data, message: 'Actualizando resultados…' } : { status: 'loading' })
      try {
        const result = await getDashboard(filters, section ?? null, controller.signal)
        if (!controller.signal.aborted) setState(result)
      } catch {
        if (!controller.signal.aborted) setState(current => current.status === 'populated' || current.status === 'stale' ? { status: 'stale', data: current.data, message: 'No se pudieron actualizar los resultados.' } : { status: 'failure', message: 'No se pudieron cargar los resultados.' })
      }
    })
    return () => controller.abort()
  }, [filters, gateway, reloadVersion, section])

  const updateFilter = (key: keyof DashboardFilters, value: string) => setSearchParams(writeFilters(searchParams, { ...filters, [key]: value }))
  const title = section ? `Reporte de ${section}` : 'Informes consolidados'
  return <Stack gap="md" component="section" aria-labelledby={section ? 'section-report-title' : 'consolidated-report-title'}>
    <div><Title order={2} id={section ? 'section-report-title' : 'consolidated-report-title'}>{title}</Title><Text>Resultados de consulta confirmados por el servidor</Text></div>
    <Card withBorder padding="md" component="form" aria-label="Filtros del reporte" onSubmit={event => event.preventDefault()}>
      <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }}>
        <TextInput type="date" label="Fecha desde" value={filters.businessDateFrom} onChange={event => updateFilter('businessDateFrom', event.currentTarget.value)} />
        <TextInput type="date" label="Fecha hasta" value={filters.businessDateTo} onChange={event => updateFilter('businessDateTo', event.currentTarget.value)} />
        <TextInput label="Turno" value={filters.shift} onChange={event => updateFilter('shift', event.currentTarget.value)} />
        <TextInput label="Máquina" value={filters.machine} onChange={event => updateFilter('machine', event.currentTarget.value)} />
        <TextInput label="Grupo de máquinas" value={filters.machineGroup} onChange={event => updateFilter('machineGroup', event.currentTarget.value)} />
        <TextInput label="Título de hilo" value={filters.yarnCount} onChange={event => updateFilter('yarnCount', event.currentTarget.value)} />
      </SimpleGrid>
    </Card>
    <ReportingResults state={state} onRetry={() => setReloadVersion(version => version + 1)} />
  </Stack>
}

function ReportingResults({ state, onRetry }: { state: RemoteState<DashboardProjection>; onRetry: () => void }) {
  if (state.status === 'loading') return <Text role="status" aria-live="polite">Cargando resultados del reporte…</Text>
  if (state.status === 'failure') return <Alert color="red" role="alert" title="No se pudieron cargar los resultados"><Group justify="space-between"><Text>{state.message}</Text><Button onClick={onRetry}>Reintentar</Button></Group></Alert>
  if (state.status === 'unavailable') return <Alert role="status" title="Reporte no disponible">{state.message}</Alert>
  if (state.status === 'empty') return <Alert role="status">No hay datos de origen para los filtros seleccionados.</Alert>
  if (state.status === 'stale') return <><Alert color="yellow" role="status">{state.message}</Alert><DashboardProjectionView projection={state.data} /></>
  if (state.status === 'populated') return <DashboardProjectionView projection={state.data} />
  return <Alert role="status">El reporte no está disponible en este estado.</Alert>
}

function DashboardProjectionView({ projection }: { projection: DashboardProjection }) {
  if (projection.sections.length === 0) return <Alert role="status">No hay datos de origen para los filtros seleccionados.</Alert>
  return <Stack gap="md">{projection.sections.map(section => <section key={section.section} aria-labelledby={`report-section-${section.section}`}><Text fw={600} id={`report-section-${section.section}`}>{section.section}</Text><SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} mt="xs">{section.metrics.map(metric => <MetricCard key={metric.name} metric={metric} />)}</SimpleGrid></section>)}</Stack>
}

function MetricCard({ metric }: { metric: DashboardMetric }) {
  const availabilityLabel = { available: 'Disponible', zero: 'Cero confirmado', not_applicable: 'No aplicable', unavailable: 'No disponible' }[metric.availability]
  const unavailableReason = metric.availability === 'available' || metric.availability === 'zero' ? null : metric.reason ?? availabilityLabel
  return <Card withBorder padding="md"><Text size="sm" c="dimmed">{metric.name}</Text><Text size="xs" c="dimmed">Unidad: {metric.unit ?? 'No informada'}</Text><Text size="xs" c="dimmed">Disponibilidad: {availabilityLabel}</Text>{unavailableReason ? <Text role="status">{unavailableReason}</Text> : <Text size="xl" fw={700} aria-label={`${metric.name}: ${metric.value} ${metric.unit ?? ''}`}>{metric.value} {metric.unit}</Text>}</Card>
}
