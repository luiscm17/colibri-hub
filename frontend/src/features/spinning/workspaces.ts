export const spinningWorkspaces = {
  preparation: 'Preparation',
  ringSpinning: 'Ring Spinning',
  bobbinWinding: 'Bobbin Winding',
  twisting: 'Twisting',
  skeining: 'Skeining',
  quality: 'Process Quality',
  waste: 'Waste',
  consolidated: 'Consolidated reporting',
} as const

export type SpinningWorkspace = keyof typeof spinningWorkspaces
