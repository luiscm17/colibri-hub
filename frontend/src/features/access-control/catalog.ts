import type { AccessRequirement } from './access-controller'

type ProtectedPath = Readonly<{ path: string; requirement: AccessRequirement }>

const anyReadOrWrite = (scope: string): AccessRequirement => ({
  anyOf: [{ action: 'read', scope }, { action: 'write', scope }],
})

export const ACCESS_CATALOG: Readonly<Record<string, AccessRequirement>> = {
  '/warehouse/bales': { action: 'read', scope: 'warehouse.raw_materials' },
  '/warehouse/bales/reception': { action: 'write', scope: 'warehouse.raw_materials' },
  '/warehouse/bales/stock': { action: 'read', scope: 'warehouse.raw_materials' },
  '/warehouse/bales/delivery': { action: 'write', scope: 'warehouse.raw_materials' },
  '/warehouse/identity': { action: 'read', scope: 'warehouse.finished_products' },
  '/warehouse/finished-product': { action: 'read', scope: 'warehouse.finished_products' },
  '/warehouse/supplies': { action: 'read', scope: 'warehouse.production_supplies' },
  '/spinning/preparation': { action: 'read', scope: 'yarn_spinning.section.preparation' },
  '/spinning/ring-spinning': { action: 'read', scope: 'yarn_spinning.section.ring_spinning' },
  '/spinning/bobbin-winding': { action: 'read', scope: 'yarn_spinning.section.bobbin_winding' },
  '/spinning/twisting': { action: 'read', scope: 'yarn_spinning.section.twisting' },
  '/spinning/skeining': { action: 'read', scope: 'yarn_spinning.section.skeining' },
  '/spinning/quality': anyReadOrWrite('yarn_spinning.process_quality'),
  '/spinning/waste': anyReadOrWrite('yarn_spinning.waste'),
  '/spinning/consolidated': { action: 'read', scope: 'transversal.consolidated_dashboard' },
  '/lots': { action: 'read', scope: 'lot_processing' },
  '/lots/queue': { action: 'read', scope: 'lot_processing' },
  '/lots/detail': { action: 'read', scope: 'lot_processing' },
  '/lots/inventory': anyReadOrWrite('lot_processing.stage.inventory'),
  '/lots/dyeing': anyReadOrWrite('lot_processing.stage.dyeing'),
  '/lots/drying': anyReadOrWrite('lot_processing.stage.drying'),
  '/lots/winding': anyReadOrWrite('lot_processing.stage.winding'),
  '/lots/bagging': anyReadOrWrite('lot_processing.stage.bagging'),
  '/lots/quality': anyReadOrWrite('lot_processing.stage.quality'),
  '/access/users': { action: 'manage_access', scope: 'access_control' },
  '/access/roles': { action: 'manage_access', scope: 'access_control' },
  '/access/presets': { action: 'manage_access', scope: 'access_control' },
  '/access/scopes': { action: 'manage_access', scope: 'access_control' },
  '/access/history': { action: 'manage_access', scope: 'access_control' },
}

export const CORRECTION_REQUIREMENTS = {
  edit: { action: 'edit', scope: 'warehouse.raw_materials' },
  editOutsideWindow: { action: 'edit_outside_window', scope: 'warehouse.raw_materials' },
} as const satisfies Readonly<Record<string, AccessRequirement>>

const catalogPaths: readonly ProtectedPath[] = Object.entries(ACCESS_CATALOG).map(([path, requirement]) => ({ path, requirement }))

export function requirementForPath(pathname: string): AccessRequirement | null {
  const path = pathname.split('?')[0] ?? pathname
  return catalogPaths.find((item) => item.path === path)?.requirement ?? null
}
