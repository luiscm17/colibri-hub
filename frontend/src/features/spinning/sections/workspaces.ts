import type { SpinningWorkspace } from '../workspaces'

const sectionWorkspaces = new Set<SpinningWorkspace>(['preparation', 'ringSpinning', 'bobbinWinding', 'twisting'])

export function isSectionWorkspace(workspace: SpinningWorkspace): boolean {
  return sectionWorkspaces.has(workspace)
}
