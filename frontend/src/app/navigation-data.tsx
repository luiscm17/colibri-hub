import type { ReactNode } from 'react'
import {
  IconBuildingWarehouse,
  IconSpiral,
  IconStack3,
  IconReport,
  IconSettings,
  IconPackage,
  IconBarcode,
  IconTruckDelivery,
  IconPackageImport,
  IconBoxSeam,
  IconHistory,
  IconDashboard,
  IconClipboardList,
  IconChartBar,
  IconTrash,
  IconSitemap,
  IconListDetails,
  IconFileAnalytics,
  IconRoute,
} from '@tabler/icons-react'

export interface NavItem {
  label: string
  path?: string
  icon?: ReactNode
  resourceType?: string
  children?: NavItem[]
}

export const navData: NavItem[] = [
  {
    label: 'Almacén',
    icon: <IconBuildingWarehouse size={18} />,
    resourceType: 'warehouse',
    children: [
      { label: 'Gestión de fardos', path: '/warehouse/bales', icon: <IconPackage size={16} />, resourceType: 'warehouse:bales' },
      { label: 'Stock de fardos', path: '/warehouse/bales/stock', icon: <IconHistory size={16} />, resourceType: 'warehouse:bales' },
      { label: 'Entrega de fardos', path: '/warehouse/bales/delivery', icon: <IconTruckDelivery size={16} />, resourceType: 'warehouse:bales' },
      { label: 'Identidad de producción', path: '/warehouse/identity', icon: <IconBarcode size={16} />, resourceType: 'warehouse:identity' },
      { label: 'Producto terminado', path: '/warehouse/finished-product', icon: <IconPackageImport size={16} />, resourceType: 'warehouse:finished-product' },
      { label: 'Insumos', path: '/warehouse/supplies', icon: <IconBoxSeam size={16} />, resourceType: 'warehouse:supplies' },
    ],
  },
  {
    label: 'Hilatura',
    icon: <IconSpiral size={18} />,
    resourceType: 'spinning',
    children: [
      { label: 'Dashboard por sección', path: '/spinning/dashboard', icon: <IconDashboard size={16} />, resourceType: 'spinning:dashboard' },
      { label: 'Descargas', path: '/spinning/unloads', icon: <IconClipboardList size={16} />, resourceType: 'spinning:unloads' },
      { label: 'Avance', path: '/spinning/progress', icon: <IconChartBar size={16} />, resourceType: 'spinning:progress' },
      { label: 'Calidad de proceso', path: '/spinning/quality', icon: <IconSitemap size={16} />, resourceType: 'spinning:quality' },
      { label: 'Desperdicio', path: '/spinning/waste', icon: <IconTrash size={16} />, resourceType: 'spinning:waste' },
      { label: 'Disponibilidad de madejas', path: '/spinning/skeins', icon: <IconStack3 size={16} />, resourceType: 'spinning:skeins' },
      { label: 'Consolidado por turno', path: '/spinning/consolidated', icon: <IconFileAnalytics size={16} />, resourceType: 'spinning:consolidated' },
    ],
  },
  {
    label: 'Proceso por Lotes',
    icon: <IconStack3 size={18} />,
    resourceType: 'lots',
    children: [
      { label: 'Cola de lotes', path: '/lots/queue', icon: <IconListDetails size={16} />, resourceType: 'lots:queue' },
      { label: 'Detalle del lote', path: '/lots/detail', icon: <IconRoute size={16} />, resourceType: 'lots:detail' },
    ],
  },
  {
    label: 'Reportes',
    icon: <IconReport size={18} />,
    resourceType: 'reports',
    children: [
      { label: 'Consolidado diario', path: '/reports/daily', icon: <IconFileAnalytics size={16} />, resourceType: 'reports:daily' },
      { label: 'Producción vs plan', path: '/reports/production', icon: <IconChartBar size={16} />, resourceType: 'reports:production' },
      { label: 'Trazabilidad de lote', path: '/reports/traceability', icon: <IconRoute size={16} />, resourceType: 'reports:traceability' },
    ],
  },
  {
    label: 'Admin',
    icon: <IconSettings size={18} />,
    resourceType: 'admin',
    children: [{ label: 'Datos maestros', path: '/admin/master-data', icon: <IconSettings size={16} />, resourceType: 'admin:master-data' }],
  },
]
