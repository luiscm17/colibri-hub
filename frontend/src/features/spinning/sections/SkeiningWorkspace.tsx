import { Stack, Text, Title } from '@mantine/core'
import { useEffect, useState } from 'react'
import type { ProductionDischargeCatalog, RemoteState, SpinningGateway } from '../integration/contracts'
import { unavailableSpinningGateway } from '../integration/unavailableGateway'
import { SkeiningGrid } from './SkeiningGrid'
import { appendSkeiningRow, createSkeiningDraft, replaceSkeiningRows } from './skeiningModel'

export function SkeiningWorkspace({ gateway = unavailableSpinningGateway }: { gateway?: SpinningGateway }) {
  const [draft, setDraft] = useState(createSkeiningDraft)
  const [catalog, setCatalog] = useState<RemoteState<ProductionDischargeCatalog>>({ status: 'loading' })

  useEffect(() => {
    const controller = new AbortController()
    void gateway.getProductionDischargeCatalog({ section: 'skeining', businessDate: '', shift: '' }, controller.signal).then(result => {
      if (!controller.signal.aborted) setCatalog(result)
    })
    return () => controller.abort()
  }, [gateway])

  return <Stack gap="lg">
    <div><Title order={1}>Madejeras</Title><Text>Producción independiente de Hilatura</Text></div>
    <SkeiningGrid catalog={catalog} draft={draft} onRowsChange={rows => setDraft(current => replaceSkeiningRows(current, rows))} onAddRow={() => setDraft(appendSkeiningRow)} />
    <Text>Los borradores permanecen locales; no se muestra un total derivado hasta que el servidor lo confirme.</Text>
  </Stack>
}
