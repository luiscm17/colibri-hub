import type { SpinningWorkspace } from '../workspaces'

export type SectionGridConfig = Readonly<{
  discharge: boolean
}>

const configurations: Readonly<Partial<Record<SpinningWorkspace, SectionGridConfig>>> = {
  preparation: { discharge: true },
  ringSpinning: { discharge: true },
  bobbinWinding: { discharge: true },
  twisting: { discharge: true },
}

export function sectionGridConfig(workspace: SpinningWorkspace): SectionGridConfig {
  return configurations[workspace] ?? { discharge: false }
}
