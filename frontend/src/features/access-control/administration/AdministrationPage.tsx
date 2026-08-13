import { Alert, Button, Card, Group, Loader, Pagination, Stack, Table, Text, TextInput, Title } from '@mantine/core'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router'
import { httpJson } from '@/api/httpClient'
import { isApiError } from '@/api/httpError'
import { resolveAdministrationOperation } from './operations'
import { AdministrationShell } from './AdministrationShell'
import { PresetCopyPanel } from './presets/PresetCopyPanel'
import { auditValues } from './scopes/history'
import { ScopeRegistrationPanel, ScopeStatusControl } from './scopes/ScopeGovernance'
import { UserRoleReplacementPanel } from './mutations/UserRoleReplacementPanel'

type Page = { items: Record<string, unknown>[]; page: number; page_size: number; total: number }
const HISTORY_FILTERS = ['subject_type', 'change_kind', 'date_from', 'date_to'] as const
const text = (value: unknown) => typeof value === 'string' ? value : ''

export default function AdministrationPage({ family: declaredFamily, mode }: { family?: string; mode?: 'edit' } = {}) {
  const { family: routeFamily, subjectId } = useParams()
  const family = declaredFamily ?? routeFamily
  const operation = resolveAdministrationOperation(family, subjectId, mode)
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const [data, setData] = useState<{ key: string; page: Page } | null>(null)
  const [failure, setFailure] = useState<{ key: string; message: string } | null>(null)
  const [query, setQuery] = useState('')
  const generation = useRef(0)
  const page = Math.max(1, Number(params.get('page')) || 1)
  const criteria = Object.fromEntries(HISTORY_FILTERS.flatMap((key) => params.get(key) ? [[key, params.get(key)!]] : []))
  const filterKey = new URLSearchParams(criteria).toString()
  const requestKey = `${family}:${subjectId ?? ''}:${page}:${filterKey}`

  const projectRoute = (route: { family: string; criteria: Readonly<Record<string, string>>; page: number; subjectId?: string }) => {
    const search = new URLSearchParams(route.criteria)
    if (route.page > 1) search.set('page', String(route.page))
    navigate(`/access/${route.family}${route.subjectId ? `/${route.subjectId}` : ''}${search.size ? `?${search}` : ''}`, { replace: true })
  }

  useEffect(() => {
    if (!operation?.endpoint || operation.request === 'none') return
    const controller = new AbortController()
    const request = ++generation.current
    const requestCriteria = Object.fromEntries(new URLSearchParams(filterKey))
    const search = new URLSearchParams({ page: String(page), page_size: '50', ...requestCriteria })
    const path = operation.request === 'detail' ? `${operation.endpoint}/${subjectId}` : `${operation.endpoint}?${search}`
    void httpJson<Record<string, unknown> | Page>(path, { signal: controller.signal, recoverAccessDenied: true })
      .then((result) => {
        if (request !== generation.current) return
        const resultPage: Page = operation.request === 'detail'
          ? { items: [result as Record<string, unknown>], page: 1, page_size: 1, total: 1 }
          : result as Page
        if (resultPage.items.length === 0 && resultPage.total > 0 && page > 1) navigate(`/access/${operation.family}?${new URLSearchParams({ ...requestCriteria, page: String(page - 1) })}`, { replace: true })
        else { setFailure(null); setData({ key: requestKey, page: resultPage }) }
      })
      .catch((error: unknown) => {
        if (isApiError(error) && error.kind === 'aborted') return
        if (isApiError(error) && error.status === 404 && operation.request === 'detail') navigate(`/access/${operation.family}?${new URLSearchParams({ ...requestCriteria, page: String(page) })}`, { replace: true })
        else if (request === generation.current) setFailure({ key: requestKey, message: 'The administration data is unavailable.' })
      })
    return () => controller.abort()
  }, [filterKey, navigate, operation?.endpoint, operation?.family, operation?.request, page, requestKey, subjectId])

  if (!operation || !family) return <Alert>Unsupported administration state.</Alert>
  if (operation.request === 'none') return <Alert>{operation.title} is not available yet.</Alert>
  const currentPage = data?.key === requestKey ? data.page : null
  const currentFailure = failure?.key === requestKey ? failure.message : null
  const label = (item: Record<string, unknown>) => text(item[operation.label!]) || text(item.scope_code) || text(item.audit_id)
  const shown = (currentPage?.items ?? []).filter((item) => label(item).toLocaleLowerCase().includes(query.toLocaleLowerCase()))
  const update = (key: string, value: string) => setParams((old) => { const next = new URLSearchParams(old); if (value) next.set(key, value); else next.delete(key); if (key !== 'page') next.set('page', '1'); return next })

  return <AdministrationShell route={{ family: operation.family, criteria, page, subjectId }} navigate={projectRoute}>
    {() => currentFailure ? <Alert>{currentFailure}</Alert> : !currentPage ? <Stack align="center" py="xl"><Loader aria-label="Loading administration" /></Stack> :
      <Stack gap="lg"><Group justify="space-between"><Title order={1}>{operation.title}</Title></Group>
          {subjectId ? <><Button variant="subtle" onClick={() => projectRoute({ family: operation.family, criteria, page })}>Back to {operation.title}</Button><Card withBorder><Text>{label(currentPage.items[0] ?? {})}</Text></Card>{operation.family === 'users' && typeof currentPage.items[0]?.version === 'number' ? <UserRoleReplacementPanel key={`${subjectId}:${currentPage.items[0].version}`} userId={subjectId} version={currentPage.items[0].version} roleIds={Array.isArray(currentPage.items[0].roles) ? currentPage.items[0].roles.flatMap((role) => typeof role === 'object' && role && typeof (role as Record<string, unknown>).role_id === 'string' ? [(role as Record<string, string>).role_id] : []) : []} /> : null}{operation.family === 'presets' ? <PresetCopyPanel preset={{ presetId: subjectId, presetCode: text(currentPage.items[0]?.preset_code), presetName: text(currentPage.items[0]?.preset_name), description: text(currentPage.items[0]?.description) || null, permissions: [] }} /> : null}</> : <>
          {operation.family === 'history' ? <Group grow>{HISTORY_FILTERS.map((key) => <TextInput key={key} label={key.split('_').map((part) => part[0].toUpperCase() + part.slice(1)).join(' ')} value={params.get(key) ?? ''} onChange={(event) => update(key, event.currentTarget.value)} />)}</Group> : <TextInput label="Filter loaded page" value={query} onChange={(event) => setQuery(event.currentTarget.value)} description="Filters this loaded page only." />}
          {operation.family === 'scopes' ? <ScopeRegistrationPanel /> : null}
          {currentPage.items.length === 0 ? <Alert>No records found.</Alert> : shown.length === 0 ? <Alert>No matches on this loaded page.</Alert> : operation.family === 'history' ? <Table style={{ minWidth: 500 }}><Table.Thead><Table.Tr>{['Actor', 'Time', 'Reason', 'Subject', 'Change kind'].map((heading) => <Table.Th key={heading}>{heading}</Table.Th>)}</Table.Tr></Table.Thead><Table.Tbody>{shown.map((item) => <Table.Tr key={text(item.audit_id)}>{auditValues(item).map((value, index) => <Table.Td key={index}>{value}</Table.Td>)}</Table.Tr>)}</Table.Tbody></Table> : <Table style={{ minWidth: 500 }}><Table.Thead><Table.Tr><Table.Th>Identity</Table.Th><Table.Th>Status</Table.Th></Table.Tr></Table.Thead><Table.Tbody>{shown.map((item) => { const id = operation.id ? text(item[operation.id]) : ''; return <Table.Tr key={id || text(item.audit_id)}><Table.Td>{id ? <Text component={Link} to={`/access/${operation.family}/${id}`}>{label(item)}</Text> : label(item)}</Table.Td><Table.Td>{operation.family === 'scopes' && id && typeof item.version === 'number' && typeof item.is_active === 'boolean' ? <ScopeStatusControl scopeId={id} version={item.version} isActive={item.is_active} /> : typeof item.is_active === 'boolean' ? item.is_active ? 'Active' : 'Inactive' : text(item.occurred_at)}</Table.Td></Table.Tr> })}</Table.Tbody></Table>}
          {currentPage.total > 50 ? <Pagination value={page} onChange={(next) => update('page', String(next))} total={Math.ceil(currentPage.total / 50)} getControlProps={(control) => control === 'next' ? { 'aria-label': 'Next page' } : {}} /> : null}
        </>}
      </Stack>}
  </AdministrationShell>
}

export function AdministrationEditPage({ family }: { family?: string }) { return <AdministrationPage family={family} mode="edit" /> }
