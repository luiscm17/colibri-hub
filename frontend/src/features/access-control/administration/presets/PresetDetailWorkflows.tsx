import { useEffect, useEffectEvent, useState } from 'react'
import { PresetCopyPanel } from './PresetCopyPanel'
import type { PresetWorkflowPreset } from './PresetWorkflow'

export function PresetDetailWorkflows({ preset, onDirtyChange, onStartAdjustable }: { preset: PresetWorkflowPreset; onDirtyChange(dirty: boolean): void; onStartAdjustable(): void }) {
  const reportDirty = useEffectEvent(onDirtyChange)
  const [copyDirty, setCopyDirty] = useState(false)
  useEffect(() => { reportDirty(copyDirty) }, [copyDirty])
  return <PresetCopyPanel preset={preset} onDirtyChange={setCopyDirty} onStartAdjustable={onStartAdjustable} />
}
