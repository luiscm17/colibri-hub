import { describe, expect, it } from 'vitest'
import { auditValues, scopeRegistrationRequest, scopeStatusRequest, unregisteredDefinitions } from './history'

describe('scope and history boundaries', () => {
  it('registers only unregistered recognized definitions and changes lifecycle with the collection version', () => {
    const definitions = [
      { definitionKey: 'warehouse.raw', isRegistered: false },
      { definitionKey: 'access', isRegistered: true },
    ]

    expect(unregisteredDefinitions(definitions)).toEqual([{ definitionKey: 'warehouse.raw', isRegistered: false }])
    expect(scopeRegistrationRequest('warehouse.raw')).toEqual({ path: '/access/scopes', method: 'POST', body: { definition_key: 'warehouse.raw', reason: '' } })
    expect(scopeStatusRequest({ scopeId: 'scope-1', version: 7 }, false)).toEqual({ path: '/access/scopes/scope-1/status', method: 'PATCH', body: { is_active: false, expected_version: 7, reason: '' } })
  })

  it('renders only the returned audit facts without inventing detail or before-after values', () => {
    expect(auditValues({
      performed_by_user_id: 'admin-1', occurred_at: '2026-08-13T10:00:00Z', reason: 'Scheduled review', subject_id: 'scope-1', change_kind: 'scope_deactivated', before_values: 'hidden',
    })).toEqual(['admin-1', '2026-08-13T10:00:00Z', 'Scheduled review', 'scope-1', 'scope_deactivated'])
  })
})
