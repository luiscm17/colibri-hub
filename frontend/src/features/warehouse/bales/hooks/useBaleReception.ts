import { useCallback, useMemo, useState } from 'react'
import type { ReceptionHeader, ReceptionGridRow } from '../model/reception'
import {
  createReceptionGridState,
  createReceptionSubmissionSnapshot,
  getReceptionFeedback,
  isReceptionReadyForSubmission,
  parseSpreadsheetPaste,
  planReceptionPaste,
  resetReceptionGrid,
  summarizeReception,
  updateReceptionRows,
  validateReceptionHeader,
  type ReceptionEditableColumn,
} from '../model/receptionGrid'

const EMPTY_HEADER: ReceptionHeader = {
  shipmentNumber: '',
  receptionDate: '',
  providerName: '',
}

export function useBaleReception() {
  const [header, setHeader] = useState<ReceptionHeader>(EMPTY_HEADER)
  const [gridState, setGridState] = useState(createReceptionGridState)

  const feedback = useMemo(() => getReceptionFeedback(gridState.rows), [gridState.rows])
  const summary = useMemo(() => summarizeReception(gridState.rows), [gridState.rows])
  const headerErrors = useMemo(() => validateReceptionHeader(header), [header])
  const isReadyForSubmission = useMemo(
    () => isReceptionReadyForSubmission(header, gridState.rows),
    [header, gridState.rows],
  )

  const updateHeader = useCallback((field: keyof ReceptionHeader, value: string) => {
    setHeader(currentHeader => ({ ...currentHeader, [field]: value }))
  }, [])

  const updateRows = useCallback((rows: readonly ReceptionGridRow[]) => {
    setGridState(currentState => updateReceptionRows(currentState, rows))
  }, [])

  const paste = useCallback((rowId: string, column: ReceptionEditableColumn, clipboardText: string) => {
    const rowIndex = gridState.rows.findIndex(row => row.rowId === rowId)
    const plan = planReceptionPaste(gridState, rowIndex, column, parseSpreadsheetPaste(clipboardText))
    if (plan.accepted) {
      setGridState(plan.state)
    }
    return plan
  }, [gridState])

  const reset = useCallback(() => {
    setHeader(EMPTY_HEADER)
    setGridState(currentState => resetReceptionGrid(currentState))
  }, [])

  const createSubmissionSnapshot = useCallback(
    () => createReceptionSubmissionSnapshot(header, gridState.rows),
    [header, gridState.rows],
  )

  return {
    header,
    headerErrors,
    rows: gridState.rows,
    feedback,
    summary,
    updateHeader,
    updateRows,
    paste,
    reset,
    createSubmissionSnapshot,
    isReadyForSubmission,
  }
}
