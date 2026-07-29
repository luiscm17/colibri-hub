import { useCallback, useMemo, useState } from 'react'
import type { DeliveryGridRow, DeliveryOutcome } from '../model/delivery'
import { applyDeliveryOutcomes, createDeliveryGridState, deliverySnapshot, feedbackFor, parseDeliveryPaste, planDeliveryPaste, readyForDelivery, resetDeliveryGrid, updateDeliveryRows, type DeliveryColumn } from '../model/deliveryGrid'

export function useBaleDelivery() {
  const [deliveryDate, setDeliveryDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [state, setState] = useState(createDeliveryGridState)
  const feedback = useMemo(() => feedbackFor(state.rows), [state.rows])
  const updateRows = useCallback((rows: readonly DeliveryGridRow[]) => setState(current => updateDeliveryRows(current, rows)), [])
  const paste = useCallback((rowId: string, column: DeliveryColumn, text: string) => {
    const plan = planDeliveryPaste(state, state.rows.findIndex(row => row.rowId === rowId), column, parseDeliveryPaste(text))
    if (plan.accepted) setState(plan.state)
    return plan
  }, [state])
  const applyOutcomes = useCallback((outcomes: readonly DeliveryOutcome[]) => setState(current => ({ ...current, rows: applyDeliveryOutcomes(current.rows, outcomes) })), [])
  const reset = useCallback(() => { setDeliveryDate(new Date().toISOString().slice(0, 10)); setState(current => resetDeliveryGrid(current)) }, [])
  return { deliveryDate, setDeliveryDate, rows: state.rows, feedback, updateRows, paste, applyOutcomes, reset, isReady: readyForDelivery(deliveryDate, state.rows), snapshot: () => deliverySnapshot(deliveryDate, state.rows) }
}
