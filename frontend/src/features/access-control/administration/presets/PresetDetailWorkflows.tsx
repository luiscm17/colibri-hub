import { useEffect, useEffectEvent, useState } from 'react'
import { PresetCopyPanel } from './PresetCopyPanel'
import { PresetWorkflow, type PresetWorkflowPreset } from './PresetWorkflow'

export function PresetDetailWorkflows({ preset, onDirtyChange }: { preset: PresetWorkflowPreset; onDirtyChange(dirty: boolean): void }) {
  const reportDirty = useEffectEvent(onDirtyChange)
  const [presetDirty, setPresetDirty] = useState(false)
  const [copyDirty, setCopyDirty] = useState(false)
  useEffect(() => { reportDirty(presetDirty || copyDirty) }, [copyDirty, presetDirty])
  return <><PresetWorkflow preset={preset} onDirtyChange={setPresetDirty} /><PresetCopyPanel preset={preset} onDirtyChange={setCopyDirty} /></>
}
