import { Alert, Button, Card, Group, Loader, Pagination, Stack, Table, Text, TextInput, Title } from '@mantine/core'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router'
import { httpJson } from '@/api/httpClient'
import { isApiError } from '@/api/httpError'
import { GovernancePanel } from './GovernancePanel'

type Family = 'users' | 'roles' | 'presets' | 'scopes' | 'history'
type Page = { items: Record<string, unknown>[]; page: number; page_size: number; total: number }
const HISTORY_FILTERS = ['subject_type', 'change_kind', 'date_from', 'date_to'] as const
const config: Record<Family, { title: string; endpoint: string; id?: string; label: string }> = {
  users: { title: 'Users', endpoint: '/access/users', id: 'user_id', label: 'display_name' },
  roles: { title: 'Roles', endpoint: '/access/roles', id: 'role_id', label: 'role_name' },
  presets: { title: 'Role presets', endpoint: '/access/role-presets', id: 'preset_id', label: 'preset_name' },
  scopes: { title: 'Scopes', endpoint: '/access/scopes', id: 'scope_id', label: 'scope_name' },
  history: { title: 'Access history', endpoint: '/access/audits', label: 'change_kind' },
}

function text(value: unknown) { return typeof value === 'string' ? value : '' }
function itemLabel(item: Record<string, unknown>, family: Family) { return text(item[config[family].label]) || text(item.scope_code) || text(item.audit_id) }

export default function AdministrationPage() {
  const { family: rawFamily, subjectId } = useParams()
  const family: Family = rawFamily && rawFamily in config ? rawFamily as Family : 'users'
  const current = config[family]
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const [data, setData] = useState<{ key: string; page: Page } | null>(null)
  const [failure, setFailure] = useState<{ key: string; message: string } | null>(null)
  const [query, setQuery] = useState('')
  const generation = useRef(0)
  const page = Math.max(1, Number(params.get('page')) || 1)
  const filterKey = HISTORY_FILTERS.map((key) => `${key}=${params.get(key) ?? ''}`).join('&')
  const requestKey = `${family}:${subjectId ?? ''}:${page}:${filterKey}`

  useEffect(() => {
    const controller = new AbortController(); const request = ++generation.current
    if (subjectId && current.id) {
      void httpJson<Record<string, unknown>>(`${current.endpoint}/${subjectId}`, { signal: controller.signal, recoverAccessDenied: true })
        .then((item) => { if (request === generation.current) { setFailure(null); setData({ key: requestKey, page: { items: [item], page: 1, page_size: 1, total: 1 } }) } })
        .catch((error: unknown) => {
          if (isApiError(error) && error.kind === 'aborted') return
          if (isApiError(error) && error.status === 404) navigate(`/access/${family}`, { replace: true })
          else if (request === generation.current) setFailure({ key: requestKey, message: 'The administration data is unavailable.' })
        })
      return () => controller.abort()
    }
    const search = new URLSearchParams({ page: String(page), page_size: '50' })
    if (family === 'history') new URLSearchParams(filterKey).forEach((value, key) => { if (value) search.set(key, value) })
    void httpJson<Page>(`${current.endpoint}?${search}`, { signal: controller.signal, recoverAccessDenied: true })
      .then((result) => { if (request === generation.current) {
        if (result.items.length === 0 && result.total > 0 && page > 1) setParams((old) => { old.set('page', String(page - 1)); return old })
        else { setFailure(null); setData({ key: requestKey, page: result }) }
      } })
      .catch((error: unknown) => {
        if (isApiError(error) && error.kind === 'aborted') return
        if (request === generation.current) setFailure({ key: requestKey, message: 'The administration data is unavailable.' })
      })
    return () => controller.abort()
  }, [current.endpoint, current.id, family, filterKey, navigate, page, requestKey, setParams, subjectId])

  const currentPage = data?.key === requestKey ? data.page : null
  const currentFailure = failure?.key === requestKey ? failure.message : null
  const shown = (currentPage?.items ?? []).filter((item) => itemLabel(item, family).toLocaleLowerCase().includes(query.toLocaleLowerCase()))
  const update = (key: string, value: string) => setParams((old) => { if (value) old.set(key, value); else old.delete(key); old.set('page', '1'); return old })
  if (currentFailure) return <Alert>{currentFailure}</Alert>
  if (!currentPage) return <Stack align="center" py="xl"><Loader aria-label="Loading administration" /></Stack>
  return <Stack gap="lg"><Group justify="space-between"><Title order={1}>{current.title}</Title></Group>
    {subjectId ? <><Button variant="subtle" onClick={() => navigate(`/access/${family}?page=${page}`)}>Back to {current.title}</Button><Card withBorder><Text>{itemLabel(currentPage.items[0] ?? {}, family)}</Text>{family === 'users' || family === 'roles' || family === 'presets' ? <GovernancePanel family={family} item={currentPage.items[0] ?? {}} onReconcile={() => navigate(`/access/${family}/${subjectId}`, { replace: true })} /> : null}</Card></> : <>
      {family === 'history' ? <Group grow>{HISTORY_FILTERS.map((key) => <TextInput key={key} label={key.split('_').map((part) => part[0].toUpperCase() + part.slice(1)).join(' ')} value={params.get(key) ?? ''} onChange={(event) => update(key, event.currentTarget.value)} />)}</Group> : <TextInput label="Filter loaded page" value={query} onChange={(event) => setQuery(event.currentTarget.value)} description="Filters this loaded page only." />}
      {currentPage.items.length === 0 ? <Alert>No records found.</Alert> : shown.length === 0 ? <Alert>No matches on this loaded page.</Alert> : <Table style={{ minWidth: 500 }}><Table.Thead><Table.Tr><Table.Th>Identity</Table.Th><Table.Th>Status</Table.Th></Table.Tr></Table.Thead><Table.Tbody>{shown.map((item) => { const id = current.id ? text(item[current.id]) : ''
        return <Table.Tr key={id || text(item.audit_id)}><Table.Td>{id ? <Text component={Link} to={`/access/${family}/${id}`}>{itemLabel(item, family)}</Text> : itemLabel(item, family)}</Table.Td><Table.Td>{typeof item.is_active === 'boolean' ? item.is_active ? 'Active' : 'Inactive' : text(item.occurred_at)}</Table.Td></Table.Tr> })}</Table.Tbody></Table>}
      {currentPage.total > 50 ? <Pagination value={page} onChange={(next) => update('page', String(next))} total={Math.ceil(currentPage.total / 50)} getControlProps={(control) => control === 'next' ? { 'aria-label': 'Next page' } : {}} /> : null}
    </>}</Stack>
}
