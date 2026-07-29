import { useCallback, useEffect, useRef, useState } from 'react'
import { getBaleDetail, getStockSummary } from '../api/baleApi'
import { BaleApiError } from '../api/baleApi.errors'
import type { BaleDetail, StockFilters, StockSummary } from '../model/stock'

type RequestState = 'idle' | 'loading' | 'error'

const initialFilters: StockFilters = {}

export function useBaleStock() {
  const [summary, setSummary] = useState<StockSummary>()
  const [summaryState, setSummaryState] = useState<RequestState>('loading')
  const [summaryError, setSummaryError] = useState<string>()
  const [appliedFilters, setAppliedFilters] = useState<StockFilters>(initialFilters)
  const [detail, setDetail] = useState<BaleDetail>()
  const [detailState, setDetailState] = useState<RequestState>('idle')
  const [detailError, setDetailError] = useState<string>()
  const [detailNotFound, setDetailNotFound] = useState(false)
  const summaryController = useRef<AbortController | undefined>(undefined)
  const detailController = useRef<AbortController | undefined>(undefined)
  const summaryRequestId = useRef(0)
  const detailRequestId = useRef(0)

  const loadSummary = useCallback(async (filters: StockFilters) => {
    summaryController.current?.abort()
    const controller = new AbortController()
    summaryController.current = controller
    const requestId = ++summaryRequestId.current
    setSummaryState('loading')
    setSummaryError(undefined)
    try {
      const nextSummary = await getStockSummary(filters, controller.signal)
      if (requestId !== summaryRequestId.current) return
      setSummary(nextSummary)
      setAppliedFilters(filters)
      setSummaryState('idle')
    } catch (error) {
      if (requestId !== summaryRequestId.current || isAborted(error)) return
      setSummaryState('error')
      setSummaryError('No se pudo actualizar el stock. Intentá nuevamente.')
    }
  }, [])

  const lookupDetail = useCallback(async (shipmentNumber: string, baleNumber: string) => {
    detailController.current?.abort()
    const controller = new AbortController()
    detailController.current = controller
    const requestId = ++detailRequestId.current
    setDetailState('loading')
    setDetailError(undefined)
    setDetailNotFound(false)
    setDetail(undefined)
    try {
      const nextDetail = await getBaleDetail(shipmentNumber, baleNumber, controller.signal)
      if (requestId !== detailRequestId.current) return
      setDetail(nextDetail)
      setDetailState('idle')
    } catch (error) {
      if (requestId !== detailRequestId.current || isAborted(error)) return
      setDetailState('idle')
      if (error instanceof BaleApiError && error.kind === 'not_found') {
        setDetailNotFound(true)
      } else {
        setDetailError('No se pudo consultar el fardo. Intentá nuevamente.')
      }
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => void loadSummary(initialFilters), 0)
    return () => {
      window.clearTimeout(timer)
      summaryController.current?.abort()
      detailController.current?.abort()
    }
  }, [loadSummary])

  return {
    summary,
    summaryState,
    summaryError,
    appliedFilters,
    detail,
    detailState,
    detailError,
    detailNotFound,
    loadSummary,
    lookupDetail,
  }
}

function isAborted(error: unknown) {
  return error instanceof BaleApiError && error.kind === 'aborted'
}
