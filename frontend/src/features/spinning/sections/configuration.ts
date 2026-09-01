import type { SpinningWorkspace } from '../workspaces'
import type { ProductionDischargeCatalog } from '../integration/contracts'

export type SectionGridConfig = Readonly<{
  discharge: boolean
  progress: boolean
}>

const configurations: Readonly<Partial<Record<SpinningWorkspace, SectionGridConfig>>> = {
  preparation: { discharge: true, progress: true },
  ringSpinning: { discharge: true, progress: true },
  bobbinWinding: { discharge: true, progress: false },
  twisting: { discharge: true, progress: true },
}

export function sectionGridConfig(workspace: SpinningWorkspace): SectionGridConfig {
  return configurations[workspace] ?? { discharge: false, progress: false }
}

export function rovingTitleMachineIds(catalog: ProductionDischargeCatalog): readonly string[] {
  return catalog.rovingTitleApplicableMachineIds.filter(machineId => catalog.applicableMachineIds.includes(machineId))
}

export function hasRovingTitleInput(catalog: ProductionDischargeCatalog): boolean {
  return rovingTitleMachineIds(catalog).length > 0
}
