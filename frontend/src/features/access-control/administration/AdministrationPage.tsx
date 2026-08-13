import { Alert, Loader, Stack } from '@mantine/core'
import { useEffect } from 'react'
import { useParams } from 'react-router'
import { httpJson } from '@/api/httpClient'
import { resolveAdministrationOperation } from './operations'
import { AdministrationShell } from './AdministrationShell'
import type { AdministrationFamily } from './operations'

export default function AdministrationPage({ family: declaredFamily, mode }: { family?: string; mode?: 'edit' } = {}) {
  const { family: routeFamily, subjectId } = useParams()
  const family = declaredFamily ?? routeFamily
  const operation = resolveAdministrationOperation(family, subjectId, mode)

  useEffect(() => {
    if (!operation?.endpoint || operation.request === 'none') return
    const controller = new AbortController()
    const path = operation.request === 'detail' ? `${operation.endpoint}/${subjectId}` : `${operation.endpoint}?page=1&page_size=50`
    void httpJson(path, { signal: controller.signal, recoverAccessDenied: true })
    return () => controller.abort()
  }, [operation, subjectId])

  if (!operation || !family) return <Alert>Unsupported administration state.</Alert>
  if (operation.request === 'none') return <Alert>{operation.title} is not available yet.</Alert>
  return <AdministrationShell route={{ family: family as AdministrationFamily, criteria: {}, page: 1, subjectId }}>
    {() => <Stack align="center" py="xl"><Loader aria-label="Loading administration" /></Stack>}
  </AdministrationShell>
}

export function AdministrationEditPage({ family }: { family?: string }) { return <AdministrationPage family={family} mode="edit" /> }
