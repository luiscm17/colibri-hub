import { ApiError, isApiError, type ApiFieldError } from '@/api/httpError'

export type BaleApiErrorKind = 'aborted' | 'conflict' | 'not_found' | 'validation' | 'unavailable' | 'unexpected'

export class BaleApiError extends Error {
  readonly kind: BaleApiErrorKind
  readonly fields: readonly ApiFieldError[]

  constructor(kind: BaleApiErrorKind, message: string, fields: readonly ApiFieldError[] = []) {
    super(message)
    this.name = 'BaleApiError'
    this.kind = kind
    this.fields = fields
  }
}

export function toBaleApiError(error: unknown): BaleApiError {
  if (!isApiError(error)) return new BaleApiError('unexpected', 'The request could not be completed.')
  return new BaleApiError(errorKind(error), error.message, error.fields)
}

function errorKind(error: ApiError): BaleApiErrorKind {
  if (error.kind === 'aborted') return 'aborted'
  if (error.kind === 'network' || (error.status !== undefined && error.status >= 500)) return 'unavailable'
  if (error.status === 409) return 'conflict'
  if (error.status === 404) return 'not_found'
  if (error.status === 422) return 'validation'
  return 'unexpected'
}
