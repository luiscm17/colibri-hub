export const spinningWorkspaces = {
    preparation: "Preparación",
    ringSpinning: "Continuas",
    bobbinWinding: "Bobinados",
    twisting: "Retorcedoras",
    skeining: "Madejeras",
    quality: "Control de Calidad",
    waste: "Desperdicio",
    consolidated: "Informes consolidados",
} as const;

export type SpinningWorkspace = keyof typeof spinningWorkspaces;
