export const spinningWorkspaces = {
  preparation: 'Preparación',
  ringSpinning: 'Hilatura de anillos',
  bobbinWinding: 'Bobinado de bobinas',
  twisting: 'Retorcido',
  skeining: 'Formación de madejas',
  quality: 'Calidad del proceso',
  waste: 'Desperdicio',
  consolidated: 'Informes consolidados',
} as const

export type SpinningWorkspace = keyof typeof spinningWorkspaces
