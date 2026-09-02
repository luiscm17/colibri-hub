import type { SpinningWorkspace } from '../workspaces'

export type SectionGridConfig = Readonly<{
  discharge: boolean
  progress: boolean
}>

const configurations: Readonly<Partial<Record<SpinningWorkspace, SectionGridConfig>>> = {
  preparation: { discharge: true, progress: false },
  ringSpinning: { discharge: true, progress: true },
  bobbinWinding: { discharge: true, progress: false },
  twisting: { discharge: true, progress: true },
  skeining: { discharge: true, progress: false },
}

export function sectionGridConfig(workspace: SpinningWorkspace): SectionGridConfig {
  return configurations[workspace] ?? { discharge: false, progress: false }
}
