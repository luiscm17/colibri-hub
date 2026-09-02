import type { SpinningWorkspace } from '../workspaces'

const sectionWorkspaces = new Set<SpinningWorkspace>(['preparation', 'ringSpinning', 'bobbinWinding', 'twisting', 'skeining'])

export function isSectionWorkspace(workspace: SpinningWorkspace): boolean {
  return sectionWorkspaces.has(workspace)
}
