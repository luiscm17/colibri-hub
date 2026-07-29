import { Alert, Button, Card, Divider, Group, Select, SimpleGrid, Stack, Text, TextInput } from '@mantine/core'
import { IconAlertCircle, IconSearch } from '@tabler/icons-react'
import { useState } from 'react'
import { PageHeader } from '@/common/components/PageHeader'
import { useBaleStock } from '../hooks/useBaleStock'
import type { BaleStatus, StockFilters } from '../model/stock'

type FilterDraft = Required<Omit<StockFilters, 'status'>> & { status: BaleStatus | '' }

const emptyFilters: FilterDraft = {
  receivedFrom: '', receivedTo: '', shipmentNumber: '', status: '', providerName: '', materialType: '', dtex: '',
}

const metricLabels = [
  ['Fardos totales', 'totalBaleCount'],
  ['Fardos en almacén', 'inWarehouseBaleCount'],
  ['Fardos entregados', 'deliveredBaleCount'],
  ['Peso neto total (kg)', 'totalNetWeightKg'],
  ['Peso neto en almacén (kg)', 'inWarehouseNetWeightKg'],
  ['Peso neto entregado (kg)', 'deliveredNetWeightKg'],
] as const

export default function BaleStockPage() {
  const stock = useBaleStock()
  const summary = stock.summary
  const [filters, setFilters] = useState<FilterDraft>(emptyFilters)
  const [filterError, setFilterError] = useState<string>()
  const [lookup, setLookup] = useState({ shipmentNumber: '', baleNumber: '' })
  const [lookupError, setLookupError] = useState<string>()

  function updateFilter(field: keyof FilterDraft, value: string | null) {
    setFilters(current => ({ ...current, [field]: value ?? '' }))
  }

  function updateLookup(field: 'shipmentNumber' | 'baleNumber', value: string) {
    setLookup(current => ({ ...current, [field]: value }))
  }

  function applyFilters() {
    if (filters.receivedFrom && filters.receivedTo && filters.receivedFrom > filters.receivedTo) {
      setFilterError('La fecha desde no puede ser posterior a la fecha hasta.')
      return
    }
    setFilterError(undefined)
    void stock.loadSummary(withOptionalValues(filters))
  }

  function searchBale() {
    if (!lookup.shipmentNumber.trim() || !lookup.baleNumber.trim()) {
      setLookupError('Ingresá el número de remito y el número de fardo para consultar.')
      return
    }
    setLookupError(undefined)
    void stock.lookupDetail(lookup.shipmentNumber, lookup.baleNumber)
  }

  return (
    <Stack gap="lg">
      <PageHeader title="Stock de fardos" />
      <Card component="section" withBorder padding="lg" aria-labelledby="stock-filters-title">
        <Stack gap="md">
          <Text id="stock-filters-title" fw={600}>Filtros de stock</Text>
          <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }}>
            <TextInput type="date" label="Recibido desde" value={filters.receivedFrom} onChange={event => updateFilter('receivedFrom', event.currentTarget.value)} />
            <TextInput type="date" label="Recibido hasta" value={filters.receivedTo} onChange={event => updateFilter('receivedTo', event.currentTarget.value)} />
            <TextInput label="Número de remito" value={filters.shipmentNumber} onChange={event => updateFilter('shipmentNumber', event.currentTarget.value)} />
            <Select label="Estado" value={filters.status} onChange={value => updateFilter('status', value)} data={[{ value: 'in_warehouse', label: 'En almacén' }, { value: 'delivered', label: 'Entregado' }]} clearable />
            <TextInput label="Proveedor" value={filters.providerName} onChange={event => updateFilter('providerName', event.currentTarget.value)} />
            <TextInput label="Material" value={filters.materialType} onChange={event => updateFilter('materialType', event.currentTarget.value)} />
            <TextInput label="Dtex" value={filters.dtex} onChange={event => updateFilter('dtex', event.currentTarget.value)} />
          </SimpleGrid>
          {filterError ? <Alert color="red" icon={<IconAlertCircle size={16} />} role="alert">{filterError}</Alert> : null}
          <Group><Button onClick={applyFilters} loading={stock.summaryState === 'loading'}>Aplicar filtros</Button></Group>
        </Stack>
      </Card>

      <section aria-labelledby="stock-summary-title" aria-busy={stock.summaryState === 'loading'}>
        <Group justify="space-between" mb="sm"><Text id="stock-summary-title" fw={600}>Resumen de stock</Text>{stock.summaryState === 'loading' ? <Text role="status">Actualizando stock…</Text> : null}</Group>
        {stock.summaryError ? <Alert color="red" icon={<IconAlertCircle size={16} />} role="alert" title="No se pudo actualizar el stock"><Group justify="space-between"><Text>{stock.summaryError}</Text><Button variant="light" color="red" onClick={() => void stock.loadSummary(stock.appliedFilters)}>Reintentar</Button></Group></Alert> : null}
        {summary ? <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }}>{metricLabels.map(([label, key]) => <Card key={key} withBorder padding="md"><Text size="sm" c="dimmed">{label}</Text><Text size="xl" fw={700}>{summary[key]}</Text></Card>)}</SimpleGrid> : null}
      </section>

      <Divider />
      <Card component="section" withBorder padding="lg" aria-labelledby="bale-lookup-title">
        <Stack gap="md">
          <Text id="bale-lookup-title" fw={600}>Consultar fardo</Text>
          <SimpleGrid cols={{ base: 1, sm: 2 }}>
            <TextInput label="Número de remito" value={lookup.shipmentNumber} onChange={event => updateLookup('shipmentNumber', event.currentTarget.value)} />
            <TextInput label="Número de fardo" value={lookup.baleNumber} onChange={event => updateLookup('baleNumber', event.currentTarget.value)} />
          </SimpleGrid>
          {lookupError ? <Alert color="red" icon={<IconAlertCircle size={16} />} role="alert">{lookupError}</Alert> : null}
          <Group><Button leftSection={<IconSearch size={16} />} onClick={searchBale} loading={stock.detailState === 'loading'}>Buscar fardo</Button></Group>
          {stock.detailState === 'loading' ? <Text role="status">Consultando fardo…</Text> : null}
          {stock.detailError ? <Alert color="red" icon={<IconAlertCircle size={16} />} role="alert" title="No se pudo consultar el fardo"><Group justify="space-between"><Text>{stock.detailError}</Text><Button variant="light" color="red" onClick={searchBale}>Reintentar</Button></Group></Alert> : null}
          {stock.detailNotFound ? <Alert color="gray" role="status">No se encontró un fardo con esa combinación de remito y número.</Alert> : null}
          {stock.detail ? <BaleDetail detail={stock.detail} /> : null}
        </Stack>
      </Card>
    </Stack>
  )
}

function BaleDetail({ detail }: { readonly detail: NonNullable<ReturnType<typeof useBaleStock>['detail']> }) {
  const fields = [
    ['Remito', detail.shipmentNumber], ['Fardo', detail.baleNumber], ['Fecha de recepción', detail.receptionDate], ['Proveedor', detail.providerName],
    ['Material', detail.materialType], ['Dtex', detail.dtex], ['Peso bruto (kg)', detail.grossWeightKg], ['Tara (kg)', detail.containerWeightKg],
    ['Peso neto (kg)', detail.netWeightKg], ['Estado', detail.status === 'in_warehouse' ? 'En almacén' : 'Entregado'],
    ...(detail.deliveryDate ? [['Fecha de entrega', detail.deliveryDate]] : []),
  ]
  return <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} aria-label="Detalle del fardo">{fields.map(([label, value]) => <Card key={label} withBorder padding="sm"><Text size="xs" c="dimmed">{label}</Text><Text fw={600}>{value}</Text></Card>)}</SimpleGrid>
}

function withOptionalValues(filters: FilterDraft): StockFilters {
  return Object.fromEntries(Object.entries(filters).filter(([, value]) => value)) as StockFilters
}
