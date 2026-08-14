import { Alert, Button, Card, Group, Loader, Pagination, Stack, Table, Text, TextInput, Title } from '@mantine/core'
import { useEffect, useEffectEvent, useRef, useState } from 'react'
import { Navigate, useNavigate, useParams, useSearchParams } from 'react-router'
import { httpJson } from '@/api/httpClient'
import { isApiError } from '@/api/httpError'
import { resolveAdministrationOperation } from './operations'
import { AdministrationShell } from './AdministrationShell'
import { PresetDetailWorkflows } from './presets/PresetDetailWorkflows'
import { PresetWorkflow } from './presets/PresetWorkflow'
import { auditValues } from './scopes/history'
import { ScopeRegistrationPanel, ScopeStatusControl } from './scopes/ScopeGovernance'
import { UserRoleReplacementPanel } from './mutations/UserRoleReplacementPanel'
import { RoleWorkflow } from './roles/RoleWorkflow'
import { decodeAdministrationOrigin, encodeAdministrationOrigin, ORIGIN_PARAM, type AdministrationRouteState } from './route-state'

type Page = { items: Record<string, unknown>[]; page: number; page_size: number; total: number }
const HISTORY_FILTERS = ['subject_type', 'change_kind', 'date_from', 'date_to'] as const
const text = (value: unknown) => typeof value === 'string' ? value : ''
const presetPermissions = (item: Record<string, unknown>) => Array.isArray(item.permissions) ? item.permissions.flatMap((permission) => typeof permission === 'object' && permission && typeof (permission as Record<string, unknown>).action === 'string' && typeof (permission as Record<string, unknown>).scope_code === 'string' ? [{ action: (permission as Record<string, string>).action, scopeCode: (permission as Record<string, string>).scope_code }] : []) : []
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

export default function AdministrationPage({ family: declaredFamily, mode }: { family?: string; mode?: 'edit' } = {}) {
  const { family: routeFamily, subjectId } = useParams()
  const family = declaredFamily ?? routeFamily
  const operation = resolveAdministrationOperation(family, subjectId, mode)
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const [data, setData] = useState<{ key: string; page: Page } | null>(null)
  const [failure, setFailure] = useState<{ key: string; message: string } | null>(null)
  const [reload, setReload] = useState(0)
  const generation = useRef(0)
  const heading = useRef<HTMLHeadingElement>(null)
  const page = Math.max(1, Number(params.get('page')) || 1)
  const routeCriteria = Object.fromEntries([...params].filter(([key]) => key !== 'page'))
  const criteria = Object.fromEntries([...params].filter(([key]) => key !== 'page' && key !== ORIGIN_PARAM))
  const query = criteria.q ?? ''
  const requestCriteria = operation?.family === 'history' ? Object.fromEntries(HISTORY_FILTERS.flatMap((key) => criteria[key] ? [[key, criteria[key]]] : [])) : {}
  const filterKey = new URLSearchParams(requestCriteria).toString()
  const origin = decodeAdministrationOrigin(params.get(ORIGIN_PARAM))
  const sourcePresetId = operation?.renderer === 'role-create' ? params.get('preset') : null
  const operationRequest = operation?.request
  const operationEndpoint = operation?.endpoint
  const malformedSubjectId = Boolean(subjectId && subjectId !== 'new' && !UUID_PATTERN.test(subjectId))
  const malformedSourcePresetId = Boolean(sourcePresetId && !UUID_PATTERN.test(sourcePresetId))
  const requestKey = `${family}:${subjectId ?? ''}:${sourcePresetId ?? ''}:${page}:${filterKey}`

  const projectRoute = (route: AdministrationRouteState) => {
    const search = new URLSearchParams(route.criteria)
    if (route.page > 1) search.set('page', String(route.page))
    const suffix = route.subjectId ? `/${route.subjectId}${route.mode === 'edit' ? '/edit' : ''}` : ''
    navigate(`/access/${route.family}${suffix}${search.size ? `?${search}` : ''}`, { replace: true })
  }

  const collectionRoute: AdministrationRouteState = { family: operation?.family ?? 'users', criteria, page }
  const detailRoute = (id: string): AdministrationRouteState => ({ family: operation!.family, criteria: { [ORIGIN_PARAM]: encodeAdministrationOrigin(collectionRoute) }, page: 1, subjectId: id })
  const currentRoute: AdministrationRouteState = { family: operation?.family ?? 'users', criteria: routeCriteria, page, subjectId, mode }
  const transitionRoute = (route: AdministrationRouteState, from: AdministrationRouteState): AdministrationRouteState => ({ ...route, criteria: { ...route.criteria, [ORIGIN_PARAM]: encodeAdministrationOrigin(from) } })
  const recover = useEffectEvent((reason: 'missing' | 'denied') => {
    if (!operation) return
    if (reason === 'missing') projectRoute(origin ?? { family: operation.family, criteria: {}, page: 1 })
    else projectRoute({ family: operation.family, criteria: {}, page: 1 })
  })
  const recoverEmptyPage = useEffectEvent((total: number, pageSize: number) => {
    if (operation) projectRoute({ family: operation.family, criteria, page: Math.max(1, Math.ceil(total / pageSize)) })
  })

  useEffect(() => {
    const endpoint = sourcePresetId ? '/access/role-presets' : operationEndpoint
    if (!endpoint || malformedSubjectId || malformedSourcePresetId || (operationRequest === 'none' && !sourcePresetId)) return
    const controller = new AbortController()
    const request = ++generation.current
    const requestCriteria = Object.fromEntries(new URLSearchParams(filterKey))
    const search = new URLSearchParams({ page: String(page), page_size: '50', ...requestCriteria })
    const path = sourcePresetId ? `${endpoint}/${sourcePresetId}` : operationRequest === 'detail' ? `${endpoint}/${subjectId}` : `${endpoint}?${search}`
    void httpJson<Record<string, unknown> | Page>(path, { signal: controller.signal, recoverAccessDenied: true })
      .then((result) => {
        if (request !== generation.current) return
        const resultPage: Page = operationRequest === 'detail' || sourcePresetId
          ? { items: [result as Record<string, unknown>], page: 1, page_size: 1, total: 1 }
          : result as Page
        if (resultPage.items.length === 0 && resultPage.total > 0 && page > 1) {
          recoverEmptyPage(resultPage.total, resultPage.page_size)
        }
        else { setFailure(null); setData({ key: requestKey, page: resultPage }) }
      })
      .catch((error: unknown) => {
        if (isApiError(error) && error.kind === 'aborted') return
        if (request !== generation.current) return
        if (isApiError(error) && error.status === 404 && (operationRequest === 'detail' || sourcePresetId)) recover('missing')
        else if (isApiError(error) && error.status === 403) { setData(null); recover('denied') }
        else setFailure({ key: requestKey, message: 'The administration data is unavailable.' })
      })
    return () => controller.abort()
  }, [filterKey, malformedSourcePresetId, malformedSubjectId, operation?.family, operationEndpoint, operationRequest, page, reload, requestKey, sourcePresetId, subjectId])

  useEffect(() => {
    if (data?.key === requestKey) heading.current?.focus()
  }, [data?.key, requestKey])

  if (!operation || !family) return <Navigate to={family && ['users', 'roles', 'presets', 'scopes', 'history'].includes(family) ? `/access/${family}` : '/access/users'} replace />
  if (malformedSubjectId || malformedSourcePresetId) return <Navigate to={`/access/${operation.family}`} replace />
  if (operation.renderer === 'role-create' && (!sourcePresetId || data?.key === requestKey)) return <AdministrationShell route={currentRoute} origin={origin} navigate={projectRoute}>
    {({ setDraftState, requestDeparture }) => <Stack gap="lg"><Group justify="space-between"><Title ref={heading} tabIndex={-1} order={1}>Create role</Title><Button variant="subtle" onClick={(event) => { event.currentTarget.focus(); requestDeparture() }}>Cancel</Button></Group><RoleWorkflow initialDraft={sourcePresetId ? { roleCode: `${text(data?.page.items[0]?.preset_code)}-copy`, roleName: `${text(data?.page.items[0]?.preset_name)} copy`, description: text(data?.page.items[0]?.description) || null, permissions: presetPermissions(data?.page.items[0] ?? {}) } : undefined} onDirtyChange={(dirty) => setDraftState('new role', dirty)} /></Stack>}
  </AdministrationShell>
  if (operation.renderer === 'role-create') return <Stack align="center" py="xl"><Loader aria-label="Loading administration" /></Stack>
  if (operation.renderer === 'preset-create') return <AdministrationShell route={currentRoute} origin={origin} navigate={projectRoute}>
    {({ setDraftState, requestDeparture }) => <Stack gap="lg"><Group justify="space-between"><Title ref={heading} tabIndex={-1} order={1}>Create preset</Title><Button variant="subtle" onClick={(event) => { event.currentTarget.focus(); requestDeparture() }}>Cancel</Button></Group><PresetWorkflow onDirtyChange={(dirty) => setDraftState('new preset', dirty)} /></Stack>}
  </AdministrationShell>
  if (operation.request === 'none') return <Alert>{operation.title} is not available yet.</Alert>
  const currentPage = data?.key === requestKey ? data.page : null
  const currentFailure = failure?.key === requestKey ? failure.message : null
  const label = (item: Record<string, unknown>) => text(item[operation.label!]) || text(item.scope_code) || text(item.audit_id)
  const shown = (currentPage?.items ?? []).filter((item) => label(item).toLocaleLowerCase().includes(query.toLocaleLowerCase()))
  const update = (key: string, value: string) => setParams((old) => { const next = new URLSearchParams(old); if (value) next.set(key, value); else next.delete(key); if (key !== 'page' && key !== 'q') next.set('page', '1'); return next })
  const refreshScopes = async () => { setReload((current) => current + 1) }
  const item = currentPage?.items[0] ?? {}
  const preset = { presetId: subjectId ?? '', presetCode: text(item.preset_code), presetName: text(item.preset_name), description: text(item.description) || null, isActive: item.is_active === true, version: typeof item.version === 'number' ? item.version : 0, permissions: presetPermissions(item) }
  const role = { roleId: subjectId ?? '', roleCode: text(item.role_code), roleName: text(item.role_name), description: text(item.description) || null, isActive: item.is_active === true, version: typeof item.version === 'number' ? item.version : 0, permissions: presetPermissions(item) }

  return <AdministrationShell route={currentRoute} origin={origin} navigate={projectRoute}>
    {({ requestDeparture, setDraftState }) => currentFailure ? <Alert role="status">{currentFailure}</Alert> : !currentPage ? <Stack align="center" py="xl"><Loader aria-label="Loading administration" /></Stack> :
      <Stack gap="lg"><Group justify="space-between"><Title ref={heading} tabIndex={-1} order={1}>{operation.title}</Title>{!subjectId && (operation.family === 'roles' || operation.family === 'presets') ? <Button onClick={() => projectRoute(transitionRoute({ family: operation.family, criteria: {}, page: 1, subjectId: 'new' }, collectionRoute))}>Create {operation.family === 'roles' ? 'role' : 'preset'}</Button> : null}</Group>
          {subjectId ? <><Group><Button variant="subtle" onClick={(event) => { event.currentTarget.focus(); requestDeparture() }}>Back to {operation.title}</Button>{(operation.family === 'roles' || operation.family === 'presets') && !operation.renderer ? <Button onClick={(event) => { event.currentTarget.focus(); requestDeparture(transitionRoute({ family: operation.family, criteria: {}, page: 1, subjectId, mode: 'edit' }, currentRoute)) }}>Edit {operation.family === 'roles' ? 'role' : 'preset'}</Button> : null}</Group><Card withBorder><Text>{label(item)}</Text></Card>
            {operation.family === 'users' && typeof item.version === 'number' ? <UserRoleReplacementPanel key={`${subjectId}:${item.version}`} userId={subjectId} version={item.version} roleIds={Array.isArray(item.roles) ? item.roles.flatMap((assignedRole) => typeof assignedRole === 'object' && assignedRole && typeof (assignedRole as Record<string, unknown>).role_id === 'string' ? [(assignedRole as Record<string, string>).role_id] : []) : []} /> : null}
            {operation.renderer === 'role-edit' ? <RoleWorkflow role={role} onDirtyChange={(dirty) => setDraftState(`role ${role.roleName || subjectId}`, dirty)} /> : null}
            {operation.family === 'presets' ? operation.renderer === 'preset-edit' ? <PresetWorkflow preset={preset} onDirtyChange={(dirty) => setDraftState(`preset ${preset.presetName || subjectId}`, dirty)} /> : <PresetDetailWorkflows preset={preset} onDirtyChange={(dirty) => setDraftState(`preset copy ${preset.presetName || subjectId}`, dirty)} onStartAdjustable={() => requestDeparture(transitionRoute({ family: 'roles', criteria: { preset: subjectId }, page: 1, subjectId: 'new' }, currentRoute))} /> : null}</> : <>
          {operation.family === 'history' ? <Group grow>{HISTORY_FILTERS.map((key) => <TextInput key={key} label={key.split('_').map((part) => part[0].toUpperCase() + part.slice(1)).join(' ')} value={params.get(key) ?? ''} onChange={(event) => update(key, event.currentTarget.value)} />)}</Group> : <TextInput label="Filter loaded page" value={query} onChange={(event) => update('q', event.currentTarget.value)} description="Filters this loaded page only." />}
          {operation.family === 'scopes' ? <ScopeRegistrationPanel refreshScopes={refreshScopes} /> : null}
          {currentPage.items.length === 0 ? <Alert role="status">No records found.</Alert> : shown.length === 0 ? <Alert role="status">No matches on this loaded page.</Alert> : operation.family === 'history' ? <Table style={{ minWidth: 500 }}><Table.Thead><Table.Tr>{['Actor', 'Time', 'Reason', 'Subject', 'Change kind'].map((heading) => <Table.Th key={heading}>{heading}</Table.Th>)}</Table.Tr></Table.Thead><Table.Tbody>{shown.map((item) => <Table.Tr key={text(item.audit_id)}>{auditValues(item).map((value, index) => <Table.Td key={index}>{value}</Table.Td>)}</Table.Tr>)}</Table.Tbody></Table> : <Table style={{ minWidth: 500 }}><Table.Thead><Table.Tr><Table.Th>Identity</Table.Th><Table.Th>Status</Table.Th></Table.Tr></Table.Thead><Table.Tbody>{shown.map((item) => { const id = operation.id ? text(item[operation.id]) : ''; const detailAllowed = id && operation.family !== 'scopes'; return <Table.Tr key={id || text(item.audit_id)}><Table.Td>{detailAllowed ? <Button variant="transparent" onClick={() => projectRoute(detailRoute(id))}>{label(item)}</Button> : label(item)}</Table.Td><Table.Td>{operation.family === 'scopes' && id && typeof item.version === 'number' && typeof item.is_active === 'boolean' ? <ScopeStatusControl scopeId={id} version={item.version} isActive={item.is_active} refreshScopes={refreshScopes} /> : typeof item.is_active === 'boolean' ? item.is_active ? 'Active' : 'Inactive' : text(item.occurred_at)}</Table.Td></Table.Tr> })}</Table.Tbody></Table>}
          {currentPage.total > 50 ? <Pagination value={page} onChange={(next) => update('page', String(next))} total={Math.ceil(currentPage.total / 50)} getControlProps={(control) => control === 'next' ? { 'aria-label': 'Next page' } : {}} /> : null}
        </>}
      </Stack>}
  </AdministrationShell>
}

export function AdministrationEditPage({ family }: { family?: string }) { return <AdministrationPage family={family} mode="edit" /> }
